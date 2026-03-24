# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Claim extraction module using Claude API."""

from __future__ import annotations

import json
import os

import anthropic

from uradori.models import Claim

_EXTRACTION_PROMPT = """\
You are a fact-checking assistant. Analyze the following news article and extract \
all factual claims that can be independently verified.

Rules:
1. Extract ONLY factual claims (not opinions, predictions, or subjective statements).
2. Each claim should be a single, specific, verifiable statement.
3. Include numbers, dates, names, and specific facts.
4. Ignore quotes that are opinions.
5. Return a JSON array of objects with "text" (the claim) \
and "original_sentence" (the source sentence).

Article:
{article_text}

Return ONLY a valid JSON array. Example format:
[
  {{"text": "Tokyo population exceeded 14 million in 2024", \
"original_sentence": "The capital surpassed 14 million last year."}},
  {{"text": "The company reported revenue of $5 billion", \
"original_sentence": "Revenue hit $5B in Q3, beating expectations."}}
]
"""


def extract_claims(article_text: str, model: str = "claude-sonnet-4-20250514") -> list[Claim]:
    """Extract factual claims from article text using Claude API.

    Args:
        article_text: The full text of the article.
        model: Claude model to use.

    Returns:
        List of extracted Claims.

    Raises:
        anthropic.APIError: If the API call fails.
        ValueError: If the response cannot be parsed.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Truncate very long articles to fit context
    max_chars = 15000
    truncated = article_text[:max_chars] if len(article_text) > max_chars else article_text

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": _EXTRACTION_PROMPT.format(article_text=truncated),
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Try to extract JSON from the response
    # Handle cases where the model wraps JSON in markdown code blocks
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
        raw_claims = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse claims from Claude response: {e}") from e

    if not isinstance(raw_claims, list):
        raise ValueError("Expected a JSON array of claims")

    claims: list[Claim] = []
    for i, item in enumerate(raw_claims):
        if isinstance(item, dict) and "text" in item:
            claims.append(
                Claim(
                    text=item["text"],
                    original_sentence=item.get("original_sentence", item["text"]),
                    claim_index=i,
                )
            )

    return claims
