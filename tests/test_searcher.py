"""Tests for web searcher module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from uradori.models import Source
from uradori.searcher import search_claim, search_claim_news


class TestSearchClaim:
    """Tests for search_claim function."""

    @patch("uradori.searcher.DDGS")
    def test_returns_sources(self, mock_ddgs_class: MagicMock) -> None:
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "snippet 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "snippet 2"},
        ]
        mock_ddgs_class.return_value = mock_ddgs

        sources = search_claim("test query")

        assert len(sources) == 2
        assert isinstance(sources[0], Source)
        assert sources[0].title == "Result 1"
        assert sources[0].url == "https://example.com/1"
        assert sources[0].snippet == "snippet 1"

    @patch("uradori.searcher.DDGS")
    def test_handles_exception(self, mock_ddgs_class: MagicMock) -> None:
        mock_ddgs_class.side_effect = Exception("Network error")
        sources = search_claim("test query")
        assert sources == []

    @patch("uradori.searcher.DDGS")
    def test_max_results(self, mock_ddgs_class: MagicMock) -> None:
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []
        mock_ddgs_class.return_value = mock_ddgs

        search_claim("test", max_results=3)

        mock_ddgs.text.assert_called_once_with(
            keywords="test",
            max_results=3,
            safesearch="moderate",
        )


class TestSearchClaimNews:
    """Tests for search_claim_news function."""

    @patch("uradori.searcher.DDGS")
    def test_returns_news_sources(self, mock_ddgs_class: MagicMock) -> None:
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.news.return_value = [
            {"title": "News 1", "url": "https://news.com/1", "body": "news snippet"},
        ]
        mock_ddgs_class.return_value = mock_ddgs

        sources = search_claim_news("test query")

        assert len(sources) == 1
        assert sources[0].title == "News 1"

    @patch("uradori.searcher.DDGS")
    def test_handles_exception(self, mock_ddgs_class: MagicMock) -> None:
        mock_ddgs_class.side_effect = Exception("Error")
        sources = search_claim_news("test query")
        assert sources == []
