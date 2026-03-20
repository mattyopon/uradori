"""Tests for the fact-checking pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from uradori.models import Claim, ClaimVerification, Source, Verdict
from uradori.pipeline import _compute_overall_score, _generate_summary, check_article


class TestComputeOverallScore:
    """Tests for overall score computation."""

    def test_empty_returns_50(self) -> None:
        assert _compute_overall_score([]) == 50

    def test_single_verified(self) -> None:
        cv = ClaimVerification(
            claim=Claim(text="t", original_sentence="s", claim_index=0),
            verdict=Verdict.VERIFIED,
            confidence_score=90,
            explanation="ok",
        )
        score = _compute_overall_score([cv])
        assert score == 90

    def test_false_claim_penalty(self) -> None:
        cv = ClaimVerification(
            claim=Claim(text="t", original_sentence="s", claim_index=0),
            verdict=Verdict.FALSE,
            confidence_score=10,
            explanation="wrong",
        )
        score = _compute_overall_score([cv])
        # 10 - 15 penalty = -5, clamped to 0
        assert score == 0

    def test_mixed_claims(self) -> None:
        claims = [
            ClaimVerification(
                claim=Claim(text="t1", original_sentence="s", claim_index=0),
                verdict=Verdict.VERIFIED,
                confidence_score=90,
                explanation="ok",
            ),
            ClaimVerification(
                claim=Claim(text="t2", original_sentence="s", claim_index=1),
                verdict=Verdict.DISPUTED,
                confidence_score=30,
                explanation="disputed",
            ),
        ]
        score = _compute_overall_score(claims)
        # avg = 60, disputed penalty = 8 -> 52
        assert score == 52

    def test_score_capped_at_100(self) -> None:
        cv = ClaimVerification(
            claim=Claim(text="t", original_sentence="s", claim_index=0),
            verdict=Verdict.VERIFIED,
            confidence_score=100,
            explanation="ok",
        )
        assert _compute_overall_score([cv]) <= 100


class TestGenerateSummary:
    """Tests for summary generation."""

    def test_no_claims_summary(self) -> None:
        from uradori.models import FactCheckReport

        report = FactCheckReport(
            article_title="t",
            article_url=None,
            article_text="",
            overall_score=50,
            claim_count=0,
            verified_count=0,
            disputed_count=0,
            false_count=0,
            unverified_count=0,
        )
        summary = _generate_summary(report)
        assert "No verifiable" in summary


class TestCheckArticle:
    """Tests for the main check_article pipeline."""

    @patch("uradori.pipeline.verify_claim")
    @patch("uradori.pipeline.search_claim_news")
    @patch("uradori.pipeline.search_claim")
    @patch("uradori.pipeline.extract_claims")
    def test_full_pipeline(
        self,
        mock_extract: MagicMock,
        mock_search: MagicMock,
        mock_search_news: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        claim = Claim(text="Test fact", original_sentence="Test", claim_index=0)
        mock_extract.return_value = [claim]
        mock_search.return_value = [
            Source(title="S1", url="https://ex.com/1", snippet="info")
        ]
        mock_search_news.return_value = []
        mock_verify.return_value = ClaimVerification(
            claim=claim,
            verdict=Verdict.VERIFIED,
            confidence_score=85,
            explanation="Confirmed",
            sources=[Source(title="S1", url="https://ex.com/1", snippet="info")],
        )

        progress_msgs: list[str] = []
        report = check_article(
            "Test article text",
            on_progress=progress_msgs.append,
        )

        assert report.claim_count == 1
        assert report.verified_count == 1
        assert report.overall_score > 0
        assert len(progress_msgs) > 0
        assert report.summary != ""

    @patch("uradori.pipeline.extract_claims")
    def test_no_claims_found(self, mock_extract: MagicMock) -> None:
        mock_extract.return_value = []

        report = check_article("Opinion piece with no facts")

        assert report.claim_count == 0
        assert report.overall_score == 50
