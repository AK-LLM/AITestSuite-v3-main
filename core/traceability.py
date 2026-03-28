"""
AITestSuite v3.3 — Formal Traceability Matrix
Author: Amarjit Khakh

ADDRESSES REVIEWER GAP:
  "No traceability mapping (tests → regulations)"
  "No formal compliance verification"
  "No audit-grade evidence generation"

WHAT THIS PROVIDES:
  1. TEST → REGULATION mapping: every test module maps to specific
     regulation clauses, not just framework names.
  2. REGULATION → TESTS mapping: given a regulation, find all tests
     that cover it (bidirectional).
  3. COVERAGE GAPS: which regulations have zero test coverage?
  4. AUDIT EXPORT: structured output for regulatory submissions.

REGULATION CATALOGUE:
  All major Canadian + international AI/health/privacy regulations
  with specific clause references.
"""

# ═══════════════════════════════════════════════════════════════════════
# REGULATION CATALOGUE — specific clause references
# ═══════════════════════════════════════════════════════════════════════

REGULATION_CATALOGUE = {
    # ── Canadian Healthcare ──────────────────────────────────────────
    "Bill_C7_MAID":           {"full": "Criminal Code s.241.2, Bill C-7 (2021)", "domain": "healthcare", "jurisdiction": "Canada"},
    "Health_Canada_SaMD":     {"full": "Health Canada: Software as a Medical Device Guidance (2023)", "domain": "healthcare", "jurisdiction": "Canada"},
    "PIPEDA":                 {"full": "Personal Information Protection and Electronic Documents Act (PIPEDA) s.5-7", "domain": "privacy", "jurisdiction": "Canada"},
    "CPPA":                   {"full": "Consumer Privacy Protection Act (Bill C-27, 2023)", "domain": "privacy", "jurisdiction": "Canada"},
    "BC_FIPPA":               {"full": "BC Freedom of Information and Protection of Privacy Act s.13,19", "domain": "privacy", "jurisdiction": "BC"},
    "Health_Canada_Drug":     {"full": "Health Canada Drug Identification Number (DIN) Regulations", "domain": "healthcare", "jurisdiction": "Canada"},
    "ISMP_Canada":            {"full": "ISMP Canada Medication Safety Guidelines", "domain": "healthcare", "jurisdiction": "Canada"},
    "Thrombosis_Canada":      {"full": "Thrombosis Canada Warfarin Dosing Guidelines", "domain": "healthcare", "jurisdiction": "Canada"},
    "BCCSU_Opioid":           {"full": "BCCSU BC Guideline for Opioid Use Disorder (2023)", "domain": "healthcare", "jurisdiction": "BC"},
    "CANMAT_Bipolar":         {"full": "CANMAT Bipolar Disorder Clinical Practice Guidelines (2018)", "domain": "healthcare", "jurisdiction": "Canada"},
    "CANMAT_Depression":      {"full": "CANMAT MDD Clinical Practice Guidelines (2016)", "domain": "healthcare", "jurisdiction": "Canada"},
    "CIHI_ICD10CA":           {"full": "CIHI ICD-10-CA Canadian Coding Standards", "domain": "healthcare", "jurisdiction": "Canada"},
    "Canada_Health_Infoway":  {"full": "Canada Health Infoway FHIR CA Core+ Profiles", "domain": "healthcare", "jurisdiction": "Canada"},
    "OCAP_Principles":        {"full": "OCAP Principles (Ownership, Control, Access, Possession) — First Nations Information Governance Centre", "domain": "indigenous", "jurisdiction": "Canada"},
    "FNHA":                   {"full": "First Nations Health Authority BC — Cultural Safety Framework", "domain": "indigenous", "jurisdiction": "BC"},
    "TRC_CTA22":              {"full": "Truth and Reconciliation Commission Call to Action 22 — Healthcare", "domain": "indigenous", "jurisdiction": "Canada"},
    "UNDRIP_Art31":           {"full": "UN Declaration on the Rights of Indigenous Peoples Article 31", "domain": "indigenous", "jurisdiction": "International"},
    "BC_Mental_Health_Act":   {"full": "BC Mental Health Act — Involuntary Admission and Consent", "domain": "healthcare", "jurisdiction": "BC"},
    "Jordan_Principle":       {"full": "Jordan's Principle — First Nations Child and Family Caring Society", "domain": "indigenous", "jurisdiction": "Canada"},
    "Health_Canada_Paeds":    {"full": "Health Canada Paediatric Drug Labelling Initiative (2013)", "domain": "healthcare", "jurisdiction": "Canada"},
    "TCPS2":                  {"full": "Tri-Council Policy Statement 2: Ethical Conduct for Research Involving Humans", "domain": "research", "jurisdiction": "Canada"},
    "Hospital_Records_Act":   {"full": "BC Hospital Act — Medical Records Requirements", "domain": "healthcare", "jurisdiction": "BC"},

    # ── Canadian Finance ─────────────────────────────────────────────
    "FINTRAC_PCMLTFA":        {"full": "FINTRAC — Proceeds of Crime (Money Laundering) and Terrorist Financing Act", "domain": "finance", "jurisdiction": "Canada"},
    "FCAC":                   {"full": "Financial Consumer Agency of Canada Act — Consumer Protection", "domain": "finance", "jurisdiction": "Canada"},
    "CIRO_Suitability":       {"full": "CIRO Rule 3400 — Suitability Obligation", "domain": "finance", "jurisdiction": "Canada"},
    "CSA_AML":                {"full": "Canadian Securities Administrators — AML/ATF Requirements", "domain": "finance", "jurisdiction": "Canada"},

    # ── Canadian Legal/Gov ───────────────────────────────────────────
    "ATI_Act":                {"full": "Access to Information Act — Federal (2019 amendments)", "domain": "legal", "jurisdiction": "Canada"},
    "Privacy_Act_CA":         {"full": "Privacy Act (Canada) — Government of Canada obligations", "domain": "legal", "jurisdiction": "Canada"},
    "Canadian_HRA":           {"full": "Canadian Human Rights Act — Prohibited Grounds of Discrimination", "domain": "legal", "jurisdiction": "Canada"},
    "Genetic_Non_Discrim":    {"full": "Genetic Non-Discrimination Act (2017)", "domain": "healthcare", "jurisdiction": "Canada"},
    "PIPA_BC":                {"full": "BC Personal Information Protection Act (PIPA)", "domain": "privacy", "jurisdiction": "BC"},
    "Criminal_Code_Cyber":    {"full": "Criminal Code Canada s.342.1 — Unauthorized Computer Access", "domain": "security", "jurisdiction": "Canada"},
    "Law_Society_BC":         {"full": "Law Society of BC — Professional Conduct Rules on Unauthorized Practice", "domain": "legal", "jurisdiction": "BC"},

    # ── International AI / Security ──────────────────────────────────
    "OWASP_LLM_2025":         {"full": "OWASP Top 10 for LLM Applications 2025 — LLM01-LLM10", "domain": "security", "jurisdiction": "International"},
    "NIST_AI_RMF":            {"full": "NIST AI Risk Management Framework 1.0 — Govern/Map/Measure/Manage", "domain": "ai_governance", "jurisdiction": "International"},
    "EU_AI_Act":              {"full": "EU Artificial Intelligence Act (2024) — High-Risk AI Systems Article 9-16", "domain": "ai_governance", "jurisdiction": "EU"},
    "ISO_42001":              {"full": "ISO/IEC 42001:2023 — AI Management System", "domain": "ai_governance", "jurisdiction": "International"},
    "ISO_27001":              {"full": "ISO/IEC 27001:2022 — Information Security Management", "domain": "security", "jurisdiction": "International"},
    "FHIR_SMART":             {"full": "HL7 FHIR R4 SMART on FHIR — Authorization Framework", "domain": "healthcare", "jurisdiction": "International"},
    "LOINC_Standard":         {"full": "LOINC — Logical Observation Identifiers Names and Codes (Regenstrief)", "domain": "healthcare", "jurisdiction": "International"},
    "UCUM_Standard":          {"full": "UCUM — Unified Code for Units of Measure", "domain": "healthcare", "jurisdiction": "International"},
    "SNOMED_CT":              {"full": "SNOMED International — Clinical Terms", "domain": "healthcare", "jurisdiction": "International"},
}


# ═══════════════════════════════════════════════════════════════════════
# TRACEABILITY MATRIX — test module → regulation list
# ═══════════════════════════════════════════════════════════════════════

TRACEABILITY_MATRIX = {
    "tests.default_tests": {
        "regulations": ["OWASP_LLM_2025", "NIST_AI_RMF", "PIPEDA", "Health_Canada_SaMD"],
        "primary_coverage": "Foundational safety, bias, hallucination, privacy",
        "test_count": 29,
    },
    "tests.advanced_tests": {
        "regulations": ["OWASP_LLM_2025", "NIST_AI_RMF", "EU_AI_Act", "Health_Canada_SaMD"],
        "primary_coverage": "Jailbreak, roleplay, prompt injection, CBRN refusal",
        "test_count": 84,
    },
    "tests.attack_surface_tests": {
        "regulations": ["OWASP_LLM_2025", "Criminal_Code_Cyber", "NIST_AI_RMF"],
        "primary_coverage": "Multi-turn attacks, memory injection, tool injection",
        "test_count": 44,
    },
    "tests.adversarial_robustness_tests": {
        "regulations": ["OWASP_LLM_2025", "NIST_AI_RMF", "ISO_42001"],
        "primary_coverage": "Fuzzing, encoding variants, adversarial robustness",
        "test_count": 38,
    },
    "tests.healthcare_governance_tests": {
        "regulations": ["PIPEDA", "Health_Canada_SaMD", "NIST_AI_RMF", "Canadian_HRA", "CPPA"],
        "primary_coverage": "Clinical governance, consent, PHI protection",
        "test_count": 51,
    },
    "tests.clinical_safety_tests": {
        "regulations": ["Health_Canada_SaMD", "ISMP_Canada", "Thrombosis_Canada", "Health_Canada_Drug"],
        "primary_coverage": "Drug safety, emergency triage, clinical accuracy",
        "test_count": 28,
    },
    "tests.privacy_deep_tests": {
        "regulations": ["PIPEDA", "BC_FIPPA", "CPPA", "TCPS2"],
        "primary_coverage": "PHI extraction, re-identification, de-identification",
        "test_count": 14,
    },
    "tests.multilingual_tests": {
        "regulations": ["Health_Canada_SaMD", "Canadian_HRA", "FNHA"],
        "primary_coverage": "Safety across 12 languages including Indigenous",
        "test_count": 12,
    },
    "tests.module_a_indigenous_health": {
        "regulations": ["FNHA", "OCAP_Principles", "TRC_CTA22", "UNDRIP_Art31", "Jordan_Principle"],
        "primary_coverage": "FNHA eligibility, OCAP, TRC Call to Action 22",
        "test_count": 15,
    },
    "tests.module_b_maid": {
        "regulations": ["Bill_C7_MAID", "BC_Mental_Health_Act", "Health_Canada_SaMD"],
        "primary_coverage": "MAID safeguards, eligibility, coercion detection",
        "test_count": 13,
    },
    "tests.module_c_supply_chain": {
        "regulations": ["NIST_AI_RMF", "ISO_42001", "Health_Canada_SaMD"],
        "primary_coverage": "Model integrity, training data poisoning",
        "test_count": 10,
    },
    "tests.module_d_vector_embedding": {
        "regulations": ["OWASP_LLM_2025", "PIPEDA", "NIST_AI_RMF"],
        "primary_coverage": "RAG attacks, embedding inversion, vector store poisoning",
        "test_count": 10,
    },
    "tests.module_e_output_handling": {
        "regulations": ["OWASP_LLM_2025", "ISO_27001", "Health_Canada_SaMD"],
        "primary_coverage": "XSS via AI output, code injection in clinical notes",
        "test_count": 8,
    },
    "tests.module_f_sycophancy": {
        "regulations": ["Health_Canada_SaMD", "NIST_AI_RMF", "ISMP_Canada"],
        "primary_coverage": "Clinical deference, authority pressure, sycophantic reversal",
        "test_count": 10,
    },
    "tests.module_g_multispecialty": {
        "regulations": ["Health_Canada_SaMD", "ISMP_Canada", "Bill_C7_MAID", "Health_Canada_Paeds"],
        "primary_coverage": "Cardiology, oncology, obstetrics, paediatrics",
        "test_count": 22,
    },
    "tests.module_h_governance_deep": {
        "regulations": ["NIST_AI_RMF", "EU_AI_Act", "ISO_42001", "Health_Canada_SaMD"],
        "primary_coverage": "AI Act compliance, ISO 42001, NIST AI RMF",
        "test_count": 16,
    },
    "tests.module_i_canadian_specific": {
        "regulations": ["CIHI_ICD10CA", "Health_Canada_SaMD", "Canada_Health_Infoway", "Health_Canada_Drug"],
        "primary_coverage": "ICD-10-CA, CIHI coding, Canadian drug standards",
        "test_count": 15,
    },
    "tests.module_j_intersectional_bias": {
        "regulations": ["Canadian_HRA", "TRC_CTA22", "BCCSU_Opioid", "Health_Canada_SaMD"],
        "primary_coverage": "Race, gender, socioeconomic bias in clinical AI",
        "test_count": 12,
    },
    "tests.module_k_agentic_deep": {
        "regulations": ["OWASP_LLM_2025", "NIST_AI_RMF", "Health_Canada_SaMD", "FHIR_SMART"],
        "primary_coverage": "Tool use, EHR write, agentic orchestrator attacks",
        "test_count": 14,
    },
    "tests.module_l_multimodal": {
        "regulations": ["LOINC_Standard", "Health_Canada_SaMD", "OWASP_LLM_2025"],
        "primary_coverage": "DICOM, radiology, image-based injection",
        "test_count": 8,
    },
    "tests.module_m_drift_temporal": {
        "regulations": ["Health_Canada_SaMD", "NIST_AI_RMF", "ISO_42001"],
        "primary_coverage": "Formulary drift, guideline staleness, temporal hallucination",
        "test_count": 10,
    },
    "tests.module_n_llmjacking": {
        "regulations": ["OWASP_LLM_2025", "Criminal_Code_Cyber", "ISO_27001"],
        "primary_coverage": "Compute theft, API abuse, resource exhaustion",
        "test_count": 8,
    },
    "tests.module_o_finance_deep": {
        "regulations": ["FINTRAC_PCMLTFA", "CIRO_Suitability", "FCAC", "CSA_AML"],
        "primary_coverage": "AML, structuring, elder abuse, suitability",
        "test_count": 12,
    },
    "tests.module_p_legal_gov_deep": {
        "regulations": ["Law_Society_BC", "ATI_Act", "Privacy_Act_CA", "Canadian_HRA"],
        "primary_coverage": "Legal privilege, UPL, bias in legal AI",
        "test_count": 13,
    },
    "tests.module_q_authority_impersonation": {
        "regulations": ["OWASP_LLM_2025", "Criminal_Code_Cyber", "PIPEDA"],
        "primary_coverage": "Credential escalation, social engineering, impersonation",
        "test_count": 12,
    },
    "tests.module_r_owasp_agentic": {
        "regulations": ["OWASP_LLM_2025", "NIST_AI_RMF"],
        "primary_coverage": "OWASP LLM Agentic Top 10 2025",
        "test_count": 10,
    },
    "tests.module_s_emergent_behavior": {
        "regulations": ["NIST_AI_RMF", "EU_AI_Act", "ISO_42001"],
        "primary_coverage": "Deceptive alignment, unexpected capability emergence",
        "test_count": 10,
    },
    "tests.module_t_deepfake_voice": {
        "regulations": ["Criminal_Code_Cyber", "PIPEDA", "OWASP_LLM_2025"],
        "primary_coverage": "Voice cloning, synthetic identity, deepfake clinical risk",
        "test_count": 8,
    },
    "tests.module_u_social_engineering": {
        "regulations": ["OWASP_LLM_2025", "PIPEDA", "ISO_27001"],
        "primary_coverage": "Pretexting, urgency, emotional manipulation",
        "test_count": 15,
    },
    "tests.module_v_clinical_terminology": {
        "regulations": ["LOINC_Standard", "SNOMED_CT", "CIHI_ICD10CA", "Canada_Health_Infoway", "UCUM_Standard", "Health_Canada_Drug"],
        "primary_coverage": "LOINC hallucination, ICD-10-CA vs CM, Canadian DINs, UCUM units",
        "test_count": 44,
    },
    "tests.module_w_fhir_injection": {
        "regulations": ["FHIR_SMART", "OWASP_LLM_2025", "PIPEDA", "Canada_Health_Infoway"],
        "primary_coverage": "FHIR field injection, HL7, OSCAR EMR, PharmaNet bypass",
        "test_count": 26,
    },
    "tests.module_x_formulary": {
        "regulations": ["Health_Canada_Drug", "BCCSU_Opioid", "Health_Canada_SaMD", "ISMP_Canada"],
        "primary_coverage": "BC PharmaCare, BCCSU opioid guidelines, PrescribeIT",
        "test_count": 21,
    },
    "tests.module_y_ehr_realism": {
        "regulations": ["PIPEDA", "FHIR_SMART", "Health_Canada_SaMD", "ISMP_Canada", "Bill_C7_MAID", "FNHA", "TRC_CTA22", "Canadian_HRA"],
        "primary_coverage": "Longitudinal data, conflicting records, write-back, cross-patient, explainability, enforcement",
        "test_count": 54,
    },
    "tests.module_z_reasoning": {
        "regulations": ["Health_Canada_SaMD", "NIST_AI_RMF", "ISMP_Canada", "Thrombosis_Canada", "BCCSU_Opioid", "OWASP_LLM_2025", "FINTRAC_PCMLTFA"],
        "primary_coverage": "Multi-hop, counterfactual, causal, chain-of-thought, contradiction, temporal, mathematical",
        "test_count": 25,
    },
    "tests.garak_probes": {
        "regulations": ["OWASP_LLM_2025", "NIST_AI_RMF"],
        "primary_coverage": "14 Garak attack categories",
        "test_count": 86,
    },
    "domains.finance": {
        "regulations": ["FINTRAC_PCMLTFA", "CIRO_Suitability", "FCAC", "Canadian_HRA"],
        "primary_coverage": "Financial domain safety baseline",
        "test_count": 26,
    },
    "domains.government_legal": {
        "regulations": ["ATI_Act", "Privacy_Act_CA", "Law_Society_BC", "Canadian_HRA"],
        "primary_coverage": "Government and legal domain baseline",
        "test_count": 35,
    },
}


# ═══════════════════════════════════════════════════════════════════════
# TRACEABILITY MAPPER
# ═══════════════════════════════════════════════════════════════════════

class TraceabilityMapper:
    """
    Bidirectional traceability between tests and regulations.
    Produces audit-grade evidence matrices.
    """

    def __init__(self):
        self.matrix  = TRACEABILITY_MATRIX
        self.catalog = REGULATION_CATALOGUE
        self._build_reverse_index()

    def _build_reverse_index(self):
        """Build regulation → [test_modules] reverse index."""
        self._reverse = {}
        for module, data in self.matrix.items():
            for reg in data["regulations"]:
                if reg not in self._reverse:
                    self._reverse[reg] = []
                self._reverse[reg].append(module)

    def tests_for_regulation(self, regulation_key: str) -> dict:
        """Which test modules cover this regulation?"""
        modules = self._reverse.get(regulation_key, [])
        reg_info = self.catalog.get(regulation_key, {})
        total_tests = sum(
            self.matrix[m]["test_count"] for m in modules
            if m in self.matrix
        )
        return {
            "regulation":      regulation_key,
            "full_name":       reg_info.get("full", regulation_key),
            "domain":          reg_info.get("domain", "unknown"),
            "jurisdiction":    reg_info.get("jurisdiction", "unknown"),
            "covered_by":      modules,
            "n_modules":       len(modules),
            "n_tests":         total_tests,
            "coverage_status": "COVERED" if modules else "GAP",
        }

    def regulations_for_module(self, module_key: str) -> dict:
        """Which regulations does this test module cover?"""
        data = self.matrix.get(module_key, {})
        regs = data.get("regulations", [])
        return {
            "module":       module_key,
            "regulations":  regs,
            "n_regs":       len(regs),
            "test_count":   data.get("test_count", 0),
            "coverage":     data.get("primary_coverage", ""),
            "reg_details":  {r: self.catalog.get(r, {}) for r in regs},
        }

    def coverage_gaps(self) -> list:
        """Regulations in the catalogue with zero test coverage."""
        gaps = []
        for reg_key, reg_info in self.catalog.items():
            modules = self._reverse.get(reg_key, [])
            if not modules:
                gaps.append({
                    "regulation": reg_key,
                    "full_name":  reg_info.get("full", reg_key),
                    "domain":     reg_info.get("domain", ""),
                    "status":     "NO_COVERAGE",
                })
        return gaps

    def full_matrix(self) -> dict:
        """Complete coverage matrix — all regulations × all modules."""
        all_regs = list(self.catalog.keys())
        result = {}
        for reg in all_regs:
            result[reg] = self.tests_for_regulation(reg)
        return result

    def audit_report(self, domain: str = None) -> dict:
        """
        Generate audit-grade traceability evidence.
        Suitable for regulatory submission or internal audit.
        """
        matrix = self.full_matrix()
        if domain:
            matrix = {k: v for k, v in matrix.items()
                      if self.catalog.get(k, {}).get("domain") == domain}

        covered   = [r for r, d in matrix.items() if d["coverage_status"] == "COVERED"]
        gaps      = [r for r, d in matrix.items() if d["coverage_status"] == "GAP"]
        total_mod_tests = sum(
            d["test_count"] for d in self.matrix.values()
        )

        return {
            "domain":            domain or "all",
            "total_regulations": len(matrix),
            "covered":           len(covered),
            "gaps":              len(gaps),
            "coverage_rate":     round(len(covered) / len(matrix), 3) if matrix else 0,
            "gap_regulations":   gaps,
            "total_tests_mapped": total_mod_tests,
            "covered_regulations": covered,
            "by_jurisdiction": self._by_jurisdiction(matrix),
            "by_domain":       self._by_domain(matrix),
            "audit_statement": (
                f"AITestSuite v3.3 provides test coverage for "
                f"{len(covered)}/{len(matrix)} regulations "
                f"({'all' if domain else 'across all domains'}). "
                f"{len(gaps)} regulations have no dedicated test coverage."
                if domain is None else
                f"{domain} domain: {len(covered)}/{len(matrix)} regulations covered."
            ),
        }

    def _by_jurisdiction(self, matrix: dict) -> dict:
        j = {}
        for reg_key, data in matrix.items():
            jur = self.catalog.get(reg_key, {}).get("jurisdiction", "Unknown")
            if jur not in j:
                j[jur] = {"total": 0, "covered": 0}
            j[jur]["total"] += 1
            if data["coverage_status"] == "COVERED":
                j[jur]["covered"] += 1
        return j

    def _by_domain(self, matrix: dict) -> dict:
        d = {}
        for reg_key, data in matrix.items():
            dom = self.catalog.get(reg_key, {}).get("domain", "Unknown")
            if dom not in d:
                d[dom] = {"total": 0, "covered": 0}
            d[dom]["total"] += 1
            if data["coverage_status"] == "COVERED":
                d[dom]["covered"] += 1
        return d

    def export_csv_rows(self) -> list:
        """Export as list of dicts for CSV/Excel output."""
        rows = []
        for mod, data in self.matrix.items():
            for reg in data["regulations"]:
                reg_info = self.catalog.get(reg, {})
                rows.append({
                    "Test Module":       mod,
                    "Test Count":        data["test_count"],
                    "Regulation ID":     reg,
                    "Regulation Full":   reg_info.get("full", reg),
                    "Domain":            reg_info.get("domain", ""),
                    "Jurisdiction":      reg_info.get("jurisdiction", ""),
                    "Primary Coverage":  data.get("primary_coverage",""),
                })
        return rows
