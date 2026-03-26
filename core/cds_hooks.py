"""
AITestSuite v3.2 — CDS Hooks Service
Author: Amarjit Khakh

CDS Hooks is how clinical AI actually gets triggered in Epic and Cerner.
When a physician opens a medication order → CDS Hook fires → AI responds.
This is not chat. This is structured clinical decision support.

Implements:
  - /cds-services (discovery)
  - /cds-services/{id} (hook handler)
  - Simulation for testing without real EHR

Hooks implemented:
  1. order-select: drug interaction check
  2. patient-view: lab alert
  3. order-sign: MAID safeguard
  4. order-sign: paediatric safety
  5. patient-view: Indigenous cultural safety
"""

import json
import logging
from typing import Optional
from core.clinical_terminology import DRUG_INTERACTIONS, LOINC_CODES, get_drug_interaction
from core.ehr_simulator import get_simulator

logger = logging.getLogger("AITestSuite.CDSHooks")

# ═══════════════════════════════════════════════════════════════════════
# CDS SERVICES CATALOG
# ═══════════════════════════════════════════════════════════════════════

CDS_SERVICES = [
    {
        "id":          "ait-drug-interaction-check",
        "hook":        "order-select",
        "title":       "AITestSuite Drug Interaction Checker",
        "description": "Checks proposed medication orders against current medications for interactions using Canadian drug interaction database.",
        "prefetch": {
            "patient":            "Patient/{{context.patientId}}",
            "medications":        "MedicationRequest?patient={{context.patientId}}&status=active",
        },
    },
    {
        "id":          "ait-lab-alert",
        "hook":        "patient-view",
        "title":       "AITestSuite Critical Lab Alert",
        "description": "Reviews recent lab results and alerts clinician to critical values using LOINC-coded observations.",
        "prefetch": {
            "patient":      "Patient/{{context.patientId}}",
            "observations": "Observation?patient={{context.patientId}}&_sort=-date&_count=20",
        },
    },
    {
        "id":          "ait-maid-safeguard",
        "hook":        "order-sign",
        "title":       "AITestSuite MAID Safeguard — Bill C-7",
        "description": "Detects medication orders associated with MAID (Medical Assistance in Dying) and triggers mandatory safeguard checklist per Bill C-7.",
        "prefetch": {
            "patient":    "Patient/{{context.patientId}}",
            "conditions": "Condition?patient={{context.patientId}}&clinical-status=active",
        },
    },
    {
        "id":          "ait-paediatric-safety",
        "hook":        "order-sign",
        "title":       "AITestSuite Paediatric Safety Check",
        "description": "Identifies medication orders contraindicated in children including codeine (Health Canada 2013), weight-based dosing verification.",
        "prefetch": {
            "patient":     "Patient/{{context.patientId}}",
            "medications": "MedicationRequest?patient={{context.patientId}}&status=active",
        },
    },
    {
        "id":          "ait-indigenous-cultural-safety",
        "hook":        "patient-view",
        "title":       "AITestSuite Indigenous Cultural Safety",
        "description": "Identifies First Nations, Metis, and Inuit patients and presents culturally safe care reminders including FNHA eligibility, OCAP principles, and trauma-informed care flags.",
        "prefetch": {
            "patient": "Patient/{{context.patientId}}",
        },
    },
]

# ═══════════════════════════════════════════════════════════════════════
# HOOK HANDLERS
# ═══════════════════════════════════════════════════════════════════════

class CDSHooksService:
    """CDS Hooks service implementation."""

    def __init__(self):
        self.simulator = get_simulator()

    def discovery(self) -> dict:
        """GET /cds-services — return service catalog."""
        return {"services": CDS_SERVICES}

    def handle_hook(self, service_id: str, request: dict) -> dict:
        """POST /cds-services/{id} — handle a hook call."""
        handlers = {
            "ait-drug-interaction-check":    self._drug_interaction_hook,
            "ait-lab-alert":                 self._lab_alert_hook,
            "ait-maid-safeguard":            self._maid_safeguard_hook,
            "ait-paediatric-safety":         self._paediatric_safety_hook,
            "ait-indigenous-cultural-safety": self._indigenous_safety_hook,
        }
        handler = handlers.get(service_id)
        if not handler:
            return {"cards": [], "error": f"Unknown service: {service_id}"}
        try:
            return handler(request)
        except Exception as e:
            logger.error(f"Hook error {service_id}: {e}")
            return {"cards": []}

    def _drug_interaction_hook(self, request: dict) -> dict:
        """order-select: check proposed drug against current medications."""
        cards = []
        context = request.get("context", {})
        prefetch = request.get("prefetch", {})
        patient_id = context.get("patientId", "4421")

        # Get proposed medication from context
        proposed_meds = context.get("medications", {}).get("entry", [])
        if not proposed_meds:
            return {"cards": []}

        # Get current medications from prefetch or simulator
        current_bundle = prefetch.get("medications") or \
                         self.simulator.get_medications(patient_id)
        current_meds = [e["resource"]["medicationCodeableConcept"]["coding"][0]["display"].lower()
                        for e in current_bundle.get("entry", [])]

        # Check each proposed drug against current medications
        for entry in proposed_meds:
            proposed_drug = entry.get("resource", {}).get(
                "medicationCodeableConcept", {}).get("coding", [{}])[0].get(
                "display", "").lower()
            if not proposed_drug:
                continue

            for current_drug in current_meds:
                interaction = get_drug_interaction(proposed_drug, current_drug)
                if interaction:
                    severity = interaction["severity"]
                    indicator = "critical" if severity == "CRITICAL" else \
                                "warning" if severity == "HIGH" else "info"
                    cards.append({
                        "summary": f"{severity}: {proposed_drug.title()} + {current_drug.title()}",
                        "detail": f"{interaction['mechanism']}\n\n"
                                  f"Consequence: {interaction['consequence']}\n\n"
                                  f"Action: {interaction['action']}",
                        "indicator": indicator,
                        "source": {"label": "AITestSuite Drug Interaction DB (Canadian)",
                                   "url": "https://health.canada.ca"},
                        "suggestions": [
                            {"label": "Flag for pharmacist review",
                             "actions": [{"type": "update", "description": "Add pharmacist review flag"}]},
                        ],
                    })
        return {"cards": cards}

    def _lab_alert_hook(self, request: dict) -> dict:
        """patient-view: alert on critical lab values."""
        cards = []
        patient_id = request.get("context", {}).get("patientId", "4421")
        prefetch = request.get("prefetch", {})

        obs_bundle = prefetch.get("observations") or self.simulator.get_labs(patient_id)
        observations = [e["resource"] for e in obs_bundle.get("entry", [])]

        for obs in observations:
            interp = obs.get("interpretation", [{}])[0].get("coding", [{}])[0].get("code", "")
            if interp in ("HH", "LL", "AA"):  # Critical values
                loinc_code = obs.get("code", {}).get("coding", [{}])[0].get("code", "")
                loinc_display = obs.get("code", {}).get("coding", [{}])[0].get("display", "")
                value = obs.get("valueQuantity", {})
                cards.append({
                    "summary": f"Critical lab value: {loinc_display}",
                    "detail": f"LOINC: {loinc_code}\n"
                              f"Value: {value.get('value')} {value.get('unit')}\n"
                              f"Status: {'Critical High' if interp == 'HH' else 'Critical Low'}\n"
                              f"Immediate physician review required.",
                    "indicator": "critical",
                    "source": {"label": f"Lab result — {obs.get('effectiveDateTime', '')[:10]}"},
                })
            elif interp in ("H", "L"):  # Abnormal
                loinc_display = obs.get("code", {}).get("coding", [{}])[0].get("display", "")
                value = obs.get("valueQuantity", {})
                cards.append({
                    "summary": f"Abnormal lab value: {loinc_display}",
                    "detail": f"Value: {value.get('value')} {value.get('unit')} "
                              f"({'Above' if interp == 'H' else 'Below'} reference range)",
                    "indicator": "warning",
                    "source": {"label": "Lab result"},
                })
        return {"cards": cards}

    def _maid_safeguard_hook(self, request: dict) -> dict:
        """order-sign: MAID safeguard — Bill C-7 compliance."""
        # MAID-associated medications that trigger the check
        maid_indicators = [
            "midazolam", "propofol", "rocuronium", "potassium chloride",
            "lidocaine", "phenobarbital", "ketamine",
        ]
        context = request.get("context", {})
        medications_context = context.get("medications", {}).get("entry", [])

        triggered = []
        for entry in medications_context:
            drug = entry.get("resource", {}).get(
                "medicationCodeableConcept", {}).get("coding", [{}])[0].get(
                "display", "").lower()
            if any(m in drug for m in maid_indicators):
                triggered.append(drug)

        if not triggered:
            return {"cards": []}

        return {"cards": [{
            "summary": "MAID Safeguard — Bill C-7 Compliance Check Required",
            "detail": (
                f"Medication(s) associated with MAID detected: {', '.join(triggered)}\n\n"
                "Bill C-7 (2021) requires ALL of the following before proceeding:\n"
                "1. Written request signed by patient with capacity\n"
                "2. Two independent assessors (physician + NP or physician + physician)\n"
                "3. 10-day reflection period (waivable only if death imminent)\n"
                "4. Final consent immediately before procedure\n"
                "5. Documentation in medical record\n\n"
                "If this is NOT a MAID order, dismiss this card and document reason."
            ),
            "indicator": "critical",
            "source": {"label": "Bill C-7 MAID Safeguards — Criminal Code s.241.2",
                       "url": "https://laws-lois.justice.gc.ca/eng/acts/C-46/section-241.2.html"},
            "suggestions": [
                {"label": "Open MAID documentation checklist",
                 "actions": [{"type": "create", "description": "Open MAID checklist form"}]},
                {"label": "This is NOT a MAID order — dismiss",
                 "actions": [{"type": "delete", "description": "Dismiss MAID alert"}]},
            ],
        }]}

    def _paediatric_safety_hook(self, request: dict) -> dict:
        """order-sign: paediatric medication safety."""
        cards = []
        patient_id = request.get("context", {}).get("patientId", "1001")
        prefetch = request.get("prefetch", {})

        # Get patient DOB
        patient_resource = prefetch.get("patient")
        if not patient_resource:
            patient_data = self.simulator.get_patient(patient_id)
            patient_resource = patient_data.get("resource", {})

        import time
        from datetime import date

        dob_str = patient_resource.get("birthDate", "")
        age_years = None
        if dob_str:
            try:
                dob = date.fromisoformat(dob_str)
                today = date.today()
                age_years = (today - dob).days / 365.25
            except Exception:
                pass

        if age_years is None or age_years >= 18:
            return {"cards": []}

        # Check for contraindicated medications in children
        context = request.get("context", {})
        medications_context = context.get("medications", {}).get("entry", [])

        contraindicated = {
            "codeine": "CONTRAINDICATED under 12 — Health Canada Advisory 2013-12. Fatal respiratory depression.",
            "tramadol": "AVOID under 12 — similar ultra-rapid metabolism risk as codeine.",
            "aspirin": "AVOID under 16 — Reye syndrome risk. Use acetaminophen.",
            "metoclopramide": "AVOID under 1 year — risk of extrapyramidal effects.",
        }

        for entry in medications_context:
            drug = entry.get("resource", {}).get(
                "medicationCodeableConcept", {}).get("coding", [{}])[0].get(
                "display", "").lower()
            for contraindic_drug, reason in contraindicated.items():
                if contraindic_drug in drug:
                    is_critical = age_years < 12 and contraindic_drug in ("codeine", "tramadol")
                    cards.append({
                        "summary": f"{'CONTRAINDICATED' if is_critical else 'AVOID'}: {contraindic_drug.title()} in patient aged {age_years:.1f} years",
                        "detail": reason,
                        "indicator": "critical" if is_critical else "warning",
                        "source": {"label": "Health Canada Paediatric Safety Advisory",
                                   "url": "https://health-products.canada.ca/medeffect-canada/"},
                    })
        return {"cards": cards}

    def _indigenous_safety_hook(self, request: dict) -> dict:
        """patient-view: Indigenous cultural safety reminders."""
        patient_id = request.get("context", {}).get("patientId", "7743")
        prefetch = request.get("prefetch", {})

        patient_resource = prefetch.get("patient")
        if not patient_resource:
            data = self.simulator.get_patient(patient_id)
            patient_resource = data.get("resource", {})

        # Check for First Nations identifier
        extensions = patient_resource.get("extension", [])
        is_indigenous = any(
            "fnha" in ext.get("url", "").lower() or
            "first nations" in str(ext.get("valueString", "")).lower() or
            "metis" in str(ext.get("valueString", "")).lower() or
            "inuit" in str(ext.get("valueString", "")).lower()
            for ext in extensions
        )

        fnha_eligible = any(
            ext.get("valueBoolean") is True and "fnha" in ext.get("url","").lower()
            for ext in extensions
        )

        if not is_indigenous:
            return {"cards": []}

        cards = [{
            "summary": "Indigenous Cultural Safety — Care Reminders",
            "detail": (
                "This patient has been identified as First Nations, Métis, or Inuit.\n\n"
                "Cultural Safety Reminders:\n"
                "• Ask patient's preferred language and cultural practices\n"
                "• Trauma-informed care — high rates of intergenerational trauma\n"
                "• OCAP principles apply to all health data collection (Ownership, Control, Access, Possession)\n"
                "• Include family and community as patient directs\n"
                "• Document any barriers to care access\n\n"
                "Indigenous-specific health considerations:\n"
                "• Higher rates: T2DM, TB, mental health, substance use\n"
                "• Jordan's Principle: disputes between governments must not delay care\n"
                "• TRC Calls to Action 18-24 on health"
            ),
            "indicator": "info",
            "source": {"label": "First Nations Health Authority Cultural Safety Standards",
                       "url": "https://www.fnha.ca/wellness/cultural-safety-and-humility"},
        }]

        if fnha_eligible:
            cards.append({
                "summary": "FNHA Benefit Eligibility — Check Coverage",
                "detail": (
                    "This patient may be eligible for FNHA Health Benefits:\n"
                    "• Dental, vision, mental health, medical transportation\n"
                    "• Non-Insured Health Benefits (NIHB) via Indigenous Services Canada\n"
                    "• Verify: https://www.fnha.ca/health-benefits\n\n"
                    "For mental health referrals: FNHA Trauma-Informed Cultural Supports program"
                ),
                "indicator": "info",
                "source": {"label": "FNHA Health Benefits",
                           "url": "https://www.fnha.ca/health-benefits"},
                "suggestions": [
                    {"label": "Check FNHA eligibility",
                     "actions": [{"type": "create", "description": "Open FNHA eligibility check"}]},
                ],
            })

        return {"cards": cards}

    def simulate_hook(self, service_id: str, patient_id: str,
                      proposed_medications: list = None) -> dict:
        """Simulate a CDS Hooks call for testing without a real EHR."""
        context = {
            "hook":     next((s["hook"] for s in CDS_SERVICES if s["id"] == service_id), "patient-view"),
            "hookInstance": f"test-{service_id}-{patient_id}",
            "patientId": patient_id,
        }
        if proposed_medications:
            context["medications"] = {
                "entry": [{"resource": {
                    "resourceType": "MedicationRequest",
                    "medicationCodeableConcept": {"coding": [
                        {"display": med, "code": "unknown",
                         "system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din"}
                    ]},
                }} for med in proposed_medications]
            }
        request = {"context": context, "prefetch": {}}
        return self.handle_hook(service_id, request)
