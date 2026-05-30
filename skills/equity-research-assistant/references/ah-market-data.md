# A/H Market Data Notes

## Identifier Conventions

- A-share Shenzhen: `000001.SZ`, `300750.SZ`
- A-share Shanghai: `600519.SH`, `688981.SH`
- Hong Kong: `00700.HK`, `09988.HK`

## Practical Source Hierarchy

1. Exchange and company announcements for corporate actions, filings, and regulatory events.
2. Official or vendor financial datasets for fundamentals.
3. Public data libraries such as AKShare for fast research and prototyping.
4. News and social sources only as catalyst discovery, not as final evidence.

## A-Share Checks

- ST or delisting risk
- Trading suspension
- Limit-up/down state
- Liquidity and turnover
- Share pledge ratio
- Major shareholder reduction plans
- Regulatory inquiry letters
- Related-party transactions

## Hong Kong Checks

- Liquidity and bid/ask spread
- Southbound Stock Connect eligibility and flows
- Short selling turnover
- HKD/CNY exposure and FX translation
- Dual listing premium/discount where applicable
- Governance and related-party risk

## Data Quality

Public data can be delayed, incomplete, or vendor-normalized. For investment-sensitive conclusions, verify against announcements, exchange filings, or company investor relations.
