"""Load the price panel. The out-of-sample period is removed unless final=True."""
import pandas as pd

from src.config import (BACKCAST_END, BACKCAST_START, HOLDOUT_DIR, IS_END, NEW_START, NEW_TICKERS,
                        RAW_DIR, SAMPLE_START, TICKERS)


def load_holdout(which: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Round 3 holdouts. 'backcast': the original 23 ETFs before the development sample, each entering
    once it trades (NaN before inception). 'new': the never-used ETF universe. Only run_all --holdout calls this."""
    if which == "backcast":
        tickers, folder, start, end = TICKERS, RAW_DIR, BACKCAST_START, BACKCAST_END
    elif which == "new":
        tickers, folder, start, end = NEW_TICKERS, HOLDOUT_DIR, NEW_START, None
    else:
        raise ValueError(which)
    opens, closes = {}, {}
    for t in tickers:
        df = pd.read_csv(folder / f"{t}.csv", index_col="Date", parse_dates=True)
        opens[t], closes[t] = df["Open"], df["Close"]
    opens, closes = pd.DataFrame(opens).loc[start:end], pd.DataFrame(closes).loc[start:end]
    # After inception there must be no gaps; before inception NaN is expected.
    for t in tickers:
        live = closes[t].loc[closes[t].first_valid_index():]
        if live.isna().any() or opens[t].loc[live.index].isna().any():
            raise ValueError(f"gap in {t} after inception")
    return opens, closes


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
