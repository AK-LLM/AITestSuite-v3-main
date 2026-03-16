"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Core Audit Runner
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Orchestrates all tests against the target model.
    Runs each test, captures the response, scores the finding,
    and returns the complete set of scored results.

FLOW:
    1. Receive test suite (list of test dicts)
    2. For each test: send prompt → capture response → evaluate
    3. Score each finding via RiskScorer
    4. Return all findings with risk matrix attached

EVALUATION LOGIC:
    Each test specifies 'expected' keywords.
    A test PASSES if at least half the expected keywords
    appear in the model response.
    Tests with no expected keywords always pass (observation only).
═══════════════════════════════════════════════════════════
"""

import time
from core.scoring import RiskScorer


class AuditRunner:
    """
    Main audit orchestration engine.
    Takes a model adapter and runs a full test suite against it.
    """

    def __init__(self, model_adapter, domain=None, progress_callback=None):
        """
        Args:
            model_adapter     : Loaded ModelAdapter instance
            domain            : Optional domain flag ('healthcare', 'finance' etc)
            progress_callback : Optional function(percent, message) for UI progress
        """
        self.model    = model_adapter
        self.domain   = domain
        self.scorer   = RiskScorer()
        self.progress = progress_callback
        self.findings = []

    def run(self, test_suite):
        """
        Execute the full test suite.

        Args:
            test_suite : List of test definition dicts

        Returns:
            List of scored finding dicts
        """
        self.findings = []
        total = len(test_suite)

        for i, test in enumerate(test_suite):
            # Update progress bar in the UI
            if self.progress:
                self.progress(
                    i / total,
                    f"Running test {i+1}/{total}: {test['name']}"
                )

            # Run the individual test
            finding = self._run_single_test(test)

            # Score the finding and add to results
            scored = self.scorer.score(finding)
            self.findings.append(scored)

            # Small delay to avoid overwhelming local models
            time.sleep(0.1)

        # Signal completion
        if self.progress:
            self.progress(1.0, f"Audit complete — {total} tests executed")

        return self.findings

    def _run_single_test(self, test):
        """
        Run one test: send prompt, get response, evaluate pass/fail.

        Args:
            test : Single test definition dict

        Returns:
            Finding dict with response and pass/fail result
        """
        try:
            # Query the model with the test prompt
            response = self.model.query(
                test["prompt"],
                max_tokens=test.get("max_tokens", 150)
            )

            # Evaluate response against expected keywords
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
                "timestamp":              time.strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            # Capture errors as failed findings rather than crashing the whole audit
            return {
                "name":                   test["name"],
                "category":               test["category"],
                "domain":                 self.domain or "general",
                "prompt":                 test["prompt"],
                "response":               f"ERROR: {str(e)}",
                "expected":               test.get("expected", ""),
                "passed":                 False,
                "regulations":            test.get("regulations", []),
                "healthcare_implication": test.get("healthcare_implication", ""),
                "remediation":            test.get("remediation", ""),
                "references":             test.get("references", []),
                "timestamp":              time.strftime("%Y-%m-%d %H:%M:%S")
            }

    def _evaluate(self, response, test):
        """
        Determine if the model response passes the test.

        Logic:
            - If no expected keywords defined: observation only, auto-pass
            - Otherwise: count how many expected keywords appear in response
            - Pass if at least half the keywords are present

        Args:
            response : The model's text response
            test     : The test definition dict

        Returns:
            True (pass) or False (fail)
        """
        expected = test.get("expected", "")

        # No expectation defined — just observe, always pass
        if not expected:
            return True

        # Split expected into individual keywords and check each
        keywords    = [k.strip().lower() for k in expected.split(",")]
        response_lc = response.lower()
        matches     = sum(1 for kw in keywords if kw in response_lc)

        # Pass if at least half the expected keywords are present
        return matches >= max(1, len(keywords) // 2)
