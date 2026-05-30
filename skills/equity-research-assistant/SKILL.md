---
name: equity-research-assistant
description: Collect, organize, and analyze A-share and Hong Kong equity information for investment research. Use when Codex is asked to research stocks, screen watchlists, summarize market/policy/news impact, analyze financials, compare companies, build an investment memo, update a stock note, or maintain A/H equity research data. This skill supports research assistance only and must not present personalized financial advice or direct buy/sell instructions.
---

# Equity Research Assistant

## Overview

Use this skill to run a disciplined equity research workflow for A-share and Hong Kong stocks. Always separate facts, sourced data, assumptions, inference, and opinion; ask for missing constraints when portfolio suitability or personal risk tolerance would matter.

## Research Rules

- Do not make direct personalized investment recommendations. Use language such as "research view", "watchlist candidate", "risk/reward setup", and "requires verification".
- Always include data dates and source names. If a source is stale, unavailable, or unofficial, say so.
- Treat AI conclusions as hypotheses. Surface the strongest opposing view before any final research view.
- For policy/news-driven screens, distinguish direct beneficiaries, indirect beneficiaries, and hype-driven names.
- For A-shares, watch policy sensitivity, trading suspensions, limit-up/down behavior, liquidity, pledge risk, ST risk, shareholder reduction plans, and regulatory inquiries.
- For Hong Kong stocks, watch liquidity, dual-listing differences, short selling, FX, Southbound flows, corporate actions, and governance risk.
- Never rely on a single vendor for critical facts. Cross-check filings, exchange announcements, or company investor relations when possible.

## Workflow

1. Clarify scope: market, tickers, sector, time horizon, benchmark, and whether the output is a quick scan or full memo.
2. Collect data: use available MCP tools for quotes, fundamentals, announcements, news, notes, and local files.
3. Normalize identifiers: A-share codes as `000001.SZ` / `600000.SH`; Hong Kong codes as `00700.HK`.
4. Build a fact table: price, market cap, revenue/profit trend, valuation, liquidity, latest announcements, and key events.
5. Analyze drivers: business model, industry cycle, policy/news catalysts, financial quality, valuation, flows, and technical context.
6. Stress test: list downside scenarios, data quality problems, accounting flags, and counterarguments.
7. Produce output: concise memo, watchlist table, or update note with next verification steps.
8. Save durable work under the project research directory when useful: `data/`, `notes/`, or a user-specified path.

## Output Templates

For a quick stock scan:

```text
Scope:
Sources and dates:
Fact summary:
Positive drivers:
Negative drivers:
Policy/news sensitivity:
Valuation/liquidity notes:
Contrary view:
Research view:
Next checks:
```

For a thematic or policy screen:

```text
Theme/policy event:
Transmission logic:
Beneficiary chain:
Candidate table:
Evidence strength:
Crowding/hype risk:
Names to exclude and why:
Next checks:
```

## MCP Usage

Prefer the local `codex-finance` MCP tools when available:

- `get_zh_quote` for A-share or Hong Kong quote snapshots.
- `get_zh_history` for daily historical prices.
- `get_financial_indicators` for A-share financial indicators when available.
- `search_stock_notes` and `save_stock_note` for local research memory.
- `run_sqlite_query` for local research database queries.
- `data_source_status` before relying on a data provider.

If MCP tools are unavailable, use web browsing and local files, then clearly mark missing automated data access.

## References

- Read `references/ah-market-data.md` when choosing data sources or interpreting A/H market quirks.
- Read `references/stock-screening.md` for policy/news-driven screening methodology.
