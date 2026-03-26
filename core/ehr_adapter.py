"""
AITestSuite v3.2 — EHR Adapter Layer
Author: Amarjit Khakh

System-specific adapter that wraps FHIRClient with the quirks,
authentication patterns, and Canadian deployment context for:
  - Epic (VGH, UHN — PHC uses Epic)
  - Cerner (Fraser Health)
  - OSCAR EMR (~30% of Canadian GP clinics)
  - Generic FHIR R4

Each adapter normalises the system-specific response format
into a consistent dict for consumption by the test suite
and simulation engine.

USAGE:
  from core.ehr_adapter import get_adapter

  # Auto-detect from EHR_SYSTEM env var or default to simulator
  adapter = get_adapter()
  patient  = adapter.get_patient("4421")
  meds     = adapter.get_medications("4421")
  
  # Explicit system
  adapter = get_adapter("cerner")   # Fraser Health
  adapter = get_adapter("epic")     # VGH / PHC
  adapter = get_adapter("oscar")    # GP clinics
"""

import os
import logging
from typing import Optional
from core.fhir_client import FHIRClient
from core.ehr_simulator import EHRSimulator

logger = logging.getLogger("AITestSuite.EHRAdapter")


# ═══════════════════════════════════════════════════════════════════════
# BASE ADAPTER
# ═══════════════════════════════════════════════════════════════════════

class BaseEHRAdapter:
    """
    Normalises EHR responses into consistent format.
    All adapters return the same dict structure regardless of source.
    """

    SYSTEM_NAME    = "Generic FHIR R4"
    SYSTEM_KEY     = "generic"
    CANADIAN_ORG   = "Unknown"
    FHIR_VERSION   = "R4"

    def __init__(self, fhir_client: Optional[FHIRClient] = None):
        self.client    = fhir_client or FHIRClient()
        self.simulator = EHRSimulator()
        self.mode      = "real" if self.client.is_real_mode() else "simulator"

    def get_patient(self, patient_id: str) -> dict:
        raw = self.client.get_patient(patient_id)
        return self._normalise_patient(raw, patient_id)

    def get_medications(self, patient_id: str) -> list:
        raw = self.client.get_medication_requests(patient_id)
        return self._normalise_medications(raw)

    def get_labs(self, patient_id: str, loinc_code: str = None) -> list:
        raw = self.client.get_observations(patient_id, loinc_code=loinc_code)
        return self._normalise_observations(raw)

    def get_conditions(self, patient_id: str) -> list:
        raw = self.client.get_conditions(patient_id)
        return self._normalise_conditions(raw)

    def get_allergies(self, patient_id: str) -> list:
        raw = self.client.get_allergy_intolerances(patient_id)
        return self._normalise_allergies(raw)

    def check_drug_interaction(self, drug1: str, drug2: str) -> dict:
        return self.simulator.check_drug_interaction(drug1, drug2)

    def check_formulary(self, drug_name: str) -> dict:
        return self.simulator.check_formulary(drug_name)

    def write_note(self, patient_id: str, note: str, author: str) -> dict:
        return self.simulator.write_clinical_note(patient_id, note, author)

    def get_tool_response(self, tool: str, context: dict = None) -> str:
        """Used by simulation.py and attack_campaigns.py."""
        return self.simulator.get_tool_response(tool, context)

    def connection_info(self) -> dict:
        return {
            "system":      self.SYSTEM_NAME,
            "key":         self.SYSTEM_KEY,
            "canadian_org":self.CANADIAN_ORG,
            "mode":        self.mode,
            "fhir_version":self.FHIR_VERSION,
            **self.client.get_connection_info(),
        }

    # ── Normalisation helpers ───────────────────────────────────────

    def _normalise_patient(self, raw: dict, patient_id: str) -> dict:
        if raw.get("error"):
            return raw
        name = raw.get("name", [{}])[0] if raw.get("name") else {}
        return {
            "id":          raw.get("id", patient_id),
            "family":      name.get("family",""),
            "given":       " ".join(name.get("given",[])),
            "dob":         raw.get("birthDate",""),
            "gender":      raw.get("gender",""),
            "mrn":         raw.get("meta",{}).get("mrn",""),
            "province":    raw.get("meta",{}).get("province",""),
            "pharmanet_id":raw.get("pharmanet_id",""),
            "fnha_eligible":raw.get("fnha_eligible", False),
            "cultural_note":raw.get("cultural_safety_note",""),
            "system":      self.SYSTEM_KEY,
            "_raw":        raw,
        }

    def _normalise_medications(self, raw: dict) -> list:
        meds = []
        for entry in raw.get("entry", []):
            r = entry.get("resource", entry)
            coding = r.get("medication", {})
            if isinstance(coding, dict):
                coding = coding.get("coding", [{}])[0]
            else:
                coding = {}
            dosage = r.get("dosageInstruction", [{}])[0] if r.get("dosageInstruction") else {}
            meds.append({
                "drug":       coding.get("display",""),
                "din":        coding.get("code",""),
                "dose":       dosage.get("text",""),
                "status":     r.get("status",""),
                "prescriber": r.get("requester",{}).get("display","") if isinstance(r.get("requester"),dict) else "",
                "indication": r.get("reasonCode",[{}])[0].get("text","") if r.get("reasonCode") else "",
            })
        return meds

    def _normalise_observations(self, raw: dict) -> list:
        obs = []
        for entry in raw.get("entry", []):
            r = entry.get("resource", entry)
            coding = r.get("code",{}).get("coding",[{}])[0] if r.get("code") else {}
            vq = r.get("valueQuantity",{})
            ref = r.get("referenceRange",[{}])[0] if r.get("referenceRange") else {}
            interp = r.get("interpretation",[{}])[0].get("coding",[{}])[0] if r.get("interpretation") else {}
            obs.append({
                "loinc":      coding.get("code",""),
                "display":    r.get("code",{}).get("text","") or coding.get("display",""),
                "value":      vq.get("value"),
                "unit":       vq.get("unit",""),
                "date":       r.get("effectiveDateTime",""),
                "status":     r.get("status",""),
                "flag":       interp.get("code","N"),
                "ref_low":    ref.get("low",{}).get("value") if isinstance(ref.get("low"),dict) else None,
                "ref_high":   ref.get("high",{}).get("value") if isinstance(ref.get("high"),dict) else None,
                "loinc_valid":r.get("loinc_validated", True),
            })
        return obs

    def _normalise_conditions(self, raw: dict) -> list:
        conds = []
        for entry in raw.get("entry", []):
            r = entry.get("resource", entry)
            coding = r.get("code",{}).get("coding",[{}])[0] if r.get("code") else {}
            conds.append({
                "snomed":  coding.get("code",""),
                "display": coding.get("display","") or r.get("code",{}).get("text",""),
                "onset":   r.get("onsetDateTime",""),
                "status":  r.get("clinicalStatus",{}).get("coding",[{}])[0].get("code","") if isinstance(r.get("clinicalStatus"),dict) else "",
            })
        return conds

    def _normalise_allergies(self, raw: dict) -> list:
        allergies = []
        for entry in raw.get("entry", []):
            r = entry.get("resource", entry)
            substance = r.get("code",{}).get("coding",[{}])[0].get("display","") if r.get("code") else ""
            reaction_list = r.get("reaction",[{}])[0].get("manifestation",[{}])[0].get("coding",[{}])[0].get("display","") if r.get("reaction") else ""
            allergies.append({
                "substance":   substance,
                "reaction":    reaction_list,
                "criticality": r.get("criticality",""),
            })
        return allergies


# ═══════════════════════════════════════════════════════════════════════
# EPIC ADAPTER — VGH, UHN, Providence Health Care
# ═══════════════════════════════════════════════════════════════════════

class EpicAdapter(BaseEHRAdapter):
    """
    Epic-specific adapter.
    PHC (Providence Health Care) and VGH use Epic.
    Epic FHIR sandbox: https://fhir.epic.com

    Epic quirks:
    - SMART on FHIR with Epic-specific scopes
    - Patient identifiers use Epic-specific system URLs
    - MyChart patient portal integration
    - CDS Hooks supported natively
    - Requires Epic App Orchard registration for production
    """

    SYSTEM_NAME    = "Epic (EpicCare)"
    SYSTEM_KEY     = "epic"
    CANADIAN_ORG   = "PHC / VGH / UHN"
    SANDBOX_URL    = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"

    EPIC_PATIENT_SYSTEM = "urn:oid:1.2.840.114350.1.13.861.1.7.5.737384.4399"

    def _normalise_patient(self, raw: dict, patient_id: str) -> dict:
        base = super()._normalise_patient(raw, patient_id)
        # Epic stores MRN in identifier array
        identifiers = raw.get("identifier", [])
        for ident in identifiers:
            if "MRN" in ident.get("type",{}).get("text","").upper():
                base["mrn"] = ident.get("value","")
                break
        base["epic_patient_id"] = raw.get("id","")
        return base

    def get_setup_instructions(self) -> str:
        return (
            "Epic Sandbox Setup:\n"
            "1. Register at https://fhir.epic.com\n"
            "2. Create Non-Production app\n"
            "3. Set environment variables:\n"
            f"   FHIR_BASE_URL={self.SANDBOX_URL}\n"
            "   FHIR_CLIENT_ID=your-epic-client-id\n"
            "   EHR_SYSTEM=epic\n"
            "Fraser Health note: PHC uses Epic — sandbox is identical API\n"
        )


# ═══════════════════════════════════════════════════════════════════════
# CERNER ADAPTER — Fraser Health, BC community hospitals
# ═══════════════════════════════════════════════════════════════════════

class CernerAdapter(BaseEHRAdapter):
    """
    Cerner (Oracle Health) adapter.
    Fraser Health uses Cerner — directly relevant to PHC Ventures.
    Cerner FHIR sandbox: https://fhir-ehr-code.cerner.com/r4/

    Cerner quirks:
    - SMART on FHIR with Cerner-specific tenant IDs
    - Different patient identifier systems per tenant
    - CDS Hooks supported
    - Millennium platform underneath
    - code.cerner.com for sandbox registration (free)
    """

    SYSTEM_NAME    = "Cerner (Oracle Health)"
    SYSTEM_KEY     = "cerner"
    CANADIAN_ORG   = "Fraser Health BC"
    SANDBOX_URL    = "https://fhir-ehr-code.cerner.com/r4/"
    TENANT_ID      = "ec2458f2-1e24-41c8-b71b-0e701af7583d"  # Sandbox tenant

    CERNER_MRN_SYSTEM = "https://fhir.cerner.com/ec2458f2-1e24-41c8-b71b-0e701af7583d/codeSet/4"

    def _normalise_patient(self, raw: dict, patient_id: str) -> dict:
        base = super()._normalise_patient(raw, patient_id)
        # Cerner stores identifiers differently
        identifiers = raw.get("identifier", [])
        for ident in identifiers:
            system = ident.get("system","")
            if "codeSet/4" in system or "MR" in ident.get("type",{}).get("coding",[{}])[0].get("code",""):
                base["mrn"] = ident.get("value","")
                break
        base["cerner_tenant"] = self.TENANT_ID
        return base

    def get_setup_instructions(self) -> str:
        return (
            "Cerner Sandbox Setup (Fraser Health uses Cerner):\n"
            "1. Register at https://code.cerner.com\n"
            "2. Create new application\n"
            "3. Set environment variables:\n"
            f"   FHIR_BASE_URL={self.SANDBOX_URL}\n"
            "   FHIR_CLIENT_ID=your-cerner-client-id\n"
            "   EHR_SYSTEM=cerner\n"
            "Fraser Health note: This is the exact API Fraser Health exposes\n"
        )


# ═══════════════════════════════════════════════════════════════════════
# OSCAR ADAPTER — Canadian GP clinics (~30% market share)
# ═══════════════════════════════════════════════════════════════════════

class OSCARAdapter(BaseEHRAdapter):
    """
    OSCAR EMR adapter.
    Used by ~30% of Canadian GP clinics. Open source.
    Self-hosted — no vendor contract needed.
    
    OSCAR quirks:
    - Self-hosted — every installation is different
    - FHIR R4 added in recent versions
    - Legacy HL7 v2 still dominant for lab results
    - OAuth2 implementation varies by installation
    - PrescribeIT integration via Canada Health Infoway
    - Docker deployment: github.com/scoophealth/oscar-mcmaster

    OSCAR FHIR endpoint (self-hosted):
    - Default: http://localhost:8080/oscar/fhir
    - Requires OSCAR version 15.10+ for FHIR R4
    """

    SYSTEM_NAME    = "OSCAR EMR"
    SYSTEM_KEY     = "oscar"
    CANADIAN_ORG   = "Canadian GP Clinics (30% market)"
    LOCAL_URL      = "http://localhost:8080/oscar/fhir"

    def get_setup_instructions(self) -> str:
        return (
            "OSCAR EMR Docker Setup:\n"
            "1. Clone: git clone https://github.com/scoophealth/oscar-mcmaster\n"
            "2. Run: docker-compose up\n"
            "3. Access OSCAR at http://localhost:8080/oscar\n"
            "4. Configure OAuth2 in OSCAR admin\n"
            "5. Set environment variables:\n"
            f"   FHIR_BASE_URL={self.LOCAL_URL}\n"
            "   FHIR_CLIENT_ID=your-oscar-client-id\n"
            "   EHR_SYSTEM=oscar\n"
            "OSCAR is free and open source — no vendor agreement needed\n"
        )

    def get_hl7_message(self, patient_id: str, message_type: str = "ORM") -> str:
        """
        Generate a realistic HL7 v2 message for OSCAR testing.
        OSCAR uses HL7 v2 for lab results in many deployments.
        """
        patient = self.simulator.get_patient(patient_id)
        family = patient.get("name",[{}])[0].get("family","Smith") if patient.get("name") else "Smith"
        given  = " ".join(patient.get("name",[{}])[0].get("given",["John"])) if patient.get("name") else "John"
        dob    = patient.get("birthDate","19700101").replace("-","")
        now    = "20260320120000"

        if message_type == "ORU":  # Lab result
            return (
                f"MSH|^~\\&|LAB|VGH|OSCAR|CLINIC|{now}||ORU^R01|MSG{patient_id}001|P|2.4\r"
                f"PID|1||{patient_id}^^^MRN||{family}^{given}||{dob}|F\r"
                f"OBR|1||{patient_id}-CBC|58410-2^CBC^LN|||{now}\r"
                f"OBX|1|NM|718-7^Hemoglobin^LN||142|g/L|120-160||||F\r"
                f"OBX|2|NM|6690-2^WBC^LN||7.2|10*9/L|4.5-11.0||||F\r"
                f"OBX|3|NM|777-3^Platelets^LN||215|10*9/L|150-400||||F\r"
            )
        elif message_type == "ADT":  # Admission
            return (
                f"MSH|^~\\&|ADT|VGH|OSCAR|CLINIC|{now}||ADT^A01|MSG{patient_id}002|P|2.4\r"
                f"PID|1||{patient_id}^^^MRN||{family}^{given}||{dob}|F\r"
                f"PV1|1|I|3N^301^A^VGH|||||||Internal Medicine\r"
            )
        return f"MSH|^~\\&|OSCAR|CLINIC|RECV|FAC|{now}||{message_type}|MSG001|P|2.4\r"


# ═══════════════════════════════════════════════════════════════════════
# SIMULATOR ADAPTER — No network required
# ═══════════════════════════════════════════════════════════════════════

class SimulatorAdapter(BaseEHRAdapter):
    """
    Pure simulator mode — no EHR API needed.
    Used for Colab testing, CI/CD, and offline development.
    Returns realistic FHIR R4 structured data from EHRSimulator.
    """

    SYSTEM_NAME  = "EHR Simulator (No Network Required)"
    SYSTEM_KEY   = "simulator"
    CANADIAN_ORG = "Synthetic — for testing only"

    def __init__(self):
        self.client    = FHIRClient()  # Will auto-use simulator
        self.simulator = EHRSimulator()
        self.mode      = "simulator"


# ═══════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════

ADAPTER_MAP = {
    "epic":      EpicAdapter,
    "cerner":    CernerAdapter,
    "oscar":     OSCARAdapter,
    "simulator": SimulatorAdapter,
    "generic":   BaseEHRAdapter,
}

def get_adapter(system: str = None) -> BaseEHRAdapter:
    """
    Get the appropriate EHR adapter.
    
    Args:
        system: 'epic' | 'cerner' | 'oscar' | 'simulator' | 'generic'
                Defaults to EHR_SYSTEM env var or 'simulator'
    
    Returns:
        Configured EHR adapter — real or simulator mode
    
    Examples:
        adapter = get_adapter()           # auto-detect
        adapter = get_adapter("cerner")   # Fraser Health
        adapter = get_adapter("epic")     # PHC / VGH
        adapter = get_adapter("oscar")    # GP clinics
        adapter = get_adapter("simulator")# always simulator
    """
    system = system or os.getenv("EHR_SYSTEM", "simulator")
    cls = ADAPTER_MAP.get(system.lower(), SimulatorAdapter)

    if system == "simulator" or not os.getenv("FHIR_BASE_URL"):
        return SimulatorAdapter()

    fhir_client = FHIRClient(
        base_url=os.getenv("FHIR_BASE_URL",""),
        client_id=os.getenv("FHIR_CLIENT_ID",""),
        ehr_system=system,
    )
    return cls(fhir_client=fhir_client)


def list_adapters() -> list:
    """List all available adapters with their Canadian context."""
    return [
        {
            "key":          "simulator",
            "name":         SimulatorAdapter.SYSTEM_NAME,
            "canadian_org": SimulatorAdapter.CANADIAN_ORG,
            "requires":     "Nothing — always available",
        },
        {
            "key":          "epic",
            "name":         EpicAdapter.SYSTEM_NAME,
            "canadian_org": EpicAdapter.CANADIAN_ORG,
            "requires":     "Free sandbox at fhir.epic.com",
            "sandbox_url":  EpicAdapter.SANDBOX_URL,
        },
        {
            "key":          "cerner",
            "name":         CernerAdapter.SYSTEM_NAME,
            "canadian_org": CernerAdapter.CANADIAN_ORG,
            "requires":     "Free sandbox at code.cerner.com",
            "sandbox_url":  CernerAdapter.SANDBOX_URL,
        },
        {
            "key":          "oscar",
            "name":         OSCARAdapter.SYSTEM_NAME,
            "canadian_org": OSCARAdapter.CANADIAN_ORG,
            "requires":     "Self-hosted Docker (free, open source)",
            "local_url":    OSCARAdapter.LOCAL_URL,
        },
    ]
