# Uradori (裏どり) - AI News Fact-Checker

**メディアの中の人が作った、ニュース裏どりAI**

Uradori is an AI-powered fact-checking CLI tool that verifies the credibility of news articles by extracting factual claims and cross-referencing them with web sources.

## How It Works

```
News Article (URL or text)
  │
  ├── 1. Fetch & parse article (if URL)
  ├── 2. Extract factual claims using Claude API
  │     (opinions and speculation are excluded)
  ├── 3. Search the web for each claim (DuckDuckGo)
  │     (prioritizes primary sources)
  ├── 4. Evaluate evidence using Claude API
  │     - Confidence score (0-100)
  │     - Verdict: VERIFIED / LIKELY_TRUE / UNVERIFIED / DISPUTED / FALSE
  ├── 5. Generate comprehensive report
  └── 6. Display results (terminal + JSON)
```

## Installation

```bash
pip install -e .
```

### Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` environment variable set

## Usage

### Check a URL

```bash
uradori check https://example.com/news/article
```

### Check text directly

```bash
uradori check "The company reported $5B in revenue for Q3 2025"
```

### Pipe from stdin

```bash
cat article.txt | uradori check -
```

### Options

```bash
uradori check <input> --model claude-sonnet-4-20250514  # Choose model
uradori check <input> --output report.json         # Save JSON report
uradori check <input> --json-only                  # JSON output only
```

## Output Example

```
╭──────────────────────────────────────────╮
│ 裏どり Fact-Check Report                  │
╰──────────────────────────────────────────╯

Article: Japan's GDP Growth Surpasses Expectations
URL: https://example.com/news/japan-gdp

╭─ Score ──────────────────────────────────╮
│ Overall Credibility Score: 72/100        │
╰──────────────────────────────────────────╯

┌─────────────────────────────────────────────────┐
│ #  │ Claim              │ Verdict    │ Score │
├────┼────────────────────┼────────────┼───────┤
│ 1  │ GDP grew 2.1%...   │ ✓ VERIFIED │   92  │
│ 2  │ BOJ rate at 0.5%   │ ✓ VERIFIED │   88  │
│ 3  │ Consumer +3.2%     │ ○ LIKELY   │   65  │
│ 4  │ Semicon exports... │ △ DISPUTED │   35  │
│ 5  │ Toyota 5T yen...   │ ? UNVERIF  │   45  │
└─────────────────────────────────────────────────┘
```

## Verdict Categories

| Verdict | Score Range | Meaning |
|---------|-----------|---------|
| VERIFIED | 80-100 | Multiple independent reliable sources confirm |
| LIKELY_TRUE | 60-79 | Some evidence supports, no contradictions |
| UNVERIFIED | 40-59 | Insufficient evidence to confirm or deny |
| DISPUTED | 20-39 | Conflicting evidence found |
| FALSE | 0-19 | Strong evidence contradicts the claim |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Architecture

```
src/uradori/
├── __init__.py      # Package init
├── models.py        # Data models (Claim, Source, Verdict, Report)
├── fetcher.py       # Article fetching & HTML parsing
├── extractor.py     # Claim extraction via Claude API
├── searcher.py      # Web search via DuckDuckGo
├── verifier.py      # Claim verification via Claude API
├── pipeline.py      # Orchestration pipeline
├── display.py       # Rich terminal output
└── cli.py           # Click CLI interface
```

## Tech Stack

- **Claude API** (anthropic SDK) - Claim extraction & verification
- **DuckDuckGo** (duckduckgo-search) - Web search (no API key needed)
- **BeautifulSoup4** - HTML parsing
- **Rich** - Terminal display
- **Click** - CLI framework
- **httpx** - HTTP client

## License

MIT
