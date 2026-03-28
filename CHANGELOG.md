# AITestSuite — Changelog

## v3.3 — Statistical Rigor + Reasoning + Traceability
*Released: 2026-03-28*

### New Files (7)
- `core/ground_truth.py` — 17 verified clinical/security ground truth pairs, `GroundTruthEvaluator`, calibration check. Addresses: *"evaluations rely heavily on heuristics, no strong linkage to verified datasets"*
- `core/metrics.py` — `wilson_ci()`, `bootstrap_ci()`, `attack_success_rate()`, `false_positive_rate()`, `z_test_proportions()`, `compute_all_metrics()`. Addresses: *"no uncertainty modeling, no quantified success metrics"*
- `core/drift_detector.py` — 6 multi-turn drift scenarios, `DriftDetector` class, consistency scoring. Addresses: *"no multi-turn drift or memory persistence evaluation"*
- `core/tool_evaluator.py` — 12 tool-use scenarios, `ToolEvaluator` class, tool selection/safety/sequence evaluation. Addresses: *"no function-calling or agent workflow tests"*
- `core/traceability.py` — 40 regulations in catalogue, bidirectional test↔regulation matrix, `TraceabilityMapper`, audit report export. Addresses: *"no traceability mapping (tests → regulations)"*
- `tests/module_z_reasoning.py` — 25 tests: multi-hop, counterfactual, causal, chain-of-thought, contradiction, temporal, mathematical clinical reasoning. Addresses: *"weak reasoning benchmarks"*
- `VERSION` — semantic version file

### Patched Files (2, non-breaking)
- `core/scoring.py` — added `quantitative_metrics()` and `verdict_with_ci()` methods
- `core/statistical_runner.py` — added `_wilson_ci()` and `_bootstrap_ci()` to per-test statistical output

### Tests
- Previous: 857 tests, 38 modules
- v3.3: 882 tests, 39 modules (+25 Module Z)

---

## v3.2 Final — EHR/EMR + Blackbox API + All Fixes
*Released: 2026-03-26*

### New Files
- `core/ehr_realism.py` — longitudinal data (14+ obs/patient), conflicting scenarios, `validate_medication_write()`, `validate_lab_write()`, `check_cross_patient_boundary()`, `check_scope_violation()`
- `tests/module_y_ehr_realism.py` — 54 tests (longitudinal, conflicting, write-back, cross-patient, explainability, enforcement)
- `blackbox/browser_adapter.py` — `BlackBoxAPIAdapter` class added: `probe_rate_limits()`, `timing_profile()`, `response_diff()`, `encoding_variants()`, `header_injection_test()`, `concurrent_test()`

### Bug Fixes
- `streamlit_app.py` — 503 health check: `@st.cache_resource` on `_load_advanced_modules()`
- `streamlit_app.py` — `use_container_width=True` removed from all `st.dataframe()` calls (32 removed)
- `streamlit_app.py` — EHR tab KeyErrors: `v["type"]`→`v["category"]`, `v["term"]`→`v["display"]`, ICD10_CA dict access, `v["brand"]`→`v["drug"]`, `v["generic"]`→`v["ingredient"]`
- `core/reporting.py` — `body_small` style, `wordWrap='LTR'`, `Paragraph()` cells, `repeatRows=1`, `WORDWRAP` directive removed

### Tests
- Previous: 803 tests, 37 modules
- v3.2: 857 tests, 38 modules (+54 Module Y)

---

## v3.2 — EHR/EMR Integration
*Released: 2026-03-20*

### New Files
- `core/clinical_terminology.py` — 38 LOINC, 25 SNOMED CT, 21 ICD-10-CA, 18 Canadian DINs, 17 UCUM units
- `core/ehr_simulator.py` — 3 FHIR R4 patients (Margaret Chen 4421, James Thunderbird 7743, Priya Patel 1001)
- `core/fhir_client.py` — FHIR R4 HTTP client with simulator fallback
- `core/smart_auth.py` — SMART on FHIR OAuth2 (Epic/Cerner/OSCAR)
- `core/cds_hooks.py` — 5 CDS services: drug interaction, lab alert, MAID safeguard, paediatric, Indigenous
- `core/ehr_adapter.py` — Epic/Cerner/OSCAR/Simulator adapters
- `tests/module_v_clinical_terminology.py` — 44 tests
- `tests/module_w_fhir_injection.py` — 26 tests
- `tests/module_x_formulary.py` — 21 tests

### Tests
- Previous: 712 tests, 34 modules
- v3.2: 803 tests, 37 modules (+91)

---

## v3.1 — Extended Domain Coverage
*Released: 2026-02-15*

### Additions
- Modules A–U (21 modules): Indigenous health, MAID, supply chain, vector/embedding, sycophancy, multispecialty, governance, Canadian-specific, intersectional bias, agentic deep, multimodal, drift, LLMjacking, finance deep, legal/gov deep, authority impersonation, OWASP agentic, emergent behavior, deepfake/voice, social engineering
- Garak probes integration (86 tests)
- Finance domain and Legal/Gov domain modules

### Tests
- Previous: 195 tests, 4 modules
- v3.1: 712 tests, 34 modules

---

## v3.0 — Initial Release
*Released: 2026-01-10*

- Core engine: `scoring.py`, `risk_engine.py`, `compliance_mapper.py`, `decision_engine.py`, `audit_session.py`, `statistical_runner.py`
- Foundation tests: `default_tests.py` (29), `advanced_tests.py` (84), `attack_surface_tests.py` (44), `adversarial_robustness_tests.py` (38)
- Healthcare, Finance, Legal/Gov domain modules (baseline)
- Streamlit UI: 16 tabs
- Campaign runner, adversarial agents, simulation layer, autonomous adversary
