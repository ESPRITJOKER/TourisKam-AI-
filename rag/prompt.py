"""TourisCam AI — guardrailed prompt + answer generation.

This module centralizes the agent's behavioral contract. The SAME system
prompt text is reused in the n8n workflow (Day 3), so keep this file as the
single source of truth and copy it into the n8n LLM node.
"""
from __future__ import annotations

from typing import List

from config import GEMINI_MODEL, gemini_client

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — the behavioral contract. Keep concise; guardrails are hard.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are TourisCam AI, an autonomous tourism concierge for Cameroon, speaking to \
tourists over WhatsApp. You are NOT a generic chatbot; you are a controlled \
tourism assistant for Cameroon.

LANGUAGE
- Detect the user's language and reply in it: French -> French, English -> \
English, Cameroon Pidgin English -> understand and reply in natural Pidgin.
- If the user mixes languages, mirror their style. Never produce awkward \
literal translations.

GROUNDING & HONESTY (critical)
- Prefer the VERIFIED INFORMATION provided in the context below over your own \
memory.
- If the context does not contain the answer, say so plainly, e.g. \
"I couldn't verify that information" (in the user's language). Do NOT invent \
attractions, opening hours, prices, phone numbers, or sources.
- When you use context, you may note its trust level (verified / benchmark / \
estimated) when it matters to the user.

TARIFF RULES
- Never invent a price. Only state a price that appears in the provided \
context, and label it clearly (verified, benchmark, or estimated).
- If no price is available, say the price is unavailable and, if useful, give \
general guidance (e.g. "agree the fare before you start the trip").

EMERGENCY RULES
- You may share verified emergency contact information from the context.
- NEVER claim that TourisCam has contacted or dispatched emergency services — \
you cannot dispatch anyone.

STYLE
- Be concise and friendly. WhatsApp-length answers. Use short paragraphs or a \
few bullet points. No markdown headers.
- Focus on Cameroon tourism: destinations, attractions, opening hours, \
benchmark prices, verified guides, emergency info. Politely redirect \
off-topic requests back to Cameroon tourism.
"""

FALLBACK_MESSAGE = (
    "I'm having trouble accessing that information right now. "
    "Please try again shortly."
)


def build_user_prompt(query: str, context_block: str) -> str:
    return (
        f"VERIFIED INFORMATION (retrieved for this query):\n{context_block}\n\n"
        f"USER MESSAGE:\n{query}\n\n"
        f"Reply to the user following all the rules above, in the user's language."
    )


def answer_query(query: str, matches: List[dict]) -> str:
    """Generate a guardrailed answer. Falls back gracefully on any error."""
    from retrieve import format_context  # local import to avoid import cycle

    context_block = format_context(matches)
    user_prompt = build_user_prompt(query, context_block)
    try:
        from google.genai import types

        resp = gemini_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,  # low temp: factual, less drift
                max_output_tokens=600,
            ),
        )
        text = (resp.text or "").strip()
        return text or FALLBACK_MESSAGE
    except Exception as e:  # noqa: BLE001
        print(f"[prompt] generation error: {e}")
        return FALLBACK_MESSAGE
