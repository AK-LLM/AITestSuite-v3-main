"""
AITestSuite v3.2 — SMART on FHIR OAuth2 Authentication
Author: Amarjit Khakh

Handles authentication for Epic, Cerner, and OSCAR.
Supports client credentials flow for backend service auth.
"""

import os
import json
import time
import base64
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger("AITestSuite.SMARTAuth")

WELL_KNOWN_ENDPOINTS = {
    "epic": {
        "token_endpoint":    "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token",
        "auth_endpoint":     "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize",
        "fhir_base":         "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
        "sandbox_note":      "Epic sandbox — free at fhir.epic.com. PHC/VGH production system.",
    },
    "cerner": {
        "token_endpoint":    "https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/token",
        "auth_endpoint":     "https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/personas/provider/authorize",
        "fhir_base":         "https://fhir-ehr-code.cerner.com/r4/",
        "sandbox_note":      "Cerner sandbox — free at code.cerner.com. Fraser Health production system.",
    },
    "oscar": {
        "token_endpoint":    "http://localhost:8080/oscar/oauth/token",
        "auth_endpoint":     "http://localhost:8080/oscar/oauth/authorize",
        "fhir_base":         "http://localhost:8080/oscar/fhir",
        "sandbox_note":      "OSCAR self-hosted — Docker. ~30% of Canadian GP clinics.",
    },
}


class SMARTAuth:
    """SMART on FHIR OAuth2 handler."""

    def __init__(self, system: str, client_id: str, client_secret: str = ""):
        self.system = system.lower()
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expiry = 0
        self.endpoints = WELL_KNOWN_ENDPOINTS.get(self.system, {})

    def get_token(self) -> str:
        """Get access token, refreshing if expired."""
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        if not self.client_id:
            raise ValueError("FHIR_CLIENT_ID not set. See setup instructions.")

        token_url = self.endpoints.get("token_endpoint")
        if not token_url:
            raise ValueError(f"Unknown EHR system: {self.system}. Use: epic, cerner, oscar")

        # Client credentials flow
        data = urllib.parse.urlencode({
            "grant_type":    "client_credentials",
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "scope":         os.environ.get("FHIR_SCOPE", "system/*.read"),
        }).encode()

        req = urllib.request.Request(token_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/json")

        if self.client_secret:
            creds = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            req.add_header("Authorization", f"Basic {creds}")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                token_data = json.loads(resp.read().decode())
                self._token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expiry = time.time() + expires_in
                logger.info(f"Token obtained for {self.system}, expires in {expires_in}s")
                return self._token
        except Exception as e:
            logger.error(f"Token request failed: {e}")
            raise

    def get_auth_url(self, redirect_uri: str, state: str = "audit") -> str:
        """Get authorization URL for user-facing OAuth2 flow."""
        auth_url = self.endpoints.get("auth_endpoint", "")
        params = urllib.parse.urlencode({
            "response_type": "code",
            "client_id":     self.client_id,
            "redirect_uri":  redirect_uri,
            "scope":         "launch/patient patient/*.read",
            "state":         state,
            "aud":           self.endpoints.get("fhir_base", ""),
        })
        return f"{auth_url}?{params}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token."""
        token_url = self.endpoints.get("token_endpoint", "")
        data = urllib.parse.urlencode({
            "grant_type":   "authorization_code",
            "code":         code,
            "redirect_uri": redirect_uri,
            "client_id":    self.client_id,
        }).encode()

        req = urllib.request.Request(token_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_setup_instructions(system: str = "epic") -> str:
        info = WELL_KNOWN_ENDPOINTS.get(system, {})
        if not info:
            return f"Unknown system: {system}. Use: epic, cerner, oscar"
        lines = [
            f"EHR SYSTEM: {system.upper()}",
            f"FHIR Base:  {info.get('fhir_base','')}",
            f"Token URL:  {info.get('token_endpoint','')}",
            f"Note:       {info.get('sandbox_note','')}",
            "",
            "Environment variables to set:",
            f"  export FHIR_BASE_URL='{info.get('fhir_base', '')}'",
            f"  export EHR_SYSTEM='{system}'",
            "  export FHIR_CLIENT_ID='your-client-id'",
            "  export FHIR_CLIENT_SECRET='your-secret-if-required'",
        ]
        return "\n".join(lines)

# Module-level convenience alias
def get_setup_instructions(system: str = "epic") -> str:
    """Module-level wrapper for SMARTAuth.get_setup_instructions."""
    return SMARTAuth.get_setup_instructions(system)
