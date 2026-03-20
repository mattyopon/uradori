"""CLI interface for Uradori fact-checking tool."""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console

from uradori import __version__
from uradori.display import display_report
from uradori.pipeline import check_article, check_url

console = Console()


def _is_url(text: str) -> bool:
    """Check if the input looks like a URL."""
    return text.startswith(("http://", "https://"))


def _progress_callback(msg: str) -> None:
    """Print progress messages."""
    console.print(f"  [dim]{msg}[/dim]")


@click.group()
@click.version_option(version=__version__, prog_name="uradori")
def main() -> None:
    """Uradori (裏どり) - AI-powered news fact-checking tool.

    Verify the credibility of news articles by extracting claims
    and cross-referencing them with web sources.
    """


@main.command()
@click.argument("input_text")
@click.option("--model", "-m", default="claude-sonnet-4-20250514", help="Claude model to use")
@click.option("--output", "-o", type=click.Path(), help="Save JSON report to file")
@click.option("--json-only", is_flag=True, help="Output only JSON (no rich display)")
def check(input_text: str, model: str, output: str | None, json_only: bool) -> None:
    """Fact-check a news article.

    INPUT_TEXT can be a URL or article text.
    For multi-line text, pipe it in or use quotes.

    Examples:

        uradori check https://example.com/news/article

        uradori check "The company announced record profits of $5B"

        cat article.txt | uradori check -
    """
    # Handle stdin
    if input_text == "-":
        input_text = sys.stdin.read()

    if not json_only:
        console.print()
        console.print("[bold magenta]裏どり[/bold magenta] [bold]Uradori Fact-Checker[/bold]")
        console.print("[dim]Verifying claims against web sources...[/dim]")
        console.print()

    try:
        if _is_url(input_text):
            report = check_url(
                url=input_text,
                model=model,
                on_progress=None if json_only else _progress_callback,
            )
        else:
            report = check_article(
                article_text=input_text,
                model=model,
                on_progress=None if json_only else _progress_callback,
            )
    except Exception as e:
        if json_only:
            click.echo(json.dumps({"error": str(e)}), err=True)
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    # Display report
    if not json_only:
        display_report(report)

    # JSON output
    report_dict = report.to_dict()

    if json_only:
        click.echo(json.dumps(report_dict, ensure_ascii=False, indent=2))

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        if not json_only:
            console.print(f"[green]Report saved to {output}[/green]")


if __name__ == "__main__":
    main()
