"""Data models for Uradori fact-checking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Verdict(StrEnum):
    """Verdict category for a claim."""

    VERIFIED = "VERIFIED"
    LIKELY_TRUE = "LIKELY_TRUE"
    UNVERIFIED = "UNVERIFIED"
    DISPUTED = "DISPUTED"
    FALSE = "FALSE"


@dataclass(frozen=True)
class Claim:
    """A single factual claim extracted from an article."""

    text: str
    original_sentence: str
    claim_index: int


@dataclass
class Source:
    """A source found during web search verification."""

    title: str
    url: str
    snippet: str
    supports_claim: bool | None = None


@dataclass
class ClaimVerification:
    """Verification result for a single claim."""

    claim: Claim
    verdict: Verdict
    confidence_score: int  # 0-100
    explanation: str
    sources: list[Source] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)


@dataclass
class FactCheckReport:
    """Full fact-check report for an article."""

    article_title: str
    article_url: str | None
    article_text: str
    overall_score: int  # 0-100
    claim_count: int
    verified_count: int
    disputed_count: int
    false_count: int
    unverified_count: int
    claims: list[ClaimVerification] = field(default_factory=list)
    summary: str = ""
    concerns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "article_title": self.article_title,
            "article_url": self.article_url,
            "overall_score": self.overall_score,
            "summary": self.summary,
            "statistics": {
                "total_claims": self.claim_count,
                "verified": self.verified_count,
                "disputed": self.disputed_count,
                "false": self.false_count,
                "unverified": self.unverified_count,
            },
            "concerns": self.concerns,
            "claims": [
                {
                    "text": cv.claim.text,
                    "original_sentence": cv.claim.original_sentence,
                    "verdict": cv.verdict.value,
                    "confidence_score": cv.confidence_score,
                    "explanation": cv.explanation,
                    "sources": [
                        {
                            "title": s.title,
                            "url": s.url,
                            "snippet": s.snippet,
                            "supports_claim": s.supports_claim,
                        }
                        for s in cv.sources
                    ],
                    "contradictions": cv.contradictions,
                }
                for cv in self.claims
            ],
        }
