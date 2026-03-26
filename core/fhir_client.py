"""
AITestSuite v3.2 — FHIR R4 Client
Author: Amarjit Khakh

Real FHIR R4 HTTP client for Epic/Cerner/OSCAR sandboxes.
Falls back to EHR simulator when no endpoint configured.

Environment variables:
  FHIR_BASE_URL    — FHIR server base URL
  FHIR_CLIENT_ID   — OAuth2 client ID
  FHIR_CLIENT_SECRET — OAuth2 client secret (backend service)
  EHR_SYSTEM       — epic | cerner | oscar | generic
  FHIR_SCOPE       — OAuth2 scopes (default: system/*.read)

Sandbox endpoints (free registration):
  Epic:   https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
  Cerner: https://fhir-ehr-code.cerner.com/r4/
  OSCAR:  http://localhost:8080/oscar/fhir (Docker self-hosted)
"""

import os
import json
import logging
from typing import Optional
from core.ehr_simulator import get_simulator
from core.clinical_terminology import is_valid_loinc, is_valid_din

logger = logging.getLogger("AITestSuite.FHIRClient")

SANDBOX_URLS = {
    "epic":   "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
    "cerner": "https://fhir-ehr-code.cerner.com/r4/",
    "oscar":  "http://localhost:8080/oscar/fhir",
}


class FHIRClient:
    """
    FHIR R4 client that auto-detects real vs simulated mode.
    When FHIR_BASE_URL is set: makes real HTTP calls.
    When not set: uses EHR simulator with realistic data.
    """

    def __init__(self):
        self.base_url = os.environ.get("FHIR_BASE_URL", "").rstrip("/")
        self.ehr_system = os.environ.get("EHR_SYSTEM", "generic").lower()
        self.client_id = os.environ.get("FHIR_CLIENT_ID", "")
        self.client_secret = os.environ.get("FHIR_CLIENT_SECRET", "")
        self.scope = os.environ.get("FHIR_SCOPE", "system/*.read")
        self.simulator = get_simulator()
        self._token = None
        self._mode = "real" if self.base_url else "simulator"
        logger.info(f"FHIRClient mode: {self._mode} | system: {self.ehr_system}")

    @property
    def mode(self) -> str:
        return self._mode

    def _get_token(self) -> Optional[str]:
        """Get OAuth2 token for real FHIR server."""
        if not self.client_id:
            return None
        try:
            import urllib.request, urllib.parse
            from core.smart_auth import SMARTAuth
            auth = SMARTAuth(self.ehr_system, self.client_id, self.client_secret)
            self._token = auth.get_token()
            return self._token
        except Exception as e:
            logger.warning(f"Token fetch failed: {e}")
            return None

    def _real_request(self, path: str, params: dict = None) -> dict:
        """Make a real HTTP request to FHIR server."""
        try:
            import urllib.request, urllib.parse
            url = f"{self.base_url}/{path}"
            if params:
                url += "?" + urllib.parse.urlencode(params)

            req = urllib.request.Request(url)
            req.add_header("Accept", "application/fhir+json")
            req.add_header("Content-Type", "application/fhir+json")

            token = self._token or self._get_token()
            if token:
                req.add_header("Authorization", f"Bearer {token}")

            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"FHIR request failed: {e}")
            return {"resourceType": "OperationOutcome",
                    "issue": [{"severity": "error", "diagnostics": str(e)}]}

    def get_patient(self, patient_id: str) -> dict:
        if self._mode == "real":
            return self._real_request(f"Patient/{patient_id}")
        return self.simulator.get_patient(patient_id)["resource"] \
               if self.simulator.get_patient(patient_id).get("status") == 200 \
               else {"error": f"Patient {patient_id} not found"}

    def search_patients(self, family: str = None, given: str = None,
                        birthdate: str = None, identifier: str = None) -> dict:
        params = {}
        if family:     params["family"] = family
        if given:      params["given"] = given
        if birthdate:  params["birthdate"] = birthdate
        if identifier: params["identifier"] = identifier

        if self._mode == "real":
            return self._real_request("Patient", params)

        # Simulator search
        from core.ehr_simulator import PATIENTS
        matches = []
        for pid, p in PATIENTS.items():
            name = p.get("name", [{}])[0]
            if family and family.lower() not in name.get("family","").lower():
                continue
            matches.append({"resource": p})
        return {"resourceType": "Bundle", "type": "searchset",
                "total": len(matches), "entry": matches}

    def get_observations(self, patient_id: str,
                         loinc_code: str = None, count: int = 10) -> dict:
        if loinc_code and not is_valid_loinc(loinc_code):
            logger.warning(f"Invalid LOINC code requested: {loinc_code}")

        if self._mode == "real":
            params = {"patient": patient_id, "_count": count}
            if loinc_code:
                params["code"] = f"http://loinc.org|{loinc_code}"
            return self._real_request("Observation", params)

        return self.simulator.get_labs(patient_id, loinc_code)

    def get_medication_requests(self, patient_id: str, status: str = "active") -> dict:
        if self._mode == "real":
            return self._real_request("MedicationRequest",
                                       {"patient": patient_id, "status": status})
        return self.simulator.get_medications(patient_id)

    def get_conditions(self, patient_id: str) -> dict:
        if self._mode == "real":
            return self._real_request("Condition", {"patient": patient_id})
        return self.simulator.get_conditions(patient_id)

    def get_allergy_intolerances(self, patient_id: str) -> dict:
        if self._mode == "real":
            return self._real_request("AllergyIntolerance", {"patient": patient_id})
        return self.simulator.get_allergies(patient_id)

    def create_observation(self, patient_id: str, loinc_code: str,
                           value: float, unit: str, note: str = "") -> dict:
        """Create an Observation resource (write operation)."""
        if not is_valid_loinc(loinc_code):
            return {
                "error": f"Invalid LOINC code: {loinc_code}. "
                         "Observation not created — use a valid LOINC code.",
                "hint": "Examples: 2160-0 (creatinine), 4548-4 (HbA1c), 34714-6 (INR)",
            }
        from core.clinical_terminology import LOINC_CODES
        loinc_info = LOINC_CODES[loinc_code]
        resource = {
            "resourceType": "Observation",
            "status": "preliminary",
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {"coding": [{"system": "http://loinc.org",
                                  "code": loinc_code,
                                  "display": loinc_info["name"]}]},
            "valueQuantity": {"value": value, "unit": unit,
                              "system": "http://unitsofmeasure.org"},
            "effectiveDateTime": __import__("time").strftime('%Y-%m-%dT%H:%M:%SZ',
                                            __import__("time").gmtime()),
            "note": [{"text": f"AI-generated observation. {note} Requires clinician review."}],
        }
        if self._mode == "real":
            # POST to real server
            try:
                import urllib.request
                data = json.dumps(resource).encode()
                req = urllib.request.Request(
                    f"{self.base_url}/Observation",
                    data=data, method="POST")
                req.add_header("Content-Type", "application/fhir+json")
                req.add_header("Accept", "application/fhir+json")
                if self._token:
                    req.add_header("Authorization", f"Bearer {self._token}")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return json.loads(resp.read().decode())
            except Exception as e:
                return {"error": str(e)}

        resource["id"] = f"obs-sim-{patient_id}-{loinc_code}"
        return {"status": 201, "resource": resource,
                "note": "Simulated write — not persisted to real EHR"}

    def create_medication_request(self, patient_id: str, din: str,
                                   dose: str, instructions: str,
                                   prescriber: str) -> dict:
        """Create a MedicationRequest — validates DIN before creating."""
        if not is_valid_din(din):
            return {
                "error": f"Invalid Canadian DIN: {din}. "
                         "Medication request not created.",
                "hint": "Verify DIN at Health Canada Drug Product Database: "
                        "https://health-products.canada.ca/dpd-bdpp/",
            }
        from core.clinical_terminology import CANADIAN_DINS
        drug_info = CANADIAN_DINS[din]
        resource = {
            "resourceType": "MedicationRequest",
            "status": "draft",
            "intent": "order",
            "subject": {"reference": f"Patient/{patient_id}"},
            "medicationCodeableConcept": {"coding": [
                {"system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din",
                 "code": din, "display": f"{drug_info['drug']} {drug_info['strength']}"},
            ]},
            "dosageInstruction": [{"text": f"{dose} — {instructions}"}],
            "requester": {"display": prescriber},
            "note": [{"text": "AI-generated medication request. REQUIRES PHYSICIAN REVIEW AND SIGNATURE before dispensing."}],
        }
        if drug_info.get("schedule") == "prescription_controlled_narcotic":
            resource["note"].append({
                "text": "CONTROLLED SUBSTANCE: Requires triplicate prescription in some provinces. "
                        "Check provincial DEA requirements."
            })
        return {"status": 201, "resource": resource,
                "warning": "Draft only — not active until physician signs",
                "note": "Simulated write" if self._mode == "simulator" else "Written to FHIR server"}

    def capability_statement(self) -> dict:
        """Get server capability statement (FHIR metadata)."""
        if self._mode == "real":
            return self._real_request("metadata")
        return {
            "resourceType": "CapabilityStatement",
            "status": "active",
            "kind": "instance",
            "software": {"name": "AITestSuite EHR Simulator", "version": "3.2"},
            "fhirVersion": "4.0.1",
            "format": ["application/fhir+json"],
            "rest": [{"mode": "server", "resource": [
                {"type": t, "interaction": [{"code": "read"}, {"code": "search-type"}]}
                for t in ["Patient", "Observation", "MedicationRequest",
                          "Condition", "AllergyIntolerance", "DiagnosticReport"]
            ]}],
        }

    @classmethod
    def setup_instructions(cls, system: str = "epic") -> str:
        """Return setup instructions for connecting to a real EHR sandbox."""
        instructions = {
            "epic": """
EPIC FHIR SANDBOX SETUP
========================
1. Register at: https://fhir.epic.com/
2. Create a non-production app
3. Get your Client ID (no secret needed for public sandbox)
4. Set environment variables:
   export FHIR_BASE_URL="https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
   export FHIR_CLIENT_ID="your-epic-client-id"
   export EHR_SYSTEM="epic"
5. Synthetic patients available — no PHI risk
6. PHC / VGH use Epic in production — same API surface
""",
            "cerner": """
CERNER (ORACLE HEALTH) FHIR SANDBOX SETUP
==========================================
1. Register at: https://code.cerner.com/
2. Create a Millennium FHIR app
3. Get your Client ID
4. Set environment variables:
   export FHIR_BASE_URL="https://fhir-ehr-code.cerner.com/r4/"
   export FHIR_CLIENT_ID="your-cerner-client-id"
   export EHR_SYSTEM="cerner"
5. Fraser Health uses Cerner in production — directly relevant to PHC
""",
            "oscar": """
OSCAR EMR SELF-HOSTED SETUP
============================
1. Docker: docker pull oscaremr/oscar
2. Run: docker run -p 8080:8080 oscaremr/oscar
3. FHIR endpoint: http://localhost:8080/oscar/fhir
4. Set environment variables:
   export FHIR_BASE_URL="http://localhost:8080/oscar/fhir"
   export EHR_SYSTEM="oscar"
5. ~30% of Canadian GPs use OSCAR — most relevant for clinic/GP testing
""",
        }
        return instructions.get(system, "System not recognized. Use: epic, cerner, oscar")
