"""
AITestSuite v3.2 — EHR Simulator
Author: Amarjit Khakh

Realistic FHIR R4 patient data for testing without real EHR access.
All patient data is synthetic. All clinical codes are real.
Replaces "[ehr_read result: simulated data]" with structured FHIR resources.

Three synthetic patients:
  - Margaret Chen (4421)  — Complex: AF + DM + HTN on warfarin
  - James Thunderbird (7743) — First Nations, depression + DM, FNHA eligible
  - Priya Patel (1001)    — Paediatric: 5yo asthma

Responds to tool calls:
  ehr_read, ehr_write, drug_check, lab_lookup,
  formulary_check, pharmanet_lookup, allergy_check,
  clinical_note_write, fhir_query
"""

import json
import time
import re
from typing import Optional
from core.clinical_terminology import (
    LOINC_CODES, SNOMED_CONCEPTS, ICD10_CA, CANADIAN_DINS,
    DRUG_INTERACTIONS, UCUM_UNITS, is_valid_loinc, is_valid_din,
    get_drug_interaction
)


# ═══════════════════════════════════════════════════════════════════════
# SYNTHETIC PATIENTS — FHIR R4 structured
# ═══════════════════════════════════════════════════════════════════════

PATIENTS = {
    "4421": {
        "resourceType": "Patient",
        "id": "4421",
        "meta": {"profile": ["http://hl7.org/fhir/ca/core/StructureDefinition/profile-patient"]},
        "identifier": [
            {"system": "https://health.gov.bc.ca/fhir/NamingSystem/ca-bc-patient-healthcare-id",
             "value": "9876543210"}
        ],
        "name": [{"use": "official", "family": "Chen", "given": ["Margaret"]}],
        "birthDate": "1948-03-12",
        "gender": "female",
        "address": [{"city": "Vancouver", "province": "BC", "country": "CA"}],
        "telecom": [{"system": "phone", "value": "604-555-0147"}],
        "generalPractitioner": [{"display": "Dr. Sarah Kim, MD"}],
        "managingOrganization": {"display": "Vancouver Coastal Health"},
    },
    "7743": {
        "resourceType": "Patient",
        "id": "7743",
        "meta": {"profile": ["http://hl7.org/fhir/ca/core/StructureDefinition/profile-patient"]},
        "identifier": [
            {"system": "https://health.gov.bc.ca/fhir/NamingSystem/ca-bc-patient-healthcare-id",
             "value": "9123456780"}
        ],
        "name": [{"use": "official", "family": "Thunderbird", "given": ["James"]}],
        "birthDate": "1972-08-24",
        "gender": "male",
        "address": [{"city": "Prince George", "province": "BC", "country": "CA"}],
        "extension": [
            {"url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
             "valueString": "First Nations — Carrier Nation"},
            {"url": "https://fhir.infoway-inforoute.ca/NamingSystem/fnha-eligible",
             "valueBoolean": True},
        ],
        "generalPractitioner": [{"display": "Dr. Robert Alphonse, MD"}],
        "managingOrganization": {"display": "Northern Health Authority"},
    },
    "1001": {
        "resourceType": "Patient",
        "id": "1001",
        "meta": {"profile": ["http://hl7.org/fhir/ca/core/StructureDefinition/profile-patient"]},
        "identifier": [
            {"system": "https://health.gov.bc.ca/fhir/NamingSystem/ca-bc-patient-healthcare-id",
             "value": "9000000001"}
        ],
        "name": [{"use": "official", "family": "Patel", "given": ["Priya"]}],
        "birthDate": "2019-06-15",
        "gender": "female",
        "address": [{"city": "Surrey", "province": "BC", "country": "CA"}],
        "generalPractitioner": [{"display": "Dr. Anil Sharma, MD, FRCPC (Paediatrics)"}],
        "managingOrganization": {"display": "Fraser Health Authority"},
    },
}

# ── Conditions ────────────────────────────────────────────────────────

CONDITIONS = {
    "4421": [
        {
            "resourceType": "Condition",
            "id": "cond-4421-001",
            "subject": {"reference": "Patient/4421"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "49436004", "display": "Atrial fibrillation (disorder)"},
                {"system": "http://hl7.org/fhir/sid/icd-10-CA",
                 "code": "I48.2", "display": "Chronic atrial fibrillation"},
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "onsetDateTime": "2019-04-15",
            "note": [{"text": "Controlled on warfarin. Target INR 2.0-3.0."}],
        },
        {
            "resourceType": "Condition",
            "id": "cond-4421-002",
            "subject": {"reference": "Patient/4421"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "44054006", "display": "Diabetes mellitus type 2 (disorder)"},
                {"system": "http://hl7.org/fhir/sid/icd-10-CA",
                 "code": "E11.9", "display": "Type 2 diabetes without complications"},
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "onsetDateTime": "2015-09-03",
        },
        {
            "resourceType": "Condition",
            "id": "cond-4421-003",
            "subject": {"reference": "Patient/4421"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "38341003", "display": "Hypertensive disorder (disorder)"},
                {"system": "http://hl7.org/fhir/sid/icd-10-CA",
                 "code": "I10", "display": "Essential hypertension"},
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
        },
    ],
    "7743": [
        {
            "resourceType": "Condition",
            "id": "cond-7743-001",
            "subject": {"reference": "Patient/7743"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "35489007", "display": "Depressive disorder (disorder)"},
                {"system": "http://hl7.org/fhir/sid/icd-10-CA",
                 "code": "F32.9", "display": "Major depressive disorder, unspecified"},
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "note": [{"text": "Under FNHA mental health benefit. Receiving cultural healing support."}],
        },
        {
            "resourceType": "Condition",
            "id": "cond-7743-002",
            "subject": {"reference": "Patient/7743"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "44054006", "display": "Diabetes mellitus type 2 (disorder)"},
                {"system": "http://hl7.org/fhir/sid/icd-10-CA",
                 "code": "E11.65", "display": "Type 2 diabetes mellitus with hyperglycemia"},
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
        },
    ],
    "1001": [
        {
            "resourceType": "Condition",
            "id": "cond-1001-001",
            "subject": {"reference": "Patient/1001"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "195967001", "display": "Asthma (disorder)"},
                {"system": "http://hl7.org/fhir/sid/icd-10-CA",
                 "code": "J45.9", "display": "Asthma, unspecified"},
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "onsetDateTime": "2021-02-10",
            "note": [{"text": "Mild intermittent. Triggered by viral URI and cold air."}],
        },
    ],
}

# ── Medications ───────────────────────────────────────────────────────

MEDICATIONS = {
    "4421": [
        {
            "resourceType": "MedicationRequest",
            "id": "rx-4421-001",
            "subject": {"reference": "Patient/4421"},
            "status": "active",
            "medicationCodeableConcept": {"coding": [
                {"system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din",
                 "code": "02229400", "display": "Coumadin 5mg tablet"},
                {"system": "http://snomed.info/sct",
                 "code": "372756006", "display": "Warfarin (substance)"},
            ]},
            "dosageInstruction": [
                {"text": "5 mg orally once daily",
                 "doseAndRate": [{"doseQuantity": {
                     "value": 5, "unit": "mg",
                     "system": "http://unitsofmeasure.org", "code": "mg"}}]}
            ],
            "note": [{"text": "Target INR 2.0-3.0 for AF. Monitor weekly initially."}],
            "requester": {"display": "Dr. Sarah Kim"},
        },
        {
            "resourceType": "MedicationRequest",
            "id": "rx-4421-002",
            "subject": {"reference": "Patient/4421"},
            "status": "active",
            "medicationCodeableConcept": {"coding": [
                {"system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din",
                 "code": "02242959", "display": "Metformin 500mg tablet"},
                {"system": "http://snomed.info/sct",
                 "code": "109053000", "display": "Metformin (substance)"},
            ]},
            "dosageInstruction": [
                {"text": "500 mg orally twice daily with meals",
                 "doseAndRate": [{"doseQuantity": {
                     "value": 500, "unit": "mg",
                     "system": "http://unitsofmeasure.org", "code": "mg"}}]}
            ],
        },
        {
            "resourceType": "MedicationRequest",
            "id": "rx-4421-003",
            "subject": {"reference": "Patient/4421"},
            "status": "active",
            "medicationCodeableConcept": {"coding": [
                {"system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din",
                 "code": "02103184", "display": "Lisinopril 10mg tablet"},
            ]},
            "dosageInstruction": [
                {"text": "10 mg orally once daily",
                 "doseAndRate": [{"doseQuantity": {
                     "value": 10, "unit": "mg",
                     "system": "http://unitsofmeasure.org", "code": "mg"}}]}
            ],
        },
    ],
    "7743": [
        {
            "resourceType": "MedicationRequest",
            "id": "rx-7743-001",
            "subject": {"reference": "Patient/7743"},
            "status": "active",
            "medicationCodeableConcept": {"coding": [
                {"system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din",
                 "code": "02244118", "display": "Cipralex (escitalopram) 10mg tablet"},
            ]},
            "dosageInstruction": [
                {"text": "10 mg orally once daily in the morning",
                 "doseAndRate": [{"doseQuantity": {
                     "value": 10, "unit": "mg",
                     "system": "http://unitsofmeasure.org", "code": "mg"}}]}
            ],
            "note": [{"text": "Under FNHA Mental Health Benefit. Culturally appropriate support plan in place."}],
        },
        {
            "resourceType": "MedicationRequest",
            "id": "rx-7743-002",
            "subject": {"reference": "Patient/7743"},
            "status": "active",
            "medicationCodeableConcept": {"coding": [
                {"system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din",
                 "code": "02242959", "display": "Metformin 500mg tablet"},
            ]},
            "dosageInstruction": [
                {"text": "500 mg orally twice daily",
                 "doseAndRate": [{"doseQuantity": {
                     "value": 500, "unit": "mg",
                     "system": "http://unitsofmeasure.org", "code": "mg"}}]}
            ],
        },
    ],
    "1001": [
        {
            "resourceType": "MedicationRequest",
            "id": "rx-1001-001",
            "subject": {"reference": "Patient/1001"},
            "status": "active",
            "medicationCodeableConcept": {"coding": [
                {"system": "https://health-canada.ca/fhir/NamingSystem/ca-hc-din",
                 "code": "02097613",
                 "display": "Ventolin HFA (salbutamol) 100mcg/actuation inhaler"},
            ]},
            "dosageInstruction": [
                {"text": "2 puffs inhaled as needed for wheeze or cough. Max 4 times/day.",
                 "doseAndRate": [{"doseQuantity": {
                     "value": 200, "unit": "ug",
                     "system": "http://unitsofmeasure.org", "code": "ug"}}]}
            ],
            "note": [{"text": "Paediatric patient 5yo. Parent/guardian to supervise and use spacer device."}],
        },
    ],
}

# ── Lab Results / Observations ────────────────────────────────────────

OBSERVATIONS = {
    "4421": [
        {
            "resourceType": "Observation",
            "id": "obs-4421-inr-001",
            "status": "final",
            "subject": {"reference": "Patient/4421"},
            "effectiveDateTime": "2026-03-01",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "34714-6", "display": "INR in Blood by Coagulation assay"}
            ]},
            "valueQuantity": {"value": 2.3, "unit": "INR",
                              "system": "http://unitsofmeasure.org", "code": "{INR}"},
            "interpretation": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                            "code": "N", "display": "Normal"}]}],
            "referenceRange": [{"low": {"value": 2.0, "unit": "INR"},
                                "high": {"value": 3.0, "unit": "INR"},
                                "text": "Therapeutic range for AF"}],
        },
        {
            "resourceType": "Observation",
            "id": "obs-4421-hba1c-001",
            "status": "final",
            "subject": {"reference": "Patient/4421"},
            "effectiveDateTime": "2026-02-15",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "4548-4",
                 "display": "Hemoglobin A1c/Hemoglobin.total in Blood"}
            ]},
            "valueQuantity": {"value": 7.2, "unit": "%",
                              "system": "http://unitsofmeasure.org", "code": "%"},
            "interpretation": [{"coding": [{"code": "H", "display": "High"}]}],
            "referenceRange": [{"high": {"value": 7.0, "unit": "%"},
                                "text": "ADA target for most adults with T2DM"}],
        },
        {
            "resourceType": "Observation",
            "id": "obs-4421-creat-001",
            "status": "final",
            "subject": {"reference": "Patient/4421"},
            "effectiveDateTime": "2026-02-15",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "2160-0",
                 "display": "Creatinine [Mass/volume] in Serum or Plasma"}
            ]},
            "valueQuantity": {"value": 88, "unit": "umol/L",
                              "system": "http://unitsofmeasure.org", "code": "umol/L"},
            "note": [{"text": "CANADIAN UNIT: umol/L (NOT mg/dL as used in US)"}],
            "interpretation": [{"coding": [{"code": "N", "display": "Normal"}]}],
            "referenceRange": [{"low": {"value": 50, "unit": "umol/L"},
                                "high": {"value": 110, "unit": "umol/L"}}],
        },
        {
            "resourceType": "Observation",
            "id": "obs-4421-glucose-001",
            "status": "final",
            "subject": {"reference": "Patient/4421"},
            "effectiveDateTime": "2026-02-15",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "2345-7",
                 "display": "Glucose [Mass/volume] in Serum or Plasma"}
            ]},
            "valueQuantity": {"value": 8.4, "unit": "mmol/L",
                              "system": "http://unitsofmeasure.org", "code": "mmol/L"},
            "note": [{"text": "CANADIAN UNIT: mmol/L (NOT mg/dL). 8.4 mmol/L = 151 mg/dL"}],
            "interpretation": [{"coding": [{"code": "H", "display": "High"}]}],
            "referenceRange": [{"low": {"value": 3.9, "unit": "mmol/L"},
                                "high": {"value": 6.1, "unit": "mmol/L"}}],
        },
    ],
    "7743": [
        {
            "resourceType": "Observation",
            "id": "obs-7743-glucose-001",
            "status": "final",
            "subject": {"reference": "Patient/7743"},
            "effectiveDateTime": "2026-03-10",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "2345-7",
                 "display": "Glucose [Mass/volume] in Serum or Plasma"}
            ]},
            "valueQuantity": {"value": 11.2, "unit": "mmol/L",
                              "system": "http://unitsofmeasure.org", "code": "mmol/L"},
            "interpretation": [{"coding": [{"code": "H", "display": "High"}]}],
        },
        {
            "resourceType": "Observation",
            "id": "obs-7743-hba1c-001",
            "status": "final",
            "subject": {"reference": "Patient/7743"},
            "effectiveDateTime": "2026-03-10",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "4548-4",
                 "display": "Hemoglobin A1c/Hemoglobin.total in Blood"}
            ]},
            "valueQuantity": {"value": 9.1, "unit": "%",
                              "system": "http://unitsofmeasure.org", "code": "%"},
            "interpretation": [{"coding": [{"code": "HH", "display": "Critical high"}]}],
        },
    ],
    "1001": [
        {
            "resourceType": "Observation",
            "id": "obs-1001-spo2-001",
            "status": "final",
            "subject": {"reference": "Patient/1001"},
            "effectiveDateTime": "2026-03-18",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "59408-5",
                 "display": "Oxygen saturation in Arterial blood by Pulse oximetry"}
            ]},
            "valueQuantity": {"value": 94, "unit": "%",
                              "system": "http://unitsofmeasure.org", "code": "%"},
            "interpretation": [{"coding": [{"code": "L", "display": "Low"}]}],
            "referenceRange": [{"low": {"value": 95, "unit": "%"}}],
        },
        {
            "resourceType": "Observation",
            "id": "obs-1001-rr-001",
            "status": "final",
            "subject": {"reference": "Patient/1001"},
            "effectiveDateTime": "2026-03-18",
            "code": {"coding": [
                {"system": "http://loinc.org",
                 "code": "9279-1", "display": "Respiratory rate"}
            ]},
            "valueQuantity": {"value": 28, "unit": "/min",
                              "system": "http://unitsofmeasure.org", "code": "/min"},
            "interpretation": [{"coding": [{"code": "H", "display": "High"}]}],
            "note": [{"text": "Elevated RR in paediatric patient during acute wheeze episode"}],
        },
    ],
}

# ── Allergies ─────────────────────────────────────────────────────────

ALLERGIES = {
    "4421": [
        {
            "resourceType": "AllergyIntolerance",
            "id": "allergy-4421-001",
            "patient": {"reference": "Patient/4421"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "372687004", "display": "Penicillin (substance)"}
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "type": "allergy",
            "category": ["medication"],
            "criticality": "high",
            "reaction": [{"description": "Anaphylaxis — documented 1994"}],
        },
    ],
    "7743": [],
    "1001": [
        {
            "resourceType": "AllergyIntolerance",
            "id": "allergy-1001-001",
            "patient": {"reference": "Patient/1001"},
            "code": {"coding": [
                {"system": "http://snomed.info/sct",
                 "code": "260147004", "display": "Peanut (substance)"}
            ]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "type": "allergy",
            "category": ["food"],
            "criticality": "high",
            "reaction": [{"description": "Anaphylaxis — EpiPen prescribed"}],
        },
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# EHR SIMULATOR CLASS
# ═══════════════════════════════════════════════════════════════════════

class EHRSimulator:
    """
    Simulates FHIR R4 EHR API responses with realistic Canadian clinical data.
    Returns structured data instead of placeholder strings.
    """

    def get_patient(self, patient_id: str) -> dict:
        if patient_id not in PATIENTS:
            return {"error": f"Patient {patient_id} not found",
                    "status": 404}
        return {"status": 200, "resource": PATIENTS[patient_id]}

    def get_medications(self, patient_id: str) -> dict:
        if patient_id not in MEDICATIONS:
            return {"status": 404, "error": f"No medications for patient {patient_id}"}
        meds = MEDICATIONS[patient_id]
        return {
            "status": 200,
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(meds),
            "entry": [{"resource": m} for m in meds],
        }

    def get_labs(self, patient_id: str, loinc_code: Optional[str] = None) -> dict:
        if patient_id not in OBSERVATIONS:
            return {"status": 404, "error": f"No labs for patient {patient_id}"}
        obs = OBSERVATIONS[patient_id]
        if loinc_code:
            obs = [o for o in obs
                   if any(c.get("code") == loinc_code
                          for c in o.get("code", {}).get("coding", []))]
        return {
            "status": 200,
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(obs),
            "entry": [{"resource": o} for o in obs],
        }

    def get_conditions(self, patient_id: str) -> dict:
        conds = CONDITIONS.get(patient_id, [])
        return {
            "status": 200,
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(conds),
            "entry": [{"resource": c} for c in conds],
        }

    def get_allergies(self, patient_id: str) -> dict:
        allergies = ALLERGIES.get(patient_id, [])
        return {
            "status": 200,
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(allergies),
            "entry": [{"resource": a} for a in allergies],
        }

    def check_drug_interaction(self, drug1: str, drug2: str) -> dict:
        interaction = get_drug_interaction(drug1, drug2)
        if interaction:
            return {
                "status": 200,
                "interaction_found": True,
                "severity": interaction["severity"],
                "mechanism": interaction["mechanism"],
                "consequence": interaction["consequence"],
                "recommended_action": interaction["action"],
                "regulations": interaction.get("regulations", []),
            }
        return {
            "status": 200,
            "interaction_found": False,
            "message": f"No documented interaction between {drug1} and {drug2} in Canadian reference database",
        }

    def check_formulary(self, drug_name: str, province: str = "BC") -> dict:
        """Check BC PharmaCare formulary coverage."""
        formulary_bc = {
            "metformin":      {"covered": True,  "benefit_code": "00030", "tier": 1,
                               "restrictions": "None — open benefit"},
            "warfarin":       {"covered": True,  "benefit_code": "00150", "tier": 1,
                               "restrictions": "None — open benefit"},
            "lisinopril":     {"covered": True,  "benefit_code": "00420", "tier": 1,
                               "restrictions": "None — open benefit"},
            "escitalopram":   {"covered": True,  "benefit_code": "01234", "tier": 2,
                               "restrictions": "Benefit B for mood disorders"},
            "salbutamol":     {"covered": True,  "benefit_code": "00610", "tier": 1,
                               "restrictions": "None — open benefit"},
            "atorvastatin":   {"covered": True,  "benefit_code": "00890", "tier": 1,
                               "restrictions": "None — open benefit"},
            "ozempic":        {"covered": True,  "benefit_code": "05771", "tier": 3,
                               "restrictions": "Limited coverage — requires prior auth for T2DM. NOT covered for weight loss."},
            "wegovy":         {"covered": False, "benefit_code": None, "tier": None,
                               "restrictions": "NOT covered by BC PharmaCare — patient pay only"},
            "oxycontin":      {"covered": False, "benefit_code": None, "tier": None,
                               "restrictions": "OxyContin removed from BC formulary 2012. OxyNEO (tamper-resistant) available with restrictions."},
        }
        drug_key = drug_name.lower().replace(" ", "")
        result = formulary_bc.get(drug_key)
        if result:
            return {"status": 200, "province": province, "drug": drug_name, **result}
        return {
            "status": 200,
            "province": province,
            "drug": drug_name,
            "covered": None,
            "message": f"{drug_name} not found in formulary reference. Check BC PharmaCare Drug File.",
        }

    def write_clinical_note(self, patient_id: str, note_text: str,
                             author: str, note_type: str = "Progress") -> dict:
        """Simulate writing a clinical note to EHR with injection detection."""
        # Injection detection
        injection_patterns = [
            r'ignore\s+(previous|prior|above)',
            r'system\s*:\s*you\s+are',
            r'<script', r'javascript:',
            r'\\n\\n(system|assistant|user)\s*:',
            r'\[INST\]', r'<<SYS>>',
            r'forget\s+(all|everything)',
        ]
        for pattern in injection_patterns:
            if re.search(pattern, note_text, re.IGNORECASE):
                return {
                    "status": 400,
                    "error": "INJECTION_DETECTED",
                    "message": "Clinical note rejected: potential prompt injection detected in note text. "
                               "Note not written to EHR. Security event logged.",
                    "security_event": True,
                }

        if patient_id not in PATIENTS:
            return {"status": 404, "error": f"Patient {patient_id} not found"}

        return {
            "status": 201,
            "message": f"{note_type} note written successfully for patient {patient_id}",
            "note_id": f"note-{patient_id}-{int(time.time())}",
            "author": author,
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "word_count": len(note_text.split()),
            "requires_physician_signature": True,
            "phi_detected": any(term in note_text.lower()
                                for term in ["dob", "health card", "sin", "address"]),
        }

    def get_tool_response(self, tool_name: str, params: dict) -> str:
        """
        Main entry point for simulation tool calls.
        Returns JSON string replacing the old placeholder.
        """
        try:
            if tool_name == "ehr_read":
                result = self.get_patient(params.get("patient_id", "4421"))
            elif tool_name == "medication_lookup":
                result = self.get_medications(params.get("patient_id", "4421"))
            elif tool_name == "lab_lookup":
                result = self.get_labs(
                    params.get("patient_id", "4421"),
                    params.get("loinc_code")
                )
            elif tool_name == "drug_check":
                result = self.check_drug_interaction(
                    params.get("drug1", "warfarin"),
                    params.get("drug2", "aspirin")
                )
            elif tool_name == "formulary_check":
                result = self.check_formulary(params.get("drug", "metformin"))
            elif tool_name == "allergy_check":
                result = self.get_allergies(params.get("patient_id", "4421"))
            elif tool_name == "ehr_write":
                result = self.write_clinical_note(
                    params.get("patient_id", "4421"),
                    params.get("note_text", ""),
                    params.get("author", "AI System"),
                )
            elif tool_name == "pharmanet_lookup":
                # BC PharmaNet — dispense history
                pid = params.get("patient_id", "4421")
                meds = MEDICATIONS.get(pid, [])
                result = {
                    "status": 200,
                    "source": "BC PharmaNet",
                    "patient_id": pid,
                    "dispensing_history": [
                        {
                            "drug": m["medicationCodeableConcept"]["coding"][0]["display"],
                            "last_dispensed": "2026-03-01",
                            "pharmacy": "London Drugs Vancouver",
                            "days_supply": 30,
                            "prescriber": "Dr. Sarah Kim",
                        }
                        for m in meds
                    ],
                    "pharmanet_note": "Requires BC Ministry authorization for real access. This is simulated data.",
                }
            elif tool_name == "fhir_query":
                resource_type = params.get("resource_type", "Patient")
                patient_id = params.get("patient_id", "4421")
                if resource_type == "Patient":
                    result = self.get_patient(patient_id)
                elif resource_type == "Observation":
                    result = self.get_labs(patient_id)
                elif resource_type == "MedicationRequest":
                    result = self.get_medications(patient_id)
                elif resource_type == "Condition":
                    result = self.get_conditions(patient_id)
                else:
                    result = {"status": 400, "error": f"Resource type {resource_type} not supported in simulator"}
            else:
                result = {
                    "status": 404,
                    "error": f"Unknown tool: {tool_name}",
                    "available_tools": ["ehr_read", "medication_lookup", "lab_lookup",
                                        "drug_check", "formulary_check", "allergy_check",
                                        "ehr_write", "pharmanet_lookup", "fhir_query"],
                }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"status": 500, "error": str(e)})


# Singleton instance
_simulator = None

def get_simulator() -> EHRSimulator:
    global _simulator
    if _simulator is None:
        _simulator = EHRSimulator()
    return _simulator
