"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — REST API Interface
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Full REST API for programmatic access to AITestSuite v3.
    Enables integration with:
    - CI/CD pipelines (beyond the CLI runner)
    - Enterprise security platforms
    - Custom dashboards and reporting tools
    - Healthcare IT governance systems
    - Third-party audit management tools

ENDPOINTS:
    POST /auth/login          — Authenticate and get token
    POST /auth/logout         — Invalidate session token

    GET  /health              — System health check
    GET  /models              — List supported model providers

    POST /audit/run           — Run a full audit (async)
    GET  /audit/{session_id}  — Get audit status and results
    GET  /audit/list          — List recent audit sessions

    GET  /findings/{session_id} — Get detailed findings
    GET  /report/{session_id}   — Download PDF report

    GET  /threats             — Get latest threat intelligence
    POST /threats/refresh     — Refresh threat feed

    GET  /users               — List users (admin only)
    POST /users               — Create user (admin only)
    DELETE /users/{username}  — Delete user (admin only)

    GET  /audit-log           — Get audit log entries

AUTHENTICATION:
    Bearer token authentication.
    Token obtained via POST /auth/login
    Include in header: Authorization: Bearer <token>

RATE LIMITING:
    10 requests per minute per token for audit runs
    100 requests per minute for other endpoints

USAGE EXAMPLE:
    # Start an audit
    curl -X POST http://localhost:8000/audit/run \
         -H "Authorization: Bearer <token>" \
         -H "Content-Type: application/json" \
         -d '{"model_name": "google/flan-t5-small",
              "model_type": "huggingface",
              "domain": "healthcare",
              "audit_mode": "standard"}'

INSTALL:
    pip install fastapi uvicorn

RUN:
    uvicorn api.rest_api:app --host 0.0.0.0 --port 8000
    OR
    python -m api.rest_api
═══════════════════════════════════════════════════════════
"""

import os
import sys
import time
import uuid
import threading
from typing import Optional

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from core.rbac import get_rbac, Permission
from core.audit_log import get_logger, AuditEvent

# ── Pydantic models ───────────────────────────────────────────────────────

if HAS_FASTAPI:

    class LoginRequest(BaseModel):
        username: str
        password: str

    class AuditRequest(BaseModel):
        model_name:  str             = "google/flan-t5-small"
        model_type:  str             = "huggingface"
        api_key:     Optional[str]   = None
        domain:      str             = "general"
        audit_mode:  str             = "standard"
        runs_per_test: int           = 5
        auditor:     str             = "API User"

    class CreateUserRequest(BaseModel):
        username: str
        password: str
        role:     str

    # ── In-memory job store ────────────────────────────────────────────────
    _audit_jobs = {}   # session_id -> {status, findings, verdict, error}

    # ── Background audit worker ───────────────────────────────────────────

    def _run_audit_background(session_id, request, auditor_name):
        """Background thread that runs the actual audit."""
        try:
            _audit_jobs[session_id]["status"] = "RUNNING"
            audit_log = get_logger(auditor=auditor_name, session_id=session_id)
            audit_log.log_audit_start(
                request.model_name, request.model_type,
                request.domain, request.audit_mode
            )

            # Load model
            from models.model_adapter import ModelAdapter
            adapter = ModelAdapter(
                model_type=request.model_type,
                model_name=request.model_name,
                api_key=request.api_key
            )
            adapter.load()

            # Build test suite
            from tests.default_tests import DEFAULT_TESTS
            from tests.advanced_tests import ADVANCED_TESTS
            test_suite = list(DEFAULT_TESTS) + list(ADVANCED_TESTS)

            if request.domain == "healthcare":
                from domains.healthcare import HEALTHCARE_TESTS
                test_suite += HEALTHCARE_TESTS
            elif request.domain == "finance":
                from domains.finance import FINANCE_TESTS
                test_suite += FINANCE_TESTS
            elif request.domain in ["legal", "government"]:
                from domains.government_legal import LEGAL_TESTS, GOVERNMENT_TESTS
                test_suite += LEGAL_TESTS + GOVERNMENT_TESTS

            # Run based on mode
            from core.scoring import RiskScorer
            scorer   = RiskScorer()
            findings = []

            if request.audit_mode in ["standard", "full"]:
                from core.automation import BatchRunner
                runner   = BatchRunner(adapter, domain=request.domain if request.domain != "general" else None)
                findings += runner.run_batch(test_suite)

            if request.audit_mode in ["statistical", "full"]:
                from core.statistical_runner import StatisticalRunner
                sr       = StatisticalRunner(adapter, runs_per_test=request.runs_per_test)
                findings += sr.run(test_suite[:10])  # Limit for API responsiveness

            if request.audit_mode in ["multiturn", "full"]:
                from core.statistical_runner import MultiTurnRunner
                from tests.multi_turn_tests import MULTI_TURN_CHAINS
                mtr      = MultiTurnRunner(adapter)
                findings += mtr.run(MULTI_TURN_CHAINS)

            verdict = scorer.verdict(findings)

            # Generate report
            try:
                from core.reporting import ReportGenerator
                generator  = ReportGenerator(output_dir="reports")
                report_path = generator.generate(
                    findings=findings,
                    verdict=verdict,
                    model_info={"model_name": request.model_name, "model_type": request.model_type},
                    domain=request.domain if request.domain != "general" else None,
                    auditor_name=auditor_name
                )
            except Exception:
                report_path = None

            # Log completion
            audit_log.log_audit_complete(
                len(findings),
                sum(1 for f in findings if f.get("passed")),
                sum(1 for f in findings if not f.get("passed")),
                verdict, report_path
            )

            _audit_jobs[session_id].update({
                "status":      "COMPLETE",
                "findings":    findings,
                "verdict":     verdict,
                "report_path": report_path,
                "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })

        except Exception as e:
            _audit_jobs[session_id].update({
                "status": "ERROR",
                "error":  str(e)
            })

    # ── FastAPI app ────────────────────────────────────────────────────────

    app = FastAPI(
        title="AITestSuite v3 — REST API",
        description="AI Security & Governance Audit Platform API — Amarjit Khakh",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS for web UI integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Auth dependency ────────────────────────────────────────────────────

    def get_current_user(authorization: str = Header(None)):
        """Extract and validate Bearer token from request."""
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        token                   = authorization.split(" ", 1)[1]
        rbac                    = get_rbac()
        username, role          = rbac.validate_token(token)
        if not username:
            raise HTTPException(status_code=401, detail="Token expired or invalid")
        return {"username": username, "role": role, "token": token}

    # ── Endpoints ──────────────────────────────────────────────────────────

    @app.get("/health")
    def health():
        """System health check — no authentication required."""
        return {
            "status":    "healthy",
            "toolkit":   "AITestSuite v3",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    @app.post("/auth/login")
    def login(req: LoginRequest):
        """Authenticate and receive a session token."""
        rbac           = get_rbac()
        token, role    = rbac.authenticate(req.username, req.password)
        if not token:
            audit_log = get_logger()
            audit_log.log_user_login(req.username, "unknown", success=False)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        audit_log = get_logger()
        audit_log.log_user_login(req.username, role, success=True)
        return {
            "token":    token,
            "username": req.username,
            "role":     role,
            "expires":  "8 hours"
        }

    @app.post("/auth/logout")
    def logout(user=Depends(get_current_user)):
        """Invalidate the current session token."""
        rbac = get_rbac()
        rbac.logout(user["token"])
        return {"message": "Logged out successfully"}

    @app.get("/models")
    def list_models(user=Depends(get_current_user)):
        """List supported model providers and example models."""
        return {
            "providers": {
                "huggingface": {
                    "description": "Local models via HuggingFace transformers (FREE)",
                    "example_models": ["google/flan-t5-small", "google/flan-t5-base", "microsoft/phi-2"],
                    "requires_api_key": False
                },
                "openai": {
                    "description": "API-based provider",
                    "example_models": ["gpt-3.5-turbo", "gpt-4"],
                    "requires_api_key": True
                },
                "anthropic": {
                    "description": "API-based provider",
                    "example_models": ["claude-haiku-4-5-20251001"],
                    "requires_api_key": True
                },
                "aws_bedrock": {
                    "description": "AWS Bedrock hosted models",
                    "example_models": ["amazon.titan-text-express-v1"],
                    "requires_api_key": True
                },
                "azure_openai": {
                    "description": "Azure OpenAI Service",
                    "example_models": ["gpt-4", "gpt-35-turbo"],
                    "requires_api_key": True
                }
            }
        }

    @app.post("/audit/run")
    def run_audit(
        req: AuditRequest,
        background_tasks: BackgroundTasks,
        user=Depends(get_current_user)
    ):
        """
        Start an audit run asynchronously.
        Returns a session_id to poll for results.
        """
        rbac = get_rbac()

        # Check permission for requested audit mode
        if not rbac.can_run_audit_mode(user["role"], req.audit_mode):
            audit_log = get_logger()
            audit_log.log_permission_deny(user["username"], user["role"], f"run_{req.audit_mode}")
            raise HTTPException(
                status_code=403,
                detail=f"Your role ({user['role']}) cannot run {req.audit_mode} audits"
            )

        session_id = str(uuid.uuid4())
        _audit_jobs[session_id] = {
            "status":       "QUEUED",
            "session_id":   session_id,
            "model_name":   req.model_name,
            "domain":       req.domain,
            "audit_mode":   req.audit_mode,
            "requested_by": user["username"],
            "started_at":   time.strftime("%Y-%m-%d %H:%M:%S"),
            "findings":     None,
            "verdict":      None,
            "error":        None
        }

        background_tasks.add_task(
            _run_audit_background,
            session_id, req, req.auditor or user["username"]
        )

        return {
            "session_id": session_id,
            "status":     "QUEUED",
            "message":    "Audit started. Poll /audit/{session_id} for results."
        }

    @app.get("/audit/{session_id}")
    def get_audit_status(session_id: str, user=Depends(get_current_user)):
        """Get the status and results of an audit run."""
        job = _audit_jobs.get(session_id)
        if not job:
            raise HTTPException(status_code=404, detail="Audit session not found")

        # Return summary without full findings for efficiency
        response = {
            "session_id":   session_id,
            "status":       job["status"],
            "model_name":   job.get("model_name"),
            "domain":       job.get("domain"),
            "audit_mode":   job.get("audit_mode"),
            "requested_by": job.get("requested_by"),
            "started_at":   job.get("started_at"),
            "completed_at": job.get("completed_at"),
            "verdict":      job.get("verdict"),
            "error":        job.get("error"),
        }

        if job.get("findings"):
            findings = job["findings"]
            response["summary"] = {
                "total":    len(findings),
                "passed":   sum(1 for f in findings if f.get("passed")),
                "failed":   sum(1 for f in findings if not f.get("passed")),
                "critical": sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
            }

        return response

    @app.get("/audit/list")
    def list_audits(user=Depends(get_current_user)):
        """List recent audit sessions."""
        return {
            "sessions": [
                {
                    "session_id":   sid,
                    "status":       job["status"],
                    "model_name":   job.get("model_name"),
                    "verdict":      job.get("verdict"),
                    "started_at":   job.get("started_at"),
                    "requested_by": job.get("requested_by"),
                }
                for sid, job in list(_audit_jobs.items())[-20:]  # Last 20
            ]
        }

    @app.get("/findings/{session_id}")
    def get_findings(session_id: str, user=Depends(get_current_user)):
        """Get detailed findings for a completed audit."""
        job = _audit_jobs.get(session_id)
        if not job:
            raise HTTPException(status_code=404, detail="Audit session not found")
        if job["status"] != "COMPLETE":
            raise HTTPException(status_code=400, detail=f"Audit not complete: {job['status']}")

        rbac = get_rbac()
        if not rbac.has_permission(user["role"], Permission.VIEW_FINDINGS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return {
            "session_id": session_id,
            "verdict":    job.get("verdict"),
            "findings":   job.get("findings", [])
        }

    @app.get("/report/{session_id}")
    def download_report(session_id: str, user=Depends(get_current_user)):
        """Download the PDF report for a completed audit."""
        job = _audit_jobs.get(session_id)
        if not job:
            raise HTTPException(status_code=404, detail="Audit session not found")

        report_path = job.get("report_path")
        if not report_path or not os.path.exists(report_path):
            raise HTTPException(status_code=404, detail="Report not generated yet")

        audit_log = get_logger()
        audit_log.log_report_generated(report_path, job.get("verdict"), 0)

        return FileResponse(
            report_path,
            media_type="application/pdf",
            filename=os.path.basename(report_path)
        )

    @app.get("/threats")
    def get_threats(user=Depends(get_current_user)):
        """Get latest AI threat intelligence."""
        from live_research.threat_feed import get_live_feed, get_feed_stats
        items = get_live_feed()
        return {
            "items": items,
            "stats": get_feed_stats(items)
        }

    @app.post("/threats/refresh")
    def refresh_threats(user=Depends(get_current_user)):
        """Refresh the threat intelligence feed."""
        from live_research.threat_feed import get_live_feed
        items = get_live_feed(max_results=10)
        audit_log = get_logger()
        audit_log.log_threat_intel_update("arXiv", len(items))
        return {"message": f"Feed refreshed: {len(items)} items", "items": items}

    @app.get("/users")
    def list_users(user=Depends(get_current_user)):
        """List all users — admin only."""
        rbac = get_rbac()
        if not rbac.has_permission(user["role"], Permission.MANAGE_USERS):
            raise HTTPException(status_code=403, detail="Admin role required")
        return {"users": rbac.get_users()}

    @app.post("/users")
    def create_user(req: CreateUserRequest, user=Depends(get_current_user)):
        """Create a new user — admin only."""
        rbac = get_rbac()
        if not rbac.has_permission(user["role"], Permission.MANAGE_USERS):
            raise HTTPException(status_code=403, detail="Admin role required")
        result = rbac.add_user(req.username, req.password, req.role, created_by=user["username"])
        if result is not True:
            raise HTTPException(status_code=400, detail=result)
        return {"message": f"User {req.username} created with role {req.role}"}

    @app.get("/audit-log")
    def get_audit_log_entries(user=Depends(get_current_user), limit: int = 100):
        """Get recent audit log entries — auditor+ role required."""
        rbac = get_rbac()
        if not rbac.has_permission(user["role"], Permission.VIEW_AUDIT_LOG):
            raise HTTPException(status_code=403, detail="Auditor role or higher required")
        audit_log = get_logger()
        entries = audit_log.get_session_log()
        return {"entries": entries[-limit:], "total": len(entries)}


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not HAS_FASTAPI:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")
        sys.exit(1)
    import uvicorn
    uvicorn.run("api.rest_api:app", host="0.0.0.0", port=8000, reload=False)
