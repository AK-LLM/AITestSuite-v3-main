"""
═══════════════════════════════════════════════════════════════════════════
AITestSuite v3 — Black Box Browser Automation Module
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════════════════════

⚠️  AUTHORISATION WARNING — READ BEFORE USE  ⚠️
════════════════════════════════════════════════════════════════════════════

THIS MODULE AUTOMATES A BROWSER TO INTERACT WITH AI CHAT INTERFACES.

LEGAL AND ETHICAL REQUIREMENTS:
    1. You MUST have EXPLICIT WRITTEN AUTHORISATION from the system owner
       before running this module against any AI interface.

    2. This module MUST NOT be used against:
       - Any public AI chat interface without written permission from that provider
       - Any system you do not own or control
       - Any production system without explicit written authorisation

    3. Authorised use cases ONLY:
       - Your own locally deployed AI web interface
       - A vendor-supplied test environment with written permission
       - A healthcare or enterprise AI pilot with written sign-off
       - Any system where explicit written authorisation has been obtained

    4. Every session MUST have an authorisation reference logged.
       This module will REFUSE to run without one.

    5. All findings from this module are for DEFENSIVE purposes only:
       identifying vulnerabilities so they can be FIXED — not exploited.

ETHICAL FRAMEWORK:
    This module follows the same ethical principles as traditional
    penetration testing: written scope, defined targets, documented
    methodology, responsible disclosure of findings.

LEGAL REFERENCES:
    - Criminal Code of Canada s.342.1 (Unauthorized Computer Access)
    - BC Computer Information Act
    - PIPEDA (data collected during testing)
    - Computer Fraud and Abuse Act (if US systems involved)

IF IN DOUBT — DO NOT RUN.

════════════════════════════════════════════════════════════════════════════

PURPOSE:
    Automates a browser to send test prompts to any AI chat web interface
    and capture responses — no API key required.

    This enables testing of:
    - AI tools deployed behind corporate intranets with no API
    - Vendor-supplied AI systems in pilot/test environments
    - Any AI web interface where you have explicit written permission

HOW IT WORKS:
    1. Opens a browser (Chrome/Firefox via Selenium)
    2. Navigates to the target URL
    3. Locates the chat input field using configurable CSS selectors
    4. Sends each test prompt
    5. Waits for and captures the response
    6. Returns results to the main audit engine for scoring

DEPENDENCIES:
    pip install selenium webdriver-manager
    Chrome or Firefox browser must be installed

SUPPORTED INTERFACES (with authorisation):
    - Any AI chat interface configurable via CSS selectors
    - Pre-configured profiles for common interface patterns
═══════════════════════════════════════════════════════════════════════════
"""

import time
import logging

# ── Module logger ─────────────────────────────────────────────────────────
logger = logging.getLogger("AITestSuite.BlackBox")

# ── Authorisation enforcement ─────────────────────────────────────────────
# This dict tracks the authorisation reference for the current session.
# The module will refuse to run without a valid authorisation reference.
_AUTHORISATION = {
    "granted":   False,
    "reference": None,
    "target":    None,
    "auditor":   None,
    "timestamp": None
}


# ── Pre-configured interface profiles ─────────────────────────────────────
# CSS selector profiles for known interface layouts.
# Add your own target interface profile here.

INTERFACE_PROFILES = {
    "generic_input_box": {
        # Works with most simple chat interfaces
        # Adjust selectors to match your specific target
        "description":      "Generic single input box interface",
        "input_selector":   "textarea",          # CSS selector for the input field
        "submit_selector":  "button[type=submit]",  # CSS selector for submit button
        "response_selector":"[data-role='response']", # CSS selector for response area
        "wait_seconds":     5,                   # Seconds to wait for response
    },
    "custom_target": {
        # Configure this for your specific authorised target
        # Example: a hospital intranet AI tool
        "description":      "Custom authorised target (configure before use)",
        "input_selector":   "textarea#chat-input",    # UPDATE THIS
        "submit_selector":  "button#send-button",     # UPDATE THIS
        "response_selector":"div.ai-response",        # UPDATE THIS
        "wait_seconds":     8,
    },
}


def authorise_session(reference, target_url, auditor_name):
    """
    ⚠️ MANDATORY: Call this before any automated testing.

    Records the authorisation reference for audit trail purposes.
    The module will refuse to run without this being called first.

    Args:
        reference    : Written authorisation reference number or description
                       e.g. "Organisation AI Test Agreement 2026-03-15"
                       e.g. "Healthcare Pilot Written Approval — Reference 2026"
        target_url   : The exact URL of the system being tested
        auditor_name : Name of the person conducting the test

    Example:
        authorise_session(
            reference    = "Healthcare Org AI Pilot Test Agreement signed 2026-03-15",
            target_url   = "https://your-authorised-target.ca/chat",
            auditor_name = "Amarjit Khakh"
        )
    """
    # Validate required fields
    if not reference or len(reference.strip()) < 10:
        raise ValueError(
            "⚠️ Authorisation reference too short. "
            "You must provide a meaningful written authorisation reference."
        )

    if not target_url.startswith("http"):
        raise ValueError(
            "⚠️ Target URL must be a valid HTTP/HTTPS URL."
        )

    # Record the authorisation
    _AUTHORISATION["granted"]   = True
    _AUTHORISATION["reference"] = reference.strip()
    _AUTHORISATION["target"]    = target_url.strip()
    _AUTHORISATION["auditor"]   = auditor_name.strip()
    _AUTHORISATION["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

    logger.info(
        f"Session authorised | Ref: {reference} | "
        f"Target: {target_url} | Auditor: {auditor_name}"
    )

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  AUTHORISATION RECORDED                                      ║
║  Reference : {reference[:50]:<50} ║
║  Target    : {target_url[:50]:<50} ║
║  Auditor   : {auditor_name[:50]:<50} ║
║  Time      : {_AUTHORISATION['timestamp']:<50} ║
╚══════════════════════════════════════════════════════════════╝
    """)

    return True


def _check_authorisation():
    """
    Internal: Verify authorisation has been granted before any test runs.
    Raises an error if not authorised.
    """
    if not _AUTHORISATION["granted"]:
        raise PermissionError("""
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  AUTHORISATION REQUIRED                                  ║
║                                                              ║
║  You must call authorise_session() before running tests.     ║
║                                                              ║
║  You need:                                                   ║
║  1. Written permission from the target system owner          ║
║  2. A reference number or document for that permission       ║
║  3. The exact URL of the system you are testing              ║
║                                                              ║
║  Example:                                                    ║
║  authorise_session(                                          ║
║      reference = "Healthcare Org Agreement 2026-03-15",        ║
║      target_url = "https://your-target.ca/chat",               ║
║      auditor_name = "Amarjit Khakh"                            ║
║  )                                                           ║
╚══════════════════════════════════════════════════════════════╝
        """)


class BlackBoxAdapter:
    """
    Browser automation adapter for testing AI chat web interfaces.

    Uses Selenium to control a real browser — no API key required.
    Implements the same interface as ModelAdapter so it plugs directly
    into the main AuditRunner without any changes.

    ⚠️ ONLY USE AGAINST SYSTEMS YOU HAVE EXPLICIT WRITTEN PERMISSION TO TEST.
    """

    def __init__(self, target_url, interface_profile="generic_input_box",
                 browser="chrome", headless=True):
        """
        Args:
            target_url        : URL of the authorised target AI interface
            interface_profile : Key from INTERFACE_PROFILES dict
            browser           : 'chrome' or 'firefox'
            headless          : Run without visible browser window (True/False)
        """
        self.target_url        = target_url
        self.profile           = INTERFACE_PROFILES.get(interface_profile, INTERFACE_PROFILES["generic_input_box"])
        self.browser           = browser
        self.headless          = headless
        self.driver            = None
        self.model_type        = "blackbox_browser"
        self.model_name        = f"BlackBox @ {target_url}"

    def load(self):
        """
        Initialise the browser driver.
        Checks authorisation before proceeding.
        """
        # ⚠️ Authorisation check — will raise if not authorised
        _check_authorisation()

        try:
            if self.browser == "chrome":
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service

                options = Options()
                if self.headless:
                    options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])

                # Auto-download matching ChromeDriver
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)

            elif self.browser == "firefox":
                from selenium import webdriver
                from selenium.webdriver.firefox.options import Options
                from webdriver_manager.firefox import GeckoDriverManager
                from selenium.webdriver.firefox.service import Service

                options = Options()
                if self.headless:
                    options.add_argument("--headless")

                service = Service(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=options)

            # Navigate to target
            self.driver.get(self.target_url)
            time.sleep(2)  # Allow page to load

            logger.info(f"Browser opened — Target: {self.target_url}")
            return True

        except ImportError:
            raise ImportError(
                "Selenium not installed. Run: pip install selenium webdriver-manager"
            )
        except Exception as e:
            raise RuntimeError(f"Browser initialisation failed: {e}")

    def query(self, prompt, max_tokens=150):
        """
        Send a prompt to the target web interface and capture the response.

        Args:
            prompt     : The test prompt to send
            max_tokens : Not used for browser mode (kept for interface compatibility)

        Returns:
            String response captured from the interface
        """
        # ⚠️ Authorisation check on every query
        _check_authorisation()

        if not self.driver:
            raise RuntimeError("Browser not initialised. Call load() first.")

        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            wait = WebDriverWait(self.driver, 15)

            # ── Find and interact with the input field ────────────────
            input_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.profile["input_selector"]))
            )

            # Clear any existing content
            input_field.clear()

            # Type the prompt
            input_field.send_keys(prompt)
            time.sleep(0.5)

            # ── Submit the prompt ─────────────────────────────────────
            try:
                # Try clicking the submit button
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, self.profile["submit_selector"])
                submit_btn.click()
            except Exception:
                # Fall back to pressing Enter
                input_field.send_keys(Keys.RETURN)

            # ── Wait for response ─────────────────────────────────────
            wait_time = self.profile.get("wait_seconds", 5)
            time.sleep(wait_time)

            # ── Capture the response ──────────────────────────────────
            try:
                response_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, self.profile["response_selector"]
                )
                if response_elements:
                    # Get the last response (most recent)
                    response = response_elements[-1].text.strip()
                else:
                    # Fallback: get all visible text in the body
                    response = self.driver.find_element(By.TAG_NAME, "body").text[-500:]
            except Exception:
                response = "CAPTURE_ERROR: Could not locate response element"

            logger.info(f"Prompt sent | Response captured ({len(response)} chars)")
            return response

        except Exception as e:
            return f"BROWSER_ERROR: {str(e)}"

    def info(self):
        """Return model info dict compatible with audit runner."""
        return {
            "model_type": "blackbox_browser",
            "model_name": self.model_name,
            "target_url": self.target_url,
            "authorisation": _AUTHORISATION.get("reference", "NOT SET")
        }

    def close(self):
        """Close the browser when testing is complete."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Browser closed")

    def __del__(self):
        """Ensure browser is closed when object is garbage collected."""
        self.close()


class ManualBlackBoxAdapter:
    """
    Manual black box adapter — NO browser automation.

    For when you want to test a chat interface MANUALLY
    (copy/paste prompts yourself) but still have the toolkit
    score and report the findings automatically.

    Perfect for:
    - Testing any public AI chat interface manually (no ToS issues)
    - Testing any chat interface without Selenium
    - Academic demonstrations

    HOW IT WORKS:
    - The app shows you each prompt
    - You copy it and paste it into the target interface manually
    - You copy the response and paste it back
    - The toolkit scores it and includes it in the PDF report
    """

    def __init__(self, target_description="Manual Black Box Test"):
        self.target_description = target_description
        self.model_type         = "manual_blackbox"
        self.model_name         = f"Manual: {target_description}"
        self._responses         = {}  # Stores manually entered responses

    def load(self):
        """No setup needed for manual mode."""
        return True

    def set_response(self, prompt_key, response):
        """
        Store a manually entered response for a given prompt.

        Args:
            prompt_key : A short identifier for the prompt
            response   : The response you got from the target interface
        """
        self._responses[prompt_key] = response

    def query(self, prompt, max_tokens=150):
        """
        Returns manually stored response or a PENDING marker.
        PENDING responses are flagged in the report for manual completion.
        """
        # Use first 50 chars of prompt as the key
        key = prompt[:50].strip()
        return self._responses.get(key, "MANUAL_PENDING: Response not yet entered")

    def info(self):
        return {
            "model_type":  "manual_blackbox",
            "model_name":  self.model_name,
            "target":      self.target_description,
        }
