"""Load the price panel. The out-of-sample period is removed unless final=True."""
import pandas as pd

from src.config import IS_END, RAW_DIR, SAMPLE_START, TICKERS


def load_panel(final: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (opens, closes): adjusted prices, dates x tickers.

    With final=False (the default) every row after IS_END is dropped before anything else
    sees the data, so development code cannot touch the out-of-sample period by accident.
    """
    opens, closes = {}, {}
    for t in TICKERS:
        path = RAW_DIR / f"{t}.csv"
        if not path.exists():
            raise FileNotFoundError(f"{path} missing: run `python data/download.py` first")
        df = pd.read_csv(path, index_col="Date", parse_dates=True)
        opens[t], closes[t] = df["Open"], df["Close"]

    opens = pd.DataFrame(opens).loc[SAMPLE_START:]
    closes = pd.DataFrame(closes).loc[SAMPLE_START:]
    if not final:
        opens, closes = opens.loc[:IS_END], closes.loc[:IS_END]

    if opens.isna().any().any() or closes.isna().any().any():
        raise ValueError("missing prices in sample; see data/download.py coverage report")
    return opens, closes


def load_rf(index: pd.DatetimeIndex) -> pd.Series:
    """Daily risk-free return on each trading day: 3-month T-bill rate (FRED DTB3) / 252.

    Uses the latest rate published on or before each day (forward-filled over holidays).
    """
    path = RAW_DIR / "tbill.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing: run `python data/download.py` first")
    rate = pd.read_csv(path, index_col="Date", parse_dates=True)["DTB3"]
    daily = rate.reindex(rate.index.union(index)).ffill().reindex(index)
    if daily.isna().any():
        raise ValueError("risk-free rate missing for part of the sample")
    return daily / 100 / 252
