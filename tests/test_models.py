# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for data models."""

from __future__ import annotations

import json

import pytest

from uradori.models import (
    Claim,
    ClaimVerification,
    FactCheckReport,
    Source,
    Verdict,
)


class TestVerdict:
    """Tests for Verdict enum."""

    def test_all_verdicts_exist(self) -> None:
        assert Verdict.VERIFIED == "VERIFIED"
        assert Verdict.LIKELY_TRUE == "LIKELY_TRUE"
        assert Verdict.UNVERIFIED == "UNVERIFIED"
        assert Verdict.DISPUTED == "DISPUTED"
        assert Verdict.FALSE == "FALSE"

    def test_verdict_from_string(self) -> None:
        assert Verdict("VERIFIED") == Verdict.VERIFIED
        assert Verdict("FALSE") == Verdict.FALSE

    def test_verdict_count(self) -> None:
        assert len(Verdict) == 5


class TestClaim:
    """Tests for Claim dataclass."""

    def test_create_claim(self) -> None:
        claim = Claim(text="Tokyo has 14M people", original_sentence="source", claim_index=0)
        assert claim.text == "Tokyo has 14M people"
        assert claim.claim_index == 0

    def test_claim_is_frozen(self) -> None:
        claim = Claim(text="test", original_sentence="test", claim_index=0)
        with pytest.raises(AttributeError):
            claim.text = "modified"  # type: ignore[misc]


class TestSource:
    """Tests for Source dataclass."""

    def test_create_source(self) -> None:
        source = Source(title="Test", url="https://example.com", snippet="info")
        assert source.supports_claim is None

    def test_source_mutable(self) -> None:
        source = Source(title="Test", url="https://example.com", snippet="info")
        source.supports_claim = True
        assert source.supports_claim is True


class TestClaimVerification:
    """Tests for ClaimVerification."""

    def test_create_verification(self) -> None:
        claim = Claim(text="test claim", original_sentence="test", claim_index=0)
        cv = ClaimVerification(
            claim=claim,
            verdict=Verdict.VERIFIED,
            confidence_score=85,
            explanation="Confirmed by sources",
        )
        assert cv.verdict == Verdict.VERIFIED
        assert cv.confidence_score == 85
        assert cv.sources == []
        assert cv.contradictions == []


class TestFactCheckReport:
    """Tests for FactCheckReport."""

    def _make_report(self) -> FactCheckReport:
        claim = Claim(text="Test claim", original_sentence="Test", claim_index=0)
        source = Source(title="Source", url="https://ex.com", snippet="info", supports_claim=True)
        cv = ClaimVerification(
            claim=claim,
            verdict=Verdict.VERIFIED,
            confidence_score=90,
            explanation="Confirmed",
            sources=[source],
            contradictions=[],
        )
        return FactCheckReport(
            article_title="Test Article",
            article_url="https://example.com/article",
            article_text="Full text here",
            overall_score=85,
            claim_count=1,
            verified_count=1,
            disputed_count=0,
            false_count=0,
            unverified_count=0,
            claims=[cv],
            summary="1 claim verified",
            concerns=[],
        )

    def test_to_dict(self) -> None:
        report = self._make_report()
        d = report.to_dict()
        assert d["article_title"] == "Test Article"
        assert d["overall_score"] == 85
        assert d["statistics"]["total_claims"] == 1
        assert d["statistics"]["verified"] == 1
        assert len(d["claims"]) == 1
        assert d["claims"][0]["verdict"] == "VERIFIED"

    def test_to_dict_serializable(self) -> None:
        report = self._make_report()
        d = report.to_dict()
        # Must be JSON serializable
        json_str = json.dumps(d, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["article_title"] == "Test Article"

    def test_empty_report(self) -> None:
        report = FactCheckReport(
            article_title="Empty",
            article_url=None,
            article_text="",
            overall_score=50,
            claim_count=0,
            verified_count=0,
            disputed_count=0,
            false_count=0,
            unverified_count=0,
        )
        d = report.to_dict()
        assert d["claims"] == []
        assert d["article_url"] is None
