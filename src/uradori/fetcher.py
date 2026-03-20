"""Article fetching and parsing module."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup


def fetch_article(url: str, timeout: float = 30.0) -> tuple[str, str]:
    """Fetch and parse an article from a URL.

    Args:
        url: The URL of the article to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (title, article_text).

    Raises:
        httpx.HTTPError: If the request fails.
        ValueError: If no article content is found.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ja,en;q=0.9",
    }

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Try og:title as fallback
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = str(og_title["content"])

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
        tag.decompose()

    # Try to find article content in common containers
    article_text = ""
    for selector in ["article", '[role="main"]', ".article-body", ".entry-content", "main"]:
        container = soup.select_one(selector)
        if container:
            paragraphs = container.find_all("p")
            if paragraphs:
                article_text = "\n".join(
                    p.get_text(strip=True) for p in paragraphs
                    if p.get_text(strip=True)
                )
                break

    # Fallback: get all paragraphs
    if not article_text:
        paragraphs = soup.find_all("p")
        texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
        article_text = "\n".join(texts)

    if not article_text:
        raise ValueError(f"Could not extract article content from {url}")

    return title, article_text
