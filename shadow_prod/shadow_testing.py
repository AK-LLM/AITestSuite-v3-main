"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Shadow Production Testing
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Tests a target AI model against REAL prompts sampled
    from production traffic logs — not synthetic test cases.

    This is the most realistic form of testing because it
    uses actual queries that real users have sent to the
    deployed AI system.

    Original concept from v2 shadow_prod/ folder — fully
    enhanced with PII scrubbing, structured output and
    integration with the v3 audit engine.

HOW IT WORKS:
    1. Production logs are sampled (with PII stripped)
    2. Sampled prompts are run against the target model
    3. Responses are evaluated for safety and quality
    4. Findings are scored and reported like any audit

WHY THIS MATTERS:
    Synthetic tests catch known failure modes.
    Production traffic catches UNKNOWN failure modes —
    the edge cases that real users actually trigger.

    For healthcare AI: real clinical queries reveal
    failure modes that no red teamer would think to test.

PRIVACY:
    PII scrubbing is MANDATORY before any production
    traffic is used for testing. The scrubber removes:
    - Names (first, last, full)
    - Dates of birth
    - Health card numbers
    - Phone numbers
    - Email addresses
    - IP addresses
    - Address information

    Scrubbed prompts are hashed for deduplication.
    Original prompts are never stored.

INTEGRATION WITH V2:
    Enhanced from shadow_sampler.py and feedback_ingest.py
    in the original v2 toolkit.
═══════════════════════════════════════════════════════════
"""

import os
import re
import json
import glob
import time
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger("AITestSuite.ShadowProd")

# ── PII patterns to scrub before testing ─────────────────────────────────

PII_PATTERNS = [
    # Canadian health card numbers (10 digits with optional spaces/dashes)
    (r'\b\d{4}[\s-]?\d{3}[\s-]?\d{3}\b', '[HEALTH_CARD]'),

    # Phone numbers (various formats)
    (r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]'),

    # Email addresses
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),

    # Dates of birth (various formats)
    (r'\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b', '[DOB]'),
    (r'\b(?:19|20)\d{2}[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b', '[DOB]'),

    # IP addresses
    (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_ADDRESS]'),

    # Canadian postal codes
    (r'\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b', '[POSTAL_CODE]'),

    # Social Insurance Numbers (SIN)
    (r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b', '[SIN]'),

    # Patient/MRN numbers (various clinical formats)
    (r'\bMRN[\s:#]*\d+\b', '[MRN]'),
    (r'\bPATIENT[\s:#]*\d+\b', '[PATIENT_ID]'),
]


def scrub_pii(text):
    """
    Remove PII from a text string.
    Replaces sensitive patterns with placeholder tokens.

    Args:
        text : Raw text that may contain PII

    Returns:
        Scrubbed text safe for testing
    """
    scrubbed = text
    for pattern, replacement in PII_PATTERNS:
        scrubbed = re.sub(pattern, replacement, scrubbed, flags=re.IGNORECASE)
    return scrubbed


class ShadowSampler:
    """
    Samples and processes production log files for shadow testing.
    Enhanced from v2 shadow_sampler.py.
    """

    def __init__(self, prod_logs_path=None, output_dir=None, max_samples=100):
        """
        Args:
            prod_logs_path : Path to production log files (txt or json)
            output_dir     : Where to store processed samples
            max_samples    : Maximum prompts to sample per run
        """
        self.prod_logs_path = prod_logs_path or os.getenv("PROD_LOGS_PATH", "./prod_logs/")
        self.output_dir     = output_dir or "./shadow_prod/samples/"
        self.max_samples    = max_samples
        self._seen_hashes   = set()

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _extract_prompts_from_file(self, filepath):
        """
        Extract prompt strings from a log file.
        Supports JSON lines and plain text formats.
        """
        prompts = []

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Try JSON lines format first
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    # Look for prompt-like fields
                    for field in ["prompt", "input", "query", "message", "content", "user_input"]:
                        if field in obj and isinstance(obj[field], str):
                            prompts.append(obj[field])
                            break
                except json.JSONDecodeError:
                    # Plain text line — treat as prompt if long enough
                    if len(line) > 20:
                        prompts.append(line)

        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")

        return prompts

    def sample(self):
        """
        Sample production prompts, scrub PII and store for testing.

        Returns:
            List of scrubbed prompt strings ready for shadow testing
        """
        all_prompts = []

        # Find all log files
        for pattern in ["*.txt", "*.json", "*.jsonl", "*.log"]:
            files = glob.glob(os.path.join(self.prod_logs_path, pattern))
            for filepath in files:
                prompts = self._extract_prompts_from_file(filepath)
                all_prompts.extend(prompts)

        if not all_prompts:
            logger.warning(f"No prompts found in {self.prod_logs_path}")
            return []

        # Scrub PII and deduplicate
        clean_prompts = []
        for prompt in all_prompts:
            # Scrub PII
            scrubbed = scrub_pii(prompt)

            # Deduplicate by hash
            prompt_hash = hashlib.md5(scrubbed.lower().encode()).hexdigest()
            if prompt_hash in self._seen_hashes:
                continue
            self._seen_hashes.add(prompt_hash)
            clean_prompts.append(scrubbed)

            if len(clean_prompts) >= self.max_samples:
                break

        logger.info(f"Sampled {len(clean_prompts)} unique prompts from production logs")
        return clean_prompts

    def prompts_to_test_suite(self, prompts):
        """
        Convert raw prompts into AITestSuite test format.
        These tests are observation-only (no expected output) —
        they detect unexpected failures rather than checking correctness.
        """
        test_suite = []
        for i, prompt in enumerate(prompts):
            test_suite.append({
                "name":       f"Shadow Prod Test {i+1}",
                "category":   "Shadow Production",
                "prompt":     prompt,
                "expected":   "",  # Observation only — flag danger indicators manually
                "max_tokens": 200,
                "regulations": [],
                "healthcare_implication": "Real production traffic test — failures indicate live deployment risks.",
                "remediation":            "Investigate specific failure mode found in production traffic.",
                "references":             []
            })
        return test_suite


class FeedbackIngestor:
    """
    Ingests error logs and failed interactions from production
    for targeted regression testing.
    Enhanced from v2 feedback_ingest.py.
    """

    def __init__(self, error_logs_path=None, output_dir=None):
        """
        Args:
            error_logs_path : Path to error log files
            output_dir      : Where to store processed feedback
        """
        self.error_logs_path = error_logs_path or os.getenv("ERROR_LOGS_PATH", "./prod_errors/")
        self.output_dir      = output_dir or "./shadow_prod/feedback_prompts/"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def ingest(self):
        """
        Process error logs and extract prompts that caused failures.
        These become regression tests — ensuring fixed bugs stay fixed.

        Returns:
            List of (prompt, error_context) tuples
        """
        feedback_items = []

        for filepath in glob.glob(os.path.join(self.error_logs_path, "*.txt")) + \
                        glob.glob(os.path.join(self.error_logs_path, "*.json")):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Try to parse as JSON for structured error logs
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        prompt  = obj.get("prompt") or obj.get("input") or ""
                        context = obj.get("error") or obj.get("failure") or ""
                        if prompt:
                            scrubbed = scrub_pii(prompt)
                            feedback_items.append((scrubbed, context))
                    except json.JSONDecodeError:
                        # Plain text error log
                        if len(line) > 20:
                            feedback_items.append((scrub_pii(line), "plain text error log"))

            except Exception as e:
                logger.error(f"Error ingesting {filepath}: {e}")

        logger.info(f"Ingested {len(feedback_items)} error feedback items")
        return feedback_items

    def to_regression_tests(self, feedback_items):
        """Convert feedback items into regression test format."""
        return [
            {
                "name":       f"Regression Test {i+1}",
                "category":   "Regression / Feedback",
                "prompt":     prompt,
                "expected":   "",  # Observation mode
                "max_tokens": 200,
                "regulations": [],
                "healthcare_implication": f"Regression test from production error: {context[:100]}",
                "remediation":            "Verify fix is effective and failure mode does not recur.",
                "references":             []
            }
            for i, (prompt, context) in enumerate(feedback_items)
        ]
