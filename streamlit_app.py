"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — AI Security & Governance Audit Platform
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Professional web interface for running AI security audits.
    Model agnostic — HuggingFace, OpenAI, Anthropic, AWS Bedrock,
    Azure OpenAI, GCP Vertex AI, Ollama.
    Supports Healthcare, Finance, Legal and Government domain flags.
    RBAC authentication, structured audit logging, multi-model
    comparison, shadow production testing.

HOW TO RUN:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

TABS:
    1. Dashboard       — Metrics, verdict, risk distribution, PDF download
    2. Audit Results   — Detailed per-finding breakdown with filters
    3. Live Threat Intel — Real-time AI security research feed
    4. Black Box       — Manual and automated black box testing
    5. Multi-Model     — Compare multiple models side by side
    6. About           — Coverage, regulatory framework, usage guide
═══════════════════════════════════════════════════════════
"""

import streamlit as st
import time
import os
import sys

# ── Ensure local modules are importable ──────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Initialise audit logger and RBAC on startup ───────────────────────────
try:
    from core.audit_log import get_logger
    from core.rbac import get_rbac
    _audit_log = get_logger(auditor="system")
    _rbac      = get_rbac()
except Exception:
    _audit_log = None
    _rbac      = None

# ════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# Must be the very first Streamlit call in the script
# ════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AITestSuite v3 | AI Audit Platform",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# Dark professional theme with cyan/purple accent palette
# Font: IBM Plex — technical, professional, distinctive
# ════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* ── Google Fonts ───────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    /* ── Global ─────────────────────────────────────────────────────── */
    * { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background: #0d0d1a; color: #e0e0f0; }

    /* ── Main header ─────────────────────────────────────────────────── */
    .main-header {
        background: linear-gradient(135deg, #1a1a3e 0%, #0d0d1a 50%, #1a0d2e 100%);
        border: 1px solid #3a3a6a;
        border-radius: 8px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #00d4ff, #7b2fff, #ff2d78);
    }
    .header-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        color: #00d4ff;
        margin: 0;
        letter-spacing: 2px;
    }
    .header-subtitle {
        color: #8888aa;
        font-size: 0.9rem;
        margin-top: 0.3rem;
        letter-spacing: 1px;
    }
    .header-badge {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #7b2fff;
        background: #1a0d2e;
        border: 1px solid #7b2fff;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 0.5rem;
    }

    /* ── Metric cards ────────────────────────────────────────────────── */
    .metric-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
    }
    .metric-label {
        font-size: 0.72rem;
        color: #8888aa;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ── Verdict banners ─────────────────────────────────────────────── */
    .verdict-banner {
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    .verdict-text {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.5rem;
        font-weight: 600;
        letter-spacing: 3px;
        margin: 0;
    }
    .verdict-pass        { background: linear-gradient(135deg,#0d2e1a,#1a4a2e); border: 2px solid #28a745; color: #28a745; }
    .verdict-fail        { background: linear-gradient(135deg,#2e0d0d,#4a1a1a); border: 2px solid #dc3545; color: #dc3545; }
    .verdict-conditional { background: linear-gradient(135deg,#2e2400,#4a3a00); border: 2px solid #ffc107; color: #ffc107; }
    .verdict-inconclusive{ background: linear-gradient(135deg,#1a1a2e,#2a2a4a); border: 2px solid #6c757d; color: #6c757d; }

    /* ── Section headers ─────────────────────────────────────────────── */
    .section-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem;
        color: #00d4ff;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 1px solid #2a2a4a;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    /* ── Sidebar ─────────────────────────────────────────────────────── */
    div[data-testid="stSidebar"] {
        background: #0d0d1a;
        border-right: 1px solid #2a2a4a;
    }
    .sidebar-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* ── Buttons ─────────────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #7b2fff, #00d4ff);
        color: white !important;
        border: none !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        letter-spacing: 1px;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #00d4ff, #7b2fff);
        transform: translateY(-1px);
    }

    /* ── Form labels ─────────────────────────────────────────────────── */
    .stSelectbox label, .stRadio label, .stTextInput label {
        color: #8888aa !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    /* ── Threat feed items ───────────────────────────────────────────── */
    .feed-item {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 6px;
        padding: 0.85rem;
        margin: 0.4rem 0;
    }
    .feed-title  { color: #e0e0f0; font-weight: 600; margin-bottom: 4px; }
    .feed-meta   { color: #4a4a6a; font-size: 0.72rem; margin-bottom: 4px; }
    .feed-summary{ color: #8888aa; font-size: 0.82rem; }

    /* ── Tags ────────────────────────────────────────────────────────── */
    .tag {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.62rem;
        padding: 2px 6px;
        border-radius: 3px;
        margin-right: 4px;
        font-weight: 600;
    }
    .tag-CRITICAL   { background: #dc3545; color: white; }
    .tag-NEW        { background: #7b2fff; color: white; }
    .tag-LIVE       { background: #00d4ff; color: black; }
    .tag-RESEARCH   { background: #17a2b8; color: white; }
    .tag-GOVERNANCE { background: #fd7e14; color: white; }
    .tag-HEALTHCARE { background: #28a745; color: white; }
    .tag-PRIVACY    { background: #6f42c1; color: white; }
    .tag-JAILBREAK  { background: #e83e8c; color: white; }
    .tag-INJECTION  { background: #dc3545; color: white; }
    .tag-SUPPLY     { background: #fd7e14; color: white; }

    /* ── About section ───────────────────────────────────────────────── */
    .about-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
    <p class="header-title">⬡ AITestSuite</p>
    <p class="header-subtitle">AI SECURITY &amp; GOVERNANCE AUDIT PLATFORM</p>
    <span class="header-badge">v3.0 — FULL THROTTLE EDITION</span>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# SIDEBAR — AUDIT CONFIGURATION
# All settings the user needs before running an audit
# ════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown('<p class="section-header">⚙ Audit Configuration</p>', unsafe_allow_html=True)

    # ── MODEL SETTINGS ────────────────────────────────────────────────
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("**🤖 Target Model**")

    model_type = st.selectbox(
        "Model Provider",
        options=["huggingface", "openai", "anthropic",
                 "aws_bedrock", "azure_openai", "gcp_vertex", "ollama"],
        index=0,
        format_func=lambda x: {
            "huggingface":  "🤗 HuggingFace (FREE — no key needed)",
            "openai":       "🔵 OpenAI API",
            "anthropic":    "🟣 Anthropic API",
            "aws_bedrock":  "🟠 AWS Bedrock",
            "azure_openai": "🔷 Azure OpenAI",
            "gcp_vertex":   "🔴 GCP Vertex AI",
            "ollama":       "🦙 Ollama (Local)"
        }[x],
        help="HuggingFace is FREE — no API key needed. Cloud providers require credentials."
    )

    model_defaults = {
        "huggingface":  "google/flan-t5-small",
        "openai":       "gpt-3.5-turbo",
        "anthropic":    "claude-haiku-4-5-20251001",
        "aws_bedrock":  "amazon.titan-text-express-v1",
        "azure_openai": "gpt-4",
        "gcp_vertex":   "gemini-1.0-pro",
        "ollama":       "llama2"
    }
    model_name = st.text_input(
        "Model Name / ID",
        value=model_defaults.get(model_type, "google/flan-t5-small"),
        help="HuggingFace: model ID | Cloud: model/deployment name"
    )

    api_key = None
    # Cloud provider specific credential fields
    if model_type == "huggingface":
        pass  # No key needed
    elif model_type == "azure_openai":
        api_key = st.text_input("Azure API Key", type="password")
        azure_endpoint = st.text_input("Azure Endpoint URL",
            placeholder="https://yourname.openai.azure.com",
            help="Your Azure OpenAI endpoint")
        if azure_endpoint:
            os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint
    elif model_type == "aws_bedrock":
        col_ak, col_sk = st.columns(2)
        with col_ak:
            aws_key = st.text_input("AWS Access Key", type="password")
        with col_sk:
            aws_secret = st.text_input("AWS Secret Key", type="password")
        aws_region = st.text_input("AWS Region", value="us-east-1")
        if aws_key:
            os.environ["AWS_ACCESS_KEY_ID"]     = aws_key
        if aws_secret:
            os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret
        if aws_region:
            os.environ["AWS_REGION"]            = aws_region
    elif model_type == "gcp_vertex":
        gcp_project = st.text_input("GCP Project ID", placeholder="my-gcp-project")
        if gcp_project:
            os.environ["GOOGLE_CLOUD_PROJECT"] = gcp_project
    elif model_type == "ollama":
        ollama_url = st.text_input("Ollama URL", value="http://localhost:11434")
        if ollama_url:
            os.environ["OLLAMA_URL"] = ollama_url
    else:
        api_key = st.text_input("API Key", type="password")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── DOMAIN FLAG ───────────────────────────────────────────────────
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("**🏳 Domain Flag**")

    domain = st.radio(
        "Audit Domain",
        options=["general", "healthcare", "finance", "legal", "government"],
        index=0,
        format_func=lambda x: {
            "general":    "🔍 General (Default)",
            "healthcare": "🏥 Healthcare — HIPAA/PIPEDA",
            "finance":    "💰 Finance — SOX/GDPR",
            "legal":      "⚖️ Legal — Privilege",
            "government": "🏛️ Government — Security"
        }[x]
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── AUDIT MODE ────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("**⚡ Audit Mode**")
    st.caption("Standard = single run. Statistical = 5 runs per test. Full = all modes combined.")

    audit_mode = st.radio(
        "Mode",
        options=["standard", "statistical", "multiturn", "fuzzing", "evolutionary", "full"],
        format_func=lambda x: {
            "standard":    "🔍 Standard — single run, all tests",
            "statistical": "📊 Statistical — 5 runs per test",
            "multiturn":   "🔗 Multi-Turn — attack chains",
            "fuzzing":     "🧬 Fuzzing — 14 mutation strategies",
            "evolutionary":"🔴 Evolutionary — genetic jailbreak",
            "full":        "💥 Full Throttle — everything"
        }[x],
        help="Full mode runs all engines — takes longer but gives highest confidence."
    )

    if audit_mode == "statistical":
        runs_per_test = st.slider("Runs per test", min_value=3, max_value=10, value=5)
    else:
        runs_per_test = 5

    if audit_mode in ["fuzzing", "full"]:
        mutations_per_seed = st.slider("Mutations per seed prompt", min_value=3, max_value=14, value=7)
    else:
        mutations_per_seed = 7

    if audit_mode in ["evolutionary", "full"]:
        evo_generations = st.slider("Evolutionary generations", min_value=2, max_value=10, value=5)
        evo_population  = st.slider("Population size", min_value=5, max_value=20, value=10)
    else:
        evo_generations = 5
        evo_population  = 10

    parallel_workers = st.slider(
        "Parallel workers",
        min_value=1, max_value=8, value=2,
        help="More workers = faster but more load on model/API"
    )

    # Garak toggle
    use_garak = st.checkbox(
        "🔬 Include Garak Probes",
        value=False,
        help="Adds Garak's probe library if installed. Run: pip install garak"
    )
    if use_garak:
        try:
            from core.garak_bridge import is_garak_available
            garak_ok = is_garak_available()
            if garak_ok:
                st.success("✅ Garak detected")
            else:
                st.warning("⚠️ Garak not installed — using extended fallback probes\npip install garak")
        except Exception:
            st.warning("⚠️ Garak bridge error — using fallback probes")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── AUDITOR INFO ──────────────────────────────────────────────────
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("**👤 Report Information**")
    auditor_name = st.text_input("Auditor Name", value="Amarjit Khakh")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    run_button = st.button("🚀 LAUNCH AUDIT", use_container_width=True)

    # ── TEST COUNT PREVIEW ────────────────────────────────────────────
    try:
        from tests.default_tests import DEFAULT_TESTS
        from tests.advanced_tests import ADVANCED_TESTS
        from tests.multi_turn_tests import MULTI_TURN_CHAINS
        from core.garak_bridge import EXTENDED_FALLBACK_PROBES

        preview_count = len(DEFAULT_TESTS) + len(ADVANCED_TESTS)
        if domain == "healthcare":
            from domains.healthcare import HEALTHCARE_TESTS
            preview_count += len(HEALTHCARE_TESTS)
        elif domain == "finance":
            from domains.finance import FINANCE_TESTS
            preview_count += len(FINANCE_TESTS)
        elif domain in ["legal", "government"]:
            from domains.government_legal import LEGAL_TESTS, GOVERNMENT_TESTS
            preview_count += len(LEGAL_TESTS) + len(GOVERNMENT_TESTS)

        if audit_mode == "statistical":
            st.caption(f"📊 {preview_count} tests × {runs_per_test} runs = {preview_count * runs_per_test} total queries")
        elif audit_mode == "multiturn":
            st.caption(f"🔗 {preview_count} tests + {len(MULTI_TURN_CHAINS)} attack chains")
        elif audit_mode == "fuzzing":
            st.caption(f"🧬 {preview_count} tests + fuzzing mutations")
        elif audit_mode == "evolutionary":
            st.caption(f"🔴 {preview_count} tests + {evo_generations} gen × {evo_population} population")
        elif audit_mode == "full":
            total_est = preview_count * runs_per_test + len(MULTI_TURN_CHAINS) + len(EXTENDED_FALLBACK_PROBES)
            st.caption(f"💥 ~{total_est}+ total queries across all modes")
        else:
            st.caption(f"📋 {preview_count} tests for **{domain.upper()}** domain")
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — FOUR TABS
# ════════════════════════════════════════════════════════════════════════

tab_dashboard, tab_results, tab_intel, tab_blackbox, tab_multimodel, tab_monitor, tab_about = st.tabs([
    "📊  Dashboard",
    "🔬  Audit Results",
    "📡  Live Threat Intel",
    "🕵️  Black Box",
    "🔀  Multi-Model",
    "🔴  Monitor",
    "📖  About"
])


# ════════════════════════════════════════════════════════════════════════
# TAB 1: DASHBOARD
# Shows: verdict, metrics, risk distribution, quick table, PDF export
# ════════════════════════════════════════════════════════════════════════

with tab_dashboard:

    if "findings" not in st.session_state:
        # ── Welcome state — no audit run yet ─────────────────────────
        _, col_c, _ = st.columns([1, 2, 1])
        with col_c:
            st.markdown("""
            <div style='text-align:center; padding:4rem 0;'>
                <p style='font-family:IBM Plex Mono; font-size:3.5rem; color:#2a2a4a; margin:0;'>⬡</p>
                <p style='font-family:IBM Plex Mono; color:#4a4a6a; letter-spacing:3px; margin:8px 0;'>
                    READY TO AUDIT
                </p>
                <p style='color:#4a4a6a; font-size:0.85rem; line-height:1.6;'>
                    Select your target model and domain in the sidebar<br>
                    then click LAUNCH AUDIT to begin
                </p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # ── Results state — audit has been run ───────────────────────
        findings = st.session_state.findings
        verdict  = st.session_state.verdict

        # ── Verdict banner ────────────────────────────────────────────
        verdict_class = {
            "PASS":             "verdict-pass",
            "FAIL":             "verdict-fail",
            "CONDITIONAL PASS": "verdict-conditional",
            "INCONCLUSIVE":     "verdict-inconclusive"
        }.get(verdict, "verdict-inconclusive")

        mode_label = st.session_state.get("audit_mode", "standard").upper()
        st.markdown(f"""
        <div class="verdict-banner {verdict_class}">
            <p class="verdict-text">AUDIT VERDICT: {verdict}</p>
            <p style="font-family:IBM Plex Mono; font-size:0.75rem; margin:4px 0 0; opacity:0.7;">
                MODE: {mode_label}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Metric cards ──────────────────────────────────────────────
        total    = len(findings)
        passed   = sum(1 for f in findings if f.get("passed"))
        failed   = total - passed
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
        avg_risk = round(
            sum(f.get("risk_matrix", {}).get("overall", 0) for f in findings) / total, 1
        ) if total > 0 else 0

        cols = st.columns(5)
        for col, value, label, colour in zip(cols, [
            (str(total),    "Tests Run",  "#00d4ff"),
            (str(passed),   "Passed",     "#28a745"),
            (str(failed),   "Failed",     "#dc3545"),
            (str(critical), "Critical",   "#ff2d78"),
            (str(avg_risk), "Avg Risk",   "#ffc107"),
        ], ["Tests Run", "Passed", "Failed", "Critical", "Avg Risk"],
           ["#00d4ff", "#28a745", "#dc3545", "#ff2d78", "#ffc107"]):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-value" style="color:{colour};">{value[0]}</p>
                    <p class="metric-label">{label}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Risk distribution chart ───────────────────────────────────
        st.markdown('<p class="section-header">Risk Distribution</p>', unsafe_allow_html=True)

        import pandas as pd
        risk_labels = {1: "Informational(1)", 2: "Low(2)", 3: "Medium(3)", 4: "High(4)", 5: "Critical(5)"}
        risk_dist   = {k: 0 for k in range(1, 6)}
        for f in findings:
            score = max(1, min(5, round(f.get("risk_matrix", {}).get("overall", 1))))
            risk_dist[score] += 1

        chart_df = pd.DataFrame({
            "Risk Level": [risk_labels[k] for k in sorted(risk_dist)],
            "Count":      [risk_dist[k]   for k in sorted(risk_dist)]
        })
        st.bar_chart(chart_df.set_index("Risk Level"))

        # ── Category breakdown ────────────────────────────────────────
        st.markdown('<p class="section-header">Category Breakdown</p>', unsafe_allow_html=True)
        categories = {}
        for f in findings:
            cat = f.get("category", "Unknown")
            if cat not in categories:
                categories[cat] = {"pass": 0, "fail": 0}
            if f.get("passed"):
                categories[cat]["pass"] += 1
            else:
                categories[cat]["fail"] += 1

        cat_df = pd.DataFrame([
            {"Category": k, "Pass": v["pass"], "Fail": v["fail"],
             "Pass Rate": f"{int(100*v['pass']/(v['pass']+v['fail']))}%"}
            for k, v in categories.items()
        ])
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

        # ── Statistical consistency section ───────────────────────────
        stat_findings = [f for f in findings if "statistical" in f]
        if stat_findings:
            st.markdown('<p class="section-header">📊 Statistical Consistency Analysis</p>', unsafe_allow_html=True)
            st.caption("Tests run multiple times to detect inconsistent behaviour. INCONSISTENT = most dangerous.")

            stat_data = []
            for f in stat_findings:
                stats = f.get("statistical", {})
                stat_data.append({
                    "Test":         f.get("name", "")[:40],
                    "Runs":         stats.get("runs", "-"),
                    "Pass Rate":    f"{stats.get('pass_rate', '-')}%",
                    "Consistency":  stats.get("consistency_label", "-"),
                    "Overall Risk": f.get("risk_matrix", {}).get("overall", "-")
                })
            st.dataframe(pd.DataFrame(stat_data), use_container_width=True, hide_index=True)

        # ── Quick findings overview ───────────────────────────────────
        st.markdown('<p class="section-header">Findings Overview</p>', unsafe_allow_html=True)
        table_data = []
        for f in findings:
            rm = f.get("risk_matrix", {})
            table_data.append({
                "Test":       f.get("name", ""),
                "Category":   f.get("category", ""),
                "Result":     "✓ PASS" if f.get("passed") else "✗ FAIL",
                "Sev":        rm.get("severity",   "-"),
                "Like":       rm.get("likelihood", "-"),
                "Impact":     rm.get("impact",     "-"),
                "Reg":        rm.get("regulatory", "-"),
                "Overall":    rm.get("overall",    "-"),
                "Risk Label": rm.get("label",      "-"),
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        # ── PDF generation ────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<p class="section-header">📄 Generate Audit Report</p>', unsafe_allow_html=True)

        if st.button("📄 GENERATE PDF AUDIT REPORT", use_container_width=True):
            with st.spinner("Generating professional PDF report..."):
                try:
                    from core.reporting import ReportGenerator
                    generator = ReportGenerator(output_dir="reports")
                    pdf_path  = generator.generate(
                        findings     = findings,
                        verdict      = verdict,
                        model_info   = {
                            "model_name": st.session_state.get("model_name", model_name),
                            "model_type": st.session_state.get("model_type", model_type)
                        },
                        domain       = domain if domain != "general" else None,
                        auditor_name = auditor_name
                    )
                    with open(pdf_path, "rb") as fh:
                        st.download_button(
                            label       = "⬇ DOWNLOAD PDF REPORT",
                            data        = fh.read(),
                            file_name   = os.path.basename(pdf_path),
                            mime        = "application/pdf",
                            use_container_width=True
                        )
                    st.success(f"✅ Report generated: {os.path.basename(pdf_path)}")
                except Exception as e:
                    st.error(f"PDF generation error: {e}")
                    st.info("Run: pip install reportlab")


# ════════════════════════════════════════════════════════════════════════
# TAB 2: AUDIT RESULTS
# Detailed per-finding view with filters and expandable cards
# ════════════════════════════════════════════════════════════════════════

with tab_results:

    if "findings" not in st.session_state:
        st.info("No audit results yet. Configure your model in the sidebar and click LAUNCH AUDIT.")

    else:
        findings = st.session_state.findings
        st.markdown('<p class="section-header">Detailed Findings</p>', unsafe_allow_html=True)

        # ── Filter controls ───────────────────────────────────────────
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_result = st.selectbox("Filter by Result",   ["All", "PASS", "FAIL"])
        with col_f2:
            all_cats      = ["All"] + sorted(set(f.get("category", "") for f in findings))
            filter_cat    = st.selectbox("Filter by Category", all_cats)
        with col_f3:
            filter_risk   = st.selectbox("Filter by Min Risk", ["All", "2+", "3+", "4+", "5 only"])

        # ── Apply filters ─────────────────────────────────────────────
        filtered = findings
        if filter_result == "PASS":
            filtered = [f for f in filtered if f.get("passed")]
        elif filter_result == "FAIL":
            filtered = [f for f in filtered if not f.get("passed")]
        if filter_cat != "All":
            filtered = [f for f in filtered if f.get("category") == filter_cat]
        if filter_risk != "All":
            min_risk = int(filter_risk[0])
            filtered = [f for f in filtered if f.get("risk_matrix", {}).get("overall", 0) >= min_risk]

        st.caption(f"Showing {len(filtered)} of {len(findings)} findings")

        # ── Expandable finding cards ──────────────────────────────────
        for i, f in enumerate(filtered):
            rm      = f.get("risk_matrix", {})
            overall = rm.get("overall", 0)
            passed  = f.get("passed", False)
            icon    = "✓" if passed else "✗"
            label   = rm.get("label", "Unknown")

            with st.expander(
                f"{icon} [{label} — {overall}/5]  {f.get('name', '')}",
                expanded=not passed  # Auto-expand failures
            ):
                col_l, col_r = st.columns(2)

                with col_l:
                    st.markdown(f"**Category:**  {f.get('category', '')}")
                    st.markdown(f"**Domain:**    {f.get('domain', 'general').upper()}")
                    st.markdown(f"**Result:**    {'✅ PASS' if passed else '❌ FAIL'}")
                    st.markdown(f"**Timestamp:** {f.get('timestamp', '')}")

                with col_r:
                    st.markdown(f"**Severity:**        {rm.get('severity',   '-')}/5")
                    st.markdown(f"**Likelihood:**      {rm.get('likelihood', '-')}/5")
                    st.markdown(f"**Impact:**          {rm.get('impact',     '-')}/5")
                    st.markdown(f"**Regulatory Exp:**  {rm.get('regulatory', '-')}/5")
                    st.markdown(f"**Overall Score:**   **{overall}/5**")

                st.markdown("**Prompt Sent:**")
                st.code(f.get("prompt", ""), language=None)

                st.markdown("**Model Response:**")
                st.code(f.get("response", ""), language=None)

                if f.get("expected"):
                    st.markdown(f"**Expected Keywords:** `{f.get('expected', '')}`")

                # Multi-turn chain conversation history
                if f.get("chain_turns"):
                    st.markdown("**🔗 Attack Chain Conversation:**")
                    for turn in f.get("chain_turns", []):
                        turn_icon = "🎯" if turn.get("is_attack_turn") else "💬"
                        label     = "ATTACK PROMPT" if turn.get("is_attack_turn") else f"Setup Turn {turn['turn']}"
                        st.markdown(f"**{turn_icon} Turn {turn['turn']} — {label}:**")
                        st.code(f"→ Sent:     {turn['prompt'][:200]}\n← Received: {turn['response'][:200]}", language=None)

                # Statistical data
                if f.get("statistical"):
                    stats = f.get("statistical", {})
                    st.markdown(f"""
                    **📊 Statistical Results:** {stats.get('pass_count','?')}/{stats.get('runs','?')} runs passed
                    ({stats.get('pass_rate','?')}%) — **{stats.get('consistency_label','?')}**
                    """)
                    if stats.get("note"):
                        st.warning(stats["note"])

                # Clinical implication — only show if relevant
                impl = f.get("healthcare_implication", "")
                if impl and impl not in ("N/A", ""):
                    st.warning(f"🏥 **Clinical Implication:** {impl}")

                # Regulatory flags
                if f.get("regulations"):
                    st.markdown(f"**Regulatory Flags:** `{'` | `'.join(f.get('regulations', []))}`")

                # Remediation
                if f.get("remediation"):
                    st.info(f"🔧 **Remediation:** {f.get('remediation')}")

                # References
                if f.get("references"):
                    for ref in f.get("references", []):
                        st.markdown(f"📎 [{ref}]({ref})")


# ════════════════════════════════════════════════════════════════════════
# TAB 3: LIVE THREAT INTELLIGENCE
# Real arXiv feed + curated static items
# ════════════════════════════════════════════════════════════════════════

with tab_intel:
    st.markdown('<p class="section-header">📡 Live AI Threat Intelligence</p>', unsafe_allow_html=True)
    st.caption("Pulls latest AI security research from arXiv in real time. Falls back to curated feed when offline.")

    # ── Controls ──────────────────────────────────────────────────────
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        refresh = st.button("🔄 Refresh Feed", use_container_width=True)

    # ── Load feed (with caching to avoid hammering arXiv) ─────────────
    if "threat_feed" not in st.session_state or refresh:
        with st.spinner("Fetching latest AI security research..."):
            try:
                from live_research.threat_feed import get_live_feed, get_feed_stats
                items = get_live_feed(max_results=5)
                st.session_state.threat_feed = items
            except Exception as e:
                from live_research.threat_feed import STATIC_FEED
                st.session_state.threat_feed = STATIC_FEED

    items = st.session_state.get("threat_feed", [])

    # ── Feed stats ────────────────────────────────────────────────────
    try:
        from live_research.threat_feed import get_feed_stats
        stats = get_feed_stats(items)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Items",      stats["total"])
        m2.metric("Critical Alerts",  stats["critical"])
        m3.metric("Live from arXiv",  stats["live"])
        m4.metric("Healthcare Items", stats["healthcare"])
    except Exception:
        pass

    st.markdown("---")

    # ── Render feed items ─────────────────────────────────────────────
    TAG_CLASSES = {
        "CRITICAL":   "tag-CRITICAL",
        "NEW":        "tag-NEW",
        "LIVE":       "tag-LIVE",
        "RESEARCH":   "tag-RESEARCH",
        "GOVERNANCE": "tag-GOVERNANCE",
        "HEALTHCARE": "tag-HEALTHCARE",
        "PRIVACY":    "tag-PRIVACY",
        "JAILBREAK":  "tag-JAILBREAK",
        "INJECTION":  "tag-INJECTION",
        "SUPPLY":     "tag-SUPPLY",
    }

    for item in items:
        tags_html = "".join([
            f'<span class="tag {TAG_CLASSES.get(t, "tag-RESEARCH")}">{t}</span>'
            for t in item.get("tags", [])
        ])
        url  = item.get("url", "#")
        link = f'<a href="{url}" target="_blank" style="color:#00d4ff; font-size:0.75rem;">→ Read More</a>' if url != "#" else ""

        st.markdown(f"""
        <div class="feed-item">
            <div style="margin-bottom:5px;">
                {tags_html}
                <span class="feed-meta" style="margin-left:8px;">
                    {item.get('source','Unknown')} · {item.get('date','Recent')}
                </span>
            </div>
            <div class="feed-title">{item.get('title','')}</div>
            <div class="feed-summary">{item.get('summary','')}</div>
            <div style="margin-top:6px;">{link}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("🔧 arXiv live feed pulls cs.CR papers tagged with LLM/AI safety keywords. Refresh to get latest.")


# ════════════════════════════════════════════════════════════════════════
# TAB 4: BLACK BOX TESTING
# Browser automation for testing AI interfaces without API keys
# ⚠️ AUTHORISED USE ONLY — prominent warnings throughout
# ════════════════════════════════════════════════════════════════════════

with tab_blackbox:

    # ── AUTHORISATION WARNING BANNER — always visible ─────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #2e0d0d, #4a1a1a);
        border: 2px solid #dc3545;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    ">
        <p style="
            font-family: IBM Plex Mono, monospace;
            color: #dc3545;
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: 2px;
            margin: 0 0 0.75rem;
        ">⚠️  AUTHORISATION REQUIRED — READ BEFORE USE</p>
        <p style="color: #e0e0f0; font-size: 0.85rem; line-height: 1.8; margin: 0;">
            This module automates a browser to send test prompts to AI chat interfaces.<br><br>
            <b>You MUST have EXPLICIT WRITTEN AUTHORISATION</b> from the system owner
            before running any test. This means a signed agreement, email confirmation,
            or documented permission — not verbal agreement.<br><br>
            <b>PERMITTED uses:</b> Your own deployed AI interface · Vendor test environments
            with written permission · Healthcare or enterprise AI pilot systems with
            written sign-off · Any system where you hold explicit written authorisation<br><br>
            <b>NOT PERMITTED:</b> Any public AI chat interface without explicit written
            authorisation from that provider. When in doubt — do not run.<br><br>
            <span style="color:#dc3545; font-weight:600;">
            Unauthorised automated access may violate Criminal Code of Canada s.342.1
            (Unauthorized Computer Access). If in doubt — do not run.
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── SUB-MODE SELECTION ────────────────────────────────────────────
    st.markdown('<p class="section-header">🕵️ Black Box Test Mode</p>', unsafe_allow_html=True)

    bb_mode = st.radio(
        "Select Testing Mode",
        options=["manual", "automated"],
        format_func=lambda x: {
            "manual":    "📋 Manual Mode — You copy/paste prompts yourself (no automation, no ToS issues)",
            "automated": "🤖 Automated Mode — Browser automation via Selenium (REQUIRES written authorisation)"
        }[x],
        help="Manual mode is always safe. Automated mode requires explicit written permission from the target system owner."
    )

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # MANUAL BLACK BOX MODE
    # User copies prompts manually — no automation, no ToS concerns
    # ════════════════════════════════════════════════════════════════════

    if bb_mode == "manual":

        st.markdown("""
        <div style="background:#1a2e1a; border:1px solid #28a745; border-radius:8px; padding:1rem; margin-bottom:1rem;">
            <p style="color:#28a745; font-family:IBM Plex Mono; font-size:0.8rem; margin:0 0 6px;">
                ✅ MANUAL MODE — SAFE TO USE
            </p>
            <p style="color:#e0e0f0; font-size:0.82rem; margin:0; line-height:1.6;">
                This mode generates test prompts for you to copy and paste manually into
                any chat interface. You enter the responses back here and the toolkit
                scores and reports them. No automation — no terms of service concerns.
                Perfect for testing any AI chat interface by hand.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Configuration ─────────────────────────────────────────────
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            manual_target = st.text_input(
                "Target Description",
                value="",
                placeholder="e.g. Vendor AI Tool v2.1 via internal test environment",
                help="Describe what you are testing — for your audit records"
            )
        with col_m2:
            manual_category = st.selectbox(
                "Test Category to Run",
                options=[
                    "All Default Tests",
                    "Hallucination Only",
                    "Bias Detection Only",
                    "Prompt Injection Only",
                    "Jailbreak Only",
                    "Privacy Leakage Only",
                    "RAG Exploitation Only"
                ]
            )

        if st.button("📋 GENERATE MANUAL TEST PROMPTS", use_container_width=True):

            if not manual_target.strip():
                st.error("Please enter a target description before generating prompts.")
            else:
                # ── Load and filter tests ─────────────────────────────
                from tests.default_tests import DEFAULT_TESTS
                tests = DEFAULT_TESTS

                # Filter by category if selected
                category_filters = {
                    "Hallucination Only":    ["Hallucination"],
                    "Bias Detection Only":   ["Bias Detection"],
                    "Prompt Injection Only": ["Prompt Injection"],
                    "Jailbreak Only":        ["Jailbreak"],
                    "Privacy Leakage Only":  ["Privacy Leakage", "Data Exfiltration", "Model Extraction"],
                    "RAG Exploitation Only": ["RAG Exploitation"],
                }

                if manual_category != "All Default Tests":
                    cats = category_filters.get(manual_category, [])
                    tests = [t for t in tests if t.get("category") in cats]

                st.session_state.manual_tests   = tests
                st.session_state.manual_target  = manual_target
                st.session_state.manual_results = {}

                st.success(f"Generated {len(tests)} test prompts for manual testing.")

        # ── Display prompts and collect responses ─────────────────────
        if "manual_tests" in st.session_state:
            tests   = st.session_state.manual_tests
            results = st.session_state.get("manual_results", {})

            st.markdown(f"**Testing Against:** `{st.session_state.get('manual_target', '')}`")
            st.markdown(f"**{len(tests)} prompts ready** — Copy each prompt, paste it into your target interface, then paste the response back below.")
            st.markdown("---")

            for i, test in enumerate(tests):
                with st.expander(f"Test {i+1}: {test['name']}", expanded=(i == 0)):

                    # ── Show the prompt to copy ───────────────────────
                    st.markdown("**📋 Copy this prompt:**")
                    st.code(test["prompt"], language=None)

                    # ── Response input field ──────────────────────────
                    response_key = f"manual_response_{i}"
                    response = st.text_area(
                        "✏️ Paste the response you received here:",
                        key=response_key,
                        height=100,
                        placeholder="Paste the AI's exact response here..."
                    )

                    if response:
                        st.session_state.manual_results[i] = {
                            "test":     test,
                            "response": response
                        }
                        st.success("Response recorded ✓")

            # ── Score and report button ───────────────────────────────
            completed = len(st.session_state.get("manual_results", {}))
            st.markdown(f"**Progress: {completed}/{len(tests)} responses entered**")

            if completed > 0:
                if st.button("📊 SCORE MANUAL RESULTS & GENERATE REPORT", use_container_width=True):

                    from core.scoring import RiskScorer
                    from core.runner import AuditRunner

                    scorer   = RiskScorer()
                    findings = []

                    for i, data in st.session_state.manual_results.items():
                        test     = data["test"]
                        response = data["response"]

                        # Evaluate response
                        expected = test.get("expected", "")
                        if expected:
                            keywords = [k.strip().lower() for k in expected.split(",")]
                            matches  = sum(1 for kw in keywords if kw in response.lower())
                            passed   = matches >= max(1, len(keywords) // 2)
                        else:
                            passed = True

                        finding = {
                            "name":                   test["name"],
                            "category":               test["category"],
                            "domain":                 "manual_blackbox",
                            "prompt":                 test["prompt"],
                            "response":               response,
                            "expected":               expected,
                            "passed":                 passed,
                            "regulations":            test.get("regulations", []),
                            "healthcare_implication": test.get("healthcare_implication", ""),
                            "remediation":            test.get("remediation", ""),
                            "references":             test.get("references", []),
                            "timestamp":              time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        findings.append(scorer.score(finding))

                    verdict = scorer.verdict(findings)
                    st.session_state.findings   = findings
                    st.session_state.verdict    = verdict
                    st.session_state.model_name = st.session_state.get("manual_target", "Manual Black Box")
                    st.session_state.model_type = "manual_blackbox"

                    st.success(f"✅ Scored {len(findings)} findings — Verdict: **{verdict}** — See Dashboard tab for full results and PDF report.")

    # ════════════════════════════════════════════════════════════════════
    # AUTOMATED BLACK BOX MODE
    # Browser automation via Selenium — requires written authorisation
    # ════════════════════════════════════════════════════════════════════

    elif bb_mode == "automated":

        # ── Prominent warning ─────────────────────────────────────────
        st.markdown("""
        <div style="background:#2e1a00; border:2px solid #fd7e14; border-radius:8px; padding:1rem; margin-bottom:1rem;">
            <p style="color:#fd7e14; font-family:IBM Plex Mono; font-size:0.8rem; margin:0 0 6px;">
                ⚠️ AUTOMATED MODE — WRITTEN AUTHORISATION REQUIRED
            </p>
            <p style="color:#e0e0f0; font-size:0.82rem; margin:0; line-height:1.6;">
                This mode controls a real browser to send prompts automatically.
                You <b>must</b> enter a written authorisation reference before testing will begin.
                The reference is logged in your audit trail and PDF report.
                <br><br>
                <b>Required before running:</b> pip install selenium webdriver-manager
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Authorisation form ────────────────────────────────────────
        st.markdown('<p class="section-header">Step 1 — Record Written Authorisation</p>', unsafe_allow_html=True)

        auth_ref = st.text_input(
            "Written Authorisation Reference *",
            placeholder="e.g. Organisation AI Test Agreement signed 2026-03-20 — Reference No. 001",
            help="This MUST reference actual written permission you have received. This is logged permanently."
        )
        auth_target = st.text_input(
            "Target URL *",
            placeholder="https://your-authorised-target.ca/chat",
            help="The exact URL of the AI interface you have permission to test"
        )
        auth_auditor = st.text_input(
            "Your Name *",
            value="Amarjit Khakh",
            help="Your name as the auditor — recorded in the audit trail"
        )

        st.markdown('<p class="section-header">Step 2 — Configure Browser & Interface</p>', unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            browser_choice = st.selectbox("Browser", ["chrome", "firefox"])
            headless_mode  = st.checkbox("Headless (no visible browser window)", value=True)
        with col_b2:
            profile_choice = st.selectbox(
                "Interface Profile",
                options=list({"generic_input_box": "Generic input box", "custom_target": "Custom target (configure in code)"}.keys()),
                format_func=lambda x: {"generic_input_box": "Generic input box", "custom_target": "Custom target (configure in code)"}[x]
            )

        # ── Custom selectors override ─────────────────────────────────
        with st.expander("🔧 Advanced — Custom CSS Selectors (if Generic profile doesn't work)"):
            st.caption("Inspect the target page in your browser to find the correct CSS selectors")
            custom_input    = st.text_input("Input Field CSS Selector",    value="textarea")
            custom_submit   = st.text_input("Submit Button CSS Selector",  value="button[type=submit]")
            custom_response = st.text_input("Response Area CSS Selector",  value="[data-role='response']")
            custom_wait     = st.number_input("Wait seconds for response", value=6, min_value=2, max_value=30)

        st.markdown('<p class="section-header">Step 3 — Select Test Suite</p>', unsafe_allow_html=True)

        auto_domain = st.radio(
            "Domain",
            ["general", "healthcare", "finance", "legal", "government"],
            horizontal=True
        )

        # ── I Confirm checkbox — final gate ──────────────────────────
        st.markdown("---")
        confirm = st.checkbox(
            "✅ I confirm I have EXPLICIT WRITTEN AUTHORISATION to test the target URL above. "
            "I understand that unauthorised access may violate Criminal Code of Canada s.342.1. "
            "I am responsible for my actions.",
            value=False
        )

        run_bb = st.button(
            "🤖 LAUNCH AUTOMATED BLACK BOX AUDIT",
            use_container_width=True,
            disabled=not confirm
        )

        if run_bb:
            # ── Final validation ──────────────────────────────────────
            if not auth_ref.strip() or len(auth_ref.strip()) < 15:
                st.error("⚠️ Authorisation reference is too short. Provide a meaningful written reference.")
            elif not auth_target.startswith("http"):
                st.error("⚠️ Target URL must start with http:// or https://")
            else:
                st.markdown('<p class="section-header">⚡ Black Box Audit In Progress</p>', unsafe_allow_html=True)
                progress_bar = st.progress(0)
                status_text  = st.empty()

                try:
                    from blackbox.browser_adapter import BlackBoxAdapter, authorise_session, INTERFACE_PROFILES

                    # Record authorisation
                    authorise_session(
                        reference    = auth_ref,
                        target_url   = auth_target,
                        auditor_name = auth_auditor
                    )

                    # Configure custom profile if overrides provided
                    if profile_choice == "generic_input_box":
                        INTERFACE_PROFILES["generic_input_box"]["input_selector"]    = custom_input
                        INTERFACE_PROFILES["generic_input_box"]["submit_selector"]   = custom_submit
                        INTERFACE_PROFILES["generic_input_box"]["response_selector"] = custom_response
                        INTERFACE_PROFILES["generic_input_box"]["wait_seconds"]      = custom_wait

                    # Initialise browser adapter
                    status_text.text("Launching browser...")
                    adapter = BlackBoxAdapter(
                        target_url        = auth_target,
                        interface_profile = profile_choice,
                        browser           = browser_choice,
                        headless          = headless_mode
                    )
                    adapter.load()

                    # Build test suite
                    from tests.default_tests import DEFAULT_TESTS
                    test_suite = list(DEFAULT_TESTS)

                    if auto_domain == "healthcare":
                        from domains.healthcare import HEALTHCARE_TESTS
                        test_suite += HEALTHCARE_TESTS
                    elif auto_domain == "finance":
                        from domains.finance import FINANCE_TESTS
                        test_suite += FINANCE_TESTS
                    elif auto_domain in ["legal", "government"]:
                        from domains.government_legal import LEGAL_TESTS, GOVERNMENT_TESTS
                        test_suite += LEGAL_TESTS + GOVERNMENT_TESTS

                    # Run audit via browser
                    from core.runner import AuditRunner

                    def bb_progress(pct, msg):
                        progress_bar.progress(min(pct, 1.0))
                        status_text.text(msg)

                    runner   = AuditRunner(
                        model_adapter     = adapter,
                        domain            = auto_domain if auto_domain != "general" else None,
                        progress_callback = bb_progress
                    )
                    findings = runner.run(test_suite)

                    from core.scoring import RiskScorer
                    verdict  = RiskScorer().verdict(findings)

                    # Close browser
                    adapter.close()

                    # Store results
                    st.session_state.findings   = findings
                    st.session_state.verdict    = verdict
                    st.session_state.model_name = f"BlackBox: {auth_target}"
                    st.session_state.model_type = "blackbox_browser"

                    progress_bar.progress(1.0)
                    status_text.text(f"✅ Black box audit complete — {len(findings)} tests | Verdict: {verdict}")
                    st.success("Results available in Dashboard tab. PDF report includes authorisation reference.")
                    st.rerun()

                except ImportError:
                    st.error("❌ Selenium not installed. Run: pip install selenium webdriver-manager")
                except PermissionError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"❌ Black box audit failed: {str(e)}")
                    st.info("Check: target URL is accessible · CSS selectors are correct · Browser is installed")


# ════════════════════════════════════════════════════════════════════════
# TAB 5: MULTI-MODEL COMPARISON
# ════════════════════════════════════════════════════════════════════════

with tab_multimodel:
    st.markdown('<p class="section-header">🔀 Multi-Model Comparison Audit</p>', unsafe_allow_html=True)
    st.caption("Run the same audit against multiple AI models and produce a comparative analysis.")

    st.markdown("""
    <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:1rem; margin-bottom:1rem;">
        <p style="color:#00d4ff; font-family:IBM Plex Mono; font-size:0.8rem; margin:0 0 6px;">USE CASE</p>
        <p style="color:#e0e0f0; font-size:0.82rem; margin:0; line-height:1.6;">
            Compare vendor AI offerings before procurement decision ·
            Benchmark fine-tuned vs base model · Produce regulatory evidence ·
            Demonstrate your chosen solution is safer than alternatives
        </p>
    </div>
    """, unsafe_allow_html=True)

    num_models = st.number_input("Number of models to compare", min_value=2, max_value=5, value=2)
    mm_configs = []

    for i in range(int(num_models)):
        st.markdown(f"**Model {i+1}**")
        c1, c2, c3 = st.columns(3)
        with c1:
            mm_type = st.selectbox("Provider", ["huggingface","openai","anthropic","aws_bedrock","azure_openai","gcp_vertex","ollama"], key=f"mm_type_{i}")
        with c2:
            mm_name = st.text_input("Model ID", value="google/flan-t5-small", key=f"mm_name_{i}")
        with c3:
            mm_label = st.text_input("Label", value=f"Model {i+1}", key=f"mm_label_{i}")
        mm_key = None
        if mm_type != "huggingface":
            mm_key = st.text_input(f"API Key {i+1}", type="password", key=f"mm_key_{i}")
        mm_configs.append({"type": mm_type, "name": mm_name, "label": mm_label, "api_key": mm_key})
        st.markdown("---")

    mm_domain = st.radio("Domain", ["general","healthcare","finance"], horizontal=True, key="mm_domain")

    if st.button("🔀 RUN MULTI-MODEL COMPARISON", use_container_width=True):
        mm_progress = st.progress(0)
        mm_status   = st.empty()
        try:
            from core.multi_model import MultiModelOrchestrator
            orch = MultiModelOrchestrator(mm_configs)
            results = orch.run_comparison(domain=mm_domain,
                progress_callback=lambda p,m: (mm_progress.progress(min(p,1.0)), mm_status.text(m)))
            report = orch.generate_comparison_report(results, output_path="reports/multi_model_comparison.json")
            mm_progress.progress(1.0)
            st.markdown('<p class="section-header">Results</p>', unsafe_allow_html=True)
            cols = st.columns(len(report["models"]))
            for col, model in zip(cols, report["models"]):
                with col:
                    v = model.get("verdict","ERROR")
                    c = {"PASS":"#28a745","FAIL":"#dc3545","CONDITIONAL PASS":"#ffc107"}.get(v,"#6c757d")
                    st.markdown(f"""<div style="background:#1a1a2e;border:2px solid {c};border-radius:8px;padding:1rem;text-align:center;">
                    <p style="color:#e0e0f0;font-weight:600;margin:0 0 4px;">{model.get('label')}</p>
                    <p style="color:{c};font-family:IBM Plex Mono;font-size:1.1rem;font-weight:700;margin:0;">{v}</p>
                    <p style="color:#8888aa;font-size:0.75rem;margin:4px 0 0;">Avg Risk: {model.get('avg_risk','?')}/5 · {model.get('pass_rate','?')} pass</p>
                    </div>""", unsafe_allow_html=True)
            if report.get("recommendation"):
                st.success(f"**Recommended:** {report['recommendation']['recommended_model']} — {report['recommendation']['reason']}")
            with st.expander("📊 Full Comparison Data"):
                st.json(report.get("comparison", {}))
        except Exception as e:
            st.error(f"Comparison failed: {str(e)}")


# ════════════════════════════════════════════════════════════════════════
# TAB 6: CONTINUOUS MONITORING + ENTERPRISE + AUDIT LOG
# ════════════════════════════════════════════════════════════════════════

with tab_monitor:
    st.markdown('<p class="section-header">🔴 Continuous Security Monitoring</p>', unsafe_allow_html=True)

    mon_sub = st.radio("Section", ["Monitoring", "Enterprise Integrations", "Audit Log", "Shadow Prod"], horizontal=True)

    # ── MONITORING ────────────────────────────────────────────────────────
    if mon_sub == "Monitoring":
        st.caption("Run scheduled re-audits and detect regression from baseline.")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            mon_interval = st.number_input("Interval (minutes)", min_value=5, max_value=1440, value=60)
        with col_m2:
            mon_domain   = st.selectbox("Domain", ["general","healthcare","finance"], key="mon_dom")

        if "monitor_instance" not in st.session_state:
            st.session_state.monitor_instance = None

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("📸 SET BASELINE", use_container_width=True):
                if "findings" in st.session_state and st.session_state.findings:
                    try:
                        from core.monitoring import SecurityMonitor
                        mon = SecurityMonitor(None, domain=mon_domain, interval_minutes=mon_interval)
                        baseline = mon.set_baseline(st.session_state.findings)
                        st.success(f"Baseline saved: {baseline['verdict']} | avg_risk={baseline['avg_risk']}")
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Run an audit first to set baseline.")

        with col_b2:
            if st.button("▶ RUN ONCE NOW", use_container_width=True):
                if "findings" not in st.session_state:
                    st.warning("Run a full audit first.")
                else:
                    st.info("Load your model in the sidebar and click RUN ONCE — monitoring uses the active model.")

        with col_b3:
            import os
            from pathlib import Path
            baseline_exists = os.path.exists("reports/monitoring_baseline.json")
            alerts_exist    = os.path.exists("logs/security_alerts.jsonl")
            st.metric("Baseline", "SET ✅" if baseline_exists else "NOT SET ❌")

        # Show baseline and alerts
        if baseline_exists:
            import json
            with open("reports/monitoring_baseline.json") as f:
                b = json.load(f)
            st.markdown("**Current Baseline:**")
            st.json(b)

        if alerts_exist:
            import json
            st.markdown("**Recent Alerts:**")
            alerts = []
            with open("logs/security_alerts.jsonl") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            alerts.append(json.loads(line))
                        except Exception:
                            pass
            if alerts:
                for alert in alerts[-5:]:
                    sev = alert.get("severity","INFO")
                    col = {"CRITICAL":"#dc3545","HIGH":"#fd7e14","MEDIUM":"#ffc107"}.get(sev,"#28a745")
                    st.markdown(f"<div style='border-left:4px solid {col};padding:8px;margin:4px 0;background:#1a1a2e;'>"
                               f"<b style='color:{col};'>[{sev}]</b> <span style='color:#e0e0f0;'>{alert.get('message','')}</span>"
                               f"</div>", unsafe_allow_html=True)

    # ── ENTERPRISE INTEGRATIONS ───────────────────────────────────────────
    elif mon_sub == "Enterprise Integrations":
        st.caption("Configure Slack, Teams, PagerDuty, Jira and SIEM webhooks for audit alerts.")

        with st.expander("🔔 Slack"):
            slack_url = st.text_input("Slack Webhook URL", type="password", placeholder="https://hooks.slack.com/services/...", key="slack_url")
            if slack_url:
                os.environ["SLACK_WEBHOOK_URL"] = slack_url
                st.success("Slack configured — will fire on next audit completion.")

        with st.expander("💬 Microsoft Teams"):
            teams_url = st.text_input("Teams Webhook URL", type="password", placeholder="https://outlook.office.com/webhook/...", key="teams_url")
            if teams_url:
                os.environ["TEAMS_WEBHOOK_URL"] = teams_url
                st.success("Teams configured.")

        with st.expander("🚨 PagerDuty"):
            pd_key = st.text_input("PagerDuty Routing Key", type="password", key="pd_key")
            if pd_key:
                os.environ["PAGERDUTY_ROUTING_KEY"] = pd_key
                st.success("PagerDuty configured — critical findings will trigger incidents.")

        with st.expander("🎫 Jira"):
            col_j1, col_j2 = st.columns(2)
            with col_j1:
                jira_url   = st.text_input("Jira URL", placeholder="https://yourorg.atlassian.net", key="jira_url_input")
                jira_email = st.text_input("Jira Email", key="jira_email_input")
            with col_j2:
                jira_token = st.text_input("Jira API Token", type="password", key="jira_token_input")
                jira_proj  = st.text_input("Project Key", value="AI", key="jira_proj_input")
            if jira_url and jira_token:
                os.environ["JIRA_URL"]         = jira_url
                os.environ["JIRA_EMAIL"]        = jira_email
                os.environ["JIRA_API_TOKEN"]    = jira_token
                os.environ["JIRA_PROJECT_KEY"]  = jira_proj
                st.success("Jira configured — critical findings will create tickets.")

        with st.expander("📡 SIEM / Generic Webhook"):
            siem_url = st.text_input("SIEM Webhook URL", type="password", placeholder="https://your-siem.com/events", key="siem_url")
            siem_key = st.text_input("API Key (optional)", type="password", key="siem_key")
            if siem_url:
                os.environ["SIEM_WEBHOOK_URL"] = siem_url
                if siem_key:
                    os.environ["SIEM_API_KEY"] = siem_key
                st.success("SIEM configured — all audit events will be forwarded.")

        st.markdown("---")
        st.caption("Configured integrations will fire automatically after every audit run.")

        # Test button
        if st.button("🧪 TEST ALL CONFIGURED INTEGRATIONS"):
            from core.enterprise import EnterpriseIntegration
            ei = EnterpriseIntegration()
            configured = ei.get_configured()
            if configured:
                test_findings = [{"name": "Test", "passed": True, "category": "Test",
                                  "risk_matrix": {"overall": 1.0, "label": "LOW"}}]
                results = ei.dispatch_all("PASS", test_findings, "TestModel")
                st.json(results)
            else:
                st.warning("No integrations configured yet.")

    # ── AUDIT LOG ─────────────────────────────────────────────────────────
    elif mon_sub == "Audit Log":
        st.caption("Forensic audit trail with SHA256 hash chain integrity.")

        import os, json
        log_path = "logs/audit.jsonl"
        if os.path.exists(log_path):
            entries = []
            with open(log_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except Exception:
                            pass

            col_l1, col_l2, col_l3 = st.columns(3)
            col_l1.metric("Total Entries", len(entries))
            col_l2.metric("Sessions", len(set(e.get("session_id","") for e in entries)))
            col_l3.metric("Errors", sum(1 for e in entries if e.get("event_type") == "ERROR"))

            # Chain integrity check
            if st.button("🔐 VERIFY CHAIN INTEGRITY"):
                try:
                    if _audit_log:
                        valid, msg, broken_at = _audit_log.verify_chain_integrity()
                        if valid:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ TAMPERED: {msg} at entry {broken_at}")
                except Exception as e:
                    st.error(str(e))

            # Show recent entries
            st.markdown("**Recent Audit Log Entries:**")
            import pandas as pd
            df_data = [{
                "Time":    e.get("timestamp","")[:19],
                "Event":   e.get("event_type",""),
                "Severity":e.get("severity",""),
                "Message": e.get("details",{}).get("message","")[:60]
            } for e in entries[-50:]]
            if df_data:
                st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
        else:
            st.info("No audit log yet. Run an audit to start logging.")

    # ── SHADOW PROD ───────────────────────────────────────────────────────
    elif mon_sub == "Shadow Prod":
        st.caption("Test against real production traffic samples with PII automatically scrubbed.")

        st.markdown("""
        <div style="background:#1a2e1a;border:1px solid #28a745;border-radius:8px;padding:1rem;margin-bottom:1rem;">
        <p style="color:#28a745;font-family:IBM Plex Mono;font-size:0.8rem;margin:0 0 4px;">HOW IT WORKS</p>
        <p style="color:#e0e0f0;font-size:0.82rem;margin:0;line-height:1.6;">
        Place production log files (JSON or TXT) in a <code>prod_logs/</code> folder.
        The sampler strips all PII automatically then runs those real prompts through the model.
        This catches failure modes that synthetic tests miss.
        </p></div>
        """, unsafe_allow_html=True)

        prod_path  = st.text_input("Production Logs Path", value="./prod_logs/")
        max_samp   = st.number_input("Max samples", min_value=10, max_value=500, value=50)

        if st.button("🔬 RUN SHADOW PROD TEST", use_container_width=True):
            from shadow_prod.shadow_testing import ShadowSampler
            sampler = ShadowSampler(prod_logs_path=prod_path, max_samples=max_samp)
            prompts = sampler.sample()
            if prompts:
                test_suite = sampler.prompts_to_test_suite(prompts)
                st.success(f"Sampled {len(prompts)} production prompts (PII scrubbed). "
                          f"Go to sidebar, run Standard audit — results will include shadow prod tests.")
                st.session_state["shadow_tests"] = test_suite
            else:
                st.warning(f"No prompts found in {prod_path}. Place production log files there first.")


# ════════════════════════════════════════════════════════════════════════
# TAB 7: ABOUT
# ════════════════════════════════════════════════════════════════════════

with tab_about:
    st.markdown('<p class="section-header">About AITestSuite v3</p>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
        <div class="about-card">
            <p style="color:#00d4ff; font-family:IBM Plex Mono; font-size:0.8rem; margin:0 0 8px;">
                DEFAULT TEST SUITE
            </p>
            <ul style="color:#e0e0f0; font-size:0.85rem; margin:0; padding-left:1.2rem;">
                <li>Hallucination detection (factual and clinical)</li>
                <li>Bias detection (gender, age, racial)</li>
                <li>Prompt injection (basic, chained, override)</li>
                <li>Jailbreak attempts (DAN, roleplay, extreme)</li>
                <li>Privacy leakage (PII, training data, system prompt)</li>
                <li>Data exfiltration (credentials, environment)</li>
                <li>Model extraction (architecture probing)</li>
                <li>Adversarial misalignment and social engineering</li>
                <li>RAG exploitation (poisoning, injection, triggers)</li>
                <li>SQL injection assistance detection</li>
                <li>DoS and resource exhaustion</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div class="about-card">
            <p style="color:#7b2fff; font-family:IBM Plex Mono; font-size:0.8rem; margin:0 0 8px;">
                DOMAIN FLAGS
            </p>
            <ul style="color:#e0e0f0; font-size:0.85rem; margin:0; padding-left:1.2rem;">
                <li>🏥 Healthcare — Clinical facts, drug safety, HIPAA/PIPEDA, emergency response, mental health crisis</li>
                <li>💰 Finance — SOX/GDPR, investment disclaimers, AML, credit bias</li>
                <li>⚖️ Legal — Privilege protection, legal advice disclaimers</li>
                <li>🏛️ Government — Classified info, political neutrality, propaganda detection</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card">
        <p style="color:#fd7e14; font-family:IBM Plex Mono; font-size:0.8rem; margin:0 0 8px;">
            RISK MATRIX SCORING
        </p>
        <p style="color:#e0e0f0; font-size:0.85rem; margin:0;">
            Each finding scored 1–5 across four dimensions:
            <b>Severity</b> (30%) · <b>Likelihood</b> (20%) · <b>Impact</b> (30%) · <b>Regulatory Exposure</b> (20%)<br><br>
            Overall score determines verdict:
            <span style="color:#28a745;">✓ PASS</span> |
            <span style="color:#ffc107;">⚠ CONDITIONAL PASS</span> |
            <span style="color:#dc3545;">✗ FAIL</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card">
        <p style="color:#00d4ff; font-family:IBM Plex Mono; font-size:0.8rem; margin:0 0 8px;">
            REGULATORY FRAMEWORK
        </p>
        <p style="color:#8888aa; font-size:0.82rem; margin:0; line-height:1.8;">
            PIPEDA (Canada) · HIPAA Privacy Rule (US) · GDPR (EU) · EU AI Act ·
            BC FIPPA · BC Human Rights Code · BC Mental Health Act ·
            Health Canada AI Guidance · BC Patient Safety Standards ·
            NIST AI Risk Management Framework · SOX · FINRA · Criminal Code of Canada
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(
        "AITestSuite v3 | Amarjit Khakh | "
        "For authorised security testing only"
    )


# ════════════════════════════════════════════════════════════════════════
# AUDIT EXECUTION ENGINE
# Triggered when LAUNCH AUDIT button is clicked
# Runs in the dashboard tab context
# ════════════════════════════════════════════════════════════════════════

if run_button:
    with tab_dashboard:
        st.markdown('<p class="section-header">⚡ Audit In Progress</p>', unsafe_allow_html=True)

        progress_bar = st.progress(0)
        status_text  = st.empty()
        all_findings = []

        try:
            # ── Step 1: Load the target model ─────────────────────────
            status_text.text(f"Loading {model_type} model: {model_name}...")
            from models.model_adapter import ModelAdapter
            adapter = ModelAdapter(
                model_type=model_type,
                model_name=model_name,
                api_key=api_key
            )
            with st.spinner(f"Initialising {model_name}..."):
                adapter.load()

            # ── Step 2: Build core test suite ─────────────────────────
            from tests.default_tests import DEFAULT_TESTS
            test_suite = list(DEFAULT_TESTS)

            # Always load advanced tests alongside default
            from tests.advanced_tests import ADVANCED_TESTS
            test_suite += ADVANCED_TESTS

            # Include shadow prod tests if available
            if "shadow_tests" in st.session_state and st.session_state.shadow_tests:
                test_suite += st.session_state.shadow_tests
                status_text.text(f"Loaded {len(st.session_state.shadow_tests)} shadow prod prompts")
            elif domain == "finance":
                from domains.finance import FINANCE_TESTS
                test_suite += FINANCE_TESTS
            elif domain in ["legal", "government"]:
                from domains.government_legal import LEGAL_TESTS, GOVERNMENT_TESTS
                test_suite += LEGAL_TESTS + GOVERNMENT_TESTS

            def update_progress(pct, msg):
                progress_bar.progress(min(float(pct), 1.0))
                status_text.text(msg)

            # ══════════════════════════════════════════════════════════
            # STANDARD MODE — Single run, all default tests
            # ══════════════════════════════════════════════════════════
            if audit_mode in ["standard", "full"]:
                status_text.text(f"Standard mode — running {len(test_suite)} tests (parallel workers: {parallel_workers})...")
                from core.automation import BatchRunner
                runner = BatchRunner(
                    model_adapter=adapter,
                    domain=domain if domain != "general" else None,
                    max_workers=parallel_workers,
                    progress_callback=update_progress
                )
                findings = runner.run_batch(test_suite)
                all_findings += findings

            # ══════════════════════════════════════════════════════════
            # STATISTICAL MODE — 5 runs per test for consistency scoring
            # ══════════════════════════════════════════════════════════
            if audit_mode in ["statistical", "full"]:
                status_text.text(f"Statistical mode — {runs_per_test} runs × {len(test_suite)} tests...")
                from core.statistical_runner import StatisticalRunner
                stat_runner = StatisticalRunner(
                    model_adapter=adapter,
                    domain=domain if domain != "general" else None,
                    runs_per_test=runs_per_test,
                    progress_callback=update_progress
                )
                stat_findings = stat_runner.run(test_suite)
                # In full mode, statistical results augment standard results
                # In statistical-only mode, they ARE the results
                if audit_mode == "statistical":
                    all_findings = stat_findings
                else:
                    # Merge: add statistical data to matching standard findings
                    stat_by_name = {f["name"]: f for f in stat_findings}
                    for f in all_findings:
                        if f["name"] in stat_by_name:
                            f["statistical"] = stat_by_name[f["name"]].get("statistical", {})

            # ══════════════════════════════════════════════════════════
            # MULTI-TURN MODE — Attack chain sequences
            # ══════════════════════════════════════════════════════════
            if audit_mode in ["multiturn", "full"]:
                from tests.multi_turn_tests import MULTI_TURN_CHAINS
                status_text.text(f"Multi-turn mode — running {len(MULTI_TURN_CHAINS)} attack chains...")
                from core.statistical_runner import MultiTurnRunner
                mt_runner = MultiTurnRunner(
                    model_adapter=adapter,
                    domain=domain if domain != "general" else None,
                    progress_callback=update_progress
                )
                mt_findings = mt_runner.run(MULTI_TURN_CHAINS)
                all_findings += mt_findings

            # ══════════════════════════════════════════════════════════
            # GARAK / EXTENDED PROBE MODE
            # ══════════════════════════════════════════════════════════
            if use_garak or audit_mode == "full":
                status_text.text("Running extended probe library...")
                from core.garak_bridge import get_probes, run_garak_probes, EXTENDED_FALLBACK_PROBES
                from core.runner import AuditRunner
                from core.scoring import RiskScorer

                probes, source = get_probes(use_garak=use_garak, model_name=model_name, model_type=model_type)

                if source == "garak":
                    # Run actual Garak probes
                    garak_results = run_garak_probes(model_name, model_type)
                    if garak_results:
                        scorer = RiskScorer()
                        for f in garak_results:
                            all_findings.append(scorer.score(f))
                else:
                    # Run extended fallback probes through normal runner
                    ext_runner = AuditRunner(
                        model_adapter=adapter,
                        domain=domain if domain != "general" else None,
                        progress_callback=update_progress
                    )
                    ext_findings = ext_runner.run(EXTENDED_FALLBACK_PROBES)
                    all_findings += ext_findings

            # ══════════════════════════════════════════════════════════
            # FUZZING MODE — 14 mutation strategies, parallel execution
            # ══════════════════════════════════════════════════════════
            if audit_mode in ["fuzzing", "full"]:
                status_text.text(f"Fuzzing mode — {mutations_per_seed} mutations per seed prompt...")
                from tests.fuzzer import FuzzEngine
                from core.scoring import RiskScorer as RS2
                fuzz_engine = FuzzEngine(adapter, max_workers=parallel_workers)
                fuzz_results = fuzz_engine.fuzz(
                    mutations_per_seed=mutations_per_seed,
                    progress_callback=update_progress
                )
                scorer2 = RS2()
                for f in fuzz_results:
                    all_findings.append(scorer2.score(f))

                # Show fuzz summary
                fuzz_summary = fuzz_engine.summary()
                if fuzz_summary.get("dangerous_hits", 0) > 0:
                    st.warning(
                        f"🔴 Fuzzing detected {fuzz_summary['dangerous_hits']} potential bypasses "
                        f"({fuzz_summary['hit_rate']} hit rate) via: "
                        f"{', '.join(fuzz_summary.get('vulnerable_mutations', []))}"
                    )

            # ══════════════════════════════════════════════════════════
            # EVOLUTIONARY JAILBREAK MODE
            # ══════════════════════════════════════════════════════════
            if audit_mode in ["evolutionary", "full"]:
                status_text.text(
                    f"Evolutionary jailbreak — {evo_generations} generations × "
                    f"{evo_population} population..."
                )
                from tests.evolutionary_jailbreak import EvolutionaryJailbreak
                from core.scoring import RiskScorer as RS3
                evo = EvolutionaryJailbreak(adapter)
                evo_results = evo.evolve(
                    generations=evo_generations,
                    population_size=evo_population,
                    progress_callback=update_progress
                )
                scorer3 = RS3()
                for f in evo_results:
                    all_findings.append(scorer3.score(f))
                bypasses = len(evo.best_hits)
                if bypasses > 0:
                    st.warning(f"🔴 Evolutionary engine found {bypasses} potential bypasses across {evo_generations} generations")

            # ── AGENT & TOOL EXPLOITATION ─────────────────────────────────
            if audit_mode == "full":
                status_text.text("Agent & tool exploitation testing — 8 scenarios...")
                from tests.agent_exploit import AgentExploitEngine
                ae = AgentExploitEngine(adapter, progress_callback=update_progress)
                ae_results = ae.run()
                all_findings += ae_results

            # ── SEMANTIC EVALUATION — enrich responses ────────────────────
            if audit_mode in ["statistical", "full"]:
                status_text.text("Running semantic evaluation on findings...")
                try:
                    from core.semantic_eval import SemanticEvaluator
                    evaluator = SemanticEvaluator(use_embeddings=False)
                    for f in all_findings:
                        response = f.get("response", "")
                        sem = evaluator.semantic_pass_fail(response)
                        f["semantic"] = sem
                        # Override pass/fail if semantic says dangerous
                        if sem.get("is_dangerous") and f.get("passed"):
                            f["passed"]              = False
                            f["semantic_override"]   = True
                except Exception:
                    pass

            # ── Step 3: Score and determine verdict ───────────────────────
            from core.scoring import RiskScorer
            scorer  = RiskScorer()
            verdict = scorer.verdict(all_findings)

            # ── Enrich findings with OWASP + MITRE mappings ───────────────
            try:
                from core.frameworks import enrich_all_findings
                all_findings = enrich_all_findings(all_findings)
            except Exception:
                pass

            # ── Log to audit trail ────────────────────────────────────────
            try:
                if _audit_log:
                    _audit_log.log_audit_complete(
                        len(all_findings),
                        sum(1 for f in all_findings if f.get("passed")),
                        sum(1 for f in all_findings if not f.get("passed")),
                        verdict
                    )
            except Exception:
                pass

            # ── Fire enterprise integrations ──────────────────────────────
            try:
                from core.enterprise import EnterpriseIntegration
                ei = EnterpriseIntegration()
                configured = ei.get_configured()
                if configured:
                    status_text.text(f"Dispatching to: {', '.join(configured)}...")
                    ei.dispatch_all(verdict, all_findings, model_name)
            except Exception:
                pass

            # ── Step 4: Store in session state ────────────────────────────
            st.session_state.findings   = all_findings
            st.session_state.verdict    = verdict
            st.session_state.model_name = model_name
            st.session_state.model_type = model_type
            st.session_state.audit_mode = audit_mode

            progress_bar.progress(1.0)
            status_text.text(
                f"✅ Audit complete — {len(all_findings)} findings | "
                f"Verdict: {verdict} | Mode: {audit_mode.upper()}"
            )
            time.sleep(0.8)
            st.rerun()

        except Exception as e:
            st.error(f"❌ Audit failed: {str(e)}")
            st.info(
                "Common fixes:\n"
                "- Check model name spelling\n"
                "- Verify API key is correct\n"
                "- Check internet connection\n"
                "- For HuggingFace: ensure transformers is installed\n"
                "- For statistical mode on slow machines: reduce runs per test"
            )
