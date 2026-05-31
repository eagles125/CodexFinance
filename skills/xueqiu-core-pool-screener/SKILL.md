---
name: xueqiu-core-pool-screener
description: Build and maintain a personal A-share or Hong Kong stock screening strategy inspired by a Xueqiu article about creating a core stock pool, then using AI scoring, rough DCF/free-cash-flow checks, announcement summaries, and per-industry diversification. Use when Codex is asked to screen stocks, create a core pool, rank candidates, apply the Xueqiu strategy, update a watchlist, or explain/execute this user's personal stock selection workflow. This skill is for research assistance only, not personalized financial advice.
---

# Xueqiu Core Pool Screener

## Overview

Use this skill to apply the user's personal "core stock pool + AI scoring" workflow. The source idea is summarized from the Xueqiu article at `https://xueqiu.com/1604026436/343442117`; do not quote or reproduce the full article.

## Guardrails

- Treat all results as a research watchlist, not a buy/sell list.
- Always show data date, source, missing data, and assumptions.
- Separate hard filters, AI scoring, and final human judgment.
- Exclude companies with obvious data gaps, trading suspension, ST/delisting risk, poor liquidity, or unverified theme-only exposure.
- Keep one company per industry or close sub-industry in the final concentrated list unless the user explicitly wants cluster exposure.

## Workflow

1. Define universe:
   - A-share, Hong Kong, or A/H combined.
   - Optional exclusions: ST, suspended names, very low liquidity, banks/real estate/cyclicals, or user-specified sectors.
2. Run hard filter:
   - Net profit growth: at least 2 recent years with YoY net profit growth above 10%.
   - Valuation: PE below 20 and PB below 2 when metrics are meaningful.
   - Quality sanity checks: positive operating cash flow or explain why not available; avoid obviously overlevered balance sheets.
3. Build base pool:
   - Keep all passing names with raw metrics and data source.
   - Do not force exactly 337 names; that count belongs to the article example, not the user's live universe.
4. AI deep scoring:
   - Business quality
   - Growth durability
   - Valuation margin of safety
   - Free cash flow quality
   - Balance sheet risk
   - Announcement/news quality
   - Institution/market attention
   - Industry position and moat
5. Rough valuation check:
   - Use simple FCF / discount rate or conservative DCF only as a sanity check.
   - State assumptions explicitly: FCF base, growth rate, discount rate, terminal assumption, and safety margin.
6. Diversify:
   - Rank by total score.
   - Keep the best name in each industry/sub-industry for the final core list.
   - If two names are close, keep the one with better data quality, cash flow, and valuation discipline.
7. Output:
   - Base pool table
   - Scoring table
   - Final core watchlist
   - Excluded names and reasons
   - Next verification tasks

## Default Scorecard

Use a 100-point score unless the user asks otherwise:

| Dimension | Weight |
| --- | ---: |
| Profit growth consistency | 15 |
| Valuation reasonableness | 15 |
| Free cash flow and cash conversion | 15 |
| Balance sheet quality | 10 |
| Business quality and moat | 15 |
| Announcement/news quality | 10 |
| Industry position and policy fit | 10 |
| Liquidity and tradability | 5 |
| Data quality | 5 |

## Output Template

```text
策略名称：
股票范围：
数据日期：
数据来源：

硬筛选条件：
通过数量：
剔除规则：

基础股票池：
| 代码 | 公司 | 市场 | 行业 | 净利润增速 | PE | PB | 现金流备注 | 数据状态 |

AI 打分：
| 代码 | 公司 | 行业 | 总分 | 增长 | 估值 | 现金流 | 负债 | 护城河 | 公告/新闻 | 主要扣分原因 |

最终核心观察名单：
| 代码 | 公司 | 行业 | 入选理由 | 安全边际 | 主要风险 | 下一步核验 |

反方观点：
需要人工确认：
```

## References

- Read `references/source-summary.md` for the strategy summary and attribution.
- Use the local CodexFinance MCP/server when available for quotes, notes, and local data.
