"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Model Adapter (v3.2)
Author: Amarjit Khakh

SUPPORTED PROVIDERS:
  huggingface  — HuggingFace models (free, requires GPU)
                 Works on: Google Colab T4, local machine with GPU
                 Models: flan-t5-small, flan-t5-xl, Mistral-7B,
                         Llama-2, Phi-2, Gemma, Falcon
  openai       — OpenAI API (GPT-4o, GPT-4, GPT-3.5)
  anthropic    — Anthropic Claude API
  aws_bedrock  — AWS Bedrock (Titan, Claude, Llama)
  azure_openai — Azure OpenAI deployments
  gcp_vertex   — Google Cloud Vertex AI
  ollama       — Local Ollama instance

LARGE MODEL SUPPORT (7B+ parameters):
  Automatically applies 4-bit quantization when bitsandbytes
  is installed. Required for Mistral-7B, Llama-2-7B etc on
  consumer / Colab T4 GPU.
  Install: pip install bitsandbytes accelerate

ENVIRONMENT NOTES:
  Google Colab T4 GPU — all providers work
  Local machine GPU   — all providers work
  Streamlit Cloud     — API providers only (OpenAI, Anthropic etc)
                        HuggingFace requires GPU not available on Cloud
═══════════════════════════════════════════════════════════
"""

import logging
import os

logger = logging.getLogger("AITestSuite.ModelAdapter")

# ── Detect available backends once at import time ────────────────────────
try:
    import torch
    TORCH_AVAILABLE    = True
    GPU_AVAILABLE      = torch.cuda.is_available()
    GPU_NAME           = torch.cuda.get_device_name(0) if GPU_AVAILABLE else "none"
except ImportError:
    TORCH_AVAILABLE    = False
    GPU_AVAILABLE      = False
    GPU_NAME           = "none"

try:
    import transformers
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import bitsandbytes
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    BITSANDBYTES_AVAILABLE = False

# ── Models requiring 4-bit quantization on T4 / consumer GPU ─────────────
REQUIRES_QUANTIZATION = {
    "mistralai/Mistral-7B-Instruct-v0.2",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "mistralai/Mistral-7B-v0.1",
    "meta-llama/Llama-2-7b-chat-hf",
    "meta-llama/Llama-2-13b-chat-hf",
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "google/flan-t5-xxl",
    "tiiuae/falcon-7b-instruct",
    "google/gemma-7b-it",
    "google/gemma-2-9b-it",
}

# ── T5-family models (seq2seq architecture) ───────────────────────────────
T5_MODELS = {"t5", "flan"}

# ── Causal LM models ──────────────────────────────────────────────────────
CAUSAL_MODELS = {
    "mistral", "llama", "gpt", "falcon", "phi",
    "gemma", "qwen", "bloom", "opt", "mpt"
}


class ModelAdapter:
    """
    Universal model wrapper. Same interface for every provider.
    """

    def __init__(self, model_type="huggingface",
                 model_name="google/flan-t5-small",
                 api_key=None):
        self.model_type = model_type.lower()
        self.model_name = model_name
        self.api_key    = api_key
        self.model      = None
        self.tokenizer  = None
        self.client     = None

    # ── PUBLIC: load ──────────────────────────────────────────────────────

    def load(self):
        """
        Initialise the model. Raises clear, actionable errors.
        Returns True on success.
        """
        if self.model_type == "huggingface":
            return self._load_huggingface()

        elif self.model_type == "openai":
            return self._load_openai()

        elif self.model_type == "anthropic":
            return self._load_anthropic()

        elif self.model_type == "aws_bedrock":
            return self._load_bedrock()

        elif self.model_type == "azure_openai":
            return self._load_azure_openai()

        elif self.model_type == "gcp_vertex":
            return self._load_vertex()

        elif self.model_type == "ollama":
            return self._load_ollama()

        raise ValueError(
            f"Unsupported model_type: '{self.model_type}'\n"
            "Supported: huggingface, openai, anthropic, "
            "aws_bedrock, azure_openai, gcp_vertex, ollama"
        )

    # ── PUBLIC: query ─────────────────────────────────────────────────────

    def query(self, prompt, max_tokens=150):
        """Send prompt, return text response."""
        if self.model_type == "huggingface":
            return self._query_huggingface(prompt, max_tokens)
        elif self.model_type == "openai":
            return self._query_openai(prompt, max_tokens)
        elif self.model_type == "anthropic":
            return self._query_anthropic(prompt, max_tokens)
        elif self.model_type == "aws_bedrock":
            return self._query_bedrock(prompt, max_tokens)
        elif self.model_type == "azure_openai":
            return self._query_azure_openai(prompt, max_tokens)
        elif self.model_type == "gcp_vertex":
            return self._query_vertex(prompt, max_tokens)
        elif self.model_type == "ollama":
            return self._query_ollama(prompt, max_tokens)
        return "ERROR: Model type not supported"

    def info(self):
        return {
            "model_type":          self.model_type,
            "model_name":          self.model_name,
            "torch_available":     TORCH_AVAILABLE,
            "gpu_available":       GPU_AVAILABLE,
            "gpu_name":            GPU_NAME,
            "transformers":        TRANSFORMERS_AVAILABLE,
            "bitsandbytes":        BITSANDBYTES_AVAILABLE,
        }

    # ── HUGGINGFACE ───────────────────────────────────────────────────────

    def _load_huggingface(self):
        if not TRANSFORMERS_AVAILABLE:
            raise EnvironmentError(
                "transformers not installed.\n"
                "Fix: pip install transformers"
            )
        if not TORCH_AVAILABLE:
            raise EnvironmentError(
                "PyTorch not found.\n"
                "On Colab:  pip install torch\n"
                "On local:  https://pytorch.org/get-started/locally/\n"
                "Note: HuggingFace models require GPU. "
                "Streamlit Cloud does not provide GPU — "
                "use an API provider (OpenAI, Anthropic) there, "
                "or run HuggingFace models from Google Colab."
            )

        needs_quant = self.model_name in REQUIRES_QUANTIZATION
        use_4bit    = needs_quant and BITSANDBYTES_AVAILABLE

        if needs_quant and not BITSANDBYTES_AVAILABLE:
            raise EnvironmentError(
                f"{self.model_name} requires 4-bit quantization "
                "but bitsandbytes is not installed.\n"
                "Fix: pip install bitsandbytes accelerate\n"
                "Then restart your runtime and try again."
            )

        try:
            import torch
            from transformers import AutoTokenizer

            logger.info(f"Loading {self.model_name} | 4-bit: {use_4bit} | GPU: {GPU_AVAILABLE}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            name_lower = self.model_name.lower()
            is_t5      = any(x in name_lower for x in T5_MODELS)
            is_causal  = any(x in name_lower for x in CAUSAL_MODELS)

            load_kw = {"trust_remote_code": True}

            if use_4bit:
                from transformers import BitsAndBytesConfig
                load_kw["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit              = True,
                    bnb_4bit_use_double_quant = True,
                    bnb_4bit_quant_type       = "nf4",
                    bnb_4bit_compute_dtype    = torch.float16,
                )
                load_kw["device_map"] = "auto"
            elif GPU_AVAILABLE:
                load_kw["torch_dtype"] = torch.float16

            if is_t5:
                from transformers import T5ForConditionalGeneration
                self.model = T5ForConditionalGeneration.from_pretrained(
                    self.model_name, **load_kw)
            elif is_causal:
                from transformers import AutoModelForCausalLM
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name, **load_kw)
            else:
                # Unknown architecture — try seq2seq then causal
                try:
                    from transformers import AutoModelForSeq2SeqLM
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(
                        self.model_name, **load_kw)
                except Exception:
                    from transformers import AutoModelForCausalLM
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name, **load_kw)

            # Move to GPU if not already placed by device_map
            if not use_4bit and GPU_AVAILABLE:
                self.model = self.model.cuda()

            logger.info(f"✅ {self.model_name} loaded successfully")
            return True

        except Exception as e:
            err = str(e)
            if "gated" in err.lower() or "access" in err.lower():
                raise EnvironmentError(
                    f"{self.model_name} is a gated model.\n"
                    "Fix: Go to huggingface.co, find the model, "
                    "accept the licence terms, then run:\n"
                    "  huggingface-cli login"
                )
            if "out of memory" in err.lower():
                raise EnvironmentError(
                    f"GPU out of memory loading {self.model_name}.\n"
                    "Fix: Try a smaller model (flan-t5-xl instead of xxl)\n"
                    "     Or install bitsandbytes for 4-bit quantization:\n"
                    "     pip install bitsandbytes accelerate"
                )
            raise RuntimeError(
                f"Failed to load {self.model_name}:\n{err}\n\n"
                "Common fixes:\n"
                "  1. Check model name spelling on huggingface.co\n"
                "  2. pip install transformers torch\n"
                "  3. For 7B+ models: pip install bitsandbytes accelerate\n"
                "  4. For gated models: huggingface-cli login"
            )

    def _query_huggingface(self, prompt, max_tokens):
        import torch
        inputs = self.tokenizer(
            prompt,
            return_tensors = "pt",
            truncation     = True,
            max_length     = 512,
            padding        = True,
        )
        if GPU_AVAILABLE:
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens = max_tokens,
                do_sample      = False,
                temperature    = None,
                top_p          = None,
                pad_token_id   = self.tokenizer.pad_token_id,
            )

        # Strip input tokens for causal models
        name_lower = self.model_name.lower()
        is_causal  = any(x in name_lower for x in CAUSAL_MODELS)
        if is_causal:
            outputs = outputs[:, inputs["input_ids"].shape[1]:]

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # ── OPENAI ────────────────────────────────────────────────────────────

    def _load_openai(self):
        if not self.api_key:
            raise ValueError("OpenAI API key required.")
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            return True
        except ImportError:
            raise EnvironmentError("pip install openai")

    def _query_openai(self, prompt, max_tokens):
        r = self.client.chat.completions.create(
            model      = self.model_name,
            messages   = [{"role": "user", "content": prompt}],
            max_tokens = max_tokens
        )
        return r.choices[0].message.content

    # ── ANTHROPIC ─────────────────────────────────────────────────────────

    def _load_anthropic(self):
        if not self.api_key:
            raise ValueError("Anthropic API key required.")
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            return True
        except ImportError:
            raise EnvironmentError("pip install anthropic")

    def _query_anthropic(self, prompt, max_tokens):
        m = self.client.messages.create(
            model      = self.model_name,
            max_tokens = max_tokens,
            messages   = [{"role": "user", "content": prompt}]
        )
        return m.content[0].text

    # ── AWS BEDROCK ───────────────────────────────────────────────────────

    def _load_bedrock(self):
        try:
            import boto3
            region = os.environ.get("AWS_REGION", "us-east-1")
            self.client = boto3.client("bedrock-runtime", region_name=region)
            return True
        except ImportError:
            raise EnvironmentError("pip install boto3")

    def _query_bedrock(self, prompt, max_tokens):
        import json
        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {"maxTokenCount": max_tokens}
        })
        r = self.client.invoke_model(
            modelId     = self.model_name,
            body        = body,
            contentType = "application/json",
            accept      = "application/json"
        )
        return json.loads(r["body"].read())["results"][0]["outputText"]

    # ── AZURE OPENAI ──────────────────────────────────────────────────────

    def _load_azure_openai(self):
        if not self.api_key:
            raise ValueError("Azure OpenAI API key required.")
        try:
            import openai
            self.client = openai.AzureOpenAI(
                api_key     = self.api_key,
                api_version = "2024-02-01",
                azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
            )
            return True
        except ImportError:
            raise EnvironmentError("pip install openai")

    def _query_azure_openai(self, prompt, max_tokens):
        r = self.client.chat.completions.create(
            model      = self.model_name,
            messages   = [{"role": "user", "content": prompt}],
            max_tokens = max_tokens
        )
        return r.choices[0].message.content

    # ── GCP VERTEX ────────────────────────────────────────────────────────

    def _load_vertex(self):
        try:
            from google.cloud import aiplatform
            aiplatform.init(project=os.environ.get("GOOGLE_CLOUD_PROJECT",""))
            return True
        except ImportError:
            raise EnvironmentError("pip install google-cloud-aiplatform")

    def _query_vertex(self, prompt, max_tokens):
        from vertexai.language_models import TextGenerationModel
        model    = TextGenerationModel.from_pretrained(self.model_name)
        response = model.predict(prompt, max_output_tokens=max_tokens)
        return response.text

    # ── OLLAMA ────────────────────────────────────────────────────────────

    def _load_ollama(self):
        import urllib.request
        url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        try:
            urllib.request.urlopen(f"{url}/api/tags", timeout=3)
            self.client = url
            return True
        except Exception:
            raise EnvironmentError(
                f"Cannot connect to Ollama at {url}\n"
                "Fix: Make sure Ollama is running: ollama serve\n"
                "     And the model is pulled: ollama pull llama2"
            )

    def _query_ollama(self, prompt, max_tokens):
        import urllib.request, json
        url  = self.client or os.environ.get("OLLAMA_URL","http://localhost:11434")
        data = json.dumps({
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }).encode()
        req  = urllib.request.Request(
            f"{url}/api/generate",
            data=data,
            headers={"Content-Type":"application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["response"]
