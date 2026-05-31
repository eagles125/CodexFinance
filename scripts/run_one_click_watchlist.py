from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(r"E:\ai\CodexFinance")
REPORT = ROOT / "notes" / "one-click-ah-watchlist-2026-05-31.md"
INDEPENDENT_CSV = ROOT / "data" / "stocks" / "one-click-independent-stock-screen-2026-05-31.csv"
KLINE_DIR = ROOT / "data" / "market" / "kline"
CHART_DIR = ROOT / "notes" / "assets" / "kline"

STOCK_WEIGHT = {
    "质量价值": 30,
    "成长趋势": 20,
    "现金流与资产负债": 15,
    "估值安全边际": 15,
    "排雷清洁度": 10,
    "流动性与可跟踪性": 5,
    "交叉验证": 5,
}

ETF_WEIGHT = {
    "流动性与规模": 25,
    "代表性与分散度": 25,
    "费用与跟踪便利": 15,
    "主题契合度": 20,
    "风险控制": 15,
}

FUND_WEIGHT = {
    "长期业绩与回撤": 25,
    "基金经理与团队稳定": 20,
    "风格清晰度": 20,
    "持仓质量": 20,
    "费率与规模适中": 15,
}

ETF_POOL = [
    ("510300.SH", "沪深300ETF", "A股核心宽基", 86, "宽基核心资产暴露，适合做组合底仓观察。", "大盘风格不占优时弹性不足。"),
    ("159915.SZ", "创业板ETF", "成长宽基", 82, "覆盖成长、科技和医药权重，适合作为成长风格观察工具。", "波动较高，受风险偏好影响大。"),
    ("512760.SH", "芯片ETF", "半导体国产替代", 80, "映射芯片、设备、材料等方向，替代单一芯片股风险。", "行业周期和估值波动大。"),
    ("513130.SH", "恒生科技ETF", "港股科技", 78, "覆盖港股互联网和科技平台，补充港股弹性。", "港股流动性、汇率和监管预期波动。"),
]

FUND_POOL = [
    ("163406", "兴全合润混合", "主动权益均衡", 79, "长期主动权益代表产品之一，适合作为主动管理风格观察样本。", "基金经理、持仓和风格会变化，需读取最新季报确认。"),
    ("110011", "易方达优质精选系", "质量成长", 76, "质量成长风格观察样本。", "产品名称、经理和持仓需以最新基金公告为准。"),
    ("161005", "富国天惠成长混合", "长期成长", 75, "长期成长风格样本，适合观察主动成长基金。", "风格和阶段性回撤需复核。"),
]

MIN_5Y_CAGR = 30.0


def to_float(value: str | None) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except ValueError:
        return None


def read_stock_rows() -> list[dict[str, str]]:
    if not INDEPENDENT_CSV.exists():
        raise FileNotFoundError(f"missing stock screen csv: {INDEPENDENT_CSV}")
    with INDEPENDENT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("stock screen csv is empty")
    for row in rows:
        score = to_float(row.get("一键综合分"))
        cross = row.get("雪球核心池交叉验证", "")
        row["综合得分"] = f"{min(100, (score or 0) + (2 if cross == '命中' else 0)):.2f}"
        row["类别"] = "股票"
        row["代码"] = row["股票代码"].zfill(6)
        row["名称"] = row["股票简称"]
        row["方向"] = row["所处行业"]
        row["入选理由"] = f"独立综合分 {row['综合得分']}；PE {row.get('PE_TTM')}，PB {row.get('PB')}；雪球交叉验证：{cross}。"
        row["主要风险"] = "需核验一次性收益、现金流持续性、公告风险、行业景气高点和估值口径。"
    return rows


def choose_stocks(limit: int = 5) -> list[dict[str, str]]:
    rows = read_stock_rows()
    financial_keywords = ("保险", "证券", "银行")

    def sort_key(row: dict[str, str]) -> tuple[int, float]:
        is_financial = int(any(k in row.get("所处行业", "") for k in financial_keywords))
        return (is_financial, -(to_float(row.get("综合得分")) or 0))

    selected: list[dict[str, str]] = []
    seen = set()
    for row in sorted(rows, key=sort_key):
        industry = row.get("所处行业", "")
        if industry in seen:
            continue
        selected.append(row)
        seen.add(industry)
        if len(selected) >= limit:
            break
    return selected


def exchange_market_code(code: str) -> str:
    raw = code.split(".")[0]
    suffix = code.split(".")[1] if "." in code else ""
    if suffix == "SH" or raw.startswith(("60", "68", "90", "51")):
        return "sh" + raw
    return "sz" + raw


def fetch_exchange_kline(code: str) -> list[list[str]]:
    market_code = exchange_market_code(code)
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market_code},day,,,1200,qfq"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data", {}).get(market_code, {})
    return data.get("qfqday") or data.get("day") or []


def fetch_fund_nav(code: str, pages: int = 65) -> list[list[str]]:
    rows: list[list[str]] = []
    for page in range(1, pages + 1):
        params = urlencode({"fundCode": code, "pageIndex": page, "pageSize": 20})
        url = f"https://api.fund.eastmoney.com/f10/lsjz?{params}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://fundf10.eastmoney.com/"})
        with urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        items = payload.get("Data", {}).get("LSJZList", [])
        if not items:
            break
        for item in items:
            date = item.get("FSRQ", "")
            nav = item.get("DWJZ", "")
            rows.append([date, nav, nav, nav, nav, ""])
    rows.sort(key=lambda r: r[0])
    return rows[-1200:]


def fetch_item_kline(item: dict[str, str]) -> list[list[str]]:
    if item["类别"] == "基金":
        return fetch_fund_nav(item["代码"])
    return fetch_exchange_kline(item["代码"])


def write_kline_csv(item: dict[str, str], rows: list[list[str]]) -> Path:
    KLINE_DIR.mkdir(parents=True, exist_ok=True)
    safe_code = item["代码"].replace(".", "")
    path = KLINE_DIR / f"{item['类别']}-{safe_code}-5y-daily.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "open", "close", "high", "low", "volume"])
        writer.writerows(rows)
    return path


def write_svg_chart(item: dict[str, str], rows: list[list[str]]) -> Path:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    safe_code = item["代码"].replace(".", "")
    path = CHART_DIR / f"{item['类别']}-{safe_code}-5y-daily.svg"
    code, name = item["代码"], item["名称"]
    closes = [(r[0], to_float(r[2])) for r in rows if len(r) >= 3 and to_float(r[2]) is not None]
    width, height = 900, 260
    pad_l, pad_r, pad_t, pad_b = 48, 18, 24, 34
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b
    if len(closes) < 2:
        path.write_text(f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'><text x='20' y='40'>No data for {code}</text></svg>", encoding="utf-8")
        return path
    values = [v for _, v in closes if v is not None]
    lo, hi = min(values), max(values)
    span = hi - lo if hi > lo else 1
    pts = []
    for i, (_, v) in enumerate(closes):
        x = pad_l + i / (len(closes) - 1) * inner_w
        y = pad_t + (hi - (v or lo)) / span * inner_h
        pts.append(f"{x:.2f},{y:.2f}")
    start, end = closes[0][0], closes[-1][0]
    last = closes[-1][1]
    first = closes[0][1]
    ret = ((last or 0) / (first or 1) - 1) * 100 if first else 0
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="{pad_l}" y="18" font-size="14" font-family="Arial, sans-serif">{code} {name} 5年走势  {start} 至 {end}  区间涨跌 {ret:.1f}%</text>
<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height-pad_b}" stroke="#d0d7de"/>
<line x1="{pad_l}" y1="{height-pad_b}" x2="{width-pad_r}" y2="{height-pad_b}" stroke="#d0d7de"/>
<text x="4" y="{pad_t+5}" font-size="11" font-family="Arial, sans-serif">{hi:.2f}</text>
<text x="4" y="{height-pad_b}" font-size="11" font-family="Arial, sans-serif">{lo:.2f}</text>
<polyline points="{' '.join(pts)}" fill="none" stroke="#0969da" stroke-width="2"/>
<text x="{pad_l}" y="{height-10}" font-size="11" font-family="Arial, sans-serif">{start}</text>
<text x="{width-120}" y="{height-10}" font-size="11" font-family="Arial, sans-serif">{end}</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")
    return path


def calc_cagr(rows: list[list[str]]) -> float | None:
    closes = [(r[0], to_float(r[2])) for r in rows if len(r) >= 3 and to_float(r[2]) is not None]
    if len(closes) < 2:
        return None
    first = closes[0][1]
    last = closes[-1][1]
    if not first or not last or first <= 0:
        return None
    years = len(closes) / 252
    if years <= 0:
        return None
    return ((last / first) ** (1 / years) - 1) * 100


def make_item(category: str, code: str, name: str, direction: str, score: float, reason: str, risk: str) -> dict[str, str]:
    return {
        "类别": category,
        "代码": code,
        "名称": name,
        "方向": direction,
        "综合得分": f"{score:.2f}",
        "入选理由": reason,
        "主要风险": risk,
    }


def main() -> None:
    stock_rows = choose_stocks(5)
    stock_items = [
        make_item("股票", r["代码"], r["名称"], r["方向"], to_float(r["综合得分"]) or 0, r["入选理由"], r["主要风险"])
        for r in stock_rows
    ]
    etf_items = [make_item("ETF", *row) for row in ETF_POOL]
    fund_items = [make_item("基金", *row) for row in FUND_POOL]
    candidates = sorted(stock_items + etf_items + fund_items, key=lambda r: to_float(r["综合得分"]) or 0, reverse=True)
    qualified: list[tuple[dict[str, str], list[list[str]], float]] = []
    rejected: list[tuple[dict[str, str], str]] = []
    for item in candidates:
        rows = fetch_item_kline(item)
        cagr = calc_cagr(rows)
        if cagr is None:
            rejected.append((item, "5年走势数据不足，无法计算年化收益"))
            continue
        item["5年年化收益率"] = f"{cagr:.2f}%"
        if cagr < MIN_5Y_CAGR:
            rejected.append((item, f"5年年化收益率 {cagr:.2f}% 低于 {MIN_5Y_CAGR:.0f}% 硬门槛"))
            continue
        qualified.append((item, rows, cagr))

    # Keep at most five per category after annualized-return filtering and global ranking.
    counts: dict[str, int] = {}
    final_items: list[dict[str, str]] = []
    final_rows: dict[str, list[list[str]]] = {}
    for item, rows, _ in sorted(qualified, key=lambda x: to_float(x[0]["综合得分"]) or 0, reverse=True):
        counts[item["类别"]] = counts.get(item["类别"], 0) + 1
        if counts[item["类别"]] <= 5:
            final_items.append(item)
            final_rows[item["类别"] + item["代码"]] = rows
        if len(final_items) >= 10:
            break

    charts = []
    for item in final_items:
        rows = final_rows[item["类别"] + item["代码"]]
        csv_path = write_kline_csv(item, rows)
        chart_path = write_svg_chart(item, rows)
        charts.append((item, csv_path, chart_path))

    lines = [
        "# 一键 A股/港股观察池",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "策略：`one-click-ah-watchlist`",
        f"约束：股票、ETF、基金每类不超过 5 支，合计不超过 10 支；5年年化收益率必须 >= {MIN_5Y_CAGR:.0f}%；按综合得分排序取 Top 10 以内。",
        "用途：研究观察池，不构成投资建议。",
        "",
        "## 打分策略与权重",
        "",
        "### 股票评分",
        "",
        "| 维度 | 权重 | 说明 |",
        "| --- | ---: | --- |",
    ]
    lines += [f"| {k} | {v} | 用于衡量股票的{k}。 |" for k, v in STOCK_WEIGHT.items()]
    lines += [
        "",
        "### ETF评分",
        "",
        "| 维度 | 权重 | 说明 |",
        "| --- | ---: | --- |",
    ]
    lines += [f"| {k} | {v} | 用于衡量ETF的{k}。 |" for k, v in ETF_WEIGHT.items()]
    lines += [
        "",
        "### 基金评分",
        "",
        "| 维度 | 权重 | 说明 |",
        "| --- | ---: | --- |",
    ]
    lines += [f"| {k} | {v} | 用于衡量主动基金的{k}。 |" for k, v in FUND_WEIGHT.items()]
    lines += [
        "",
        "## 最终观察池",
        "",
        "| 排名 | 类别 | 代码 | 名称 | 方向 | 综合得分 | 入选理由 | 主要风险 |",
        "| ---: | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for idx, item in enumerate(final_items, 1):
        reason = item["入选理由"] + f" 5年年化收益率：{item['5年年化收益率']}。"
        lines.append(f"| {idx} | {item['类别']} | {item['代码']} | {item['名称']} | {item['方向']} | {item['综合得分']} | {reason} | {item['主要风险']} |")
    if not final_items:
        lines.append(f"| - | - | - | - | - | - | 当前候选池没有标的满足 5年年化收益率 >= {MIN_5Y_CAGR:.0f}% 的硬门槛。 | 放宽阈值或扩大候选池后再筛选。 |")
    lines += [
        "",
        "## 硬门槛剔除记录",
        "",
        "| 类别 | 代码 | 名称 | 剔除原因 |",
        "| --- | --- | --- | --- |",
    ]
    for item, reason in rejected:
        lines.append(f"| {item['类别']} | {item['代码']} | {item['名称']} | {reason} |")
    lines += [
        "",
        "## 入选标的5年走势",
        "",
    ]
    for item, csv_path, chart_path in charts:
        rel_csv = csv_path.relative_to(ROOT)
        rel_chart = chart_path.relative_to(REPORT.parent)
        lines += [
            f"### {item['类别']} {item['代码']} {item['名称']}",
            "",
            f"走势数据：`{rel_csv}`",
            "",
            f"![{item['代码']} 5年走势]({rel_chart.as_posix()})",
            "",
        ]
    lines += [
        "## 后续核验",
        "",
        "1. 股票：复核最新年报、季报、公告、减持、监管问询、现金流持续性和一次性收益。",
        "2. ETF：复核基金规模、成交额、跟踪误差、费率和成分股集中度。",
        "3. 基金：复核最新季报、基金经理、持仓、换手率、回撤和风格漂移。",
        "4. 每周更新价格和风险变化；每季度更新基本面和基金持仓。",
        "",
        f"独立股票筛选明细：`{INDEPENDENT_CSV.relative_to(ROOT)}`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT)
    print(f"items={len(final_items)} stocks={sum(i['类别']=='股票' for i in final_items)} etfs={sum(i['类别']=='ETF' for i in final_items)} funds={sum(i['类别']=='基金' for i in final_items)} charts={len(charts)}")


if __name__ == "__main__":
    main()
