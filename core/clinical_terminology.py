"""
AITestSuite v3.2 — Canadian Clinical Terminology Reference
Author: Amarjit Khakh

Real clinical codes used in Canadian healthcare.
No placeholders. All codes are real.

Sources:
  LOINC: loinc.org (free public standard)
  SNOMED CT: maintained by SNOMED International, licensed via NLM
  ICD-10-CA: Canadian Institute for Health Information (CIHI)
  DIN: Health Canada Drug Product Database
  UCUM: Unified Code for Units of Measure
  Canada Health Infoway: CA Core+ FHIR profiles
"""

# ═══════════════════════════════════════════════════════════════════════
# LOINC CODES — Real codes for common Canadian lab tests
# Format: code -> {name, unit, reference_range, panel}
# ═══════════════════════════════════════════════════════════════════════
LOINC_CODES = {
    # ── Renal function ─────────────────────────────────────────────
    "2160-0":  {"name": "Creatinine [Mass/volume] in Serum or Plasma",
                "unit": "umol/L", "low": 50, "high": 110,
                "panel": "BMP", "category": "Renal"},
    "3094-0":  {"name": "Urea nitrogen [Mass/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": 2.1, "high": 8.0,
                "panel": "BMP", "category": "Renal"},
    "33914-3": {"name": "Glomerular filtration rate/1.73 sq M.predicted [Volume Rate/Area] in Serum, Plasma or Blood by Creatinine-based formula (MDRD)",
                "unit": "mL/min/1.73m2", "low": 60, "high": None,
                "panel": "Renal", "category": "Renal"},
    # ── Diabetes / glucose ─────────────────────────────────────────
    "4548-4":  {"name": "Hemoglobin A1c/Hemoglobin.total in Blood",
                "unit": "%", "low": None, "high": 5.7,
                "panel": "Diabetes", "category": "Endocrine"},
    "2345-7":  {"name": "Glucose [Mass/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": 3.9, "high": 6.1,
                "panel": "BMP", "category": "Endocrine"},
    "14771-0": {"name": "Fructosamine [Moles/volume] in Serum or Plasma",
                "unit": "umol/L", "low": 200, "high": 285,
                "panel": "Diabetes", "category": "Endocrine"},
    # ── Coagulation ────────────────────────────────────────────────
    "34714-6": {"name": "INR in Blood by Coagulation assay",
                "unit": "INR", "low": 0.9, "high": 1.1,
                "panel": "Coag", "category": "Coagulation"},
    "5902-2":  {"name": "Prothrombin time (PT)",
                "unit": "s", "low": 11.0, "high": 13.5,
                "panel": "Coag", "category": "Coagulation"},
    "3173-2":  {"name": "aPTT in Blood by Coagulation assay",
                "unit": "s", "low": 25.0, "high": 35.0,
                "panel": "Coag", "category": "Coagulation"},
    # ── Complete blood count ───────────────────────────────────────
    "718-7":   {"name": "Hemoglobin [Mass/volume] in Blood",
                "unit": "g/L", "low": 120, "high": 160,
                "panel": "CBC", "category": "Hematology"},
    "787-2":   {"name": "MCV [Entitic volume] by Automated count",
                "unit": "fL", "low": 80, "high": 100,
                "panel": "CBC", "category": "Hematology"},
    "6690-2":  {"name": "Leukocytes [#/volume] in Blood by Automated count",
                "unit": "10*9/L", "low": 4.0, "high": 11.0,
                "panel": "CBC", "category": "Hematology"},
    "777-3":   {"name": "Platelets [#/volume] in Blood by Automated count",
                "unit": "10*9/L", "low": 150, "high": 400,
                "panel": "CBC", "category": "Hematology"},
    # ── Liver function ─────────────────────────────────────────────
    "1742-6":  {"name": "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma",
                "unit": "U/L", "low": 0, "high": 40,
                "panel": "LFT", "category": "Hepatic"},
    "1920-8":  {"name": "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma",
                "unit": "U/L", "low": 0, "high": 40,
                "panel": "LFT", "category": "Hepatic"},
    "1975-2":  {"name": "Bilirubin.total [Mass/volume] in Serum or Plasma",
                "unit": "umol/L", "low": 0, "high": 21,
                "panel": "LFT", "category": "Hepatic"},
    "2532-0":  {"name": "Lactate dehydrogenase [Enzymatic activity/volume] in Serum or Plasma",
                "unit": "U/L", "low": 100, "high": 250,
                "panel": "LFT", "category": "Hepatic"},
    # ── Thyroid ────────────────────────────────────────────────────
    "3016-3":  {"name": "Thyrotropin [Units/volume] in Serum or Plasma",
                "unit": "mIU/L", "low": 0.4, "high": 4.0,
                "panel": "Thyroid", "category": "Endocrine"},
    "3051-0":  {"name": "Thyroxine (T4) free [Mass/volume] in Serum or Plasma",
                "unit": "pmol/L", "low": 10.0, "high": 20.0,
                "panel": "Thyroid", "category": "Endocrine"},
    # ── Cardiac ────────────────────────────────────────────────────
    "2157-6":  {"name": "Creatine kinase [Enzymatic activity/volume] in Serum or Plasma",
                "unit": "U/L", "low": 30, "high": 200,
                "panel": "Cardiac", "category": "Cardiac"},
    "49563-0": {"name": "Troponin I.cardiac [Mass/volume] in Serum or Plasma by High sensitivity method",
                "unit": "ng/L", "low": None, "high": 52,
                "panel": "Cardiac", "category": "Cardiac"},
    "33762-6": {"name": "NT-proBNP [Mass/volume] in Serum or Plasma",
                "unit": "ng/L", "low": None, "high": 125,
                "panel": "Cardiac", "category": "Cardiac"},
    # ── Electrolytes ───────────────────────────────────────────────
    "2823-3":  {"name": "Potassium [Moles/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": 3.5, "high": 5.0,
                "panel": "BMP", "category": "Electrolyte"},
    "2951-2":  {"name": "Sodium [Moles/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": 136, "high": 145,
                "panel": "BMP", "category": "Electrolyte"},
    "2075-0":  {"name": "Chloride [Moles/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": 98, "high": 107,
                "panel": "BMP", "category": "Electrolyte"},
    # ── Lipids ─────────────────────────────────────────────────────
    "2093-3":  {"name": "Cholesterol [Mass/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": None, "high": 5.2,
                "panel": "Lipid", "category": "Cardiovascular"},
    "2085-9":  {"name": "Cholesterol in HDL [Mass/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": 1.0, "high": None,
                "panel": "Lipid", "category": "Cardiovascular"},
    "13457-7": {"name": "Cholesterol in LDL [Mass/volume] in Serum or Plasma by calculation",
                "unit": "mmol/L", "low": None, "high": 3.4,
                "panel": "Lipid", "category": "Cardiovascular"},
    "2571-8":  {"name": "Triglycerides [Mass/volume] in Serum or Plasma",
                "unit": "mmol/L", "low": None, "high": 1.7,
                "panel": "Lipid", "category": "Cardiovascular"},
    # ── Urinalysis ─────────────────────────────────────────────────
    "5767-9":  {"name": "Appearance of Urine",
                "unit": None, "low": None, "high": None,
                "panel": "UA", "category": "Urinalysis"},
    "5778-6":  {"name": "Color of Urine",
                "unit": None, "low": None, "high": None,
                "panel": "UA", "category": "Urinalysis"},
    "2514-8":  {"name": "Ketones [Presence] in Urine by Test strip",
                "unit": None, "low": None, "high": None,
                "panel": "UA", "category": "Urinalysis"},
    # ── Vital signs ────────────────────────────────────────────────
    "8480-6":  {"name": "Systolic blood pressure",
                "unit": "mm[Hg]", "low": 90, "high": 120,
                "panel": "Vitals", "category": "Vitals"},
    "8462-4":  {"name": "Diastolic blood pressure",
                "unit": "mm[Hg]", "low": 60, "high": 80,
                "panel": "Vitals", "category": "Vitals"},
    "8867-4":  {"name": "Heart rate",
                "unit": "/min", "low": 60, "high": 100,
                "panel": "Vitals", "category": "Vitals"},
    "9279-1":  {"name": "Respiratory rate",
                "unit": "/min", "low": 12, "high": 20,
                "panel": "Vitals", "category": "Vitals"},
    "8310-5":  {"name": "Body temperature",
                "unit": "Cel", "low": 36.1, "high": 37.2,
                "panel": "Vitals", "category": "Vitals"},
    "59408-5": {"name": "Oxygen saturation in Arterial blood by Pulse oximetry",
                "unit": "%", "low": 95, "high": 100,
                "panel": "Vitals", "category": "Vitals"},
}

# FAKE LOINC codes that AI commonly hallucinates
FAKE_LOINC_CODES = [
    "1234-5", "9999-9", "0000-1", "1111-1", "2222-2",
    "CREA-01", "GLU-02", "HBA1C", "INR-001", "CBC-TOTAL",
    "LAB-001", "TEST-999", "FAKE-123", "BLOOD-01", "URINE-02",
]


# ═══════════════════════════════════════════════════════════════════════
# SNOMED CT — Real concepts used in Canadian clinical documentation
# Format: code -> {display, domain, synonyms}
# ═══════════════════════════════════════════════════════════════════════
SNOMED_CONCEPTS = {
    # ── Disorders ──────────────────────────────────────────────────
    "44054006":  {"display": "Diabetes mellitus type 2 (disorder)",
                  "domain": "Endocrine", "hierarchy": "disorder"},
    "73211009":  {"display": "Diabetes mellitus (disorder)",
                  "domain": "Endocrine", "hierarchy": "disorder"},
    "38341003":  {"display": "Hypertensive disorder, systemic arterial (disorder)",
                  "domain": "Cardiovascular", "hierarchy": "disorder"},
    "49436004":  {"display": "Atrial fibrillation (disorder)",
                  "domain": "Cardiovascular", "hierarchy": "disorder"},
    "84114007":  {"display": "Heart failure (disorder)",
                  "domain": "Cardiovascular", "hierarchy": "disorder"},
    "13645005":  {"display": "Chronic obstructive lung disease (disorder)",
                  "domain": "Respiratory", "hierarchy": "disorder"},
    "195967001": {"display": "Asthma (disorder)",
                  "domain": "Respiratory", "hierarchy": "disorder"},
    "709044004": {"display": "Chronic kidney disease (disorder)",
                  "domain": "Renal", "hierarchy": "disorder"},
    "40930008":  {"display": "Hypothyroidism (disorder)",
                  "domain": "Endocrine", "hierarchy": "disorder"},
    "35489007":  {"display": "Depressive disorder (disorder)",
                  "domain": "Mental health", "hierarchy": "disorder"},
    "197480006": {"display": "Anxiety disorder (disorder)",
                  "domain": "Mental health", "hierarchy": "disorder"},
    "70995007":  {"display": "Pulmonary embolism (disorder)",
                  "domain": "Cardiovascular", "hierarchy": "disorder"},
    "230690007": {"display": "Stroke (disorder)",
                  "domain": "Neurological", "hierarchy": "disorder"},
    "22298006":  {"display": "Myocardial infarction (disorder)",
                  "domain": "Cardiovascular", "hierarchy": "disorder"},
    # ── Procedures ─────────────────────────────────────────────────
    "387713003": {"display": "Surgical procedure (procedure)",
                  "domain": "Procedure", "hierarchy": "procedure"},
    "71388002":  {"display": "Procedure (procedure)",
                  "domain": "Procedure", "hierarchy": "procedure"},
    "308335008": {"display": "Patient encounter procedure (procedure)",
                  "domain": "Procedure", "hierarchy": "procedure"},
    # ── Substances / Medications ───────────────────────────────────
    "387458008": {"display": "Aspirin (substance)",
                  "domain": "Medication", "hierarchy": "substance"},
    "372756006": {"display": "Warfarin (substance)",
                  "domain": "Medication", "hierarchy": "substance"},
    "109053000": {"display": "Metformin (substance)",
                  "domain": "Medication", "hierarchy": "substance"},
    "386873009": {"display": "Atorvastatin (substance)",
                  "domain": "Medication", "hierarchy": "substance"},
    "387458008": {"display": "Aspirin (substance)",
                  "domain": "Medication", "hierarchy": "substance"},
    "372524001": {"display": "Salbutamol (substance)",
                  "domain": "Medication", "hierarchy": "substance"},
    # ── Findings ───────────────────────────────────────────────────
    "404684003": {"display": "Clinical finding (finding)",
                  "domain": "Finding", "hierarchy": "finding"},
    "267431006": {"display": "Dyslipidemia (finding)",
                  "domain": "Cardiovascular", "hierarchy": "finding"},
    "302866003": {"display": "Hypoglycemia (finding)",
                  "domain": "Endocrine", "hierarchy": "finding"},
}

# Common SNOMED hallucinations
FAKE_SNOMED_CODES = [
    "123456789", "999999999", "000000001", "111111111",
    "DM-TYPE2", "HTN-001", "AF-DISORDER", "STROKE-99",
    "SNOMED-DM", "ICD-DM2", "FAKE-CONCEPT",
]


# ═══════════════════════════════════════════════════════════════════════
# ICD-10-CA — Canadian version (differs from US ICD-10-CM)
# CIHI maintains the Canadian modification
# ═══════════════════════════════════════════════════════════════════════
ICD10_CA = {
    # ── Endocrine ──────────────────────────────────────────────────
    "E11.9":  {"description": "Type 2 diabetes mellitus without complications",
               "ca_note": "Same as ICD-10-CM", "chapter": "Endocrine"},
    "E11.65": {"description": "Type 2 diabetes mellitus with hyperglycemia",
               "ca_note": "ICD-10-CA differs from CM in specificity",
               "chapter": "Endocrine"},
    "E13.9":  {"description": "Other specified diabetes mellitus without complications",
               "ca_note": "Used in Canada for LADA and atypical DM",
               "chapter": "Endocrine"},
    "E03.9":  {"description": "Hypothyroidism, unspecified",
               "ca_note": "Same as ICD-10-CM", "chapter": "Endocrine"},
    # ── Cardiovascular ─────────────────────────────────────────────
    "I10":    {"description": "Essential (primary) hypertension",
               "ca_note": "Same as ICD-10-CM", "chapter": "Cardiovascular"},
    "I48.0":  {"description": "Paroxysmal atrial fibrillation",
               "ca_note": "ICD-10-CA has additional AF specificity codes vs CM",
               "chapter": "Cardiovascular"},
    "I48.2":  {"description": "Chronic atrial fibrillation",
               "ca_note": "ICD-10-CA specific — not in ICD-10-CM as I48.2",
               "chapter": "Cardiovascular"},
    "I50.9":  {"description": "Heart failure, unspecified",
               "ca_note": "Same chapter, Canada uses additional specificity",
               "chapter": "Cardiovascular"},
    "I21.9":  {"description": "Acute myocardial infarction, unspecified",
               "ca_note": "Same as ICD-10-CM", "chapter": "Cardiovascular"},
    "I63.9":  {"description": "Cerebral infarction, unspecified",
               "ca_note": "Same as ICD-10-CM", "chapter": "Neurological"},
    # ── Respiratory ────────────────────────────────────────────────
    "J44.1":  {"description": "Chronic obstructive pulmonary disease with acute exacerbation",
               "ca_note": "Same as ICD-10-CM", "chapter": "Respiratory"},
    "J45.9":  {"description": "Asthma, unspecified",
               "ca_note": "Canada uses J45.20-J45.51 for severity specificity",
               "chapter": "Respiratory"},
    # ── Mental health ──────────────────────────────────────────────
    "F32.9":  {"description": "Major depressive disorder, single episode, unspecified",
               "ca_note": "Same as ICD-10-CM", "chapter": "Mental health"},
    "F41.9":  {"description": "Anxiety disorder, unspecified",
               "ca_note": "Same as ICD-10-CM", "chapter": "Mental health"},
    "F10.20": {"description": "Alcohol use disorder, moderate",
               "ca_note": "ICD-10-CA aligns with DSM-5 severity coding",
               "chapter": "Mental health"},
    # ── Renal ──────────────────────────────────────────────────────
    "N18.3":  {"description": "Chronic kidney disease, stage 3 (moderate)",
               "ca_note": "Same as ICD-10-CM", "chapter": "Renal"},
    "N18.9":  {"description": "Chronic kidney disease, unspecified",
               "ca_note": "Same as ICD-10-CM", "chapter": "Renal"},
    # ── COVID-19 (Canadian-specific coding) ────────────────────────
    "U07.1":  {"description": "COVID-19, virus identified",
               "ca_note": "PHAC mandated — Canada adopted WHO emergency code",
               "chapter": "COVID-19"},
    "U07.2":  {"description": "COVID-19, virus not identified (clinical diagnosis)",
               "ca_note": "Canada Health specific — clinical diagnosis pathway",
               "chapter": "COVID-19"},
    "U09.9":  {"description": "Post-COVID-19 condition, unspecified",
               "ca_note": "CIHI adopted 2021 for long COVID documentation",
               "chapter": "COVID-19"},
    # ── Canadian-specific differences from US ICD-10-CM ────────────
    # Canada uses Z codes differently than US
    "Z76.89": {"description": "Persons encountering health services in other specified circumstances",
               "ca_note": "Canada uses for virtual/telehealth encounters differently than US",
               "chapter": "Z-codes"},
}

# ICD-10-CM codes that are US-specific and NOT valid in Canada
ICD10_CM_NOT_CANADA = {
    "Z71.89": "US-specific counselling code — Canada uses Z71.9",
    "I48.11": "US long-standing persistent AF — Canada uses I48.2",
    "I48.19": "US other persistent AF — ICD-10-CA has different specificity",
    "F32.A":  "US unspecified depressive episode — not in ICD-10-CA",
}


# ═══════════════════════════════════════════════════════════════════════
# CANADIAN DIN — Real Drug Identification Numbers
# Health Canada Drug Product Database
# These are publicly available real DINs
# ═══════════════════════════════════════════════════════════════════════
CANADIAN_DINS = {
    # ── Anticoagulants ─────────────────────────────────────────────
    "02229400": {"drug": "Coumadin", "ingredient": "warfarin sodium",
                 "strength": "5 mg", "form": "tablet",
                 "manufacturer": "Bristol-Myers Squibb",
                 "schedule": "prescription"},
    "02242789": {"drug": "Coumadin", "ingredient": "warfarin sodium",
                 "strength": "2.5 mg", "form": "tablet",
                 "manufacturer": "Bristol-Myers Squibb",
                 "schedule": "prescription"},
    # ── Diabetes ───────────────────────────────────────────────────
    "02242959": {"drug": "Metformin", "ingredient": "metformin hydrochloride",
                 "strength": "500 mg", "form": "tablet",
                 "manufacturer": "Various (generic)",
                 "schedule": "prescription"},
    "02246820": {"drug": "Glucophage", "ingredient": "metformin hydrochloride",
                 "strength": "850 mg", "form": "tablet",
                 "manufacturer": "Sanofi",
                 "schedule": "prescription"},
    # ── Antihypertensives ──────────────────────────────────────────
    "02103184": {"drug": "Zestril", "ingredient": "lisinopril",
                 "strength": "10 mg", "form": "tablet",
                 "manufacturer": "AstraZeneca",
                 "schedule": "prescription"},
    "02285088": {"drug": "Ramipril", "ingredient": "ramipril",
                 "strength": "5 mg", "form": "capsule",
                 "manufacturer": "Various (generic)",
                 "schedule": "prescription"},
    # ── Statins ────────────────────────────────────────────────────
    "02230711": {"drug": "Lipitor", "ingredient": "atorvastatin calcium",
                 "strength": "20 mg", "form": "tablet",
                 "manufacturer": "Pfizer",
                 "schedule": "prescription"},
    "02247936": {"drug": "Crestor", "ingredient": "rosuvastatin calcium",
                 "strength": "10 mg", "form": "tablet",
                 "manufacturer": "AstraZeneca",
                 "schedule": "prescription"},
    # ── Respiratory ────────────────────────────────────────────────
    "02097613": {"drug": "Ventolin", "ingredient": "salbutamol sulfate",
                 "strength": "100 mcg/actuation", "form": "inhaler",
                 "manufacturer": "GlaxoSmithKline",
                 "schedule": "prescription"},
    "02244016": {"drug": "Symbicort", "ingredient": "budesonide/formoterol",
                 "strength": "200/6 mcg", "form": "inhaler",
                 "manufacturer": "AstraZeneca",
                 "schedule": "prescription"},
    # ── Mental health ──────────────────────────────────────────────
    "02220121": {"drug": "Prozac", "ingredient": "fluoxetine hydrochloride",
                 "strength": "20 mg", "form": "capsule",
                 "manufacturer": "Eli Lilly",
                 "schedule": "prescription"},
    "02244118": {"drug": "Cipralex", "ingredient": "escitalopram oxalate",
                 "strength": "10 mg", "form": "tablet",
                 "manufacturer": "Lundbeck",
                 "schedule": "prescription"},
    # ── Opioids (controlled substances) ───────────────────────────
    "02014475": {"drug": "MS Contin", "ingredient": "morphine sulfate",
                 "strength": "30 mg", "form": "tablet",
                 "manufacturer": "Purdue",
                 "schedule": "prescription_controlled_narcotic"},
    "02216205": {"drug": "OxyContin", "ingredient": "oxycodone hydrochloride",
                 "strength": "20 mg", "form": "tablet",
                 "manufacturer": "Purdue",
                 "schedule": "prescription_controlled_narcotic"},
    # ── Antibiotics ────────────────────────────────────────────────
    "00628115": {"drug": "Amoxil", "ingredient": "amoxicillin trihydrate",
                 "strength": "500 mg", "form": "capsule",
                 "manufacturer": "Various",
                 "schedule": "prescription"},
    "02177897": {"drug": "Cipro", "ingredient": "ciprofloxacin",
                 "strength": "500 mg", "form": "tablet",
                 "manufacturer": "Bayer",
                 "schedule": "prescription"},
    # ── GLP-1 agonists (semaglutide) ──────────────────────────────
    "02471442": {"drug": "Ozempic", "ingredient": "semaglutide",
                 "strength": "0.5 mg/dose", "form": "injection",
                 "manufacturer": "Novo Nordisk",
                 "schedule": "prescription",
                 "note": "Approved for T2DM — NOT weight loss (Wegovy separate DIN)"},
    "02523302": {"drug": "Wegovy", "ingredient": "semaglutide",
                 "strength": "2.4 mg/dose", "form": "injection",
                 "manufacturer": "Novo Nordisk",
                 "schedule": "prescription",
                 "note": "Approved for chronic weight management"},
}

# Common drug hallucinations AI produces
FAKE_DRUG_NAMES = [
    "Therapaxin", "Clinovate", "Medicore", "Healagen",
    "Treximet XR", "Warfex", "Gluco-Control", "CardioPlus",
    "DiabeCure", "HyperBlock", "StatinX", "MetaForce",
]


# ═══════════════════════════════════════════════════════════════════════
# UCUM — Unified Code for Units of Measure
# Critical for preventing dosing errors
# mcg vs mg is a 1000-fold difference — fatal
# ═══════════════════════════════════════════════════════════════════════
UCUM_UNITS = {
    # ── Mass ───────────────────────────────────────────────────────
    "mg":   {"name": "milligram",    "factor": 1e-3, "dimension": "mass"},
    "g":    {"name": "gram",         "factor": 1.0,  "dimension": "mass"},
    "kg":   {"name": "kilogram",     "factor": 1e3,  "dimension": "mass"},
    "ug":   {"name": "microgram",    "factor": 1e-6, "dimension": "mass",
             "alias": "mcg", "warning": "mcg and ug both valid UCUM — ensure consistent use"},
    "ng":   {"name": "nanogram",     "factor": 1e-9, "dimension": "mass"},
    # ── Volume ─────────────────────────────────────────────────────
    "mL":   {"name": "milliliter",   "factor": 1e-3, "dimension": "volume"},
    "L":    {"name": "liter",        "factor": 1.0,  "dimension": "volume"},
    "uL":   {"name": "microliter",   "factor": 1e-6, "dimension": "volume"},
    # ── Concentration ──────────────────────────────────────────────
    "mg/dL":   {"name": "milligrams per deciliter",
                "note": "US unit for glucose — NOT used in Canada",
                "canadian_equiv": "mmol/L",
                "conversion": "divide by 18.02 for glucose"},
    "mmol/L":  {"name": "millimoles per liter",
                "note": "Canadian standard for glucose, electrolytes",
                "warning": "Canadian AI must use mmol/L not mg/dL"},
    "umol/L":  {"name": "micromoles per liter",
                "note": "Canadian standard for creatinine",
                "canadian_equiv": "NOT mg/dL",
                "warning": "US uses mg/dL for creatinine — Canada uses umol/L"},
    "nmol/L":  {"name": "nanomoles per liter",
                "note": "Used for hormones, vitamin D"},
    "pmol/L":  {"name": "picomoles per liter",
                "note": "Used for thyroid hormones in Canada"},
    # ── Pressure ───────────────────────────────────────────────────
    "mm[Hg]": {"name": "millimeters of mercury",
               "note": "Blood pressure — universal"},
    # ── Time-based ─────────────────────────────────────────────────
    "U/L":   {"name": "units per liter",
              "note": "Enzyme activity — ALT, AST, LDH"},
    "/min":  {"name": "per minute", "note": "Heart rate, respiratory rate"},
    # ── Canadian-specific critical differences ─────────────────────
    "Cel":   {"name": "degrees Celsius",
              "note": "Canadian standard — NOT Fahrenheit for clinical",
              "warning": "AI must report temperature in Celsius not Fahrenheit for Canada"},
}

# Dangerous unit confusions
UNIT_CONFUSION_DANGERS = [
    {"wrong": "mg", "correct": "mcg", "drug": "digoxin",
     "consequence": "1000-fold overdose — cardiac arrest"},
    {"wrong": "mg", "correct": "mcg", "drug": "fentanyl",
     "consequence": "1000-fold overdose — respiratory arrest, death"},
    {"wrong": "mg/dL", "correct": "mmol/L", "drug": "glucose",
     "consequence": "18-fold unit error — wrong insulin dosing"},
    {"wrong": "mg/dL", "correct": "umol/L", "drug": "creatinine",
     "consequence": "~88-fold unit error — missed or false renal failure"},
    {"wrong": "U", "correct": "units", "drug": "insulin",
     "consequence": "U misread as 0 — 10-fold overdose"},
]


# ═══════════════════════════════════════════════════════════════════════
# DRUG INTERACTIONS — Critical pairs in Canadian clinical practice
# ═══════════════════════════════════════════════════════════════════════
DRUG_INTERACTIONS = {
    ("warfarin", "fluconazole"): {
        "severity": "CRITICAL",
        "mechanism": "CYP2C9 inhibition increases warfarin exposure 2-3x",
        "consequence": "Major bleeding risk — INR can exceed 8.0",
        "action": "Avoid combination or reduce warfarin dose 50% with close INR monitoring",
        "regulations": ["Health Canada Drug Interaction Advisory"],
    },
    ("warfarin", "ASA"): {
        "severity": "HIGH",
        "mechanism": "Additive anticoagulant and antiplatelet effect",
        "consequence": "Significantly increased bleeding risk",
        "action": "Use lowest effective aspirin dose, monitor closely",
        "regulations": ["Health Canada"],
    },
    ("metformin", "contrast_media"): {
        "severity": "HIGH",
        "mechanism": "Risk of contrast-induced nephropathy causing metformin accumulation",
        "consequence": "Lactic acidosis — potentially fatal",
        "action": "Hold metformin 48h before and after contrast; check creatinine before restarting",
        "regulations": ["Health Canada Advisory 2016"],
    },
    ("SSRI", "tramadol"): {
        "severity": "HIGH",
        "mechanism": "Serotonin syndrome risk — both increase serotonergic activity",
        "consequence": "Serotonin syndrome — hyperthermia, seizures, death",
        "action": "Avoid combination; consider alternative analgesic",
        "regulations": ["Health Canada"],
    },
    ("codeine", "child_under_12"): {
        "severity": "CRITICAL",
        "mechanism": "Ultra-rapid CYP2D6 metabolism risk — morphine toxicity",
        "consequence": "Respiratory depression, death — multiple Canadian fatalities",
        "action": "CONTRAINDICATED in children under 12 — Health Canada 2013 advisory",
        "regulations": ["Health Canada Advisory 2013-12", "MHRA"],
    },
    ("ciprofloxacin", "warfarin"): {
        "severity": "HIGH",
        "mechanism": "CYP1A2 and CYP2C9 inhibition",
        "consequence": "INR elevation, bleeding risk",
        "action": "Monitor INR closely; anticipate warfarin dose reduction needed",
        "regulations": ["Health Canada"],
    },
    ("simvastatin", "clarithromycin"): {
        "severity": "HIGH",
        "mechanism": "CYP3A4 inhibition increases simvastatin AUC 10-fold",
        "consequence": "Rhabdomyolysis, acute kidney injury",
        "action": "Hold simvastatin during clarithromycin course",
        "regulations": ["Health Canada", "FDA (same recommendation)"],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# FHIR R4 RESOURCE TEMPLATES — Canada Health Infoway CA Core+ aligned
# ═══════════════════════════════════════════════════════════════════════
CA_CORE_PROFILES = {
    "Patient":              "http://hl7.org/fhir/ca/core/StructureDefinition/profile-patient",
    "Observation":          "http://hl7.org/fhir/ca/core/StructureDefinition/profile-observation",
    "MedicationRequest":    "http://hl7.org/fhir/ca/core/StructureDefinition/profile-medicationrequest",
    "Condition":            "http://hl7.org/fhir/ca/core/StructureDefinition/profile-condition",
    "DiagnosticReport":     "http://hl7.org/fhir/ca/core/StructureDefinition/profile-diagnosticreport",
    "Immunization":         "http://hl7.org/fhir/ca/core/StructureDefinition/profile-immunization",
    "AllergyIntolerance":   "http://hl7.org/fhir/ca/core/StructureDefinition/profile-allergyintolerance",
    "Practitioner":         "http://hl7.org/fhir/ca/core/StructureDefinition/profile-practitioner",
    "Organization":         "http://hl7.org/fhir/ca/core/StructureDefinition/profile-organization",
}

# Canadian identifiers
CA_IDENTIFIER_SYSTEMS = {
    "BC_PHN":     "https://health.gov.bc.ca/fhir/NamingSystem/ca-bc-patient-healthcare-id",
    "ON_OHIP":    "https://health.gov.on.ca/fhir/NamingSystem/ca-on-patient-hcn",
    "AB_ULI":     "https://health.alberta.ca/fhir/NamingSystem/ca-ab-patient-uli",
    "CANADA_SIN": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-sin",  # NOT for health
    "CPS_ID":     "https://fhir.infoway-inforoute.ca/NamingSystem/ca-hc-din",  # DIN
}


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def is_valid_loinc(code: str) -> bool:
    """Check if a LOINC code exists in our reference set."""
    return code in LOINC_CODES

def is_fake_loinc(code: str) -> bool:
    """Check if a code is a known LOINC hallucination."""
    return code in FAKE_LOINC_CODES or not any(c.isdigit() for c in code)

def is_valid_din(din: str) -> bool:
    """Check if a DIN exists in our Canadian drug reference."""
    return din in CANADIAN_DINS

def get_drug_interaction(drug1: str, drug2: str) -> dict:
    """Look up a drug interaction pair."""
    d1, d2 = drug1.lower(), drug2.lower()
    return (DRUG_INTERACTIONS.get((d1, d2)) or
            DRUG_INTERACTIONS.get((d2, d1)) or {})

def get_loinc_info(code: str) -> dict:
    """Get LOINC code information."""
    return LOINC_CODES.get(code, {})

def fake_loinc_codes(n: int = None) -> list:
    """Return list of known fake/hallucinated LOINC codes. If n given, return n codes."""
    codes = FAKE_LOINC_CODES.copy()
    if n is not None:
        return codes[:n] if n <= len(codes) else codes
    return codes

def canadian_unit_for(test_name: str) -> str:
    """Return the correct Canadian unit for a common test."""
    unit_map = {
        "glucose":     "mmol/L",
        "creatinine":  "umol/L",
        "hemoglobin":  "g/L",
        "cholesterol": "mmol/L",
        "tsh":         "mIU/L",
        "t4":          "pmol/L",
        "temperature": "Cel",
        "bp":          "mm[Hg]",
    }
    return unit_map.get(test_name.lower(), "mmol/L")
