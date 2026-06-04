"""Groq generation service wrapper."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class GroqClientService:
    """Groq LLM generation service."""

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        api_key: Optional[str] = None,
    ):
        """Initialize Groq client service.

        Args:
            model: Groq model identifier.
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.

        Raises:
            ValueError: If API key is not provided and GROQ_API_KEY env var not set.
        """
        self.model = model

        if api_key is None:
            api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            logger.error("GROQ_API_KEY not provided and not in environment")
            raise ValueError("GROQ_API_KEY must be provided or set in environment")

        try:
            from groq import Groq

            self.client = Groq(api_key=api_key)
            logger.info(f"Groq client initialized with model: {model}")
        except ImportError:
            logger.error("groq library not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Generate text using Groq.

        Args:
            system_prompt: System instruction for the model.
            user_prompt: User input/query.
            temperature: Sampling temperature (0.0-2.0). Default 0.2 for deterministic.
            max_tokens: Maximum tokens in response.

        Returns:
            Generated text response.

        Raises:
            ValueError: If inputs are invalid.
            Exception: If Groq API call fails.
        """
        if not system_prompt or not isinstance(system_prompt, str):
            logger.error(f"Invalid system_prompt: {system_prompt}")
            raise ValueError("system_prompt must be a non-empty string")

        if not user_prompt or not isinstance(user_prompt, str):
            logger.error(f"Invalid user_prompt: {user_prompt}")
            raise ValueError("user_prompt must be a non-empty string")

        if not (0.0 <= temperature <= 2.0):
            logger.error(f"Invalid temperature: {temperature}")
            raise ValueError("temperature must be between 0.0 and 2.0")

        try:
            logger.debug(f"Generating with model={self.model}, temp={temperature}, max_tokens={max_tokens}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            generated_text = response.choices[0].message.content

            logger.info(f"Generation succeeded, response length: {len(generated_text)}")
            return generated_text

        except ValueError as e:
            logger.error(f"Validation error in generate: {e}")
            raise
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
