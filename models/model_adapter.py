"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Model Adapter Layer
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Model agnostic interface — plug in ANY AI model.
    Supports HuggingFace (free/local), OpenAI, and Anthropic.
    Default: google/flan-t5-small — free, no API key needed.

USAGE:
    adapter = ModelAdapter(model_type="huggingface", model_name="google/flan-t5-small")
    adapter.load()
    response = adapter.query("What is the capital of France?")

SUPPORTED PROVIDERS:
    - huggingface : Local models via transformers library (FREE)
    - openai      : API-based provider (requires API key)
    - anthropic   : API-based provider (requires API key)
═══════════════════════════════════════════════════════════
"""


class ModelAdapter:
    """
    Universal model wrapper.
    Abstracts away provider differences so the audit engine
    never needs to know which model it is testing.
    """

    def __init__(self, model_type="huggingface", model_name="google/flan-t5-small", api_key=None):
        """
        Args:
            model_type  : Provider — 'huggingface', 'openai', or 'anthropic'
            model_name  : Model identifier (HF model ID or API model name)
            api_key     : API key for openai or anthropic providers (not needed for HuggingFace)
        """
        self.model_type = model_type
        self.model_name = model_name
        self.api_key = api_key
        self.model = None
        self.tokenizer = None
        self.client = None

    def load(self):
        """
        Download and initialise the target model.
        Returns True on success, raises exception on failure.
        """

        if self.model_type == "huggingface":
            # ── HuggingFace: Download model weights locally ──────────────
            from transformers import (
                T5Tokenizer, T5ForConditionalGeneration,
                AutoTokenizer, AutoModelForCausalLM
            )
            try:
                # Try T5 family first (flan-t5-small, flan-t5-base etc)
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
                self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            except Exception:
                # Fall back to generic AutoModel for other HF models
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            return True

        elif self.model_type == "openai":
            # ── OpenAI: Initialise client with API key ───────────────────
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            return True

        elif self.model_type == "anthropic":
            # ── Anthropic: Initialise client ──────────────────────────────────
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            return True

        raise ValueError(f"Unsupported model_type: {self.model_type}")

    def query(self, prompt, max_tokens=150):
        """
        Send a prompt to the loaded model and return the text response.

        Args:
            prompt     : The text prompt to send
            max_tokens : Maximum tokens in the response

        Returns:
            String response from the model
        """

        if self.model_type == "huggingface":
            # ── HuggingFace inference ────────────────────────────────────
            # 1. Tokenize prompt → numbers
            # 2. Model generates output numbers
            # 3. Decode numbers → text
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            outputs = self.model.generate(**inputs, max_new_tokens=max_tokens)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        elif self.model_type == "openai":
            # ── OpenAI Chat Completion ───────────────────────────────────
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        elif self.model_type == "anthropic":
            # ── Anthropic Messages API ───────────────────────────────────
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        return "ERROR: Model type not supported"

    def info(self):
        """Return a summary dict of the loaded model configuration."""
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "has_api_key": self.api_key is not None
        }
