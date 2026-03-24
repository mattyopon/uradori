# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Rich terminal display for fact-check results."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from uradori.models import FactCheckReport, Verdict

console = Console()

_VERDICT_COLORS: dict[Verdict, str] = {
    Verdict.VERIFIED: "green",
    Verdict.LIKELY_TRUE: "cyan",
    Verdict.UNVERIFIED: "yellow",
    Verdict.DISPUTED: "dark_orange",
    Verdict.FALSE: "red",
}

_VERDICT_EMOJI: dict[Verdict, str] = {
    Verdict.VERIFIED: "[green]✓[/green]",
    Verdict.LIKELY_TRUE: "[cyan]○[/cyan]",
    Verdict.UNVERIFIED: "[yellow]?[/yellow]",
    Verdict.DISPUTED: "[dark_orange]△[/dark_orange]",
    Verdict.FALSE: "[red]✗[/red]",
}


def _score_color(score: int) -> str:
    """Get color based on score."""
    if score >= 80:
        return "green"
    if score >= 60:
        return "cyan"
    if score >= 40:
        return "yellow"
    if score >= 20:
        return "dark_orange"
    return "red"


def display_report(report: FactCheckReport) -> None:
    """Display a fact-check report in the terminal with rich formatting."""
    console.print()

    # Header
    title_text = report.article_title or "Unknown Article"
    score_color = _score_color(report.overall_score)

    header = Text()
    header.append("裏どり ", style="bold magenta")
    header.append("Fact-Check Report", style="bold white")

    console.print(Panel(header, border_style="magenta"))
    console.print()

    # Article info
    console.print(f"[bold]Article:[/bold] {title_text}")
    if report.article_url:
        console.print(f"[bold]URL:[/bold] {report.article_url}")
    console.print()

    # Overall score
    score_display = f"[bold {score_color}]{report.overall_score}/100[/bold {score_color}]"
    console.print(Panel(
        f"Overall Credibility Score: {score_display}",
        title="Score",
        border_style=score_color,
    ))
    console.print()

    # Summary
    if report.summary:
        console.print(Panel(report.summary, title="Summary", border_style="blue"))
        console.print()

    # Claims table
    if report.claims:
        table = Table(title="Claim Verification Details", show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Claim", width=50)
        table.add_column("Verdict", width=14)
        table.add_column("Score", width=6)
        table.add_column("Sources", width=8)

        for i, cv in enumerate(report.claims, 1):
            verdict_color = _VERDICT_COLORS.get(cv.verdict, "white")
            emoji = _VERDICT_EMOJI.get(cv.verdict, "")
            table.add_row(
                str(i),
                cv.claim.text[:80] + ("..." if len(cv.claim.text) > 80 else ""),
                f"{emoji} [{verdict_color}]{cv.verdict.value}[/{verdict_color}]",
                f"[{_score_color(cv.confidence_score)}]{cv.confidence_score}[/{_score_color(cv.confidence_score)}]",
                str(len(cv.sources)),
            )

        console.print(table)
        console.print()

    # Detailed results
    for i, cv in enumerate(report.claims, 1):
        verdict_color = _VERDICT_COLORS.get(cv.verdict, "white")
        emoji = _VERDICT_EMOJI.get(cv.verdict, "")

        console.print(
            f"[bold]Claim #{i}:[/bold] {cv.claim.text}"
        )
        console.print(
            f"  {emoji} [{verdict_color}]{cv.verdict.value}[/{verdict_color}] "
            f"(confidence: {cv.confidence_score}/100)"
        )
        console.print(f"  [dim]{cv.explanation}[/dim]")

        if cv.sources:
            console.print("  [bold]Sources:[/bold]")
            for src in cv.sources[:3]:
                support = ""
                if src.supports_claim is True:
                    support = " [green](supports)[/green]"
                elif src.supports_claim is False:
                    support = " [red](contradicts)[/red]"
                console.print(f"    - {src.title}{support}")
                console.print(f"      [dim]{src.url}[/dim]")

        if cv.contradictions:
            console.print("  [bold red]Contradictions:[/bold red]")
            for contradiction in cv.contradictions:
                console.print(f"    [red]! {contradiction}[/red]")

        console.print()

    # Concerns
    if report.concerns:
        console.print(Panel(
            "\n".join(f"[dark_orange]! {c}[/dark_orange]" for c in report.concerns),
            title="[bold]Concerns & Warnings[/bold]",
            border_style="dark_orange",
        ))
        console.print()

    # Statistics
    stats_table = Table(title="Statistics")
    stats_table.add_column("Category", style="bold")
    stats_table.add_column("Count")
    stats_table.add_row("Total Claims", str(report.claim_count))
    stats_table.add_row("[green]Verified[/green]", str(report.verified_count))
    stats_table.add_row("[dark_orange]Disputed[/dark_orange]", str(report.disputed_count))
    stats_table.add_row("[red]False[/red]", str(report.false_count))
    stats_table.add_row("[yellow]Unverified[/yellow]", str(report.unverified_count))
    console.print(stats_table)
    console.print()
