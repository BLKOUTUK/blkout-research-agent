"""
LLM Client - Groq integration with fallbacks
"""

import os
import json
from typing import Optional, List, Dict, Any
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMClient:
    """Unified LLM client using Groq free tier"""

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.default_model = "llama-3.3-70b-versatile"
        self.fast_model = "llama-3.1-8b-instant"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """Generate completion from LLM"""
        model = model or self.default_model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def complete_json(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate JSON completion"""
        result = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt + "\n\nRespond with valid JSON only.",
            model=model,
            json_mode=True,
        )
        return json.loads(result)

    async def analyze_relevance(
        self,
        title: str,
        content: str,
        source: str,
        url: str,
    ) -> Dict[str, Any]:
        """Analyze content relevance to BLKOUT community"""
        system_prompt = """You are a relevance scoring agent for the BLKOUT community platform.
Score content relevance to Black LGBTQ+ people in the UK from 0-100.

90-100: Explicitly Black LGBTQ+ UK content
70-89: Strong intersectional relevance
50-69: Moderate relevance
0-49: Low or no relevance

Return JSON with:
- relevance_score: number 0-100
- reasoning: brief explanation
- recommended_action: "publish" | "review" | "skip"
- suggested_tags: list of tags
- suggested_category: "news" | "culture" | "health" | "community" | "politics" | "events"
"""

        prompt = f"""Analyze this content:

Title: {title}
Source: {source}
Content: {content[:1000]}
URL: {url}

Return relevance analysis as JSON."""

        return await self.complete_json(prompt, system_prompt, model=self.fast_model)

    async def extract_event_data(self, raw_html: str, url: str) -> Dict[str, Any]:
        """Extract structured event data from HTML"""
        system_prompt = """Extract event information from this webpage content.
Return JSON with:
- name: event title
- date: ISO date string
- venue: venue name
- address: full address
- city: city name
- price: ticket price or "Free"
- description: brief description
- organizer: who's running it
- event_type: "party" | "community" | "cultural" | "health" | "pride"
- tags: relevant tags list

If information is not found, use null."""

        prompt = f"""Extract event data from this content:

URL: {url}
Content: {raw_html[:3000]}

Return structured event data as JSON."""

        return await self.complete_json(prompt, system_prompt, model=self.fast_model)


# Singleton instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
