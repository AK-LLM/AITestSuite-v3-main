"""
AITestSuite v3 — Enterprise Integration Layer
Author: Amarjit Khakh
"""

import json
import os
import time
import logging

logger = logging.getLogger("AITestSuite.Enterprise")


class EnterpriseIntegration:
    """
    Sends audit alerts and findings to enterprise platforms.
    Supports Slack, Microsoft Teams, PagerDuty, Jira, and generic SIEM webhooks.
    Configure via environment variables or constructor arguments.

    ENV VARS:
        SLACK_WEBHOOK_URL      — Slack incoming webhook URL
        TEAMS_WEBHOOK_URL      — MS Teams incoming webhook URL
        PAGERDUTY_ROUTING_KEY  — PagerDuty Events API v2 routing key
        JIRA_URL               — Jira base URL
        JIRA_EMAIL             — Jira account email
        JIRA_API_TOKEN         — Jira API token
        JIRA_PROJECT_KEY       — Jira project key for creating issues
        SIEM_WEBHOOK_URL       — Generic SIEM/webhook endpoint
        SIEM_API_KEY           — Optional API key header for SIEM
    """

    def __init__(self, config=None):
        cfg = config or {}
        self.slack_url        = cfg.get("slack_url")        or os.getenv("SLACK_WEBHOOK_URL")
        self.teams_url        = cfg.get("teams_url")        or os.getenv("TEAMS_WEBHOOK_URL")
        self.pagerduty_key    = cfg.get("pagerduty_key")    or os.getenv("PAGERDUTY_ROUTING_KEY")
        self.jira_url         = cfg.get("jira_url")         or os.getenv("JIRA_URL")
        self.jira_email       = cfg.get("jira_email")       or os.getenv("JIRA_EMAIL")
        self.jira_token       = cfg.get("jira_token")       or os.getenv("JIRA_API_TOKEN")
        self.jira_project     = cfg.get("jira_project")     or os.getenv("JIRA_PROJECT_KEY", "AI")
        self.siem_url         = cfg.get("siem_url")         or os.getenv("SIEM_WEBHOOK_URL")
        self.siem_key         = cfg.get("siem_key")         or os.getenv("SIEM_API_KEY")

    def _post(self, url, payload, headers=None):
        """Send an HTTP POST request."""
        try:
            import urllib.request
            headers = headers or {"Content-Type": "application/json"}
            data    = json.dumps(payload).encode("utf-8")
            req     = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, resp.read().decode()
        except Exception as e:
            logger.error(f"POST failed to {url}: {e}")
            return None, str(e)

    # ── Slack ─────────────────────────────────────────────────────────────

    def send_slack(self, verdict, findings, model_name, report_path=None):
        """Send audit results to Slack."""
        if not self.slack_url:
            return False, "SLACK_WEBHOOK_URL not configured"

        total    = len(findings)
        passed   = sum(1 for f in findings if f.get("passed"))
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
        color    = {"PASS": "#28a745", "FAIL": "#dc3545", "CONDITIONAL PASS": "#ffc107"}.get(verdict, "#6c757d")
        emoji    = {"PASS": ":white_check_mark:", "FAIL": ":rotating_light:", "CONDITIONAL PASS": ":warning:"}.get(verdict, ":question:")

        payload = {
            "attachments": [{
                "color": color,
                "title": f"{emoji} AITestSuite v3 — Audit Complete",
                "fields": [
                    {"title": "Model",   "value": model_name, "short": True},
                    {"title": "Verdict", "value": f"*{verdict}*", "short": True},
                    {"title": "Tests",   "value": f"{passed}/{total} passed", "short": True},
                    {"title": "Critical","value": str(critical), "short": True},
                ],
                "footer": f"AITestSuite v3 | {time.strftime('%Y-%m-%d %H:%M')}",
                "text": f"Report: {report_path}" if report_path else ""
            }]
        }
        status, body = self._post(self.slack_url, payload)
        logger.info(f"Slack notification: {status}")
        return status == 200, body

    # ── Microsoft Teams ───────────────────────────────────────────────────

    def send_teams(self, verdict, findings, model_name, report_path=None):
        """Send audit results to Microsoft Teams."""
        if not self.teams_url:
            return False, "TEAMS_WEBHOOK_URL not configured"

        total    = len(findings)
        passed   = sum(1 for f in findings if f.get("passed"))
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
        color    = {"PASS": "Good", "FAIL": "Attention", "CONDITIONAL PASS": "Warning"}.get(verdict, "default")

        payload = {
            "@type":      "MessageCard",
            "@context":   "http://schema.org/extensions",
            "themeColor": {"PASS": "28a745", "FAIL": "dc3545"}.get(verdict, "6c757d"),
            "summary":    f"AI Audit Complete: {verdict}",
            "sections": [{
                "activityTitle": f"AITestSuite v3 — {verdict}",
                "activitySubtitle": model_name,
                "facts": [
                    {"name": "Tests Passed", "value": f"{passed}/{total}"},
                    {"name": "Critical Findings", "value": str(critical)},
                    {"name": "Time", "value": time.strftime('%Y-%m-%d %H:%M')},
                    {"name": "Report", "value": report_path or "N/A"},
                ]
            }]
        }
        status, body = self._post(self.teams_url, payload)
        logger.info(f"Teams notification: {status}")
        return status in [200, 202], body

    # ── PagerDuty ─────────────────────────────────────────────────────────

    def trigger_pagerduty(self, verdict, findings, model_name, severity=None):
        """Trigger a PagerDuty incident for critical findings."""
        if not self.pagerduty_key:
            return False, "PAGERDUTY_ROUTING_KEY not configured"

        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
        if verdict == "PASS" and critical == 0:
            return True, "No alert needed — audit passed"

        pd_severity = severity or ("critical" if verdict == "FAIL" else "warning")

        payload = {
            "routing_key":  self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary":   f"AI Audit {verdict}: {model_name} — {critical} critical findings",
                "severity":  pd_severity,
                "source":    "AITestSuite v3",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "custom_details": {
                    "model":          model_name,
                    "verdict":        verdict,
                    "total_tests":    len(findings),
                    "critical":       critical,
                }
            }
        }
        status, body = self._post("https://events.pagerduty.com/v2/enqueue", payload)
        logger.info(f"PagerDuty alert: {status}")
        return status == 202, body

    # ── Jira ──────────────────────────────────────────────────────────────

    def create_jira_ticket(self, finding, model_name):
        """Create a Jira ticket for a critical finding."""
        if not all([self.jira_url, self.jira_email, self.jira_token]):
            return False, "Jira not fully configured"

        import base64
        creds   = base64.b64encode(f"{self.jira_email}:{self.jira_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {creds}",
            "Content-Type":  "application/json"
        }

        rm    = finding.get("risk_matrix", {})
        score = rm.get("overall", 0)

        payload = {
            "fields": {
                "project":     {"key": self.jira_project},
                "summary":     f"[AI Security] {finding.get('name', 'Unknown')} — Risk {score}/5",
                "issuetype":   {"name": "Bug"},
                "priority":    {"name": "Critical" if score >= 4.5 else "High"},
                "description": {
                    "type":    "doc",
                    "version": 1,
                    "content": [{
                        "type":    "paragraph",
                        "content": [{
                            "type": "text",
                            "text": (
                                f"Model: {model_name}\n"
                                f"Category: {finding.get('category')}\n"
                                f"Risk Score: {score}/5\n\n"
                                f"Healthcare Implication: {finding.get('healthcare_implication', 'N/A')}\n\n"
                                f"Remediation: {finding.get('remediation', 'See audit report')}\n\n"
                                f"Regulations: {', '.join(finding.get('regulations', []))}"
                            )
                        }]
                    }]
                }
            }
        }

        url    = f"{self.jira_url.rstrip('/')}/rest/api/3/issue"
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req  = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                ticket_key = result.get("key", "unknown")
                logger.info(f"Jira ticket created: {ticket_key}")
                return True, ticket_key
        except Exception as e:
            logger.error(f"Jira ticket failed: {e}")
            return False, str(e)

    # ── Generic SIEM / Webhook ────────────────────────────────────────────

    def send_siem(self, findings, verdict, model_name):
        """
        Send findings to a generic SIEM or webhook endpoint.
        Compatible with Splunk HTTP Event Collector, Datadog,
        Elastic, and any REST endpoint.
        """
        if not self.siem_url:
            return False, "SIEM_WEBHOOK_URL not configured"

        headers = {"Content-Type": "application/json"}
        if self.siem_key:
            headers["Authorization"] = f"Bearer {self.siem_key}"

        payload = {
            "source":     "AITestSuite_v3",
            "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model":      model_name,
            "verdict":    verdict,
            "total":      len(findings),
            "passed":     sum(1 for f in findings if f.get("passed")),
            "failed":     sum(1 for f in findings if not f.get("passed")),
            "critical":   sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5),
            "findings":   [
                {
                    "name":      f.get("name"),
                    "category":  f.get("category"),
                    "passed":    f.get("passed"),
                    "risk":      f.get("risk_matrix", {}).get("overall"),
                    "timestamp": f.get("timestamp")
                }
                for f in findings if not f.get("passed")  # Only failed findings
            ]
        }
        status, body = self._post(self.siem_url, payload, headers)
        logger.info(f"SIEM event sent: {status}")
        return status in [200, 201, 202], body

    # ── Dispatch all configured integrations ─────────────────────────────

    def dispatch_all(self, verdict, findings, model_name, report_path=None):
        """
        Fire all configured integrations simultaneously.
        Returns dict of results per integration.
        """
        results = {}

        # Only alert if there is something to alert about
        critical = sum(1 for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5)
        should_alert = verdict in ["FAIL", "CONDITIONAL PASS"] or critical > 0

        if self.slack_url:
            ok, msg = self.send_slack(verdict, findings, model_name, report_path)
            results["slack"] = {"ok": ok, "message": msg}

        if self.teams_url:
            ok, msg = self.send_teams(verdict, findings, model_name, report_path)
            results["teams"] = {"ok": ok, "message": msg}

        if self.pagerduty_key and should_alert:
            ok, msg = self.trigger_pagerduty(verdict, findings, model_name)
            results["pagerduty"] = {"ok": ok, "message": msg}

        if self.siem_url:
            ok, msg = self.send_siem(findings, verdict, model_name)
            results["siem"] = {"ok": ok, "message": msg}

        # Create Jira tickets for critical findings
        if self.jira_url and critical > 0:
            critical_findings = [f for f in findings if f.get("risk_matrix", {}).get("overall", 0) >= 4.5]
            jira_results = []
            for f in critical_findings[:5]:  # Max 5 tickets per run
                ok, key = self.create_jira_ticket(f, model_name)
                jira_results.append({"ok": ok, "key": key, "finding": f.get("name")})
            results["jira"] = jira_results

        configured = [k for k in results]
        logger.info(f"Enterprise dispatch complete: {configured}")
        return results

    def get_configured(self):
        """Return list of configured integrations."""
        configured = []
        if self.slack_url:      configured.append("Slack")
        if self.teams_url:      configured.append("Microsoft Teams")
        if self.pagerduty_key:  configured.append("PagerDuty")
        if self.jira_url:       configured.append("Jira")
        if self.siem_url:       configured.append("SIEM/Webhook")
        return configured
