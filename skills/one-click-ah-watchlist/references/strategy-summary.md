# Combined One-Click Watchlist Strategy

## Source Inputs

- Buffett-style quality value investing principles.
- A-share super-investor and shareholder-clue investing heuristics.
- A-share red-flag risk control framework.
- Xueqiu core-pool screening workflow from `https://xueqiu.com/1604026436/343442117`, used as a cross-check rather than the primary stock source.
- Zhihu question `https://www.zhihu.com/question/57199649`.

## Zhihu Access Note

The Zhihu page returned HTTP 403 during automated access on 2026-05-31. The strategy here summarizes commonly visible high-quality Zhihu-style stock-selection heuristics rather than claiming a complete extraction of every high-vote answer. If the user provides copied answer text, update this reference with exact user-provided excerpts and tighten the rules.

## Strategy Summary

The combined strategy is:

1. Use this skill's independent hard filters to narrow the universe.
2. Prefer companies with real profit growth, healthy cash flow, low leverage, and acceptable valuation.
3. Use qualitative business judgment: industry space, competitive advantage, management, and long-term demand.
4. Avoid story-only names and companies with accounting or governance red flags.
5. Use shareholder/institutional clues only as a secondary signal, never as the primary reason.
6. Diversify across stocks, ETFs, and funds to reduce single-name risk.
7. Keep the final list small enough for manual tracking.
8. Cross-check selected stocks against the Xueqiu core-pool result if available, but do not let that result determine the list.
9. Continuously verify with announcements, financial reports, and price/valuation changes.

## Primary Stock Flow

The stock flow must run independently:

1. Fetch financial report data.
2. Fetch current quote, PE/PB, liquidity, and market value data.
3. Apply red-flag exclusions.
4. Score candidates using the one-click scorecard.
5. Diversify by industry.
6. Add a cross-check column showing whether each selected name also appears in `xueqiu-core-screen`.

## Scoring Weights

| Lens | Weight |
| --- | ---: |
| Quality/value fundamentals | 30 |
| Growth and industry trend | 20 |
| Cash flow and balance sheet | 15 |
| Valuation safety margin | 15 |
| Super-investor/shareholder clues | 5 |
| Red-flag cleanliness | 10 |
| Liquidity and trackability | 5 |
