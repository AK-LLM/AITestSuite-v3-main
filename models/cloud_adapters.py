"""
═══════════════════════════════════════════════════════════
AITestSuite v3 — Cloud Provider Adapters
Author: Amarjit Khakh
═══════════════════════════════════════════════════════════

PURPOSE:
    Extends the model adapter layer to support cloud-hosted
    AI services. Implements the same interface as ModelAdapter
    so cloud models plug directly into the audit engine
    with zero changes to the test suite or scoring.

SUPPORTED CLOUD PROVIDERS:
    AWS Bedrock    — Amazon hosted foundation models
                     (Titan, Llama, Mistral, Cohere etc)

    Azure OpenAI   — Microsoft Azure hosted models
                     (GPT-4, GPT-3.5, custom deployments)

    GCP Vertex AI  — Google Cloud hosted models
                     (Gemini, PaLM, custom tuned models)

INSTALL:
    AWS:   pip install boto3
    Azure: pip install openai azure-identity
    GCP:   pip install google-cloud-aiplatform

CONFIGURATION:
    AWS:
        Set environment variables:
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
        OR use IAM role if running on EC2/Lambda

    Azure:
        AZURE_OPENAI_ENDPOINT — Your Azure OpenAI endpoint URL
        AZURE_OPENAI_API_KEY  — Your Azure API key
        AZURE_OPENAI_VERSION  — API version (default: 2024-02-01)

    GCP:
        Set GOOGLE_APPLICATION_CREDENTIALS to service account JSON
        OR use Application Default Credentials

HEALTHCARE RELEVANCE:
    Many healthcare organisations use cloud AI services.
    Healthcare organisations may use AWS or Azure
    hosted clinical AI. This adapter enables testing those
    specific deployments directly.
═══════════════════════════════════════════════════════════
"""

import os
import logging

logger = logging.getLogger("AITestSuite.CloudAdapters")


class AWSBedrockAdapter:
    """
    Adapter for AWS Bedrock hosted foundation models.
    Supports all Bedrock text generation models.
    """

    def __init__(self, model_id="amazon.titan-text-express-v1",
                 region=None, access_key=None, secret_key=None):
        """
        Args:
            model_id   : Bedrock model ID
                         e.g. 'amazon.titan-text-express-v1'
                              'meta.llama2-70b-chat-v1'
                              'mistral.mistral-7b-instruct-v0:2'
            region     : AWS region (default: us-east-1)
            access_key : AWS access key (uses env vars if None)
            secret_key : AWS secret key (uses env vars if None)
        """
        self.model_id    = model_id
        self.region      = region or os.getenv("AWS_REGION", "us-east-1")
        self.access_key  = access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key  = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.model_type  = "aws_bedrock"
        self.model_name  = model_id
        self.client      = None

    def load(self):
        """Initialise the Bedrock client."""
        try:
            import boto3
        except ImportError:
            raise ImportError("AWS SDK not installed. Run: pip install boto3")

        session_kwargs = {
            "region_name": self.region
        }
        if self.access_key and self.secret_key:
            session_kwargs["aws_access_key_id"]     = self.access_key
            session_kwargs["aws_secret_access_key"] = self.secret_key

        session    = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime")
        logger.info(f"AWS Bedrock client initialised: {self.model_id} in {self.region}")
        return True

    def query(self, prompt, max_tokens=150):
        """
        Send a prompt to AWS Bedrock and return the response.
        Handles different request/response formats per model family.
        """
        import json

        if not self.client:
            raise RuntimeError("Client not initialised. Call load() first.")

        # ── Build request body based on model family ──────────────────────
        if "titan" in self.model_id:
            # Amazon Titan format
            body = json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature":   0.3
                }
            })
        elif "llama" in self.model_id:
            # Meta Llama format
            body = json.dumps({
                "prompt":       f"[INST] {prompt} [/INST]",
                "max_gen_len":  max_tokens,
                "temperature":  0.3
            })
        elif "mistral" in self.model_id:
            # Mistral format
            body = json.dumps({
                "prompt":         f"<s>[INST] {prompt} [/INST]",
                "max_tokens":     max_tokens,
                "temperature":    0.3
            })
        elif "claude" in self.model_id:
            # Anthropic Claude on Bedrock
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens":        max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            })
        else:
            # Generic format fallback
            body = json.dumps({
                "prompt":    prompt,
                "max_tokens": max_tokens
            })

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            response_body = json.loads(response["body"].read())

            # ── Extract text based on model family ────────────────────────
            if "titan" in self.model_id:
                return response_body.get("results", [{}])[0].get("outputText", "")
            elif "llama" in self.model_id:
                return response_body.get("generation", "")
            elif "mistral" in self.model_id:
                return response_body.get("outputs", [{}])[0].get("text", "")
            elif "claude" in self.model_id:
                return response_body.get("content", [{}])[0].get("text", "")
            else:
                return str(response_body)

        except Exception as e:
            logger.error(f"Bedrock query failed: {e}")
            return f"ERROR: {str(e)}"

    def info(self):
        return {"model_type": "aws_bedrock", "model_name": self.model_id, "region": self.region}


class AzureOpenAIAdapter:
    """
    Adapter for Azure OpenAI Service.
    Supports all Azure-hosted model deployments.
    """

    def __init__(self, deployment_name, endpoint=None, api_key=None, api_version=None):
        """
        Args:
            deployment_name : Your Azure deployment name (not model name)
            endpoint        : Azure OpenAI endpoint URL
            api_key         : Azure OpenAI API key
            api_version     : API version string
        """
        self.deployment_name = deployment_name
        self.endpoint        = endpoint    or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key         = api_key     or os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version     = api_version or os.getenv("AZURE_OPENAI_VERSION", "2024-02-01")
        self.model_type      = "azure_openai"
        self.model_name      = f"azure:{deployment_name}"
        self.client          = None

    def load(self):
        """Initialise the Azure OpenAI client."""
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise ImportError("OpenAI SDK not installed. Run: pip install openai")

        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OpenAI requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY "
                "environment variables or constructor arguments."
            )

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        logger.info(f"Azure OpenAI client initialised: {self.deployment_name}")
        return True

    def query(self, prompt, max_tokens=150):
        """Send a prompt to Azure OpenAI."""
        if not self.client:
            raise RuntimeError("Client not initialised. Call load() first.")
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI query failed: {e}")
            return f"ERROR: {str(e)}"

    def info(self):
        return {
            "model_type":      "azure_openai",
            "model_name":      self.model_name,
            "deployment_name": self.deployment_name,
            "endpoint":        self.endpoint
        }


class GCPVertexAdapter:
    """
    Adapter for Google Cloud Vertex AI.
    Supports Gemini and other Vertex-hosted models.
    """

    def __init__(self, model_name="gemini-1.0-pro", project_id=None, location=None):
        """
        Args:
            model_name : Vertex AI model name
            project_id : GCP project ID
            location   : GCP region (default: us-central1)
        """
        self.vertex_model_name = model_name
        self.project_id        = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location          = location   or os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        self.model_type        = "gcp_vertex"
        self.model_name        = f"vertex:{model_name}"
        self._model            = None

    def load(self):
        """Initialise the Vertex AI client."""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
        except ImportError:
            raise ImportError(
                "Google Cloud AI Platform not installed. "
                "Run: pip install google-cloud-aiplatform"
            )

        if not self.project_id:
            raise ValueError(
                "GCP project ID required. Set GOOGLE_CLOUD_PROJECT "
                "environment variable or pass project_id argument."
            )

        vertexai.init(project=self.project_id, location=self.location)
        self._model = GenerativeModel(self.vertex_model_name)
        logger.info(f"Vertex AI client initialised: {self.vertex_model_name}")
        return True

    def query(self, prompt, max_tokens=150):
        """Send a prompt to Vertex AI."""
        if not self._model:
            raise RuntimeError("Client not initialised. Call load() first.")
        try:
            response = self._model.generate_content(
                prompt,
                generation_config={"max_output_tokens": max_tokens, "temperature": 0.3}
            )
            return response.text
        except Exception as e:
            logger.error(f"Vertex AI query failed: {e}")
            return f"ERROR: {str(e)}"

    def info(self):
        return {
            "model_type":  "gcp_vertex",
            "model_name":  self.model_name,
            "project_id":  self.project_id,
            "location":    self.location
        }


class OllamaAdapter:
    """
    Adapter for Ollama — local model serving.
    Runs models locally via the Ollama API.
    Perfect for air-gapped or high-security environments.
    """

    def __init__(self, model_name="llama2", base_url=None):
        """
        Args:
            model_name : Ollama model name (must be pulled first)
            base_url   : Ollama API URL (default: http://localhost:11434)
        """
        self.ollama_model = model_name
        self.base_url     = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model_type   = "ollama"
        self.model_name   = f"ollama:{model_name}"

    def load(self):
        """Verify Ollama is running and model is available."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                if self.ollama_model not in [m.split(":")[0] for m in models]:
                    logger.warning(
                        f"Model {self.ollama_model} not found in Ollama. "
                        f"Run: ollama pull {self.ollama_model}"
                    )
            logger.info(f"Ollama connected: {self.ollama_model}")
            return True
        except Exception as e:
            raise RuntimeError(f"Cannot connect to Ollama at {self.base_url}: {e}")

    def query(self, prompt, max_tokens=150):
        """Send a prompt to Ollama."""
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model":  self.ollama_model,
                    "prompt": prompt,
                    "options": {"num_predict": max_tokens, "temperature": 0.3},
                    "stream": False
                },
                timeout=60
            )
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return f"ERROR: {str(e)}"

    def info(self):
        return {"model_type": "ollama", "model_name": self.model_name, "base_url": self.base_url}


# ── Cloud adapter factory ─────────────────────────────────────────────────

def create_cloud_adapter(provider, **kwargs):
    """
    Factory function to create the appropriate cloud adapter.

    Args:
        provider : 'aws_bedrock', 'azure_openai', 'gcp_vertex', 'ollama'
        **kwargs : Provider-specific configuration

    Returns:
        Appropriate adapter instance

    Example:
        adapter = create_cloud_adapter('aws_bedrock',
                                        model_id='amazon.titan-text-express-v1')
        adapter = create_cloud_adapter('azure_openai',
                                        deployment_name='gpt-4',
                                        endpoint='https://myazure.openai.azure.com')
        adapter = create_cloud_adapter('gcp_vertex',
                                        model_name='gemini-1.0-pro',
                                        project_id='my-gcp-project')
        adapter = create_cloud_adapter('ollama', model_name='llama2')
    """
    adapters = {
        "aws_bedrock":  AWSBedrockAdapter,
        "azure_openai": AzureOpenAIAdapter,
        "gcp_vertex":   GCPVertexAdapter,
        "ollama":       OllamaAdapter,
    }

    adapter_class = adapters.get(provider)
    if not adapter_class:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Valid providers: {list(adapters.keys())}"
        )

    return adapter_class(**kwargs)
