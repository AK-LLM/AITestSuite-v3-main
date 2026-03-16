"""
AITestSuite v3 — OWASP LLM Top 10 2025 & MITRE ATLAS Mappings
Author: Amarjit Khakh
"""

# ── OWASP LLM Top 10 2025 ────────────────────────────────────────────────

OWASP_LLM_2025 = {
    "LLM01": {
        "title":       "Prompt Injection",
        "description": "Manipulating LLM behaviour through crafted inputs that override instructions.",
        "categories":  ["Prompt Injection", "Indirect Prompt Injection", "Token Smuggling"],
        "url":         "https://genai.owasp.org/llmrisk/llm01-prompt-injection/"
    },
    "LLM02": {
        "title":       "Sensitive Information Disclosure",
        "description": "LLMs inadvertently revealing confidential data, credentials or PII.",
        "categories":  ["Privacy Leakage", "Training Data Extraction", "Data Exfiltration"],
        "url":         "https://genai.owasp.org/llmrisk/llm02-sensitive-information-disclosure/"
    },
    "LLM03": {
        "title":       "Supply Chain",
        "description": "Vulnerabilities in LLM supply chain including poisoned models and components.",
        "categories":  ["Supply Chain"],
        "url":         "https://genai.owasp.org/llmrisk/llm03-supply-chain/"
    },
    "LLM04": {
        "title":       "Data and Model Poisoning",
        "description": "Manipulation of training data or fine-tuning to introduce backdoors or bias.",
        "categories":  ["RLHF Attack", "Supply Chain", "Bias Detection"],
        "url":         "https://genai.owasp.org/llmrisk/llm04-data-and-model-poisoning/"
    },
    "LLM05": {
        "title":       "Improper Output Handling",
        "description": "Insufficient validation of LLM outputs leading to downstream attacks.",
        "categories":  ["Code Injection", "Steganography", "Self-Replicating Payload"],
        "url":         "https://genai.owasp.org/llmrisk/llm05-improper-output-handling/"
    },
    "LLM06": {
        "title":       "Excessive Agency",
        "description": "LLM-based systems performing actions with too much autonomy or access.",
        "categories":  ["Agent Hijacking", "Agent Tool Exploitation", "Function Call Injection"],
        "url":         "https://genai.owasp.org/llmrisk/llm06-excessive-agency/"
    },
    "LLM07": {
        "title":       "System Prompt Leakage",
        "description": "Exposing confidential system prompts through various extraction techniques.",
        "categories":  ["Zero Day", "Extreme / Blackhat", "Context Leak"],
        "url":         "https://genai.owasp.org/llmrisk/llm07-system-prompt-leakage/"
    },
    "LLM08": {
        "title":       "Vector and Embedding Weaknesses",
        "description": "Exploiting weaknesses in vector databases and embedding models.",
        "categories":  ["RAG Exploitation", "Multi-Agent Exploitation"],
        "url":         "https://genai.owasp.org/llmrisk/llm08-vector-and-embedding-weaknesses/"
    },
    "LLM09": {
        "title":       "Misinformation",
        "description": "LLMs generating plausible but incorrect information that can cause harm.",
        "categories":  ["Hallucination", "Medical AI Specific"],
        "url":         "https://genai.owasp.org/llmrisk/llm09-misinformation/"
    },
    "LLM10": {
        "title":       "Unbounded Consumption",
        "description": "Excessive resource consumption leading to service disruption.",
        "categories":  ["Compression / DoS", "Adversarial"],
        "url":         "https://genai.owasp.org/llmrisk/llm10-unbounded-consumption/"
    }
}

# ── MITRE ATLAS Framework ─────────────────────────────────────────────────

MITRE_ATLAS = {
    "AML.T0006": {
        "title":       "Active Scanning",
        "tactic":      "Reconnaissance",
        "description": "Probe the ML system to gather information about its capabilities.",
        "categories":  ["Model Extraction", "Training Data Extraction"]
    },
    "AML.T0012": {
        "title":       "Valid Accounts",
        "tactic":      "Initial Access",
        "description": "Use valid credentials to gain access to ML systems.",
        "categories":  ["State Pollution", "RBAC Bypass"]
    },
    "AML.T0020": {
        "title":       "Exploit Public-Facing Application",
        "tactic":      "Initial Access",
        "description": "Attack internet-facing ML system interfaces.",
        "categories":  ["Prompt Injection", "Indirect Prompt Injection"]
    },
    "AML.T0043": {
        "title":       "Craft Adversarial Data",
        "tactic":      "ML Attack Staging",
        "description": "Create adversarial inputs to manipulate ML model outputs.",
        "categories":  ["Adversarial", "Fuzzing", "Token Smuggling", "Steganography"]
    },
    "AML.T0051": {
        "title":       "LLM Prompt Injection",
        "tactic":      "ML Attack Staging",
        "description": "Manipulate LLM output by injecting prompts into model inputs.",
        "categories":  ["Prompt Injection", "Indirect Prompt Injection", "Chain of Thought Injection"]
    },
    "AML.T0054": {
        "title":       "LLM Jailbreak",
        "tactic":      "ML Attack Staging",
        "description": "Circumvent LLM safety measures through crafted inputs.",
        "categories":  ["Jailbreak", "Extreme / Blackhat", "Multilingual Bypass", "Evolutionary Jailbreak"]
    },
    "AML.T0048": {
        "title":       "Backdoor ML Model",
        "tactic":      "Persistence",
        "description": "Insert backdoors into ML models during training or fine-tuning.",
        "categories":  ["Supply Chain", "RLHF Attack"]
    },
    "AML.T0040": {
        "title":       "ML Model Inference API Access",
        "tactic":      "Collection",
        "description": "Query model to extract information about training data.",
        "categories":  ["Training Data Extraction", "Model Extraction"]
    },
    "AML.T0025": {
        "title":       "Exfiltration via ML Inference API",
        "tactic":      "Exfiltration",
        "description": "Use the ML API to exfiltrate sensitive data.",
        "categories":  ["Data Exfiltration", "Privacy Leakage", "State Pollution"]
    },
    "AML.T0029": {
        "title":       "Denial of ML Service",
        "tactic":      "Impact",
        "description": "Degrade or disrupt ML system availability.",
        "categories":  ["Compression / DoS", "Adversarial"]
    },
    "AML.T0031": {
        "title":       "Erode ML Model Integrity",
        "tactic":      "Impact",
        "description": "Corrupt model behaviour to cause incorrect outputs.",
        "categories":  ["Hallucination", "Bias Detection", "Medical AI Specific"]
    },
    "AML.T0047": {
        "title":       "Discover ML Artifacts",
        "tactic":      "Discovery",
        "description": "Identify ML model files, APIs and infrastructure.",
        "categories":  ["Model Extraction", "Zero Day"]
    },
}


def get_owasp_mapping(category):
    """Return OWASP LLM IDs that map to a test category."""
    results = []
    for owasp_id, info in OWASP_LLM_2025.items():
        if category in info.get("categories", []):
            results.append(f"{owasp_id}: {info['title']}")
    return results


def get_mitre_mapping(category):
    """Return MITRE ATLAS technique IDs that map to a test category."""
    results = []
    for technique_id, info in MITRE_ATLAS.items():
        if category in info.get("categories", []):
            results.append(f"{technique_id}: {info['title']} ({info['tactic']})")
    return results


def enrich_finding_with_frameworks(finding):
    """Add OWASP and MITRE mappings to a finding dict."""
    category = finding.get("category", "")
    finding["owasp_mapping"]  = get_owasp_mapping(category)
    finding["mitre_mapping"]  = get_mitre_mapping(category)
    return finding


def enrich_all_findings(findings):
    """Add OWASP and MITRE mappings to all findings."""
    return [enrich_finding_with_frameworks(f) for f in findings]
