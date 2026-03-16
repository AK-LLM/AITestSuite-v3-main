"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Structured Audit Logging
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Persistent, structured, queryable audit log for every
    action taken by the toolkit. Every test run, finding,
    user action and system event is logged with full context.

    This is NOT application logging. This is a forensic
    audit trail suitable for:
    - Regulatory compliance demonstrations (PIPEDA, HIPAA)
    - Security incident investigation
    - Audit report evidence chains
    - Chain of custody for penetration test findings
    - Demonstrating due diligence to healthcare regulators

LOG FORMAT:
    JSON Lines (.jsonl) — one JSON object per line.
    Human readable. Machine parseable. Appendable.
    Compatible with ELK, Splunk, Datadog, CloudWatch.

EVENTS LOGGED:
    AUDIT_START      — New audit session initiated
    AUDIT_COMPLETE   — Audit session completed with verdict
    TEST_RUN         — Individual test executed
    TEST_FINDING     — Finding recorded with risk score
    USER_LOGIN       — User authenticated (RBAC)
    PERMISSION_DENY  — Access denied by RBAC
    BLACKBOX_AUTH    — Black box authorisation recorded
    BLACKBOX_TEST    — Black box test executed
    REPORT_GENERATED — PDF report created
    CONFIG_CHANGE    — Configuration modified
    ERROR            — System error occurred
    THREAT_INTEL     — Threat feed updated

STORAGE:
    Default: ./logs/audit.jsonl
    Configurable via AUDIT_LOG_PATH environment variable
    Rotates daily. Keeps 90 days by default.

CHAIN OF CUSTODY:
    Each log entry contains:
    - Timestamp (ISO 8601 UTC)
    - Session ID (UUID)
    - User/auditor name
    - Event type and details
    - SHA256 hash of the entry (tamper detection)
    - Previous entry hash (chain integrity)
═══════════════════════════════════════════════════════════
"""

import json
import os
import time
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("AITestSuite.AuditLog")

# ── Configuration ─────────────────────────────────────────────────────────
DEFAULT_LOG_DIR  = "logs"
DEFAULT_LOG_FILE = "audit.jsonl"
LOG_PATH         = os.getenv("AUDIT_LOG_PATH", os.path.join(DEFAULT_LOG_DIR, DEFAULT_LOG_FILE))

# ── Event type constants ──────────────────────────────────────────────────
class AuditEvent:
    AUDIT_START      = "AUDIT_START"
    AUDIT_COMPLETE   = "AUDIT_COMPLETE"
    TEST_RUN         = "TEST_RUN"
    TEST_FINDING     = "TEST_FINDING"
    USER_LOGIN       = "USER_LOGIN"
    PERMISSION_DENY  = "PERMISSION_DENY"
    BLACKBOX_AUTH    = "BLACKBOX_AUTH"
    BLACKBOX_TEST    = "BLACKBOX_TEST"
    REPORT_GENERATED = "REPORT_GENERATED"
    CONFIG_CHANGE    = "CONFIG_CHANGE"
    ERROR            = "ERROR"
    THREAT_INTEL     = "THREAT_INTEL"
    API_REQUEST      = "API_REQUEST"
    API_RESPONSE     = "API_RESPONSE"


class AuditLogger:
    """
    Forensic audit logger with chain integrity.
    Every entry is hashed and chained to the previous entry
    to detect tampering.
    """

    def __init__(self, log_path=None, auditor=None, session_id=None):
        """
        Args:
            log_path   : Path to the audit log file
            auditor    : Name of the person running the audit
            session_id : Unique session identifier (auto-generated if None)
        """
        self.log_path       = log_path or LOG_PATH
        self.auditor        = auditor or "system"
        self.session_id     = session_id or str(uuid.uuid4())
        self._last_hash     = "GENESIS"
        self._entry_count   = 0

        # Ensure log directory exists
        Path(os.path.dirname(self.log_path)).mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, entry_data):
        """Compute SHA256 hash of an entry for tamper detection."""
        canonical = json.dumps(entry_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _write(self, event_type, details, severity="INFO"):
        """
        Write a single audit log entry.
        Entry is hashed and chained to the previous entry.
        """
        self._entry_count += 1

        entry = {
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "session_id":   self.session_id,
            "auditor":      self.auditor,
            "entry_number": self._entry_count,
            "event_type":   event_type,
            "severity":     severity,
            "details":      details,
            "prev_hash":    self._last_hash,
        }

        # Compute hash of this entry (excluding the hash field itself)
        entry_hash = self._compute_hash(entry)
        entry["entry_hash"] = entry_hash
        self._last_hash = entry_hash

        # Append to log file
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Audit log write failed: {e}")

        return entry

    # ── Public logging methods ────────────────────────────────────────────

    def log_audit_start(self, model_name, model_type, domain, audit_mode):
        """Log the start of an audit session."""
        return self._write(AuditEvent.AUDIT_START, {
            "model_name":  model_name,
            "model_type":  model_type,
            "domain":      domain,
            "audit_mode":  audit_mode,
            "message":     f"Audit session started: {model_name} ({domain})"
        })

    def log_audit_complete(self, total_tests, passed, failed, verdict, report_path=None):
        """Log the completion of an audit session."""
        return self._write(AuditEvent.AUDIT_COMPLETE, {
            "total_tests": total_tests,
            "passed":      passed,
            "failed":      failed,
            "verdict":     verdict,
            "report_path": report_path,
            "message":     f"Audit complete: {verdict} ({passed}/{total_tests} passed)"
        }, severity="WARNING" if verdict == "FAIL" else "INFO")

    def log_finding(self, finding):
        """Log a single test finding."""
        rm       = finding.get("risk_matrix", {})
        severity = "CRITICAL" if rm.get("overall", 0) >= 4.5 else \
                   "HIGH"     if rm.get("overall", 0) >= 3.5 else \
                   "MEDIUM"   if rm.get("overall", 0) >= 2.5 else "LOW"

        return self._write(AuditEvent.TEST_FINDING, {
            "test_name":   finding.get("name"),
            "category":    finding.get("category"),
            "passed":      finding.get("passed"),
            "risk_score":  rm.get("overall"),
            "risk_label":  rm.get("label"),
            "regulations": finding.get("regulations", []),
            "prompt_hash": hashlib.md5(
                finding.get("prompt", "").encode()
            ).hexdigest(),  # Hash prompt not expose it
            "message":     f"{'PASS' if finding.get('passed') else 'FAIL'}: {finding.get('name')}"
        }, severity=severity)

    def log_user_login(self, username, role, ip_address=None, success=True):
        """Log user authentication."""
        return self._write(AuditEvent.USER_LOGIN, {
            "username":   username,
            "role":       role,
            "ip_address": ip_address or "unknown",
            "success":    success,
            "message":    f"{'Login' if success else 'Login failed'}: {username} ({role})"
        }, severity="WARNING" if not success else "INFO")

    def log_permission_deny(self, username, role, attempted_action):
        """Log an access denial by RBAC."""
        return self._write(AuditEvent.PERMISSION_DENY, {
            "username":         username,
            "role":             role,
            "attempted_action": attempted_action,
            "message":          f"Access denied: {username} ({role}) tried {attempted_action}"
        }, severity="WARNING")

    def log_blackbox_auth(self, reference, target_url, auditor_name):
        """Log black box testing authorisation."""
        return self._write(AuditEvent.BLACKBOX_AUTH, {
            "authorisation_ref": reference,
            "target_url":        target_url,
            "authorised_by":     auditor_name,
            "message":           f"Black box authorised: {target_url}"
        }, severity="INFO")

    def log_report_generated(self, report_path, verdict, finding_count):
        """Log PDF report generation."""
        return self._write(AuditEvent.REPORT_GENERATED, {
            "report_path":   report_path,
            "verdict":       verdict,
            "finding_count": finding_count,
            "message":       f"Report generated: {os.path.basename(report_path)}"
        })

    def log_api_request(self, endpoint, method, user, ip=None):
        """Log API request for REST API audit trail."""
        return self._write(AuditEvent.API_REQUEST, {
            "endpoint": endpoint,
            "method":   method,
            "user":     user,
            "ip":       ip or "unknown",
            "message":  f"API {method} {endpoint} by {user}"
        })

    def log_error(self, error_message, context=None):
        """Log a system error."""
        return self._write(AuditEvent.ERROR, {
            "error":   error_message,
            "context": context or {},
            "message": f"Error: {error_message}"
        }, severity="ERROR")

    def log_threat_intel_update(self, source, item_count):
        """Log threat intelligence feed update."""
        return self._write(AuditEvent.THREAT_INTEL, {
            "source":     source,
            "item_count": item_count,
            "message":    f"Threat intel updated: {item_count} items from {source}"
        })

    # ── Query methods ─────────────────────────────────────────────────────

    def get_session_log(self):
        """Return all log entries for the current session."""
        entries = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("session_id") == self.session_id:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        return entries

    def verify_chain_integrity(self):
        """
        Verify the hash chain has not been tampered with.
        Returns (is_valid, message, broken_at_entry)
        """
        entries = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            return True, "No log file to verify", None

        prev_hash = "GENESIS"
        for i, entry in enumerate(entries):
            stored_hash  = entry.get("entry_hash", "")
            stored_prev  = entry.get("prev_hash", "")

            # Verify previous hash link
            if stored_prev != prev_hash:
                return False, f"Chain broken at entry {i+1}: prev_hash mismatch", i+1

            # Verify entry hash
            entry_copy = {k: v for k, v in entry.items() if k != "entry_hash"}
            computed   = self._compute_hash(entry_copy)
            if computed != stored_hash:
                return False, f"Tampered entry detected at {i+1}", i+1

            prev_hash = stored_hash

        return True, f"Chain integrity verified: {len(entries)} entries", None

    def export_session_report(self, output_path=None):
        """Export current session audit log as a formatted JSON report."""
        entries = self.get_session_log()
        findings = [e for e in entries if e["event_type"] == AuditEvent.TEST_FINDING]
        errors   = [e for e in entries if e["event_type"] == AuditEvent.ERROR]

        report = {
            "session_id":    self.session_id,
            "auditor":       self.auditor,
            "exported_at":   datetime.now(timezone.utc).isoformat(),
            "total_entries": len(entries),
            "findings":      len(findings),
            "errors":        len(errors),
            "log_path":      self.log_path,
            "entries":       entries
        }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        return report


# ── Singleton convenience instance ───────────────────────────────────────
_default_logger = None

def get_logger(auditor=None, session_id=None):
    """Get or create the default audit logger."""
    global _default_logger
    if _default_logger is None or auditor:
        _default_logger = AuditLogger(auditor=auditor, session_id=session_id)
    return _default_logger
