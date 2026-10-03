"""Download daily split- and dividend-adjusted bars for the pre-registered universe.

Source: Yahoo Finance via yfinance (auto_adjust=True adjusts open/high/low/close for
splits and dividends). Raw files go to data/raw/ and are not committed.

Usage:  python data/download.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

UNIVERSE = {
    "Equities": ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "EWZ", "FXI"],
    "Bonds": ["SHY", "IEF", "TLT", "LQD", "HYG", "TIP"],
    "Commodities": ["GLD", "SLV", "DBC", "USO", "DBA"],
    "Currencies": ["UUP", "FXE", "FXY"],
    "Real estate": ["VNQ"],
}
TICKERS = [t for group in UNIVERSE.values() for t in group]
RAW_DIR = Path(__file__).resolve().parent / "raw"


def download(start: str = "2000-01-01") -> dict[str, pd.DataFrame]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    frames = {}
    for ticker in TICKERS:
        df = yf.download(ticker, start=start, auto_adjust=True, progress=False, multi_level_index=False)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
        df.index.name = "Date"
        df.to_csv(RAW_DIR / f"{ticker}.csv")
        frames[ticker] = df
    return frames


def coverage_report(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Data-quality checks only: dates, gaps, and suspicious one-day jumps (bad prints or
    missing split adjustments). Deliberately reports no strategy or performance numbers."""
    rows = []
    for ticker, df in frames.items():
        jumps = df["Close"].pct_change().abs()
        rows.append({
            "ticker": ticker,
            "first": df.index.min().date(),
            "last": df.index.max().date(),
            "bars": len(df),
            "missing_close": int(df["Close"].isna().sum()),
            "zero_volume_days": int((df["Volume"] == 0).sum()),
            "days_abs_move_gt_25pct": int((jumps > 0.25).sum()),
        })
    return pd.DataFrame(rows).set_index("ticker")


if __name__ == "__main__":
    report = coverage_report(download())
    print(report.to_string())
    print(f"\nCommon start (all {len(TICKERS)} assets trading): {max(report['first'])}")
