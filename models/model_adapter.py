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
        elif self.model_type in ("local", "gguf", "local_gguf"):
            return self._load_local()

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
        elif self.model_type in ("local", "gguf", "local_gguf"):
            return self._query_local(prompt, max_tokens)
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

    # ════════════════════════════════════════════════════════════════════════
    # LOCAL MODEL SUPPORT — USB drives, local folders, GGUF files
    # ════════════════════════════════════════════════════════════════════════

    def _load_local(self):
        """
        Load a model from a local path — USB drive, external SSD, or any folder.

        Supports three formats:
          1. GGUF (llama.cpp)   — single .gguf file, e.g. /media/usb/Llama-3-8B.Q4_K_M.gguf
          2. HuggingFace folder — folder containing config.json + safetensors/bin weights
          3. GGUF via Ollama    — model already pulled into Ollama (pass model_name only)

        Usage:
          # GGUF file on USB (Mac/Linux):
          model = ModelAdapter('local', '/Volumes/USB/models/Llama-3-8B.Q4_K_M.gguf')
          # GGUF file on USB (Windows):
          model = ModelAdapter('local', 'E:/models/Llama-3-8B.Q4_K_M.gguf')
          # HuggingFace folder on USB:
          model = ModelAdapter('local', '/Volumes/USB/Mistral-7B-Instruct-v0.2')
          # Auto-detect: scan a directory for any model
          model = ModelAdapter('local', '/Volumes/USB/models')
        """
        import os

        path = self.model_name  # model_name IS the path for local type

        # ── Clean up path — Windows Explorer sometimes adds quotes ───────────
        path = path.strip().strip('"').strip("'")

        # ── Auto-detect: if path is a directory, find the first usable model ──
        if os.path.isdir(path):
            path = self._find_model_in_dir(path)
            logger.info(f"Auto-detected model: {path}")

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model path not found: {path}\n"
                f"Check that:\n"
                f"  1. The USB drive is still connected\n"
                f"  2. The path is correct (tip: right-click the file → Copy as path)\n"
                f"  3. On Windows, remove any surrounding quotes if present"
            )

        self._local_path = path
        ext = os.path.splitext(path)[1].lower()

        # ── GGUF format — use llama-cpp-python ─────────────────────────────
        if ext == '.gguf' or self.model_type == 'gguf':
            return self._load_gguf(path)

        # ── HuggingFace folder format ──────────────────────────────────────
        if os.path.isdir(path) and os.path.exists(os.path.join(path, 'config.json')):
            return self._load_hf_local(path)

        raise ValueError(
            f"Unrecognised local model format at: {path}\n"
            f"Supported: .gguf files, or folders containing config.json"
        )

    def _find_model_in_dir(self, directory: str) -> str:
        """
        Scan a directory and return the path to the first usable model found.
        Priority: GGUF files > HuggingFace folders > subfolders with config.json
        """
        import os

        # Look for GGUF files first (most common on USB)
        for f in sorted(os.listdir(directory)):
            if f.lower().endswith('.gguf'):
                return os.path.join(directory, f)

        # Look for HuggingFace model folder (has config.json)
        if os.path.exists(os.path.join(directory, 'config.json')):
            return directory

        # Look one level deep for model subfolders
        for d in sorted(os.listdir(directory)):
            sub = os.path.join(directory, d)
            if os.path.isdir(sub):
                if os.path.exists(os.path.join(sub, 'config.json')):
                    return sub
                for f in os.listdir(sub):
                    if f.lower().endswith('.gguf'):
                        return os.path.join(sub, f)

        raise FileNotFoundError(
            f"No supported model found in {directory}\n"
            f"Expected: .gguf file or folder with config.json"
        )

    def _load_gguf(self, path: str):
        """Load a GGUF model using llama-cpp-python."""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise EnvironmentError(
                "llama-cpp-python is required for GGUF models.\n"
                "Install: pip install llama-cpp-python\n"
                "With GPU (CUDA): CMAKE_ARGS='-DLLAMA_CUDA=on' pip install llama-cpp-python --force-reinstall\n"
                "With GPU (Metal/Mac): CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python --force-reinstall"
            )
        import os
        size_gb = os.path.getsize(path) / 1e9
        logger.info(f"Loading GGUF: {os.path.basename(path)} ({size_gb:.1f}GB)")

        # Detect quantisation from filename for logging
        fname = os.path.basename(path).upper()
        quant = next((q for q in ['Q2_K','Q3_K','Q4_K_M','Q4_K_S','Q5_K','Q6_K','Q8_0','F16']
                      if q in fname), 'unknown')

        # n_gpu_layers=-1 uses all GPU layers if GPU available, 0 for CPU only
        n_gpu = -1 if GPU_AVAILABLE else 0

        self.model = Llama(
            model_path  = path,
            n_ctx       = 4096,       # context window
            n_gpu_layers= n_gpu,      # -1 = max GPU offload
            verbose     = False,
        )
        self._gguf_path = path
        self._gguf_quant = quant
        logger.info(f"GGUF loaded: {quant} quantisation, GPU layers: {'all' if n_gpu == -1 else 'none'}")
        return True

    def _load_hf_local(self, path: str):
        """Load a HuggingFace model from a local folder (no internet needed)."""
        if not TRANSFORMERS_AVAILABLE:
            raise EnvironmentError("pip install transformers")
        if not TORCH_AVAILABLE:
            raise EnvironmentError("pip install torch")

        from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
        import torch
        import os

        size_gb = sum(
            os.path.getsize(os.path.join(root, f))
            for root, _, files in os.walk(path)
            for f in files
        ) / 1e9
        logger.info(f"Loading local HF model: {os.path.basename(path)} ({size_gb:.1f}GB)")

        self.tokenizer = AutoTokenizer.from_pretrained(
            path,
            local_files_only=True,   # never call home — USB mode
            trust_remote_code=True,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        load_kw = {"local_files_only": True, "trust_remote_code": True}
        if GPU_AVAILABLE and BITSANDBYTES_AVAILABLE and size_gb > 4:
            from transformers import BitsAndBytesConfig
            load_kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
            load_kw["device_map"] = "auto"
        elif GPU_AVAILABLE:
            load_kw["device_map"] = "auto"
        else:
            load_kw["torch_dtype"] = torch.float32

        try:
            self.model = AutoModelForSeq2SeqLM.from_pretrained(path, **load_kw)
        except Exception:
            self.model = AutoModelForCausalLM.from_pretrained(path, **load_kw)

        return True

    def _query_local(self, prompt: str, max_tokens: int) -> str:
        """Query a locally loaded model (GGUF or HF local folder)."""
        if hasattr(self, '_gguf_path'):
            return self._query_gguf(prompt, max_tokens)
        return self._query_hf_local(prompt, max_tokens)

    def _query_gguf(self, prompt: str, max_tokens: int) -> str:
        """Query a GGUF model via llama-cpp-python."""
        output = self.model(
            prompt,
            max_tokens  = max_tokens,
            temperature = 0.1,
            stop        = ["\n\n", "User:", "Human:"],
            echo        = False,
        )
        return output["choices"][0]["text"].strip()

    def _query_hf_local(self, prompt: str, max_tokens: int) -> str:
        """Query a locally loaded HuggingFace model."""
        import torch
        inputs  = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        device  = next(self.model.parameters()).device
        inputs  = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens = max_tokens,
                do_sample      = False,
                temperature    = 1.0,
                pad_token_id   = self.tokenizer.pad_token_id,
            )
        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Strip the prompt echo if present
        if decoded.startswith(prompt):
            decoded = decoded[len(prompt):].strip()
        return decoded

    def scan_local_models(self, directory: str) -> list:
        """
        Scan a directory (USB or local folder) and return all discoverable models.
        Returns a list of dicts with path, name, format, and estimated size.

        Usage:
          adapter = ModelAdapter('local', '/Volumes/USB')
          models = adapter.scan_local_models('/Volumes/USB')
          for m in models:
              print(m['name'], m['format'], m['size_gb'])
        """
        import os
        found = []

        for root, dirs, files in os.walk(directory):
            # GGUF files
            for f in files:
                if f.lower().endswith('.gguf'):
                    full_path = os.path.join(root, f)
                    size_gb   = os.path.getsize(full_path) / 1e9
                    # Parse quantisation from filename
                    fname_up  = f.upper()
                    quant     = next((q for q in ['Q2_K','Q3_K','Q4_K_M','Q4_K_S','Q5_K','Q6_K','Q8_0','F16']
                                      if q in fname_up), None)
                    found.append({
                        "name":    f.replace('.gguf','').replace('.GGUF',''),
                        "path":    full_path,
                        "format":  "GGUF",
                        "size_gb": round(size_gb, 1),
                        "quant":   quant,
                        "usable":  True,
                    })

            # HuggingFace model folders (have config.json)
            if 'config.json' in files:
                size_gb = sum(
                    os.path.getsize(os.path.join(root, f))
                    for f in files
                ) / 1e9
                found.append({
                    "name":    os.path.basename(root),
                    "path":    root,
                    "format":  "HuggingFace",
                    "size_gb": round(size_gb, 1),
                    "quant":   None,
                    "usable":  True,
                })

        return sorted(found, key=lambda x: x['name'])

