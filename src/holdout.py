"""Round 3 holdout evaluation (HYPOTHESIS.md, Round 3). Run once, via `python run_all.py --holdout`.

Two untouched test sets: a backcast of the original universe before the development sample, and a
universe of ETFs never used in development. Primary test: S5 vs S1 at L = 252.
"""
import numpy as np
import pandas as pd

from src.analysis import bootstrap_sharpe, summarize
from src.backtest import simulate
from src.config import (ASSET_CLASS, COST_BPS, COST_BPS_STRESS, LOOKBACKS, NEW_ASSET_CLASS,
                        PRIMARY_LOOKBACK, RAW_DIR)
from src.data import load_holdout, load_rf
from src.signals import features, holdout_signal_dates, target_weights

ORDER = ["S5", "S1", "S3", "LongOnly"]      # S5 first, S1 second: bootstrap reports S5 minus S1
WINDOWS = {
    "backcast": {"2002 bear (2002-04 to 2002-10)": ("2002-04-01", "2002-10-09"),
                 "2003 rebound (2003-03 to 2003-12)": ("2003-03-12", "2003-12-31"),
                 "2006 May-June sell-off": ("2006-05-10", "2006-06-13")},
    "new": {"GFC (2008-09 to 2009-03)": ("2008-09-01", "2009-03-31"),
            "Momentum crash rebound (2009-03 to 2009-06)": ("2009-03-09", "2009-06-30"),
            "COVID crash (2020-02-20 to 2020-03-23)": ("2020-02-20", "2020-03-23"),
            "2022 rate shock (2022-01 to 2022-10)": ("2022-01-01", "2022-10-31")},
}


def _spy_excess(rf_index):
    spy = pd.read_csv(RAW_DIR / "SPY.csv", index_col="Date", parse_dates=True)["Close"]
    return spy.reindex(rf_index).pct_change()


def evaluate(which: str, results_dir) -> dict:
    opens, closes = load_holdout(which)
    rf = load_rf(closes.index)
    feats = features(closes)
    dates = holdout_signal_dates(closes, feats, max(LOOKBACKS))
    classes = ASSET_CLASS if which == "backcast" else NEW_ASSET_CLASS
    wfn = lambda lookback, sizing: target_weights(closes, feats, lookback, sizing, dates, rf, classes)

    daily, rows = {}, []
    for lookback in LOOKBACKS:
        for sizing in ("S1", "S3", "S5"):
            w = wfn(lookback, sizing)
            for cost in (COST_BPS, COST_BPS_STRESS):
                d = simulate(opens, closes, w, cost, rf=rf)
                rows.append({"lookback": lookback, "sizing": sizing, "cost_bps": cost, **summarize(d)})
                if lookback == PRIMARY_LOOKBACK and cost == COST_BPS:
                    daily[sizing] = d
    long_only = wfn(PRIMARY_LOOKBACK, "S1").abs()
    daily["LongOnly"] = simulate(opens, closes, long_only, COST_BPS, rf=rf)
    rows.append({"lookback": PRIMARY_LOOKBACK, "sizing": "LongOnly", "cost_bps": COST_BPS,
                 **summarize(daily["LongOnly"])})

    spy = _spy_excess(closes.index) - rf
    stress = []
    for name, (a, b) in WINDOWS[which].items():
        row = {"window": name, "SPY": (1 + spy.loc[a:b]).prod() - 1}
        for s in ORDER:
            part = daily[s].loc[a:b, "excess"]
            row[s] = (1 + part).prod() - 1 if len(part) else np.nan
        stress.append(row)

    n_assets = (closes.loc[dates].notna()).sum(axis=1)
    tables = {
        "variants": pd.DataFrame(rows),
        "bootstrap_sharpe": bootstrap_sharpe(pd.DataFrame({s: daily[s]["excess"] for s in ORDER})),
        "stress_windows": pd.DataFrame(stress).set_index("window"),
        "coverage": pd.Series({"first_signal": dates[0].date(), "last_signal": dates[-1].date(),
                               "month_ends": len(dates), "assets_at_start": int(n_assets.iloc[0]),
                               "assets_at_end": int(n_assets.iloc[-1])}),
    }
    for name, table in tables.items():
        table.to_csv(results_dir / f"holdout_{which}_{name}.csv")
    return tables
