"""
Keywords AI Client

Unified LLM client that routes all AI calls through Keywords AI gateway.
Provides logging, cost tracking, caching, and provider fallback capabilities.

Keywords AI acts as an OpenAI-compatible proxy, making it easy to switch
between providers (OpenAI, Anthropic, Perplexity, etc.) without code changes.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path
import requests

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

KEYWORDS_API_KEY = os.getenv("KEYWORDS_API_KEY")
KEYWORDS_BASE_URL = "https://api.keywordsai.co/api/chat/completions"


class KeywordsAIClient:
    """
    Unified client for LLM calls through Keywords AI gateway.

    Keywords AI provides:
    - Unified API across multiple LLM providers
    - Request logging and analytics
    - Cost tracking and budgeting
    - Caching for repeated queries
    - Automatic fallbacks between providers
    """

    def __init__(self, api_key: str = None, default_model: str = "gpt-4o"):
        """
        Initialize the Keywords AI client.

        Args:
            api_key: Keywords AI API key (defaults to KEYWORDS_API_KEY env var)
            default_model: Default model to use for completions
        """
        self.api_key = api_key or KEYWORDS_API_KEY
        self.default_model = default_model
        self.base_url = KEYWORDS_BASE_URL

        if not self.api_key:
            raise ValueError(
                "KEYWORDS_API_KEY not found. Please add it to your .env file. "
                "Get your API key from https://keywordsai.co"
            )

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a request to Keywords AI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            metadata: Custom metadata for logging/tracking
            **kwargs: Additional parameters passed to the API

        Returns:
            API response as dict
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        # Add metadata for tracking if provided
        if metadata:
            payload["metadata"] = metadata

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()

    def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        Simple completion with a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            metadata: Custom metadata for tracking

        Returns:
            Generated text response
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        result = self._make_request(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
            **kwargs
        )

        return result["choices"][0]["message"]["content"]

    def analyze_profile(
        self,
        profile_url: str,
        analysis_prompt: str = None,
        model: str = "perplexity/sonar",
    ) -> Dict[str, Any]:
        """
        Analyze a social media profile using web-enabled model.

        Args:
            profile_url: URL of the profile to analyze
            analysis_prompt: Custom analysis instructions
            model: Model to use (default: perplexity/sonar for web access)

        Returns:
            Dict with analysis results
        """
        default_prompt = """Analyze this professional profile and extract:
1. Current job title and company
2. Years of experience in current role
3. Total professional experience (estimated years)
4. Industry/sector
5. Education level (High School, Bachelor's, Master's, PhD)
6. Career trajectory (declining, stable, growing, rapidly growing)
7. Job stability indicators
8. Professional network strength (if visible)
9. Any red flags or concerns
10. Overall professional assessment

Provide structured, factual information based on publicly available data."""

        prompt = f"""Profile URL: {profile_url}

{analysis_prompt or default_prompt}

Return the analysis in a structured format."""

        system_prompt = """You are a professional profile analyst for mortgage underwriting purposes.
Extract factual, objective information from professional profiles.
Be thorough but concise. Flag any information that could not be verified."""

        try:
            response = self.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=0.2,
                max_tokens=2000,
                metadata={
                    "task": "profile_analysis",
                    "profile_url": profile_url
                }
            )

            return {
                "status": "success",
                "analysis": response,
                "profile_url": profile_url,
                "model": model
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "profile_url": profile_url
            }

    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, Any],
        model: str = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from text according to a schema.

        Args:
            text: Text to extract data from
            schema: JSON schema describing expected output
            model: Model to use

        Returns:
            Extracted data as dict
        """
        prompt = f"""Extract structured data from the following text according to this schema:

Schema:
{json.dumps(schema, indent=2)}

Text:
{text}

Return ONLY valid JSON matching the schema. No explanations or markdown."""

        response = self.complete(
            prompt=prompt,
            system_prompt="You are a data extraction assistant. Extract structured data and return valid JSON only.",
            model=model,
            temperature=0.1,
            max_tokens=2000,
            metadata={"task": "structured_extraction"}
        )

        # Clean response and parse JSON
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    def generate_risk_explanation(
        self,
        risk_score: float,
        features: Dict[str, Any],
        model: str = None
    ) -> str:
        """
        Generate human-readable explanation for a risk score.

        Args:
            risk_score: The calculated risk score (0-100)
            features: Feature dict used in scoring
            model: Model to use

        Returns:
            Human-readable explanation
        """
        prompt = f"""A mortgage loan application received a risk score of {risk_score}/100
(higher = more risky).

The following factors were considered:
{json.dumps(features, indent=2)}

Provide a clear, professional explanation of:
1. What this risk score means
2. Key factors contributing to the score
3. Any concerns or positive indicators
4. Recommendations (if applicable)

Keep the explanation concise and suitable for an underwriting report."""

        return self.complete(
            prompt=prompt,
            system_prompt="You are a mortgage underwriting assistant. Provide clear, professional risk explanations.",
            model=model,
            temperature=0.3,
            max_tokens=1000,
            metadata={"task": "risk_explanation", "risk_score": risk_score}
        )


# Convenience function for quick completions
def complete(prompt: str, **kwargs) -> str:
    """Quick completion using default client."""
    client = KeywordsAIClient()
    return client.complete(prompt, **kwargs)


if __name__ == "__main__":
    # Test the client
    print("Testing Keywords AI Client...")

    try:
        client = KeywordsAIClient()
        response = client.complete(
            "What are the key factors in mortgage underwriting?",
            max_tokens=200
        )
        print("Response:", response)
    except ValueError as e:
        print(f"Setup required: {e}")
    except Exception as e:
        print(f"Error: {e}")
