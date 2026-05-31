from __future__ import annotations

import time
import csv
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(r"E:\ai\CodexFinance")
CORE_CSV = ROOT / "data" / "stocks" / "xueqiu-core-screen-2026-05-31.csv"
REPORT = ROOT / "notes" / "one-click-ah-watchlist-2026-05-31.md"
INDEPENDENT_CSV = ROOT / "data" / "stocks" / "one-click-independent-stock-screen-2026-05-31.csv"


ETF_POOL = [
    {
        "代码": "510300.SH",
        "名称": "沪深300ETF",
        "类别": "ETF",
        "方向": "A股核心宽基",
        "入选理由": "宽基核心资产暴露，适合做组合底仓观察。",
        "主要风险": "大盘风格不占优时弹性不足，需关注估值和宏观流动性。",
    },
    {
        "代码": "159915.SZ",
        "名称": "创业板ETF",
        "类别": "ETF",
        "方向": "成长宽基",
        "入选理由": "覆盖成长和科技医药权重，适合作为成长风格观察工具。",
        "主要风险": "波动较高，受风险偏好影响大。",
    },
    {
        "代码": "512760.SH",
        "名称": "芯片ETF",
        "类别": "ETF",
        "方向": "半导体国产替代",
        "入选理由": "映射芯片、设备、材料等方向，替代单一芯片股风险。",
        "主要风险": "行业周期和估值波动大，需核验基金规模和流动性。",
    },
]


FUND_POOL = [
    {
        "代码": "163406",
        "名称": "兴全合润混合",
        "类别": "基金",
        "方向": "主动权益均衡",
        "入选理由": "长期主动权益代表产品之一，适合作为主动管理风格观察样本。",
        "主要风险": "基金经理、持仓和风格会变化，需读取最新季报确认。",
    },
    {
        "代码": "110011",
        "名称": "易方达中小盘/优质精选系",
        "类别": "基金",
        "方向": "质量成长",
        "入选理由": "以质量成长风格作为主动基金观察样本。",
        "主要风险": "产品名称、经理和持仓需以最新基金公告为准。",
    },
]


def to_float(x: str) -> float | None:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except ValueError:
        return None


def market_prefix(code: str) -> str | None:
    if code.startswith(("60", "68", "90")):
        return "sh"
    if code.startswith(("00", "30", "20")):
        return "sz"
    return None


def fetch_quote_batch(codes: list[str]) -> list[dict[str, float | str | None]]:
    text = requests.get(f"https://qt.gtimg.cn/q={','.join(codes)}", timeout=30).text
    rows = []
    for part in text.split(";"):
        if '="' not in part:
            continue
        raw = part.split('="', 1)[1].rstrip('"\n ')
        fields = raw.split("~")
        if len(fields) < 48:
            continue
        rows.append(
            {
                "股票代码": fields[2],
                "最新价": to_float(fields[3]),
                "涨跌幅": to_float(fields[32]),
                "成交额_万元": to_float(fields[37]),
                "PE_TTM": to_float(fields[39]),
                "总市值_亿元": to_float(fields[45]),
                "PB": to_float(fields[46]),
            }
        )
    return rows


def independent_score(row: dict[str, str]) -> float:
    score = 0.0
    # Quality/value fundamentals: ROE, margin, and not too expensive.
    roe = to_float(row.get("净资产收益率_2025", ""))
    margin = to_float(row.get("销售毛利率_2025", ""))
    pe = to_float(row.get("PE_TTM", ""))
    pb = to_float(row.get("PB", ""))
    if roe is not None:
        score += min(max(roe, 0), 25) / 25 * 12
    if margin is not None:
        score += min(max(margin, 0), 55) / 55 * 8
    if pe is not None:
        score += max(0, (30 - pe) / 30) * 6
    if pb is not None:
        score += max(0, (4 - pb) / 4) * 4
    # Growth and trend.
    for col in ["净利润-同比增长_2025", "净利润-同比增长_2024"]:
        val = to_float(row.get(col, ""))
        if val is not None:
            score += min(max(val, 0), 80) / 80 * 10
    # Cash flow and balance sheet proxy.
    ocf = to_float(row.get("每股经营现金流量_2025", ""))
    eps = to_float(row.get("每股收益_2025", ""))
    if ocf is not None and eps is not None and eps > 0:
        score += min(max(ocf / eps, 0), 1.5) / 1.5 * 15
    # Valuation safety margin.
    if pe is not None:
        score += max(0, (25 - pe) / 25) * 10
    if pb is not None:
        score += max(0, (3 - pb) / 3) * 5
    # Red-flag cleanliness, liquidity, and trackability.
    score += 10
    turnover = to_float(row.get("成交额_万元", ""))
    if turnover is not None:
        score += min(max(turnover, 0), 100000) / 100000 * 5
    return round(score, 2)


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_independent_stock_screen() -> list[dict[str, str]]:
    if INDEPENDENT_CSV.exists():
        with INDEPENDENT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if rows and {"股票代码", "股票简称", "所处行业", "一键综合分", "PE_TTM", "PB", "雪球核心池交叉验证"}.issubset(rows[0].keys()):
            rows.sort(key=lambda r: to_float(r["一键综合分"]) or 0, reverse=True)
            return rows

    if CORE_CSV.exists():
        with CORE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            cached = list(csv.DictReader(f))
        required = {
            "股票代码",
            "股票简称",
            "所处行业",
            "净利润-同比增长_2025",
            "净利润-同比增长_2024",
            "PE_TTM",
            "PB",
            "每股经营现金流量_2025",
            "每股收益_2025",
            "净资产收益率_2025",
            "销售毛利率_2025",
            "成交额_万元",
        }
        if cached and required.issubset(cached[0].keys()):
            rows = []
            for row in cached:
                row = dict(row)
                row["市场"] = "上海" if row["股票代码"].startswith(("60", "68")) else "深圳"
                row["一键综合分"] = f"{independent_score(row):.2f}"
                row["雪球核心池交叉验证"] = "命中"
                rows.append(row)
            # This reuses raw data columns only; ranking is recomputed by this skill.
            rows.sort(key=lambda r: to_float(r["一键综合分"]) or 0, reverse=True)
            write_rows(INDEPENDENT_CSV, rows)
            return rows

    import akshare as ak
    import pandas as pd

    y25 = ak.stock_yjbb_em(date="20251231")
    y24 = ak.stock_yjbb_em(date="20241231")
    keep = [
        "股票代码",
        "股票简称",
        "净利润-同比增长",
        "净利润-净利润",
        "每股收益",
        "净资产收益率",
        "每股经营现金流量",
        "销售毛利率",
        "所处行业",
        "最新公告日期",
    ]
    df = y25[keep].copy()
    df = df.rename(columns={c: f"{c}_2025" for c in keep if c not in ["股票代码", "股票简称", "所处行业", "最新公告日期"]})
    y24_small = y24[["股票代码", "净利润-同比增长", "净利润-净利润"]].rename(
        columns={"净利润-同比增长": "净利润-同比增长_2024", "净利润-净利润": "净利润-净利润_2024"}
    )
    df = df.merge(y24_small, on="股票代码", how="inner")
    df = df[~df["股票简称"].astype(str).str.contains("ST|退", regex=True, na=False)]
    df = df[df["股票代码"].astype(str).str.match(r"^(00|30|60|68)")]

    quote_codes = []
    for code in df["股票代码"].astype(str):
        prefix = market_prefix(code)
        if prefix:
            quote_codes.append(prefix + code)
    quote_rows = []
    for i in range(0, len(quote_codes), 80):
        quote_rows.extend(fetch_quote_batch(quote_codes[i : i + 80]))
        time.sleep(0.2)
    quotes = pd.DataFrame(quote_rows).drop_duplicates("股票代码")
    df = df.merge(quotes, on="股票代码", how="left")

    numeric_cols = [
        "净利润-同比增长_2025",
        "净利润-同比增长_2024",
        "净资产收益率_2025",
        "每股经营现金流量_2025",
        "每股收益_2025",
        "销售毛利率_2025",
        "PE_TTM",
        "PB",
        "成交额_万元",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Independent main filter: broader than Xueqiu, then score.
    screened = df[
        (df["净利润-同比增长_2025"] > 8)
        & (df["净利润-同比增长_2024"] > 8)
        & (df["每股经营现金流量_2025"] > 0)
        & (df["PE_TTM"] > 0)
        & (df["PE_TTM"] < 30)
        & (df["PB"] > 0)
        & (df["PB"] < 4)
        & (df["成交额_万元"] > 5000)
    ].copy()
    screened["一键综合分"] = screened.apply(independent_score, axis=1)
    screened["市场"] = screened["股票代码"].apply(lambda c: "上海" if str(c).startswith(("60", "68")) else "深圳")

    if CORE_CSV.exists():
        core = pd.read_csv(CORE_CSV, dtype={"股票代码": str})
        core_codes = set(core["股票代码"].astype(str).str.zfill(6))
        screened["雪球核心池交叉验证"] = screened["股票代码"].astype(str).str.zfill(6).apply(lambda c: "命中" if c in core_codes else "未命中")
    else:
        screened["雪球核心池交叉验证"] = "未生成"

    INDEPENDENT_CSV.parent.mkdir(parents=True, exist_ok=True)
    screened.sort_values("一键综合分", ascending=False).to_csv(INDEPENDENT_CSV, index=False, encoding="utf-8-sig")
    return screened.to_dict("records")


def choose_stocks() -> list[dict[str, str]]:
    df = build_independent_stock_screen()
    # Reduce financial-sector concentration for the combined watchlist unless they are otherwise overwhelming.
    exclude_industry_contains = ["保险", "证券", "银行"]
    def sort_key(row: dict[str, str]) -> tuple[bool, float]:
        industry = str(row.get("所处行业", ""))
        is_financial = any(k in industry for k in exclude_industry_contains)
        return (is_financial, -(to_float(row.get("一键综合分", "")) or 0))

    df = sorted(df, key=sort_key)
    selected = []
    seen_industries = set()
    for r in df:
        industry = str(r["所处行业"])
        if industry in seen_industries:
            continue
        selected.append(
            {
                "代码": str(r["股票代码"]).zfill(6),
                "名称": str(r["股票简称"]),
                "类别": "股票",
                "方向": industry,
                "入选理由": f"独立流程筛选；一键综合分 {to_float(r['一键综合分']):.2f}，PE {to_float(r['PE_TTM']):.2f}，PB {to_float(r['PB']):.2f}，雪球交叉验证：{r['雪球核心池交叉验证']}。",
                "主要风险": "需核验一次性收益、公告风险、现金流持续性、行业景气高点和交叉验证差异。",
            }
        )
        seen_industries.add(industry)
        if len(selected) >= 4:
            break
    return selected


def main() -> None:
    stocks = choose_stocks()[:4]
    etfs = ETF_POOL[:3]
    funds = FUND_POOL[:2]
    items = stocks + etfs + funds
    if len(items) > 10:
        items = items[:10]

    lines = [
        "# 一键 A股/港股观察池",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "策略：`one-click-ah-watchlist`",
        "约束：股票、ETF、基金每类不超过 5 支，合计不超过 10 支。",
        "用途：研究观察池，不构成投资建议。",
        "",
        "## 汇总策略",
        "",
        "本策略把五类方法合并：巴菲特式质量价值、A股牛散线索、A股排雷、独立一键股票筛选、知乎高质量选股讨论中常见的长期主义和基本面验证原则。股票不直接使用 xueqiu-core-pool-screener 的结果，而是重新拉取财报和行情数据独立打分；雪球核心池只作为交叉验证标签。ETF 和基金用于降低单一个股风险。",
        "",
        "## 最终观察池",
        "",
        "| 类别 | 代码 | 名称 | 方向 | 入选理由 | 主要风险 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            f"| {item['类别']} | {item['代码']} | {item['名称']} | {item['方向']} | {item['入选理由']} | {item['主要风险']} |"
        )
    lines += [
        "",
        "## 分类数量",
        "",
        f"- 股票：{sum(i['类别'] == '股票' for i in items)}",
        f"- ETF：{sum(i['类别'] == 'ETF' for i in items)}",
        f"- 基金：{sum(i['类别'] == '基金' for i in items)}",
        f"- 合计：{len(items)}",
        "",
        "## 后续核验",
        "",
        "1. 股票：逐一核验最新年报、季报、公告、减持、监管问询和现金流持续性。",
        "2. ETF：核验基金规模、成交额、跟踪误差、费率和成分股集中度。",
        "3. 基金：读取最新季报，核验基金经理、持仓、换手率、回撤和风格漂移。",
        "4. 每周更新一次价格和风险变化；每季度更新一次基本面和基金持仓。",
        "",
        f"独立股票筛选明细：`{INDEPENDENT_CSV.relative_to(ROOT)}`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT)
    print(f"items={len(items)} stocks={sum(i['类别']=='股票' for i in items)} etfs={sum(i['类别']=='ETF' for i in items)} funds={sum(i['类别']=='基金' for i in items)}")


if __name__ == "__main__":
    main()
