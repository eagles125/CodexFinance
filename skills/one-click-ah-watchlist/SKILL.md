---
name: one-click-ah-watchlist
description: Generate a one-click A-share and Hong Kong market research watchlist that combines stocks, ETFs, and mutual funds, with no more than five items per category and no more than ten total. Use when Codex is asked to produce a compact investment observation pool, combine Buffett-style quality value, A-share super-investor clues, red-flag checks, Xueqiu core-pool screening, or Zhihu-style stock selection heuristics. This skill is for research assistance only, not personalized financial advice.
---

# One Click A/H Watchlist

## Overview

Use this skill to create a compact research watchlist across stocks, ETFs, and funds. The watchlist must be small enough to review manually: each category no more than 5 items and total no more than 10 items.

## Strategy Blend

Combine five lenses:

1. Buffett quality value:
   - Durable business, high and stable ROE, good free cash flow, low leverage, understandable model, reasonable valuation.
2. A-share super-investor clues:
   - Institutional/shareholder changes, buybacks, equity incentives, hidden champions, cycle reversal, industry inflection.
3. Red-flag checker:
   - ST/delisting risk, pledge risk, cash-flow/profit divergence, high receivables/inventory, goodwill impairment, regulatory inquiry, frequent reductions.
4. Independent primary stock screening:
   - Build the stock list from live financial and quote data using this skill's own scorecard. Do not directly reuse `xueqiu-core-screen` output as the stock source.
5. Zhihu high-vote strategy summary:
   - Prefer simple, repeatable logic; buy good companies at acceptable prices; avoid stories without financial confirmation; use industry comparison; combine qualitative business judgment with quantitative filters; keep watchlists small and verify continuously.
6. Xueqiu core-pool cross-check:
   - Use `xueqiu-core-pool-screener` only as a secondary validation label. Mark whether a selected stock also appears in the Xueqiu core-pool result, but do not require it.

## Output Rules

- Total items: no more than 10.
- Stocks: no more than 5.
- ETFs: no more than 5.
- Funds: no more than 5.
- Use "观察池" language, not "推荐买入".
- Include source date and missing data warnings.
- Add a short "why included" and "what can go wrong" for every item.
- Prefer diversified exposure:
  - 3-5 stocks for alpha candidates.
  - 2-4 ETFs for theme/broad-market exposure.
  - 1-3 funds for manager/strategy exposure.

## Default Selection Logic

Stocks:

1. Pull current financial report data and quote/valuation data.
2. Score independently with the one-click watchlist scorecard:
   - Quality/value fundamentals
   - Growth and industry trend
   - Cash flow and balance sheet
   - Valuation safety margin
   - Red-flag cleanliness
   - Liquidity and trackability
3. Exclude ST/退市 labels, negative or missing PE/PB, weak cash flow, tiny liquidity, and obvious data-quality failures.
4. Penalize banks/insurance/brokers unless the user explicitly wants financial value names.
5. Keep industry diversification and pick no more than 5 stocks.
6. Cross-check against `xueqiu-core-screen` CSV if available and add a "雪球核心池交叉验证" field.

ETFs:

1. Prefer broad or liquid thematic ETFs that map to the user's themes.
2. Avoid tiny scale, poor liquidity, or overly narrow products unless the theme is explicit.
3. Include one defensive/broad-market ETF when the stock list is aggressive.

Funds:

1. Prefer established active funds or index-enhanced funds with clear style, manager continuity, and reasonable drawdown history.
2. Avoid chasing short-term top performers only.
3. Mark fund data as "needs latest fund report verification" unless current holdings and manager data are checked.

## One-Command Behavior

When the user says:

```text
用 one-click-ah-watchlist 生成一键观察池
```

Run the project script when available:

```powershell
python E:\ai\CodexFinance\scripts\run_one_click_watchlist.py
```

Then summarize the generated Markdown report.

## References

- Read `references/strategy-summary.md` for the combined strategy summary.
- Use `xueqiu-core-pool-screener` only for cross-validation, not as the primary stock source.
- Use `equity-research-assistant` for follow-up single-name analysis.
