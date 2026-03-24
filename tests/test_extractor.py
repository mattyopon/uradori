# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for claim extractor module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from uradori.extractor import extract_claims
from uradori.models import Claim


class TestExtractClaims:
    """Tests for extract_claims function."""

    def test_missing_api_key_raises(self) -> None:
        with patch.dict("os.environ", {}, clear=True), pytest.raises(
            ValueError, match="ANTHROPIC_API_KEY"
        ):
            extract_claims("Some article text")

    @patch("uradori.extractor.anthropic.Anthropic")
    def test_successful_extraction(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='[{"text": "GDP grew 3%", "original_sentence": "The GDP grew 3% last year."}]'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            claims = extract_claims("The GDP grew 3% last year.")

        assert len(claims) == 1
        assert isinstance(claims[0], Claim)
        assert claims[0].text == "GDP grew 3%"
        assert claims[0].claim_index == 0

    @patch("uradori.extractor.anthropic.Anthropic")
    def test_markdown_wrapped_json(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='```json\n[{"text": "claim", "original_sentence": "src"}]\n```'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            claims = extract_claims("text")

        assert len(claims) == 1
        assert claims[0].text == "claim"

    @patch("uradori.extractor.anthropic.Anthropic")
    def test_invalid_json_raises(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not json at all")]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}), pytest.raises(
            ValueError, match="Failed to parse"
        ):
            extract_claims("text")

    @patch("uradori.extractor.anthropic.Anthropic")
    def test_empty_claims_array(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="[]")]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            claims = extract_claims("An opinion article with no facts.")

        assert claims == []

    @patch("uradori.extractor.anthropic.Anthropic")
    def test_truncates_long_articles(self, mock_anthropic_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="[]")]
        mock_client.messages.create.return_value = mock_response

        long_text = "A" * 20000

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            extract_claims(long_text)

        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]["messages"][0]["content"]
        # Should be truncated - the prompt template + 15000 chars
        assert len(prompt) < 20000
