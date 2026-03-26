"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — PDF Report Generator
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Generates a professional audit report in PDF format.
    Suitable for submission to healthcare organisations,
    regulators, or any authorised audit engagement.

REPORT SECTIONS:
    1. Cover header with audit metadata
    2. Overall verdict banner (PASS / CONDITIONAL / FAIL)
    3. Executive summary
    4. Risk matrix summary table (all findings at a glance)
    5. Detailed findings (one section per test)
    6. Remediation recommendations
    7. Footer with generation timestamp

DEPENDENCIES:
    pip install reportlab
═══════════════════════════════════════════════════════════
"""

import os
import time

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        Table, TableStyle, HRFlowable, PageBreak
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ── Colour palette matching Streamlit UI ─────────────────────────────────
COLOUR_PRIMARY  = colors.HexColor("#1a1a2e")   # Dark navy
COLOUR_ACCENT   = colors.HexColor("#00d4ff")   # Cyan
COLOUR_PURPLE   = colors.HexColor("#7b2fff")   # Purple
COLOUR_PASS     = colors.HexColor("#28a745")   # Green
COLOUR_WARN     = colors.HexColor("#ffc107")   # Amber
COLOUR_FAIL     = colors.HexColor("#dc3545")   # Red
COLOUR_LIGHT    = colors.HexColor("#f5f5f5")   # Light grey

# ── Risk score → reportlab colour ────────────────────────────────────────
RISK_COLOURS_RL = {
    1: colors.HexColor("#28a745"),
    2: colors.HexColor("#85c44d"),
    3: colors.HexColor("#ffc107"),
    4: colors.HexColor("#fd7e14"),
    5: colors.HexColor("#dc3545")
}


class ReportGenerator:
    """
    Generates a professional PDF audit report from a set of scored findings.
    """

    def __init__(self, output_dir="reports"):
        """
        Args:
            output_dir : Directory to save generated PDFs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, findings, verdict, model_info, domain=None, auditor_name="AITestSuite v3"):
        """
        Generate the full PDF report.

        Args:
            findings      : List of scored finding dicts
            verdict       : Overall verdict string
            model_info    : Dict with model_name and model_type
            domain        : Optional domain flag
            auditor_name  : Name of the auditor for the report cover

        Returns:
            Path to the generated PDF file
        """
        # ── File naming ───────────────────────────────────────────────────
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        domain_label = domain.upper() if domain else "GENERAL"
        filename = f"{self.output_dir}/AIAuditReport_{domain_label}_{timestamp}.pdf"

        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm,   bottomMargin=2*cm
        )

        # ── Build styles ──────────────────────────────────────────────────
        base   = getSampleStyleSheet()
        styles = self._build_styles(base)
        story  = []

        # ── Build report sections ─────────────────────────────────────────
        story += self._section_header(styles, model_info, domain_label, auditor_name, len(findings))
        story += self._section_verdict(styles, verdict)
        story += self._section_executive_summary(styles, findings, verdict, domain_label)
        story += self._section_deployment_readiness(styles, findings)
        story += self._section_risk_matrix(styles, findings)
        story += self._section_statistical_summary(styles, findings)
        story.append(PageBreak())
        story += self._section_detailed_findings(styles, findings)
        story += self._section_recommendations(styles, findings)
        story += self._section_footer(styles)

        doc.build(story)
        return filename

    # ── STYLE DEFINITIONS ────────────────────────────────────────────────

    def _build_styles(self, base):
        """Create all custom paragraph styles for the report."""
        return {
            "title": ParagraphStyle("RptTitle",
                parent=base["Title"], fontSize=22,
                textColor=COLOUR_PRIMARY, spaceAfter=4),

            "subtitle": ParagraphStyle("RptSubtitle",
                parent=base["Normal"], fontSize=10,
                textColor=colors.HexColor("#4a4a6a"), spaceAfter=3),

            "section": ParagraphStyle("RptSection",
                parent=base["Heading2"], fontSize=13,
                textColor=COLOUR_PRIMARY, spaceBefore=12, spaceAfter=6),

            "body": ParagraphStyle("RptBody",
                parent=base["Normal"], fontSize=9,
                textColor=colors.HexColor("#333333"), spaceAfter=4, leading=14),

            "verdict": ParagraphStyle("RptVerdict",
                parent=base["Normal"], fontSize=18,
                textColor=colors.white, alignment=TA_CENTER,
                fontName="Helvetica-Bold"),

            "finding_header": ParagraphStyle("RptFindingHdr",
                parent=base["Normal"], fontSize=10,
                textColor=colors.white, fontName="Helvetica-Bold"),

            "footer": ParagraphStyle("RptFooter",
                parent=base["Normal"], fontSize=7,
                textColor=colors.HexColor("#999999"), alignment=TA_CENTER),

            "cell": ParagraphStyle("RptCell",
                parent=base["Normal"], fontSize=8,
                textColor=colors.HexColor("#333333"), leading=11),

            "body_small": ParagraphStyle("RptBodySmall",
                parent=base["Normal"], fontSize=7.5,
                textColor=colors.HexColor("#333333"), leading=10,
                wordWrap="LTR", splitLongWords=True),
        }

    # ── REPORT SECTIONS ──────────────────────────────────────────────────

    def _section_header(self, styles, model_info, domain_label, auditor_name, test_count):
        """Cover header block with metadata table."""
        story = []

        story.append(Paragraph("AITestSuite v3", styles["title"]))
        story.append(Paragraph("AI Security & Governance Audit Report", styles["subtitle"]))
        story.append(HRFlowable(width="100%", thickness=2, color=COLOUR_PRIMARY))
        story.append(Spacer(1, 0.3*cm))

        meta = [
            ["Audit Date",    time.strftime("%B %d, %Y at %H:%M")],
            ["Model Audited", model_info.get("model_name", "Unknown")],
            ["Model Type",    model_info.get("model_type", "Unknown").upper()],
            ["Audit Domain",  domain_label],
            ["Total Tests",   str(test_count)],
            ["Auditor",       auditor_name],
            ["Toolkit",       "AITestSuite v3"],
        ]

        t = Table(meta, colWidths=[4*cm, 12*cm])
        t.setStyle(TableStyle([
            ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
            ("TEXTCOLOR",  (0,0), (0,-1), COLOUR_PRIMARY),
            ("BACKGROUND", (0,0), (0,-1), COLOUR_LIGHT),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#fafafa")]),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING",    (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))
        return story

    def _section_verdict(self, styles, verdict):
        """Coloured verdict banner — PASS / CONDITIONAL PASS / FAIL."""
        story = []

        colour_map = {
            "PASS":             COLOUR_PASS,
            "CONDITIONAL PASS": COLOUR_WARN,
            "FAIL":             COLOUR_FAIL,
            "INCONCLUSIVE":     colors.HexColor("#6c757d")
        }
        bg = colour_map.get(verdict, colors.HexColor("#6c757d"))

        t = Table(
            [[Paragraph(f"OVERALL AUDIT VERDICT:  {verdict}", styles["verdict"])]],
            colWidths=[16*cm]
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg),
            ("PADDING",    (0,0), (-1,-1), 14),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))
        return story

    def _section_executive_summary(self, styles, findings, verdict, domain_label):
        """Plain English summary of the audit for executives and clinical managers."""
        story = []
        story.append(Paragraph("Executive Summary", styles["section"]))

        passed   = sum(1 for f in findings if f.get("passed"))
        failed   = len(findings) - passed
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
        high     = sum(1 for f in findings if 3.5 <= f.get("risk_matrix", {}).get("overall", 0) < 4.5)

        domain_txt = f"with {domain_label} domain-specific scenarios included" if domain_label != "GENERAL" else ""

        # Verdict specific conclusion text
        conclusion_map = {
            "FAIL":             "⚠ This model presents significant safety risks and MUST NOT be deployed without remediation.",
            "CONDITIONAL PASS": "This model requires specific remediations before deployment is recommended.",
            "PASS":             "This model meets baseline safety requirements for the tested scenarios.",
            "INCONCLUSIVE":     "Insufficient tests were run to determine deployment suitability."
        }
        conclusion = conclusion_map.get(verdict, "")

        summary = f"""
        This audit evaluated the target AI model across <b>{len(findings)} test cases</b> covering
        hallucination detection, bias assessment, prompt injection vulnerability, privacy leakage,
        and adversarial robustness{" " + domain_txt if domain_txt else ""}.
        <br/><br/>
        Of {len(findings)} tests: <b>{passed} passed</b> and <b>{failed} failed</b>.
        The audit identified <b>{critical} critical</b> and <b>{high} high severity</b> findings.
        <br/><br/>
        <b>{conclusion}</b>
        """
        story.append(Paragraph(summary, styles["body"]))
        story.append(Spacer(1, 0.3*cm))
        return story

    def _section_risk_matrix(self, styles, findings):
        """Summary risk matrix table — all findings at a glance."""
        story = []
        story.append(Paragraph("Risk Matrix Summary", styles["section"]))

        # Table headers
        headers = ["#", "Test Name", "Category", "Sev", "Like", "Imp", "Reg", "Score", "Result"]
        # cell style for wrapping
        cs = styles["body_small"]
        data = [headers]

        for i, f in enumerate(findings):
            rm = f.get("risk_matrix", {})
            data.append([
                Paragraph(str(i + 1), cs),
                Paragraph(f.get("name", "")[:60], cs),
                Paragraph(f.get("category", "")[:35], cs),
                Paragraph(str(rm.get("severity",   "-")), cs),
                Paragraph(str(rm.get("likelihood", "-")), cs),
                Paragraph(str(rm.get("impact",     "-")), cs),
                Paragraph(str(rm.get("regulatory", "-")), cs),
                Paragraph(str(rm.get("overall",    "-")), cs),
                Paragraph("PASS" if f.get("passed") else "FAIL", cs),
            ])

        # letter page: 21.59cm - 4cm margins = 17.59cm usable
        t = Table(data, colWidths=[0.6*cm, 4.8*cm, 3.2*cm, 1.0*cm, 1.0*cm, 1.0*cm, 1.0*cm, 1.5*cm, 1.5*cm],
                  repeatRows=1)

        ts = [
            ("FONTNAME",       (0,0),  (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0,0),  (-1,-1), 7.5),
            ("BACKGROUND",     (0,0),  (-1,0),  COLOUR_PRIMARY),
            ("TEXTCOLOR",      (0,0),  (-1,0),  colors.white),
            ("GRID",           (0,0),  (-1,-1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING",        (0,0),  (-1,-1), 5),
            ("ROWBACKGROUNDS", (0,1),  (-1,-1), [colors.white, colors.HexColor("#fafafa")]),
            ("VALIGN",         (0,0),  (-1,-1), "MIDDLE"),
        ]

        # Colour overall score cells and result cells per row
        for i, f in enumerate(findings):
            rm      = f.get("risk_matrix", {})
            overall = rm.get("overall", 0)
            colour  = RISK_COLOURS_RL.get(round(overall), colors.HexColor("#6c757d"))
            row     = i + 1
            ts.append(("BACKGROUND", (7, row), (7, row), colour))
            ts.append(("TEXTCOLOR",  (7, row), (7, row), colors.white))
            ts.append(("FONTNAME",   (7, row), (7, row), "Helvetica-Bold"))
            result_colour = COLOUR_PASS if f.get("passed") else COLOUR_FAIL
            ts.append(("TEXTCOLOR",  (8, row), (8, row), result_colour))
            ts.append(("FONTNAME",   (8, row), (8, row), "Helvetica-Bold"))

        t.setStyle(TableStyle(ts))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))
        return story

    def _section_detailed_findings(self, styles, findings):
        """One detailed block per finding with full context."""
        story = []
        story.append(Paragraph("Detailed Findings", styles["section"]))

        for i, f in enumerate(findings):
            rm      = f.get("risk_matrix", {})
            overall = rm.get("overall", 0)
            colour  = RISK_COLOURS_RL.get(round(overall), colors.HexColor("#6c757d"))
            passed  = f.get("passed", False)

            # ── Finding header bar ────────────────────────────────────────
            header_text = (
                f"Finding {i+1}: {f.get('name', '')}  |  "
                f"Risk: {overall}/5 ({rm.get('label', '')})  |  "
                f"{'PASS' if passed else 'FAIL'}"
            )
            hdr = Table(
                [[Paragraph(header_text, styles["finding_header"])]],
                colWidths=[16*cm]
            )
            hdr.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), colour),
                ("PADDING",    (0,0), (-1,-1), 8),
            ]))
            story.append(hdr)

            # ── Finding detail table ──────────────────────────────────────
            # All value cells wrapped in Paragraph so ReportLab word-wraps
            def _p(text):
                return Paragraph(str(text), styles["body_small"])

            detail = [
                ["Category",    _p(f.get("category", ""))],
                ["Domain",      _p(f.get("domain", "general").upper())],
                ["Timestamp",   _p(f.get("timestamp", ""))],
                ["Severity",    _p(f"{rm.get('severity','-')}/5 | Likelihood: {rm.get('likelihood','-')}/5 | Impact: {rm.get('impact','-')}/5 | Regulatory: {rm.get('regulatory','-')}/5")],
                ["Prompt Sent", _p(f.get("prompt", "")[:600])],
                ["Response",    _p(f.get("response", "")[:600])],
                ["Expected",    _p(f.get("expected", "N/A")[:300])],
            ]

            # Only add rows that have content
            if f.get("healthcare_implication") and f.get("healthcare_implication") != "N/A":
                detail.append(["Clinical Risk", _p(f.get("healthcare_implication", ""))])

            if f.get("regulations"):
                detail.append(["Regulations", _p(" | ".join(f.get("regulations", [])))])

            if f.get("remediation"):
                detail.append(["Remediation", _p(f.get("remediation", ""))])

            if f.get("references"):
                detail.append(["References", _p(" | ".join(f.get("references", [])))])

            dt = Table(detail, colWidths=[3.5*cm, 13.0*cm])
            dt.setStyle(TableStyle([
                ("FONTNAME",       (0,0),  (0,-1),  "Helvetica-Bold"),
                ("FONTSIZE",       (0,0),  (-1,-1), 8),
                ("TEXTCOLOR",      (0,0),  (0,-1),  COLOUR_PRIMARY),
                ("BACKGROUND",     (0,0),  (0,-1),  COLOUR_LIGHT),
                ("ROWBACKGROUNDS", (0,0),  (-1,-1), [colors.white, colors.HexColor("#fafafa")]),
                ("GRID",           (0,0),  (-1,-1), 0.5, colors.HexColor("#dddddd")),
                ("PADDING",        (0,0),  (-1,-1), 6),
                ("VALIGN",         (0,0),  (-1,-1), "TOP"),
            ]))
            story.append(dt)
            story.append(Spacer(1, 0.3*cm))

        return story

    def _section_statistical_summary(self, styles, findings):
        """Statistical consistency summary — only shown when statistical mode was used."""
        # Only show if findings have statistical data
        statistical_findings = [f for f in findings if "statistical" in f]
        if not statistical_findings:
            return []

        story = []
        story.append(Paragraph("Statistical Consistency Analysis", styles["section"]))
        story.append(Paragraph(
            "Tests were run multiple times to detect inconsistent behaviour. "
            "INCONSISTENT findings are highlighted as the most dangerous — "
            "they indicate a vulnerability exists but is intermittent.",
            styles["body"]
        ))

        headers = ["Test Name", "Runs", "Pass Rate", "Consistency", "Risk"]
        data    = [headers]

        for f in statistical_findings:
            stats = f.get("statistical", {})
            data.append([
                f.get("name", "")[:35],
                str(stats.get("runs", "-")),
                f"{stats.get('pass_rate', '-')}%",
                stats.get("consistency_label", "-"),
                f"{f.get('risk_matrix', {}).get('overall', '-')}/5"
            ])

        t = Table(data, colWidths=[6*cm, 1.5*cm, 2*cm, 4*cm, 2.5*cm])
        ts = [
            ("FONTNAME",   (0,0),  (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",   (0,0),  (-1,-1), 8),
            ("BACKGROUND", (0,0),  (-1,0),  COLOUR_PRIMARY),
            ("TEXTCOLOR",  (0,0),  (-1,0),  colors.white),
            ("GRID",       (0,0),  (-1,-1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING",    (0,0),  (-1,-1), 5),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fafafa")]),
        ]
        # Colour inconsistent rows orange
        for i, f in enumerate(statistical_findings):
            label = f.get("statistical", {}).get("consistency_label", "")
            if label == "INCONSISTENT":
                ts.append(("BACKGROUND", (3, i+1), (3, i+1), colors.HexColor("#fd7e14")))
                ts.append(("TEXTCOLOR",  (3, i+1), (3, i+1), colors.white))
                ts.append(("FONTNAME",   (3, i+1), (3, i+1), "Helvetica-Bold"))

        t.setStyle(TableStyle(ts))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))
        return story

    def _section_recommendations(self, styles, findings):
        """Consolidated remediation recommendations for all failed tests."""
        story = []
        story.append(Paragraph("Remediation Recommendations", styles["section"]))

        failed = [f for f in findings if not f.get("passed") and f.get("remediation")]

        if not failed:
            story.append(Paragraph(
                "No critical remediations required. Continue monitoring with periodic re-audits.",
                styles["body"]
            ))
        else:
            for f in failed:
                story.append(Paragraph(
                    f"<b>{f.get('name')}:</b> {f.get('remediation')}",
                    styles["body"]
                ))

        story.append(Spacer(1, 0.5*cm))
        return story

    def _section_deployment_readiness(self, styles, findings):
        """Clinical deployment readiness section with category gap analysis."""
        from core.scoring import RiskScorer
        scorer    = RiskScorer()
        readiness = scorer.deployment_readiness(findings)
        cats      = scorer.category_analysis(findings)

        story = []
        story.append(Paragraph("Clinical Deployment Readiness Assessment", styles["section"]))

        # Summary row
        dr_color = colors.HexColor("#27AE60") if readiness["deployment_ready"] else colors.HexColor("#C0392B")
        status   = "READY FOR CONDITIONAL DEPLOYMENT" if readiness["deployment_ready"] else "NOT READY FOR DEPLOYMENT"

        summary_data = [
            ["Deployment Status", status],
            ["Categories Meeting Minimum", f"{readiness['categories_meeting']} / {readiness['categories_total']}"],
            ["Blocking Issues",   str(len(readiness["blocking_categories"]))],
            ["Overall Recommendation", readiness["recommendation"][:120]],
        ]
        t = Table(summary_data, colWidths=[4*cm, 12*cm])
        t.setStyle(TableStyle([
            ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0),(-1,-1), 8),
            ("BACKGROUND",(0,0),(0,-1), colors.HexColor("#F0F0F8")),
            ("TEXTCOLOR", (1,0),(1,0), dr_color),
            ("FONTNAME",  (1,0),(1,0), "Helvetica-Bold"),
            ("GRID",      (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
            ("PADDING",   (0,0),(-1,-1), 5),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, colors.HexColor("#FAFAFA")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

        # Category gap table — only show failing categories
        failing = {cat: data for cat, data in cats.items() if not data["meets_minimum"]}
        if failing:
            story.append(Paragraph("Categories Below Clinical Minimum", styles.get("body", styles["section"])))
            story.append(Spacer(1, 0.1*cm))
            gap_data = [["Category", "Pass Rate", "Required", "Gap", "Critical"]]
            for cat, data in sorted(failing.items(), key=lambda x: x[1]["gap"], reverse=True)[:15]:
                gap_data.append([
                    cat[:35],
                    f"{data['pass_pct']}%",
                    f"{data['minimum_required']}%",
                    f"-{data['gap']}%",
                    str(data["critical"]),
                ])
            gt = Table(gap_data, colWidths=[6*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm])
            gt.setStyle(TableStyle([
                ("FONTNAME",     (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",     (0,0),(-1,-1), 8),
                ("BACKGROUND",   (0,0),(-1,0), colors.HexColor("#1F3864")),
                ("TEXTCOLOR",    (0,0),(-1,0), colors.white),
                ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
                ("PADDING",      (0,0),(-1,-1), 4),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#FFF5F5")]),
                ("TEXTCOLOR",    (3,1),(3,-1), colors.HexColor("#C0392B")),
                ("FONTNAME",     (3,1),(3,-1), "Helvetica-Bold"),
            ]))
            story.append(gt)
            story.append(Spacer(1, 0.3*cm))

        return story

    def _section_footer(self, styles):
        """Footer with generation info and disclaimer."""
        story = []
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))
        story.append(Paragraph(
            f"Generated by AITestSuite v3 | Amarjit Khakh | "
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} | For authorised security testing only",
            styles["footer"]
        ))
        return story
