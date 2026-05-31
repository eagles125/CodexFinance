from __future__ import annotations

import csv
import math
import time
from pathlib import Path

import akshare as ak
import pandas as pd
import requests


ROOT = Path(r"E:\ai\CodexFinance")
OUT = ROOT / "data" / "stocks" / "xueqiu-core-screen-2026-05-31.csv"
REPORT = ROOT / "notes" / "xueqiu-core-screen-top10-2026-05-31.md"


def market_prefix(code: str) -> str | None:
    if code.startswith(("60", "68", "90")):
        return "sh"
    if code.startswith(("00", "30", "20")):
        return "sz"
    return None


def fetch_quote_batch(codes: list[str]) -> list[dict[str, str]]:
    q = ",".join(codes)
    text = requests.get(f"https://qt.gtimg.cn/q={q}", timeout=30).text
    rows = []
    for part in text.split(";"):
        if '="' not in part:
            continue
        raw = part.split('="', 1)[1].rstrip('"\n ')
        f = raw.split("~")
        if len(f) < 48:
            continue
        rows.append(
            {
                "股票代码": f[2],
                "股票简称_q": f[1],
                "最新价": to_float(f[3]),
                "涨跌幅": to_float(f[32]),
                "成交额_万元": to_float(f[37]),
                "总市值_亿元": to_float(f[45]),
                "PE_TTM": to_float(f[39]),
                "PB": to_float(f[46]),
            }
        )
    return rows


def to_float(x: str) -> float | None:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except ValueError:
        return None


def score(row: pd.Series) -> float:
    s = 0.0
    # Growth, capped to avoid one-off distortions.
    s += min(max(row["净利润-同比增长_2025"], 0), 80) / 80 * 15
    s += min(max(row["净利润-同比增长_2024"], 0), 80) / 80 * 15
    # Valuation.
    pe = row["PE_TTM"]
    pb = row["PB"]
    if pd.notna(pe):
        s += max(0, (20 - pe) / 20) * 15
    if pd.notna(pb):
        s += max(0, (2 - pb) / 2) * 10
    # Cash conversion and profitability.
    ocf = row["每股经营现金流量_2025"]
    eps = row["每股收益_2025"]
    if pd.notna(ocf) and pd.notna(eps) and eps > 0:
        s += min(max(ocf / eps, 0), 1.5) / 1.5 * 15
    roe = row["净资产收益率_2025"]
    if pd.notna(roe):
        s += min(max(roe, 0), 20) / 20 * 10
    margin = row["销售毛利率_2025"]
    if pd.notna(margin):
        s += min(max(margin, 0), 50) / 50 * 10
    turnover = row["成交额_万元"]
    if pd.notna(turnover):
        s += min(max(turnover, 0), 100000) / 100000 * 5
    # Data quality.
    s += 5
    return round(s, 2)


def main() -> None:
    y25 = ak.stock_yjbb_em(date="20251231")
    y24 = ak.stock_yjbb_em(date="20241231")
    keep_cols = [
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
    a = y25[keep_cols].copy()
    b = y24[["股票代码", "净利润-同比增长", "净利润-净利润"]].copy()
    a = a.rename(columns={c: f"{c}_2025" for c in keep_cols if c not in ["股票代码", "股票简称", "所处行业", "最新公告日期"]})
    b = b.rename(columns={"净利润-同比增长": "净利润-同比增长_2024", "净利润-净利润": "净利润-净利润_2024"})
    df = a.merge(b, on="股票代码", how="inner")
    df = df[~df["股票简称"].astype(str).str.contains("ST|退", regex=True, na=False)]
    df = df[df["股票代码"].astype(str).str.match(r"^(00|30|60|68)")]

    quote_codes = []
    for code in df["股票代码"].astype(str):
        p = market_prefix(code)
        if p:
            quote_codes.append(p + code)

    qrows = []
    for i in range(0, len(quote_codes), 80):
        qrows.extend(fetch_quote_batch(quote_codes[i : i + 80]))
        time.sleep(0.2)
    qdf = pd.DataFrame(qrows).drop_duplicates("股票代码")
    df = df.merge(qdf, on="股票代码", how="left")

    for col in ["净利润-同比增长_2025", "净利润-同比增长_2024", "PE_TTM", "PB", "每股经营现金流量_2025", "每股收益_2025"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    screened = df[
        (df["净利润-同比增长_2025"] > 10)
        & (df["净利润-同比增长_2024"] > 10)
        & (df["PE_TTM"] > 0)
        & (df["PE_TTM"] < 20)
        & (df["PB"] > 0)
        & (df["PB"] < 2)
        & (df["每股经营现金流量_2025"] > 0)
        & (df["成交额_万元"] > 5000)
    ].copy()
    screened["总分"] = screened.apply(score, axis=1)
    screened["市场"] = screened["股票代码"].apply(lambda c: "上海" if str(c).startswith(("60", "68")) else "深圳")

    selected = (
        screened.sort_values(["总分", "成交额_万元"], ascending=False)
        .groupby("所处行业", dropna=False)
        .head(1)
        .sort_values("总分", ascending=False)
        .head(10)
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "股票代码",
        "股票简称",
        "市场",
        "所处行业",
        "总分",
        "净利润-同比增长_2025",
        "净利润-同比增长_2024",
        "PE_TTM",
        "PB",
        "每股经营现金流量_2025",
        "净资产收益率_2025",
        "销售毛利率_2025",
        "最新价",
        "涨跌幅",
        "成交额_万元",
        "总市值_亿元",
        "最新公告日期",
    ]
    screened.sort_values("总分", ascending=False)[cols].to_csv(OUT, index=False, encoding="utf-8-sig")

    lines = [
        "# 雪球核心池策略筛选 Top 10",
        "",
        "日期：2026-05-31",
        "策略：`xueqiu-core-pool-screener`",
        "范围：A 股普通股票，剔除 ST/退市风险标签，按行业分散后取前 10。",
        "用途：研究观察名单，不构成投资建议。",
        "",
        "## 筛选条件",
        "",
        "- 2025 年净利润同比增长 > 10%",
        "- 2024 年净利润同比增长 > 10%",
        "- PE_TTM > 0 且 < 20",
        "- PB > 0 且 < 2",
        "- 2025 年每股经营现金流量 > 0",
        "- 成交额 > 5000 万元",
        "- 每个行业最多保留 1 只",
        "",
        f"基础通过数量：{len(screened)}",
        "",
        "## 最终核心观察名单",
        "",
        "| 排名 | 代码 | 公司 | 市场 | 行业 | 总分 | 2025净利增速% | 2024净利增速% | PE | PB | 每股经营现金流 | ROE% | 最新价 | 主要风险 |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for idx, (_, r) in enumerate(selected.iterrows(), 1):
        risks = "需核验增长是否来自一次性收益、现金流持续性、公告和行业景气。"
        lines.append(
            f"| {idx} | {r['股票代码']} | {r['股票简称']} | {r['市场']} | {r['所处行业']} | {r['总分']:.2f} | "
            f"{r['净利润-同比增长_2025']:.2f} | {r['净利润-同比增长_2024']:.2f} | {r['PE_TTM']:.2f} | {r['PB']:.2f} | "
            f"{r['每股经营现金流量_2025']:.2f} | {r['净资产收益率_2025']:.2f} | {r['最新价']:.2f} | {risks} |"
        )
    lines += [
        "",
        "## 反方观点",
        "",
        "- 2025 年数据可能包含业绩预告、快报或不同口径，必须用正式年报复核。",
        "- PE/PB 来自公开行情接口，可能与专业终端口径不同。",
        "- 两年高增长可能来自低基数或一次性收益，不能直接视为高质量成长。",
        "- 每行业只选 1 只会牺牲部分行业内更优替代，需要人工复核同业对比。",
        "",
        "## 需要人工确认",
        "",
        "1. 最近公告是否存在减持、问询、诉讼、资产减值、一次性收益。",
        "2. 经营现金流是否连续多年为正，而不是单年改善。",
        "3. 行业景气是否处于上行阶段，还是利润高点。",
        "4. 是否存在流动性、股权质押、客户集中、存货和应收账款风险。",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"base_pool={len(screened)}")
    print(f"wrote={OUT}")
    print(f"report={REPORT}")
    print(selected[["股票代码", "股票简称", "所处行业", "总分", "PE_TTM", "PB"]].to_string(index=False))


if __name__ == "__main__":
    main()
