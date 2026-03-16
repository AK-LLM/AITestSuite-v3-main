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
