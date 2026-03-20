"""Tests for CLI interface."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from uradori.cli import _is_url, main


class TestIsUrl:
    """Tests for URL detection."""

    def test_http_url(self) -> None:
        assert _is_url("http://example.com") is True

    def test_https_url(self) -> None:
        assert _is_url("https://example.com/article") is True

    def test_plain_text(self) -> None:
        assert _is_url("The GDP grew 3% last year") is False

    def test_empty_string(self) -> None:
        assert _is_url("") is False


class TestCli:
    """Tests for CLI commands."""

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "裏どり" in result.output

    def test_check_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["check", "--help"])
        assert result.exit_code == 0
        assert "INPUT_TEXT" in result.output

    @patch("uradori.cli.check_article")
    def test_check_text(self, mock_check: MagicMock) -> None:
        from uradori.models import FactCheckReport

        mock_check.return_value = FactCheckReport(
            article_title="Test",
            article_url=None,
            article_text="text",
            overall_score=75,
            claim_count=0,
            verified_count=0,
            disputed_count=0,
            false_count=0,
            unverified_count=0,
            summary="No claims",
        )

        runner = CliRunner()
        result = runner.invoke(main, ["check", "Some article text"])
        assert result.exit_code == 0

    @patch("uradori.cli.check_article")
    def test_check_json_only(self, mock_check: MagicMock) -> None:
        from uradori.models import FactCheckReport

        mock_check.return_value = FactCheckReport(
            article_title="Test",
            article_url=None,
            article_text="text",
            overall_score=75,
            claim_count=0,
            verified_count=0,
            disputed_count=0,
            false_count=0,
            unverified_count=0,
        )

        runner = CliRunner()
        result = runner.invoke(main, ["check", "--json-only", "Some text"])
        assert result.exit_code == 0
        assert '"overall_score"' in result.output
