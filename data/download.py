"""Download daily split- and dividend-adjusted bars for the pre-registered universe.

Sources: Yahoo Finance via yfinance (auto_adjust=True adjusts open/high/low/close for
splits and dividends), and the Kenneth French Data Library (daily Fama-French factors and momentum,
for the factor-exposure check). Raw files go to data/raw/ and are not committed.

Usage:  python data/download.py
"""
from __future__ import annotations

import io
import urllib.request
import zipfile
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


FRENCH_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{}_CSV.zip"
FRENCH_FILES = {"ff3": "F-F_Research_Data_Factors_daily", "mom": "F-F_Momentum_Factor_daily"}


def download_french() -> pd.DataFrame:
    """Daily Mkt-RF, SMB, HML, RF and Mom, in decimal returns."""
    parts = []
    for name in FRENCH_FILES.values():
        with urllib.request.urlopen(FRENCH_URL.format(name)) as resp:
            raw = zipfile.ZipFile(io.BytesIO(resp.read()))
        text = raw.read(raw.namelist()[0]).decode("latin-1").splitlines()
        start = next(i for i, line in enumerate(text) if line.strip().startswith(","))
        rows = [line for line in text[start + 1:] if line[:8].strip().isdigit()]
        df = pd.read_csv(io.StringIO("\n".join(rows)), header=None, index_col=0)
        df.columns = [c.strip() for c in text[start].split(",")[1:]]
        df.index = pd.to_datetime(df.index.astype(str), format="%Y%m%d")
        parts.append(df / 100)
    factors = pd.concat(parts, axis=1).dropna()
    factors.index.name = "Date"
    factors.to_csv(RAW_DIR / "french_factors.csv")
    return factors


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
    factors = download_french()
    print(f"French factors: {factors.index.min().date()} to {factors.index.max().date()}, "
          f"columns {list(factors.columns)}\n")
    print(report.to_string())
    print(f"\nCommon start (all {len(TICKERS)} assets trading): {max(report['first'])}")
