"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — CI/CD Command Line Runner
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Command line entry point for CI/CD pipeline integration.
    Runs the full audit and exits with appropriate exit codes.

USAGE:
    # Basic run against free default model
    python run_ci.py

    # Specify model and domain
    python run_ci.py --model google/flan-t5-small --domain healthcare

    # Fail build on any critical finding
    python run_ci.py --fail-on critical

    # Export JUnit XML for CI test reporting
    python run_ci.py --junit reports/results.xml

EXIT CODES:
    0 = PASS
    1 = FAIL (critical findings)
    2 = CONDITIONAL PASS (warnings)
    3 = ERROR (toolkit failure)
═══════════════════════════════════════════════════════════
"""

import argparse
import sys
import os
import time

# ── Ensure local modules importable ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AITestSuite v3 — AI Security Audit CI Runner"
    )
    parser.add_argument(
        "--model",
        default="google/flan-t5-small",
        help="Model to audit (HuggingFace ID or provider model name)"
    )
    parser.add_argument(
        "--model-type",
        default="huggingface",
        choices=["huggingface", "openai", "anthropic"],
        help="Model provider type"
    )
    parser.add_argument(
        "--domain",
        default="general",
        choices=["general", "healthcare", "finance", "legal", "government"],
        help="Audit domain flag"
    )
    parser.add_argument(
        "--output",
        default="reports",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--junit",
        default=None,
        help="Path for JUnit XML output (for CI test reporting)"
    )
    parser.add_argument(
        "--fail-on",
        default="fail",
        choices=["fail", "conditional", "any"],
        help="Verdict level that triggers non-zero exit code"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Tests per batch (default 25)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Parallel worker threads (auto-detected if not set)"
    )
    parser.add_argument(
        "--auditor",
        default="AITestSuite v3 CI",
        help="Auditor name for the report"
    )
    return parser.parse_args()


def main():
    """Main CI runner entry point."""
    args = parse_args()

    print("=" * 60)
    print("AITestSuite v3 — AI Security Audit")
    print("=" * 60)
    print(f"Model:    {args.model}")
    print(f"Type:     {args.model_type}")
    print(f"Domain:   {args.domain}")
    print(f"Output:   {args.output}")
    print(f"Time:     {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # ── Load model ────────────────────────────────────────────────
        print("\n[1/5] Loading model...")
        from models.model_adapter import ModelAdapter

        api_key = None
        if args.model_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("ERROR: OPENAI_API_KEY environment variable not set")
                sys.exit(3)
        elif args.model_type == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("ERROR: ANTHROPIC_API_KEY environment variable not set")
                sys.exit(3)

        adapter = ModelAdapter(
            model_type=args.model_type,
            model_name=args.model,
            api_key=api_key
        )
        adapter.load()
        print(f"  ✓ Model loaded: {args.model}")

        # ── Build test suite ──────────────────────────────────────────
        print("\n[2/5] Building test suite...")
        from tests.default_tests import DEFAULT_TESTS
        from tests.advanced_tests import ADVANCED_TESTS
        test_suite = list(DEFAULT_TESTS) + list(ADVANCED_TESTS)

        if args.domain == "healthcare":
            from domains.healthcare import HEALTHCARE_TESTS
            test_suite += HEALTHCARE_TESTS
        elif args.domain == "finance":
            from domains.finance import FINANCE_TESTS
            test_suite += FINANCE_TESTS
        elif args.domain in ["legal", "government"]:
            from domains.government_legal import LEGAL_TESTS, GOVERNMENT_TESTS
            test_suite += LEGAL_TESTS + GOVERNMENT_TESTS

        print(f"  ✓ {len(test_suite)} tests ready for {args.domain.upper()} domain")

        # ── Run audit ─────────────────────────────────────────────────
        print(f"\n[3/5] Running audit ({len(test_suite)} tests)...")
        from core.automation import BatchRunner

        def progress(pct, msg):
            bar_len = 30
            filled  = int(bar_len * pct)
            bar     = '█' * filled + '░' * (bar_len - filled)
            print(f"\r  [{bar}] {int(pct*100)}% {msg}", end='', flush=True)

        runner = BatchRunner(
            model_adapter=adapter,
            domain=args.domain if args.domain != "general" else None,
            max_workers=args.workers,
            progress_callback=progress
        )

        findings = runner.run_batch(test_suite, batch_size=args.batch_size)
        print()  # New line after progress bar

        # ── Determine verdict ─────────────────────────────────────────
        from core.scoring import RiskScorer
        verdict = RiskScorer().verdict(findings)
        print(f"\n[4/5] Audit complete — Verdict: {verdict}")

        total    = len(findings)
        passed   = sum(1 for f in findings if f.get("passed"))
        failed   = total - passed
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)

        print(f"       Total: {total} | Passed: {passed} | Failed: {failed} | Critical: {critical}")

        # ── Export results ────────────────────────────────────────────
        print(f"\n[5/5] Exporting results to {args.output}/...")
        from core.automation import CIExporter

        model_info = {"model_name": args.model, "model_type": args.model_type}

        # JSON export
        json_path = CIExporter.export_json(
            findings, verdict,
            output_path=os.path.join(args.output, "ci_results.json"),
            model_info=model_info
        )
        print(f"  ✓ JSON: {json_path}")

        # JUnit XML export
        junit_path = args.junit or os.path.join(args.output, "junit_results.xml")
        CIExporter.export_junit_xml(findings, verdict, output_path=junit_path)
        print(f"  ✓ JUnit: {junit_path}")

        # Text summary
        summary_path = CIExporter.export_text_summary(
            findings, verdict,
            output_path=os.path.join(args.output, "summary.txt")
        )
        print(f"  ✓ Summary: {summary_path}")

        # PDF report
        try:
            from core.reporting import ReportGenerator
            generator = ReportGenerator(output_dir=args.output)
            pdf_path  = generator.generate(
                findings=findings, verdict=verdict,
                model_info=model_info,
                domain=args.domain if args.domain != "general" else None,
                auditor_name=args.auditor
            )
            print(f"  ✓ PDF: {pdf_path}")
        except Exception as e:
            print(f"  ⚠ PDF generation skipped: {e}")

        # ── Determine exit code ───────────────────────────────────────
        print("\n" + "=" * 60)
        exit_code = CIExporter.get_exit_code(verdict)

        # Adjust based on --fail-on flag
        if args.fail_on == "conditional" and verdict == "CONDITIONAL PASS":
            exit_code = 1
        elif args.fail_on == "any" and verdict != "PASS":
            exit_code = 1

        if exit_code == 0:
            print(f"✅ AUDIT PASSED — {verdict}")
        elif exit_code == 2:
            print(f"⚠️  AUDIT CONDITIONAL — {verdict}")
            print("   Review findings before deploying to production")
        else:
            print(f"❌ AUDIT FAILED — {verdict}")
            print(f"   {critical} critical findings require immediate remediation")

        print("=" * 60)
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n❌ AUDIT ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
