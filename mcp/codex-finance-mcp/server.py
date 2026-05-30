from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from mcp.server.fastmcp import FastMCP

try:
    import akshare as ak
except Exception as exc:  # pragma: no cover - surfaced by data_source_status
    ak = None
    AKSHARE_IMPORT_ERROR = repr(exc)
else:
    AKSHARE_IMPORT_ERROR = ""


HOME = Path(os.environ.get("CODEX_FINANCE_HOME", r"E:\ai\CodexFinance"))
DATA_DIR = HOME / "data"
NOTES_DIR = HOME / "notes"
DB_PATH = DATA_DIR / "codex_finance.sqlite"

mcp = FastMCP("codex-finance")


def _records(df: pd.DataFrame, limit: int = 20) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    safe = df.head(limit).where(pd.notnull(df), None)
    return json.loads(safe.to_json(orient="records", force_ascii=False))


def _require_akshare() -> Any:
    if ak is None:
        raise RuntimeError(f"akshare is unavailable: {AKSHARE_IMPORT_ERROR}")
    return ak


def _normalize_market_code(symbol: str) -> tuple[str, str]:
    raw = symbol.strip().upper()
    if raw.endswith(".HK"):
        return "hk", raw.split(".")[0].zfill(5)
    if raw.endswith(".SH") or raw.endswith(".SZ"):
        return "a", raw.split(".")[0]
    if raw.startswith("HK"):
        return "hk", raw[2:].zfill(5)
    if len(raw) <= 5 and raw.isdigit():
        return "hk", raw.zfill(5)
    return "a", raw


@mcp.tool()
def data_source_status() -> dict[str, Any]:
    """Return local data source availability for the finance MCP server."""
    return {
        "home": str(HOME),
        "database": str(DB_PATH),
        "akshare_available": ak is not None,
        "akshare_error": AKSHARE_IMPORT_ERROR,
        "alpha_vantage_key_present": bool(os.environ.get("ALPHA_VANTAGE_API_KEY")),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


@mcp.tool()
def get_zh_quote(symbol: str) -> dict[str, Any]:
    """Get a quick quote snapshot for an A-share or Hong Kong stock."""
    aks = _require_akshare()
    market, code = _normalize_market_code(symbol)
    if market == "hk":
        df = aks.stock_hk_spot_em()
        matches = df[df.astype(str).apply(lambda row: code in row.to_string(), axis=1)]
    else:
        df = aks.stock_zh_a_spot_em()
        matches = df[df.astype(str).apply(lambda row: code in row.to_string(), axis=1)]
    return {
        "symbol": symbol,
        "market": market,
        "source": "AKShare",
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "records": _records(matches, 5),
    }


@mcp.tool()
def get_zh_history(symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> dict[str, Any]:
    """Get daily historical prices. Dates use YYYYMMDD. adjust can be qfq, hfq, or empty."""
    aks = _require_akshare()
    market, code = _normalize_market_code(symbol)
    if market == "hk":
        df = aks.stock_hk_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
    else:
        df = aks.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
    return {
        "symbol": symbol,
        "market": market,
        "source": "AKShare",
        "start_date": start_date,
        "end_date": end_date,
        "records": _records(df, 200),
    }


@mcp.tool()
def get_financial_indicators(symbol: str) -> dict[str, Any]:
    """Get A-share financial analysis indicators when available."""
    aks = _require_akshare()
    market, code = _normalize_market_code(symbol)
    if market != "a":
        return {"symbol": symbol, "market": market, "error": "Financial indicators currently support A-shares via AKShare."}
    df = aks.stock_financial_analysis_indicator(symbol=code)
    return {
        "symbol": symbol,
        "market": market,
        "source": "AKShare",
        "records": _records(df, 80),
    }


@mcp.tool()
def save_stock_note(symbol: str, title: str, content: str) -> dict[str, str]:
    """Save a Markdown research note for a stock."""
    market, code = _normalize_market_code(symbol)
    folder = NOTES_DIR / f"{code}.{market}"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = folder / f"{stamp}-{title.strip().replace(' ', '-')}.md"
    path.write_text(content, encoding="utf-8")
    return {"path": str(path)}


@mcp.tool()
def search_stock_notes(query: str, limit: int = 20) -> list[dict[str, str]]:
    """Search local Markdown notes by plain text."""
    results: list[dict[str, str]] = []
    if not NOTES_DIR.exists():
        return results
    needle = query.lower()
    for path in NOTES_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if needle in text.lower() or needle in path.name.lower():
            excerpt = text[:500].replace("\n", " ")
            results.append({"path": str(path), "excerpt": excerpt})
            if len(results) >= limit:
                break
    return results


@mcp.tool()
def run_sqlite_query(sql: str) -> dict[str, Any]:
    """Run a read-only SQLite query against the local research database."""
    stripped = sql.strip().lower()
    if not stripped.startswith("select") and not stripped.startswith("with"):
        return {"error": "Only SELECT/WITH queries are allowed."}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(sql, conn)
    return {"database": str(DB_PATH), "records": _records(df, 500)}


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    mcp.run()
