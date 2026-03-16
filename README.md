# AITestSuite v3

**AI Safety and Governance Audit Framework  
for Clinical AI Deployment in BC Healthcare**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OWASP](https://img.shields.io/badge/OWASP-LLM%20Top%2010%202025-red.svg)](https://genai.owasp.org)
[![MITRE](https://img.shields.io/badge/MITRE-ATLAS-orange.svg)](https://atlas.mitre.org)

---

## What This Is

AITestSuite v3 is an open-source AI security 
and governance audit platform purpose-built 
for healthcare environments. It enables any 
BC health authority or digital health 
organisation to systematically evaluate 
AI systems for safety, bias, privacy 
compliance and regulatory alignment — 
before and after clinical deployment.

**The problem it solves:** Healthcare 
organisations across BC are adopting AI 
systems without standardised audit 
frameworks to evaluate their safety 
characteristics. No accessible, 
PIPEDA-mapped, clinically-contextualised 
audit tool existed. This is that tool.

---

## What It Tests

| Category | Tests | Description |
|----------|-------|-------------|
| Attack Security | 29 | Prompt injection, jailbreaking, agent hijacking, token smuggling |
| Privacy & Data | 22 | PHI leakage, state pollution, compliance evasion, RAG exploitation |
| Clinical Safety | 14 | Hallucination, drug safety, bias detection, mental health crisis |
| Governance | 51 | PIPEDA, informed consent, explainability, Indigenous health equity |
| Benchmarks | 36 | TruthfulQA, BBQ, WinoBias, ToxiGen |
| Advanced Attacks | 26 | Evolutionary jailbreak, LLM-driven attack generation, supply chain |

**Total: 178 static + 36 benchmark + 24+ dynamic per run**

---

## Regulatory Framework

Every finding is mapped to:

- **OWASP LLM Top 10 2025** (LLM01–LLM10)
- **MITRE ATLAS** (adversarial ML techniques)
- **PIPEDA** (Schedule 1 — all 10 Fair Information Principles)
- **BC FIPPA** (Section 30 security obligations)
- **HIPAA** (Privacy Rule)
- **EU AI Act** (Articles 5, 9, 10, 13, 14 — high-risk AI)
- **Health Canada SaMD Guidance** (Software as a Medical Device)
- **WHO Ethics and Governance of AI for Health**
- **TRC Calls to Action 18–24** (Indigenous health)
- **UNDRIP Article 24** (Indigenous health rights)
- **NIST AI RMF 1.0** (Govern, Map, Measure, Manage)

---

## Key Features

- **PDF Audit Report** — professional report with risk matrix, 
  findings, regulatory flags and remediation guidance
- **Risk Scoring** — 4-dimension matrix (severity, likelihood, 
  patient impact, regulatory exposure) scored 1–5
- **Multi-Model Comparison** — test multiple AI systems 
  side-by-side for procurement decisions
- **Statistical Analysis** — N-run consistency testing 
  to detect intermittent vulnerabilities
- **LLM-Driven Attack Generation** — uses a second AI 
  as attacker to generate novel, contextually appropriate attacks
- **Evolutionary Jailbreak Engine** — genetic algorithm 
  that breeds increasingly effective jailbreak prompts
- **Continuous Monitoring** — anomaly detection, 
  jailbreak rate tracking, conversation drift detection
- **Enterprise Integration** — Slack, Teams, 
  PagerDuty, Jira, SIEM webhooks
- **RBAC** — 5-role access control for multi-user deployments
- **Forensic Audit Trail** — SHA256 hash-chain logging

---

## Quick Start

### Option 1 — Streamlit UI (Recommended)
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open your browser at `http://localhost:8501`

Select model → Select domain → Run Audit → Download PDF Report

### Option 2 — Google Colab (No Installation)
```python
!git clone https://github.com/AK-LLM/AITestSuite-v3-main.git
%cd AITestSuite-v3-main
!pip install -r requirements.txt

from models.model_adapter import ModelAdapter
from tests.default_tests import DEFAULT_TESTS
from domains.healthcare import HEALTHCARE_TESTS
from core.automation import BatchRunner
from core.scoring import RiskScorer

model = ModelAdapter("google/flan-t5-small", 
                     model_type="huggingface")
runner = BatchRunner(model, domain="healthcare")
findings = runner.run_batch(
    DEFAULT_TESTS + HEALTHCARE_TESTS
)
scorer = RiskScorer()
print(scorer.verdict(findings))
```

### Option 3 — CI/CD Pipeline
```bash
python run_ci.py \
  --model google/flan-t5-small \
  --domain healthcare
```

---

## Supported Models

| Provider | Examples |
|----------|---------|
| HuggingFace (free) | flan-t5-small, flan-t5-base, any public model |
| OpenAI | gpt-4o, gpt-3.5-turbo |
| Anthropic | claude-3-haiku, claude-3-sonnet |
| AWS Bedrock | amazon.titan, anthropic.claude |
| Azure OpenAI | Any deployed endpoint |
| GCP Vertex AI | gemini-pro, medpalm2 |
| Ollama (local) | llama3, mistral, any local model |

---

## Healthcare Domain Coverage

The healthcare module includes 14 HIPAA/PIPEDA-specific 
tests plus 51 governance tests covering:

- Clinical safety (hallucination, drug interactions, 
  vital signs, emergency triage)
- Patient privacy (PHI leakage, consent, 
  de-identification limits)
- Indigenous health equity (TRC Calls to Action, 
  UNDRIP, OCAP principles)
- Mental health safe messaging (CAMH guidelines, 
  crisis resources)
- Explainability and transparency rights
- Health Canada SaMD regulatory compliance
- EU AI Act high-risk AI obligations

---

## Output — PDF Audit Report

Every audit generates a professional PDF report including:

- Executive summary with overall verdict 
  (PASS / CONDITIONAL PASS / FAIL)
- Risk matrix table — all findings scored 1–5
- OWASP LLM Top 10 2025 mapping
- MITRE ATLAS technique mapping
- Regulatory compliance flags 
  (PIPEDA, HIPAA, BC FIPPA, EU AI Act)
- Clinical safety implications per finding
- Specific remediation recommendations
- Forensic audit trail with SHA256 hash chain

---

## Academic Benchmarks

| Benchmark | Description | Reference |
|-----------|-------------|-----------|
| TruthfulQA | Truthfulness evaluation | Lin et al. 2022 |
| BBQ | Demographic bias in QA | Parrish et al. 2022 |
| WinoBias | Occupational gender bias | Zhao et al. 2018 |
| ToxiGen | Implicit toxicity detection | Hosseini et al. 2023 |

Benchmarks load live from HuggingFace datasets 
when available, or use curated static samples 
as fallback.

---

## Project Context

Developed as part of the BCIT Digital Health 
Advanced Certificate (DIGH 7500 Capstone) 
by Amarjit Khakh — a senior technology 
risk and governance professional with 20+ years 
in regulated environments (CISSP, PMP) 
pivoting to Healthcare AI Governance.

This toolkit addresses a critical gap in 
BC's digital health ecosystem: no standardised, 
accessible, PIPEDA-mapped clinical AI audit 
framework existed. AITestSuite v3 is that framework.

---

## References

- Suresh & Guttag (2021) — A Framework for 
  Understanding Sources of Harm Throughout 
  the Machine Learning Life Cycle
- Carlini et al. (2021) — Extracting Training 
  Data from Large Language Models
- Perez & Ribeiro (2022) — Ignore Previous Prompt: 
  Attack Techniques for Language Models
- Hubinger et al. (2024) — Sleeper Agents: 
  Training Deceptive LLMs that Persist Through 
  Safety Training

---

## License

MIT License — free to use, modify and deploy.  
If you use this toolkit in your organisation, 
a citation or acknowledgement is appreciated.

---

*Built for BC healthcare. Applicable everywhere.*
