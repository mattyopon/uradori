"""Claim verification module using Claude API."""

from __future__ import annotations

import json
import os

import anthropic

from uradori.models import Claim, ClaimVerification, Source, Verdict

_VERIFICATION_PROMPT = """\
You are a rigorous fact-checker. Evaluate the following claim based on the provided \
search results (evidence). Be conservative — only mark as VERIFIED if strong evidence supports it.

Claim: {claim_text}

Evidence from web search:
{evidence}

Evaluate the claim and return a JSON object with:
- "verdict": one of "VERIFIED", "LIKELY_TRUE", "UNVERIFIED", "DISPUTED", "FALSE"
- "confidence_score": integer 0-100 (how confident you are in the verdict)
- "explanation": brief explanation of your verdict (2-3 sentences)
- "contradictions": array of strings listing any contradictions found (empty if none)
- "source_assessments": array of objects with "url" and "supports_claim" (true/false/null)

Scoring guide:
- VERIFIED (80-100): Multiple independent reliable sources confirm the claim
- LIKELY_TRUE (60-79): Some evidence supports it, no contradictions found
- UNVERIFIED (40-59): Insufficient evidence to confirm or deny
- DISPUTED (20-39): Conflicting evidence or credible sources disagree
- FALSE (0-19): Strong evidence contradicts the claim

Return ONLY valid JSON.
"""


def verify_claim(
    claim: Claim,
    sources: list[Source],
    model: str = "claude-sonnet-4-20250514",
) -> ClaimVerification:
    """Verify a claim against collected evidence using Claude API.

    Args:
        claim: The claim to verify.
        sources: Sources found during web search.
        model: Claude model to use for evaluation.

    Returns:
        ClaimVerification with verdict and explanation.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    # If no sources found, return UNVERIFIED
    if not sources:
        return ClaimVerification(
            claim=claim,
            verdict=Verdict.UNVERIFIED,
            confidence_score=30,
            explanation="No relevant sources found through web search to verify this claim.",
            sources=[],
            contradictions=[],
        )

    # Format evidence for the prompt
    evidence_parts: list[str] = []
    for i, source in enumerate(sources, 1):
        evidence_parts.append(
            f"[Source {i}] {source.title}\n"
            f"URL: {source.url}\n"
            f"Content: {source.snippet}\n"
        )
    evidence_text = "\n".join(evidence_parts)

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": _VERIFICATION_PROMPT.format(
                    claim_text=claim.text,
                    evidence=evidence_text,
                ),
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Parse JSON from response
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            if in_block:
                json_lines.append(line)
        response_text = "\n".join(json_lines)

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback if parsing fails
        return ClaimVerification(
            claim=claim,
            verdict=Verdict.UNVERIFIED,
            confidence_score=20,
            explanation="Failed to parse verification result.",
            sources=sources,
            contradictions=[],
        )

    # Map verdict string to enum
    verdict_str = result.get("verdict", "UNVERIFIED")
    try:
        verdict = Verdict(verdict_str)
    except ValueError:
        verdict = Verdict.UNVERIFIED

    # Update source support info from assessments
    assessments = result.get("source_assessments", [])
    for assessment in assessments:
        url = assessment.get("url", "")
        supports = assessment.get("supports_claim")
        for source in sources:
            if source.url == url:
                source.supports_claim = supports

    return ClaimVerification(
        claim=claim,
        verdict=verdict,
        confidence_score=result.get("confidence_score", 50),
        explanation=result.get("explanation", ""),
        sources=sources,
        contradictions=result.get("contradictions", []),
    )
