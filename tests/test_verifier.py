"""Tests for claim verifier module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from uradori.models import Claim, Source, Verdict
from uradori.verifier import verify_claim


class TestVerifyClaim:
    """Tests for verify_claim function."""

    def _make_claim(self) -> Claim:
        return Claim(text="GDP grew 3%", original_sentence="GDP grew 3% last year", claim_index=0)

    def _make_sources(self) -> list[Source]:
        return [
            Source(title="Source 1", url="https://ex.com/1", snippet="GDP grew 3%"),
            Source(title="Source 2", url="https://ex.com/2", snippet="Economic growth"),
        ]

    def test_no_sources_returns_unverified(self) -> None:
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = verify_claim(self._make_claim(), [])

        assert result.verdict == Verdict.UNVERIFIED
        assert result.confidence_score == 30

    def test_missing_api_key_raises(self) -> None:
        with patch.dict("os.environ", {}, clear=True), pytest.raises(
            ValueError, match="ANTHROPIC_API_KEY"
        ):
            verify_claim(self._make_claim(), self._make_sources())

    @patch("uradori.verifier.anthropic.Anthropic")
    def test_successful_verification(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text="""{
                    "verdict": "VERIFIED",
                    "confidence_score": 85,
                    "explanation": "Multiple sources confirm GDP growth of 3%.",
                    "contradictions": [],
                    "source_assessments": [
                        {"url": "https://ex.com/1", "supports_claim": true}
                    ]
                }"""
            )
        ]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = verify_claim(self._make_claim(), self._make_sources())

        assert result.verdict == Verdict.VERIFIED
        assert result.confidence_score == 85
        assert "GDP" in result.explanation

    @patch("uradori.verifier.anthropic.Anthropic")
    def test_invalid_json_fallback(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = verify_claim(self._make_claim(), self._make_sources())

        assert result.verdict == Verdict.UNVERIFIED
        assert result.confidence_score == 20

    @patch("uradori.verifier.anthropic.Anthropic")
    def test_disputed_verdict(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text="""{
                    "verdict": "DISPUTED",
                    "confidence_score": 35,
                    "explanation": "Sources disagree.",
                    "contradictions": ["Source A says 3%, Source B says 2%"],
                    "source_assessments": []
                }"""
            )
        ]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = verify_claim(self._make_claim(), self._make_sources())

        assert result.verdict == Verdict.DISPUTED
        assert len(result.contradictions) == 1
