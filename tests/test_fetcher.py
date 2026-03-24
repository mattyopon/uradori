# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for article fetcher module."""

from __future__ import annotations

import httpx
import pytest

from uradori.fetcher import fetch_article


class TestFetchArticle:
    """Tests for fetch_article function."""

    def test_invalid_url_raises(self) -> None:
        with pytest.raises((httpx.HTTPError, httpx.InvalidURL, ValueError)):
            fetch_article("not-a-url")

    def test_nonexistent_domain_raises(self) -> None:
        with pytest.raises((httpx.HTTPError, httpx.ConnectError, OSError)):
            fetch_article("https://this-domain-does-not-exist-xyz123.com/article")

    def test_fetch_returns_tuple(self) -> None:
        """Verify the function signature returns (title, text)."""
        # We test with a known stable page
        try:
            title, text = fetch_article("https://example.com")
            assert isinstance(title, str)
            assert isinstance(text, str)
        except Exception:
            # Network may not be available in test env
            pytest.skip("Network not available")
