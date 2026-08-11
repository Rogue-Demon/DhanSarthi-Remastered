"""
Hugging Face model provider implementing the LLMProvider and EmbeddingProvider interfaces.
"""

from __future__ import annotations

import httpx
from app.ai.exceptions import AIConfigurationError, AIProviderError
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.schemas.advisor import AIContext
from app.core.config import settings


class HuggingFaceProvider(LLMProvider, EmbeddingProvider):
    """Integrates with Hugging Face Inference API for text generation and embeddings."""

    def __init__(self) -> None:
        self.api_key = settings.ai_provider_api_key
        self.model = settings.ai_model
        self.max_tokens = settings.ai_max_tokens
        self.temperature = settings.ai_temperature

        # Verify key is present when initializing the production provider
        if not self.api_key:
            raise AIConfigurationError(
                "Hugging Face API Key is not configured. Set AI_PROVIDER_API_KEY environment variable."
            )

        self.endpoint = f"https://api-inference.huggingface.co/models/{self.model}"

    async def generate(self, context: AIContext, prompt: str) -> str:
        """
        Query Hugging Face Inference API for text generation.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "return_full_text": False,  # Only return the newly generated text
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)

                if response.status_code == 401:
                    raise AIConfigurationError("Invalid Hugging Face API key credentials.")
                if response.status_code != 200:
                    raise AIProviderError(
                        f"Hugging Face API returned error status {response.status_code}: {response.text}"
                    )

                data = response.json()
                if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                    return str(data[0]["generated_text"]).strip()
                elif isinstance(data, dict) and "generated_text" in data:
                    return str(data["generated_text"]).strip()
                else:
                    raise AIProviderError(f"Unexpected response format from Hugging Face: {data}")

        except httpx.RequestError as exc:
            raise AIProviderError(f"HTTP request to Hugging Face failed: {str(exc)}") from exc

    async def embed(self, text: str) -> list[float]:
        """
        Query Hugging Face Feature Extraction model for vector embeddings.
        """
        # Embed uses the same api_key but normally a different feature extraction model.
        # For simplicity of the abstraction, we use the same key and a standard embedding model
        embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        endpoint = f"https://api-inference.huggingface.co/models/{embedding_model}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {"inputs": text}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(endpoint, headers=headers, json=payload)

                if response.status_code != 200:
                    raise AIProviderError(
                        f"Hugging Face embedding API returned error status {response.status_code}: {response.text}"
                    )

                data = response.json()
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], float):
                    return [float(x) for x in data]
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    return [float(x) for x in data[0]]
                else:
                    raise AIProviderError(f"Unexpected embedding format from Hugging Face: {data}")

        except httpx.RequestError as exc:
            raise AIProviderError(f"HTTP request to Hugging Face embedding API failed: {str(exc)}") from exc
