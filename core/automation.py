"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Automation & Scaling Engine
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Handles high-volume automated testing with:
    - Parallel test execution across multiple threads
    - Batch processing of large test suites
    - Progress tracking and ETA calculation
    - Results caching to avoid duplicate queries
    - Rate limiting to prevent API throttling
    - Retry logic for transient failures
    - JSON export for CI/CD pipeline integration

CI/CD INTEGRATION:
    This module supports automated testing in pipelines.
    Output format is compatible with common CI tools.
    Exit codes: 0 = PASS, 1 = FAIL, 2 = CONDITIONAL PASS

    Example GitHub Actions usage:
        python -m AITestSuite.run_ci --model google/flan-t5-small
                                     --domain healthcare
                                     --fail-on critical

BATCH PROCESSING:
    Large test suites are split into batches to:
    - Prevent memory issues with very large suites
    - Enable resuming from checkpoints
    - Provide intermediate progress updates

SCALING:
    Thread count scales automatically based on:
    - API rate limits (slower for paid APIs)
    - Model type (local HF = more threads safe)
    - Test suite size

USAGE:
    from core.automation import BatchRunner, CIExporter
    runner = BatchRunner(model_adapter, max_workers=8)
    results = runner.run_batch(test_suite, batch_size=50)
    CIExporter.export(results, "audit_results.json")
═══════════════════════════════════════════════════════════
"""

import json
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.scoring import RiskScorer

logger = logging.getLogger("AITestSuite.Automation")

# ── CI exit codes ─────────────────────────────────────────────────────────
EXIT_PASS             = 0
EXIT_CONDITIONAL_PASS = 2
EXIT_FAIL             = 1
EXIT_ERROR            = 3

# ── Default batch size ────────────────────────────────────────────────────
DEFAULT_BATCH_SIZE = 25

# ── Rate limiting presets by provider ────────────────────────────────────
RATE_LIMITS = {
    "huggingface":     0.05,   # 50ms between requests — local, fast
    "openai":          0.5,    # 500ms — API rate limits
    "anthropic":       0.5,    # 500ms — API rate limits
    "blackbox_browser": 2.0,   # 2s — browser automation, slow
    "manual_blackbox": 0.0,    # No limit — manual mode
}

# ── Thread count presets by provider ─────────────────────────────────────
THREAD_COUNTS = {
    "huggingface":      2,   # Local model — limited by CPU/GPU not network
    "openai":           4,   # API — can handle parallel requests
    "anthropic":        4,   # API — can handle parallel requests
    "blackbox_browser": 1,   # Browser — must be sequential
    "manual_blackbox":  1,   # Manual — sequential by nature
}


class BatchRunner:
    """
    High-performance batch test runner with parallel execution.
    Automatically optimises thread count and rate limiting
    based on the target model provider.
    """

    def __init__(self, model_adapter, domain=None,
                 max_workers=None, progress_callback=None):
        """
        Args:
            model_adapter    : Loaded ModelAdapter instance
            domain           : Optional domain flag for findings
            max_workers      : Thread count (auto-detected if None)
            progress_callback: Optional function(percent, message)
        """
        self.model    = model_adapter
        self.domain   = domain
        self.progress = progress_callback
        self.scorer   = RiskScorer()
        self._cache   = {}   # Cache responses to avoid duplicate queries

        # Auto-detect optimal thread count
        model_type = getattr(model_adapter, 'model_type', 'huggingface')
        self.max_workers  = max_workers or THREAD_COUNTS.get(model_type, 2)
        self.rate_limit   = RATE_LIMITS.get(model_type, 0.1)

        logger.info(
            f"BatchRunner: provider={model_type} | "
            f"workers={self.max_workers} | "
            f"rate_limit={self.rate_limit}s"
        )

    def run_batch(self, test_suite, batch_size=DEFAULT_BATCH_SIZE,
                  retry_failures=True):
        """
        Run the full test suite in batches with parallel execution.

        Args:
            test_suite     : List of test definition dicts
            batch_size     : Tests per batch (default 25)
            retry_failures : Retry failed tests once (default True)

        Returns:
            List of scored finding dicts
        """
        total     = len(test_suite)
        all_findings = []
        failed_tests = []

        # Split into batches
        batches = [
            test_suite[i:i + batch_size]
            for i in range(0, total, batch_size)
        ]

        logger.info(
            f"Starting batch run: {total} tests | "
            f"{len(batches)} batches | "
            f"batch_size={batch_size}"
        )

        start_time = time.time()
        completed  = 0

        for batch_num, batch in enumerate(batches):
            if self.progress:
                elapsed = time.time() - start_time
                eta     = (elapsed / max(completed, 1)) * (total - completed)
                self.progress(
                    completed / total,
                    f"Batch {batch_num+1}/{len(batches)} | "
                    f"{completed}/{total} tests | "
                    f"ETA: {int(eta)}s"
                )

            # Run batch in parallel
            batch_results, batch_failures = self._run_parallel_batch(batch)
            all_findings  += batch_results
            failed_tests  += batch_failures
            completed     += len(batch)

            # Small pause between batches to avoid overwhelming local models
            time.sleep(0.2)

        # Retry failed tests sequentially
        if retry_failures and failed_tests:
            logger.info(f"Retrying {len(failed_tests)} failed tests...")
            if self.progress:
                self.progress(
                    0.95,
                    f"Retrying {len(failed_tests)} failed tests..."
                )
            for test in failed_tests:
                result  = self._run_single_with_retry(test, max_retries=2)
                scored  = self.scorer.score(result)
                all_findings.append(scored)

        elapsed = time.time() - start_time
        logger.info(
            f"Batch run complete: {len(all_findings)} findings | "
            f"{elapsed:.1f}s elapsed | "
            f"{elapsed/max(len(all_findings),1):.2f}s per test"
        )

        if self.progress:
            self.progress(1.0, f"Complete: {len(all_findings)} tests in {elapsed:.1f}s")

        return all_findings

    def _run_parallel_batch(self, batch):
        """
        Run a single batch in parallel using ThreadPoolExecutor.
        Returns (successful_findings, failed_tests) tuple.
        """
        findings = []
        failures = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_test = {
                executor.submit(self._run_single_with_retry, test): test
                for test in batch
            }

            for future in as_completed(future_to_test):
                test = future_to_test[future]
                try:
                    result = future.result(timeout=30)
                    if result.get("response", "").startswith("ERROR"):
                        failures.append(test)
                    else:
                        scored = self.scorer.score(result)
                        findings.append(scored)
                except Exception as e:
                    logger.error(f"Test failed: {test.get('name', '?')} — {e}")
                    failures.append(test)

        return findings, failures

    def _run_single_with_retry(self, test, max_retries=1):
        """
        Run a single test with retry logic.
        Returns a finding dict (unscored).
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Check cache first — avoid duplicate queries
                cache_key = test["prompt"][:100]
                if cache_key in self._cache:
                    response = self._cache[cache_key]
                else:
                    response = self.model.query(
                        test["prompt"],
                        max_tokens=test.get("max_tokens", 150)
                    )
                    self._cache[cache_key] = response

                # Rate limiting
                time.sleep(self.rate_limit)

                # Evaluate
                passed = self._evaluate(response, test)

                return {
                    "name":                   test["name"],
                    "category":               test["category"],
                    "domain":                 self.domain or "general",
                    "prompt":                 test["prompt"],
                    "response":               response,
                    "expected":               test.get("expected", ""),
                    "passed":                 passed,
                    "regulations":            test.get("regulations", []),
                    "healthcare_implication": test.get("healthcare_implication", ""),
                    "remediation":            test.get("remediation", ""),
                    "references":             test.get("references", []),
                    "timestamp":              time.strftime("%Y-%m-%d %H:%M:%S"),
                    "attempt":                attempt + 1
                }

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    time.sleep(1.0)  # Wait before retry

        # All retries exhausted
        return {
            "name":                   test["name"],
            "category":               test["category"],
            "domain":                 self.domain or "general",
            "prompt":                 test["prompt"],
            "response":               f"ERROR after {max_retries+1} attempts: {last_error}",
            "expected":               test.get("expected", ""),
            "passed":                 False,
            "regulations":            test.get("regulations", []),
            "healthcare_implication": test.get("healthcare_implication", ""),
            "remediation":            test.get("remediation", ""),
            "references":             test.get("references", []),
            "timestamp":              time.strftime("%Y-%m-%d %H:%M:%S"),
            "attempt":                max_retries + 1
        }

    def _evaluate(self, response, test):
        """Evaluate response against expected keywords."""
        expected = test.get("expected", "")
        if not expected:
            return True
        keywords    = [k.strip().lower() for k in expected.split(",")]
        response_lc = response.lower()
        matches     = sum(1 for kw in keywords if kw in response_lc)
        return matches >= max(1, len(keywords) // 2)

    def clear_cache(self):
        """Clear the response cache."""
        self._cache = {}
        logger.info("Response cache cleared")


class CIExporter:
    """
    Exports audit results in formats suitable for CI/CD pipelines.
    Supports JSON, JUnit XML, and plain text summary.
    """

    @staticmethod
    def export_json(findings, verdict, output_path="reports/ci_results.json",
                    model_info=None):
        """
        Export full results as JSON for CI pipeline consumption.

        Args:
            findings    : List of scored finding dicts
            verdict     : Overall verdict string
            output_path : Where to save the JSON file
            model_info  : Dict with model metadata

        Returns:
            Path to the exported file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        total    = len(findings)
        passed   = sum(1 for f in findings if f.get("passed"))
        failed   = total - passed
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
        avg_risk = round(
            sum(f.get("risk_matrix", {}).get("overall", 0) for f in findings) / max(total, 1),
            2
        )

        export = {
            "toolkit":     "AITestSuite v3",
            "timestamp":   time.strftime("%Y-%m-%d %H:%M:%S"),
            "model":       model_info or {},
            "verdict":     verdict,
            "exit_code":   CIExporter.get_exit_code(verdict),
            "summary": {
                "total_tests":    total,
                "passed":         passed,
                "failed":         failed,
                "critical":       critical,
                "average_risk":   avg_risk,
                "pass_rate":      f"{round(passed/max(total,1)*100, 1)}%"
            },
            "findings": [
                {
                    "name":        f.get("name"),
                    "category":    f.get("category"),
                    "passed":      f.get("passed"),
                    "risk_score":  f.get("risk_matrix", {}).get("overall"),
                    "risk_label":  f.get("risk_matrix", {}).get("label"),
                    "regulations": f.get("regulations", []),
                    "remediation": f.get("remediation", ""),
                    "timestamp":   f.get("timestamp")
                }
                for f in findings
            ]
        }

        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(export, fh, indent=2)

        logger.info(f"CI results exported to: {output_path}")
        return output_path

    @staticmethod
    def export_junit_xml(findings, verdict, output_path="reports/junit_results.xml"):
        """
        Export results as JUnit XML — compatible with Jenkins, GitHub Actions,
        GitLab CI and most CI platforms.

        Args:
            findings    : List of scored finding dicts
            verdict     : Overall verdict string
            output_path : Where to save the XML file

        Returns:
            Path to the exported file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        total  = len(findings)
        failed = sum(1 for f in findings if not f.get("passed"))

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<testsuite name="AITestSuite-v3" tests="{total}" failures="{failed}" '
            f'timestamp="{time.strftime("%Y-%m-%dT%H:%M:%S")}">',
        ]

        for f in findings:
            name    = f.get("name", "Unknown").replace('"', "'")
            cat     = f.get("category", "General")
            passed  = f.get("passed", False)
            risk    = f.get("risk_matrix", {}).get("overall", 0)

            lines.append(
                f'  <testcase name="{name}" classname="{cat}" '
                f'time="0.1">'
            )

            if not passed:
                remediation = f.get("remediation", "See audit report").replace('<', '&lt;').replace('>', '&gt;')
                lines.append(
                    f'    <failure message="Risk Score: {risk}/5" type="SecurityFailure">'
                    f'{remediation}'
                    f'    </failure>'
                )

            lines.append('  </testcase>')

        lines.append('</testsuite>')

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write('\n'.join(lines))

        logger.info(f"JUnit XML exported to: {output_path}")
        return output_path

    @staticmethod
    def export_text_summary(findings, verdict, output_path="reports/summary.txt"):
        """
        Export a plain text summary suitable for CLI output and logs.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        total    = len(findings)
        passed   = sum(1 for f in findings if f.get("passed"))
        failed   = total - passed
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)

        lines = [
            "=" * 60,
            "AITestSuite v3 — Audit Summary",
            "=" * 60,
            f"Verdict:      {verdict}",
            f"Total Tests:  {total}",
            f"Passed:       {passed}",
            f"Failed:       {failed}",
            f"Critical:     {critical}",
            f"Timestamp:    {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "FAILED TESTS:",
            "-" * 40,
        ]

        failed_findings = [f for f in findings if not f.get("passed")]
        if failed_findings:
            for f in failed_findings:
                rm = f.get("risk_matrix", {})
                lines.append(
                    f"[{rm.get('label','?')} {rm.get('overall','?')}/5] "
                    f"{f.get('name','?')}"
                )
        else:
            lines.append("None — all tests passed")

        lines += ["", "=" * 60]

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write('\n'.join(lines))

        return output_path

    @staticmethod
    def get_exit_code(verdict):
        """
        Return the appropriate process exit code for CI pipeline use.
        0 = pass (build continues), 1 = fail (build stops), 2 = conditional
        """
        return {
            "PASS":             EXIT_PASS,
            "CONDITIONAL PASS": EXIT_CONDITIONAL_PASS,
            "FAIL":             EXIT_FAIL,
            "INCONCLUSIVE":     EXIT_ERROR
        }.get(verdict, EXIT_ERROR)
