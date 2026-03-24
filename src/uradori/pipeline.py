# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Main fact-checking pipeline orchestrating all modules."""

from __future__ import annotations

from collections.abc import Callable

from uradori.extractor import extract_claims
from uradori.fetcher import fetch_article
from uradori.models import ClaimVerification, FactCheckReport, Verdict
from uradori.searcher import search_claim, search_claim_news
from uradori.verifier import verify_claim


def _compute_overall_score(verifications: list[ClaimVerification]) -> int:
    """Compute overall article score from individual claim scores."""
    if not verifications:
        return 50  # No claims = neutral

    total = sum(v.confidence_score for v in verifications)
    base_score = total // len(verifications)

    # Penalty for FALSE or DISPUTED claims
    false_count = sum(1 for v in verifications if v.verdict == Verdict.FALSE)
    disputed_count = sum(1 for v in verifications if v.verdict == Verdict.DISPUTED)

    penalty = false_count * 15 + disputed_count * 8
    return max(0, min(100, base_score - penalty))


def _generate_summary(report: FactCheckReport) -> str:
    """Generate a human-readable summary of the report."""
    parts: list[str] = []

    if report.claim_count == 0:
        return "No verifiable factual claims were found in this article."

    parts.append(
        f"Analyzed {report.claim_count} factual claim(s) from the article."
    )

    if report.verified_count > 0:
        parts.append(f"{report.verified_count} claim(s) were verified by multiple sources.")

    likely_true = sum(
        1 for c in report.claims if c.verdict == Verdict.LIKELY_TRUE
    )
    if likely_true > 0:
        parts.append(f"{likely_true} claim(s) are likely true based on available evidence.")

    if report.disputed_count > 0:
        parts.append(f"{report.disputed_count} claim(s) have conflicting evidence.")

    if report.false_count > 0:
        parts.append(f"{report.false_count} claim(s) appear to be FALSE.")

    if report.unverified_count > 0:
        parts.append(f"{report.unverified_count} claim(s) could not be verified.")

    return " ".join(parts)


def check_article(
    article_text: str,
    article_url: str | None = None,
    article_title: str = "",
    model: str = "claude-sonnet-4-20250514",
    on_progress: Callable[[str], None] | None = None,
) -> FactCheckReport:
    """Run the full fact-checking pipeline on an article.

    Args:
        article_text: The full text of the article to check.
        article_url: Optional URL of the article.
        article_title: Title of the article.
        model: Claude model to use.
        on_progress: Optional callback for progress updates.

    Returns:
        FactCheckReport with all verification results.
    """

    def _progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    # Step 1: Extract claims
    _progress("Extracting factual claims from article...")
    claims = extract_claims(article_text, model=model)
    _progress(f"Found {len(claims)} factual claim(s)")

    # Step 2 & 3: Search and verify each claim
    verifications: list[ClaimVerification] = []
    concerns: list[str] = []

    for i, claim in enumerate(claims):
        _progress(f"Verifying claim {i + 1}/{len(claims)}: {claim.text[:60]}...")

        # Web search for evidence
        web_sources = search_claim(claim.text, max_results=5)
        news_sources = search_claim_news(claim.text, max_results=3)

        # Combine and deduplicate sources
        all_sources = web_sources.copy()
        seen_urls = {s.url for s in all_sources}
        for ns in news_sources:
            if ns.url not in seen_urls:
                all_sources.append(ns)
                seen_urls.add(ns.url)

        # Verify claim against evidence
        verification = verify_claim(claim, all_sources, model=model)
        verifications.append(verification)

        # Track concerns
        if verification.verdict in (Verdict.FALSE, Verdict.DISPUTED):
            concerns.append(
                f"Claim #{i + 1} ({verification.verdict.value}): {claim.text}"
            )
        if verification.contradictions:
            for contradiction in verification.contradictions:
                concerns.append(f"Contradiction in claim #{i + 1}: {contradiction}")

    # Step 4: Build report
    verified_count = sum(1 for v in verifications if v.verdict == Verdict.VERIFIED)
    likely_true_count = sum(1 for v in verifications if v.verdict == Verdict.LIKELY_TRUE)
    disputed_count = sum(1 for v in verifications if v.verdict == Verdict.DISPUTED)
    false_count = sum(1 for v in verifications if v.verdict == Verdict.FALSE)
    unverified_count = sum(1 for v in verifications if v.verdict == Verdict.UNVERIFIED)

    report = FactCheckReport(
        article_title=article_title,
        article_url=article_url,
        article_text=article_text,
        overall_score=_compute_overall_score(verifications),
        claim_count=len(verifications),
        verified_count=verified_count + likely_true_count,
        disputed_count=disputed_count,
        false_count=false_count,
        unverified_count=unverified_count,
        claims=verifications,
        concerns=concerns,
    )

    report.summary = _generate_summary(report)
    _progress("Fact-check complete!")

    return report


def check_url(
    url: str,
    model: str = "claude-sonnet-4-20250514",
    on_progress: Callable[[str], None] | None = None,
) -> FactCheckReport:
    """Fetch an article from URL and run fact-checking.

    Args:
        url: URL of the article to check.
        model: Claude model to use.
        on_progress: Optional callback for progress updates.

    Returns:
        FactCheckReport with all verification results.
    """

    def _progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    _progress(f"Fetching article from {url}...")
    title, text = fetch_article(url)
    _progress(f"Fetched: {title}")

    return check_article(
        article_text=text,
        article_url=url,
        article_title=title,
        model=model,
        on_progress=on_progress,
    )
