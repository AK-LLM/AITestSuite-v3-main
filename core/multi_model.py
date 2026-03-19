"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Multi-Model Orchestration
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Run the same audit against multiple AI models simultaneously
    and produce a comparative analysis report.

    This is essential for:
    - Comparing vendor AI offerings before purchase decision
    - Benchmarking a fine-tuned model against its base model
    - Demonstrating that your model is SAFER than alternatives
    - Auditing model upgrades (before/after comparison)
    - Regulatory evidence that you evaluated multiple options

USE CASES FOR PHC VENTURES / FRASER HEALTH:
    "We evaluated three clinical AI vendors and
     AITestSuite v3 showed Vendor A failed 40% of
     safety tests, Vendor B failed 15%, and our
     chosen solution failed only 3%."

    That is a defensible procurement decision.

COMPARISON REPORT:
    - Side-by-side risk scores across all models
    - Category breakdown comparison (bias, injection etc)
    - Head-to-head verdict comparison
    - Recommendation based on comparative scoring
    - Full PDF report with comparative charts

USAGE:
    from core.multi_model import MultiModelOrchestrator

    orchestrator = MultiModelOrchestrator([
        {"type": "huggingface", "name": "google/flan-t5-small"},
        {"type": "huggingface", "name": "google/flan-t5-base"},
    ])
    results = orchestrator.run_comparison(domain="healthcare")
    report  = orchestrator.generate_comparison_report(results)
═══════════════════════════════════════════════════════════
"""

import time
import concurrent.futures
import logging

from core.scoring import RiskScorer

logger = logging.getLogger("AITestSuite.MultiModel")


class MultiModelOrchestrator:
    """
    Runs the same audit suite against multiple models
    and produces a comparative analysis.
    """

    def __init__(self, model_configs, max_workers=2):
        """
        Args:
            model_configs : List of model configuration dicts, each with:
                            {
                                "type":    "huggingface",  # or openai, anthropic, aws_bedrock etc
                                "name":    "model-name",
                                "api_key": "optional-key",
                                "label":   "Friendly Name for Reports"  # optional
                            }
            max_workers   : Max parallel model evaluations (default 2)
        """
        self.model_configs = model_configs
        self.max_workers   = max_workers
        self.scorer        = RiskScorer()

    def _run_single_model(self, config, test_suite, domain):
        """
        Run the full audit against a single model.
        Returns (config, findings, verdict, error)
        """
        model_label = config.get("label") or config.get("name", "unknown")
        logger.info(f"Starting audit: {model_label}")

        try:
            # Load the appropriate adapter
            model_type = config.get("type", "huggingface")

            if model_type in ["aws_bedrock", "azure_openai", "gcp_vertex", "ollama"]:
                from models.cloud_adapters import create_cloud_adapter
                adapter = create_cloud_adapter(
                    provider=model_type,
                    **{k: v for k, v in config.items()
                       if k not in ["type", "label"]}
                )
            else:
                from models.model_adapter import ModelAdapter
                adapter = ModelAdapter(
                    model_type=config.get("type", "huggingface"),
                    model_name=config.get("name"),
                    api_key=config.get("api_key")
                )

            adapter.load()

            # Run standard batch
            from core.automation import BatchRunner
            runner   = BatchRunner(
                adapter,
                domain=domain if domain != "general" else None,
                max_workers=1  # Single worker per model to avoid resource conflicts
            )
            findings = runner.run_batch(test_suite)
            verdict  = self.scorer.verdict(findings)

            logger.info(f"Completed: {model_label} — Verdict: {verdict}")
            return config, findings, verdict, None

        except Exception as e:
            logger.error(f"Failed: {model_label} — {e}")
            return config, [], "ERROR", str(e)

    def run_comparison(self, test_suite=None, domain="general",
                       progress_callback=None):
        """
        Run the audit against all configured models.

        Args:
            test_suite        : Tests to run (uses default + advanced if None)
            domain            : Domain flag for all models
            progress_callback : Optional progress function

        Returns:
            List of (config, findings, verdict) tuples
        """
        if test_suite is None:
            from tests.default_tests import DEFAULT_TESTS
            from tests.advanced_tests import ADVANCED_TESTS
            test_suite = list(DEFAULT_TESTS) + list(ADVANCED_TESTS)

            if domain == "healthcare":
                from domains.healthcare import HEALTHCARE_TESTS
                test_suite += HEALTHCARE_TESTS
                from tests.healthcare_governance_tests import HEALTHCARE_GOVERNANCE_TESTS
                test_suite += HEALTHCARE_GOVERNANCE_TESTS
            elif domain == "finance":
                from domains.finance import FINANCE_TESTS
                test_suite += FINANCE_TESTS
            elif domain in ["legal", "government"]:
                from domains.government_legal import LEGAL_TESTS, GOVERNMENT_TESTS
                test_suite += LEGAL_TESTS + GOVERNMENT_TESTS

        total   = len(self.model_configs)
        results = []
        done    = 0

        if progress_callback:
            progress_callback(0, f"Starting comparison: {total} models")

        # Run models (sequential to avoid GPU conflicts with local models)
        # Use parallel for API-based models only
        for config in self.model_configs:
            result = self._run_single_model(config, test_suite, domain)
            results.append(result)
            done += 1
            if progress_callback:
                label = config.get("label") or config.get("name", "?")
                progress_callback(done / total, f"Completed: {label} ({done}/{total})")

        return results

    def generate_comparison_report(self, results, output_path=None):
        """
        Generate a structured comparison report from multi-model results.

        Args:
            results     : Output from run_comparison()
            output_path : Optional path to save JSON report

        Returns:
            Comparison report dict
        """
        import json
        import os

        report = {
            "report_type":  "multi_model_comparison",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_count":  len(results),
            "models":       [],
            "comparison":   {},
            "recommendation": None
        }

        # Build per-model summary
        best_score   = float('inf')
        best_model   = None

        for config, findings, verdict, error in results:
            label = config.get("label") or config.get("name", "unknown")

            if error:
                report["models"].append({
                    "label":   label,
                    "type":    config.get("type"),
                    "name":    config.get("name"),
                    "status":  "ERROR",
                    "error":   error,
                    "verdict": "ERROR"
                })
                continue

            total      = len(findings)
            passed     = sum(1 for f in findings if f.get("passed"))
            failed     = total - passed
            avg_risk   = sum(f.get("risk_matrix", {}).get("overall", 0) for f in findings) / max(total, 1)
            critical   = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)

            # Category breakdown
            cat_scores = {}
            for f in findings:
                cat = f.get("category", "Unknown")
                if cat not in cat_scores:
                    cat_scores[cat] = {"pass": 0, "fail": 0, "avg_risk": 0, "risks": []}
                cat_scores[cat]["pass"  if f.get("passed") else "fail"] += 1
                cat_scores[cat]["risks"].append(f.get("risk_matrix", {}).get("overall", 0))

            for cat in cat_scores:
                risks = cat_scores[cat]["risks"]
                cat_scores[cat]["avg_risk"] = round(sum(risks) / max(len(risks), 1), 2)
                del cat_scores[cat]["risks"]

            model_summary = {
                "label":        label,
                "type":         config.get("type"),
                "name":         config.get("name"),
                "status":       "COMPLETE",
                "verdict":      verdict,
                "total_tests":  total,
                "passed":       passed,
                "failed":       failed,
                "pass_rate":    f"{round(passed/max(total,1)*100, 1)}%",
                "avg_risk":     round(avg_risk, 2),
                "critical":     critical,
                "categories":   cat_scores
            }

            report["models"].append(model_summary)

            # Track best performer
            if avg_risk < best_score:
                best_score = avg_risk
                best_model = label

        # Build head-to-head comparison
        if len(report["models"]) >= 2:
            report["comparison"] = self._build_comparison_matrix(report["models"])

        # Recommendation
        if best_model:
            best = next(m for m in report["models"] if m["label"] == best_model)
            report["recommendation"] = {
                "recommended_model": best_model,
                "reason": (
                    f"{best_model} achieved the lowest average risk score "
                    f"({best_score:.2f}/5.0) with {best.get('passed', 0)} tests passed "
                    f"and verdict {best.get('verdict', 'UNKNOWN')}."
                )
            }

        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)

        return report

    def _build_comparison_matrix(self, models):
        """Build a head-to-head comparison matrix across all models."""
        complete_models = [m for m in models if m["status"] == "COMPLETE"]
        if not complete_models:
            return {}

        # All categories across all models
        all_cats = set()
        for m in complete_models:
            all_cats.update(m.get("categories", {}).keys())

        matrix = {
            "verdict_comparison": {m["label"]: m["verdict"]    for m in complete_models},
            "pass_rate":          {m["label"]: m["pass_rate"]   for m in complete_models},
            "avg_risk":           {m["label"]: m["avg_risk"]    for m in complete_models},
            "critical_findings":  {m["label"]: m["critical"]    for m in complete_models},
            "category_breakdown": {}
        }

        # Per-category comparison
        for cat in sorted(all_cats):
            matrix["category_breakdown"][cat] = {}
            for m in complete_models:
                cat_data = m.get("categories", {}).get(cat, {})
                matrix["category_breakdown"][cat][m["label"]] = {
                    "pass":     cat_data.get("pass",     0),
                    "fail":     cat_data.get("fail",     0),
                    "avg_risk": cat_data.get("avg_risk", 0)
                }

        return matrix

    def generate_individual_pdfs(self, results, domain=None, auditor_name="Amarjit Khakh"):
        """
        Generate one PDF audit report per model.

        Returns:
            List of (label, pdf_path) tuples
        """
        from core.reporting import ReportGenerator
        import os

        os.makedirs("reports", exist_ok=True)
        pdf_paths = []

        for config, findings, verdict, error in results:
            label = config.get("label") or config.get("name", "unknown")
            if error or not findings:
                continue
            try:
                generator = ReportGenerator(output_dir="reports")
                pdf_path  = generator.generate(
                    findings     = findings,
                    verdict      = verdict,
                    model_info   = {
                        "model_name": config.get("name", label),
                        "model_type": config.get("type", "unknown").upper()
                    },
                    domain       = domain if domain and domain != "general" else None,
                    auditor_name = auditor_name
                )
                pdf_paths.append((label, pdf_path))
                logger.info(f"Individual PDF generated for {label}: {pdf_path}")
            except Exception as e:
                logger.error(f"PDF generation failed for {label}: {e}")

        return pdf_paths

    def generate_comparison_pdf(self, results, domain=None, auditor_name="Amarjit Khakh"):
        """
        Generate a single combined comparison PDF report
        showing all models side by side with full findings.

        Returns:
            Path to the generated comparison PDF
        """
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable, PageBreak)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import os

        os.makedirs("reports", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output    = f"reports/MultiModel_Comparison_{timestamp}.pdf"

        doc    = SimpleDocTemplate(output, pagesize=landscape(A4),
                                   rightMargin=1.5*cm, leftMargin=1.5*cm,
                                   topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        story  = []

        # ── Colour scheme ─────────────────────────────────────────────
        NAVY   = colors.HexColor("#1F3864")
        BLUE   = colors.HexColor("#2E75B6")
        WHITE  = colors.white
        LGRAY  = colors.HexColor("#F2F2F2")
        RED    = colors.HexColor("#C0392B")
        GREEN  = colors.HexColor("#27AE60")
        GOLD   = colors.HexColor("#C9A84C")
        ORANGE = colors.HexColor("#E67E22")

        VERDICT_COLORS = {
            "PASS":             GREEN,
            "CONDITIONAL PASS": ORANGE,
            "FAIL":             RED,
            "ERROR":            colors.grey
        }

        title_style = ParagraphStyle("T", parent=styles["Title"],
                                     fontSize=22, textColor=NAVY, spaceAfter=4)
        sub_style   = ParagraphStyle("S", parent=styles["Normal"],
                                     fontSize=11, textColor=BLUE, spaceAfter=8)
        head_style  = ParagraphStyle("H", parent=styles["Heading2"],
                                     fontSize=13, textColor=NAVY, spaceBefore=12, spaceAfter=6)
        body_style  = ParagraphStyle("B", parent=styles["Normal"],
                                     fontSize=9,  textColor=colors.HexColor("#333333"), spaceAfter=4)

        # ── Cover ─────────────────────────────────────────────────────
        story.append(Paragraph("AITestSuite v3", title_style))
        story.append(Paragraph("Multi-Model Comparative Audit Report", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=NAVY))
        story.append(Spacer(1, 0.3*cm))

        meta = [
            ["Report Type",   "Multi-Model Comparison Audit"],
            ["Audit Date",    time.strftime("%B %d, %Y at %H:%M")],
            ["Domain",        (domain or "general").upper()],
            ["Models Tested", str(sum(1 for _,f,_,e in results if not e))],
            ["Auditor",       auditor_name],
            ["Toolkit",       "AITestSuite v3"],
        ]
        meta_tbl = Table(meta, colWidths=[4*cm, 10*cm])
        meta_tbl.setStyle(TableStyle([
            ("FONTNAME",    (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0),(-1,-1), 9),
            ("BACKGROUND",  (0,0),(0,-1), colors.HexColor("#F0F0F8")),
            ("TEXTCOLOR",   (0,0),(0,-1), NAVY),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE, colors.HexColor("#FAFAFA")]),
            ("GRID",        (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("PADDING",     (0,0),(-1,-1), 6),
        ]))
        story.append(meta_tbl)
        story.append(Spacer(1, 0.6*cm))

        # ── Verdict summary banner ─────────────────────────────────────
        story.append(Paragraph("Verdict Summary", head_style))

        valid = [(c,f,v,e) for c,f,v,e in results if not e and f]
        if not valid:
            story.append(Paragraph("No valid results to display.", body_style))
        else:
            summary_data = [["Model", "Verdict", "Tests", "Passed", "Failed", "Pass Rate", "Avg Risk", "Critical"]]
            for config, findings, verdict, error in valid:
                label    = config.get("label") or config.get("name","?")
                total    = len(findings)
                passed   = sum(1 for f in findings if f.get("passed"))
                failed   = total - passed
                avg_risk = round(sum(f.get("risk_matrix",{}).get("overall",0) for f in findings)/max(total,1), 2)
                critical = sum(1 for f in findings if f.get("risk_matrix",{}).get("overall",0) >= 4.5)
                summary_data.append([
                    label, verdict, str(total), str(passed), str(failed),
                    f"{round(passed/max(total,1)*100,1)}%", str(avg_risk), str(critical)
                ])

            col_w = [4*cm, 3.5*cm, 2*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm]
            s_tbl = Table(summary_data, colWidths=col_w)
            s_style = [
                ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0),(-1,-1), 8.5),
                ("BACKGROUND", (0,0),(-1,0), NAVY),
                ("TEXTCOLOR",  (0,0),(-1,0), WHITE),
                ("GRID",       (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
                ("PADDING",    (0,0),(-1,-1), 6),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, colors.HexColor("#F4F7FB")]),
            ]
            # Colour verdict cells
            for i, (config, findings, verdict, error) in enumerate(valid):
                vc = VERDICT_COLORS.get(verdict, colors.grey)
                s_style.append(("BACKGROUND", (1, i+1), (1, i+1), vc))
                s_style.append(("TEXTCOLOR",  (1, i+1), (1, i+1), WHITE))
                s_style.append(("FONTNAME",   (1, i+1), (1, i+1), "Helvetica-Bold"))
            s_tbl.setStyle(TableStyle(s_style))
            story.append(s_tbl)
            story.append(Spacer(1, 0.4*cm))

            # ── Recommendation ─────────────────────────────────────────
            best = min(valid, key=lambda x: sum(f.get("risk_matrix",{}).get("overall",0)
                                                 for f in x[1]) / max(len(x[1]),1))
            best_label = best[0].get("label") or best[0].get("name","?")
            story.append(Paragraph(
                f"<b>Recommendation:</b> {best_label} achieved the lowest average risk score "
                f"and is the safest option among the models tested.",
                body_style
            ))
            story.append(Spacer(1, 0.4*cm))

            # ── Category comparison ────────────────────────────────────
            story.append(Paragraph("Category-Level Comparison", head_style))

            all_cats = set()
            model_cats = {}
            for config, findings, verdict, error in valid:
                label = config.get("label") or config.get("name","?")
                model_cats[label] = {}
                for f in findings:
                    cat = f.get("category","Unknown")
                    all_cats.add(cat)
                    if cat not in model_cats[label]:
                        model_cats[label][cat] = {"pass":0,"fail":0,"risks":[]}
                    model_cats[label][cat]["pass" if f.get("passed") else "fail"] += 1
                    model_cats[label][cat]["risks"].append(
                        f.get("risk_matrix",{}).get("overall",0))

            labels   = [c.get("label") or c.get("name","?") for c,f,v,e in valid]
            cat_hdr  = ["Category"] + labels
            cat_data = [cat_hdr]
            for cat in sorted(all_cats):
                row = [cat[:35]]
                for lbl in labels:
                    cd     = model_cats.get(lbl,{}).get(cat,{})
                    p      = cd.get("pass",0)
                    total_c = p + cd.get("fail",0)
                    risks  = cd.get("risks",[0])
                    avg_r  = round(sum(risks)/max(len(risks),1),1)
                    row.append(f"{p}/{total_c} ({avg_r})")
                cat_data.append(row)

            cw = [5*cm] + [max(3*cm, 21*cm/max(len(labels),1)) for _ in labels]
            c_tbl = Table(cat_data, colWidths=cw[:len(cat_hdr)])
            c_tbl.setStyle(TableStyle([
                ("FONTNAME",        (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",        (0,0),(-1,-1), 8),
                ("BACKGROUND",      (0,0),(-1,0), BLUE),
                ("TEXTCOLOR",       (0,0),(-1,0), WHITE),
                ("GRID",            (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
                ("PADDING",         (0,0),(-1,-1), 5),
                ("ROWBACKGROUNDS",  (0,1),(-1,-1),[WHITE, LGRAY]),
                ("FONTNAME",        (0,1),(0,-1), "Helvetica-Bold"),
                ("TEXTCOLOR",       (0,1),(0,-1), NAVY),
            ]))
            story.append(c_tbl)
            story.append(Spacer(1, 0.4*cm))

            # ── Per-model detailed findings ────────────────────────────
            for config, findings, verdict, error in valid:
                label = config.get("label") or config.get("name","?")
                story.append(PageBreak())
                story.append(Paragraph(f"Detailed Findings — {label}", head_style))
                story.append(Paragraph(
                    f"Model: {config.get('name',label)} | "
                    f"Verdict: {verdict} | "
                    f"Passed: {sum(1 for f in findings if f.get('passed'))}/{len(findings)}",
                    body_style
                ))
                story.append(Spacer(1, 0.2*cm))

                # Findings table — critical and high only for brevity
                important = [f for f in findings
                             if f.get("risk_matrix",{}).get("overall",0) >= 3.5][:30]
                if important:
                    fhdr = [["#","Test Name","Category","Risk","Result"]]
                    frows = []
                    for i, f in enumerate(important):
                        rm = f.get("risk_matrix",{})
                        frows.append([
                            str(i+1),
                            f.get("name","")[:40],
                            f.get("category","")[:25],
                            str(rm.get("overall","-")),
                            "PASS" if f.get("passed") else "FAIL"
                        ])
                    ftbl = Table(fhdr + frows,
                                 colWidths=[1*cm, 8*cm, 5.5*cm, 2*cm, 2*cm])
                    ft_style = [
                        ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
                        ("FONTSIZE",   (0,0),(-1,-1), 8),
                        ("BACKGROUND", (0,0),(-1,0), NAVY),
                        ("TEXTCOLOR",  (0,0),(-1,0), WHITE),
                        ("GRID",       (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
                        ("PADDING",    (0,0),(-1,-1), 5),
                        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
                    ]
                    for i, f in enumerate(important):
                        ov = f.get("risk_matrix",{}).get("overall",0)
                        rc = RED if ov >= 4.5 else ORANGE if ov >= 3.5 else colors.grey
                        ft_style.append(("BACKGROUND",(3,i+1),(3,i+1), rc))
                        ft_style.append(("TEXTCOLOR", (3,i+1),(3,i+1), WHITE))
                        rc2 = RED if not f.get("passed") else GREEN
                        ft_style.append(("TEXTCOLOR", (4,i+1),(4,i+1), rc2))
                        ft_style.append(("FONTNAME",  (4,i+1),(4,i+1), "Helvetica-Bold"))
                    ftbl.setStyle(TableStyle(ft_style))
                    story.append(ftbl)
                    if len(findings) > 30:
                        story.append(Paragraph(
                            f"Showing top {len(important)} findings by risk score. "
                            f"See individual model PDF reports for complete findings.",
                            body_style
                        ))

        # ── Footer ────────────────────────────────────────────────────
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#DDDDDD")))
        story.append(Paragraph(
            f"Generated by AITestSuite v3 | {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"| Auditor: {auditor_name} | For authorised security testing only",
            ParagraphStyle("F", parent=styles["Normal"],
                           fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
        ))

        doc.build(story)
        logger.info(f"Comparison PDF generated: {output}")
        return output
