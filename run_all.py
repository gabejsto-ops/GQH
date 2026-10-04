"""Reproduce every number in the note.

    python data/download.py      # once
    python run_all.py            # in-sample only (development)
    python run_all.py --final    # adds the out-of-sample period; run once, at the end
"""
import argparse

import pandas as pd

from src.analysis import deflated_sharpe, h1_panel, h1_test, h3_test, h5a_test, summarize
from src.backtest import simulate
from src.config import (COST_BPS, COST_BPS_STRESS, IS_END, LOOKBACKS, OOS_START, PRIMARY_LOOKBACK,
                        RESULTS_DIR, SIZINGS)
from src.data import load_panel
from src.signals import common_signal_dates, features, target_weights


def main(final: bool) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    opens, closes = load_panel(final=final)
    feats = features(closes)
    dates = common_signal_dates(closes, feats, max(LOOKBACKS))
    periods = {"IS": (None, IS_END)} | ({"OOS": (OOS_START, None)} if final else {})

    rows, daily_by_variant = [], {}
    for lookback in LOOKBACKS:
        for sizing in SIZINGS:
            w = target_weights(closes, feats, lookback, sizing, dates)
            for cost in (COST_BPS, COST_BPS_STRESS):
                daily = simulate(opens, closes, w, cost)
                daily_by_variant[(lookback, sizing, cost)] = daily
                for period, (a, b) in periods.items():
                    rows.append({"lookback": lookback, "sizing": sizing, "cost_bps": cost,
                                 "period": period, **summarize(daily.loc[a:b])})
    table = pd.DataFrame(rows)

    # Deflated Sharpe over all strategy trials, in-sample, base cost.
    base = {k: v.loc[:IS_END, "net"] for k, v in daily_by_variant.items() if k[2] == COST_BPS}
    trial_srs = [r.mean() / r.std() for r in base.values()]
    dsr = {k: deflated_sharpe(r, trial_srs) for k, r in base.items()}
    table["dsr_prob"] = [dsr[(l, s, c)][0] if c == COST_BPS and p == "IS" else None
                         for l, s, c, p in table[["lookback", "sizing", "cost_bps", "period"]].values]

    suffix = "final" if final else "is"
    table.to_csv(RESULTS_DIR / f"variants_{suffix}.csv", index=False)
    for (l, s, c), daily in daily_by_variant.items():
        if l == PRIMARY_LOOKBACK and c == COST_BPS:
            daily.to_csv(RESULTS_DIR / f"daily_L{l}_{s}_{suffix}.csv")

    pd.set_option("display.width", 200, "display.float_format", "{:.3f}".format)
    print(f"Signals: {dates[0].date()} to {dates[-1].date()} ({len(dates)} month-ends)")
    print(f"Deflated Sharpe hurdle from {len(trial_srs)} trials (annualized SR): {next(iter(dsr.values()))[1]:.3f}\n")
    print(table.drop(columns=["start", "end"]).to_string(index=False))

    for period, (a, b) in periods.items():
        panel = h1_panel(opens, closes, feats, dates, PRIMARY_LOOKBACK).loc[a:b]
        for name, test in (("h1", h1_test), ("h3", h3_test), ("h5a", h5a_test)):
            res = pd.Series(test(panel), name=f"{name.upper()} ({period}, L={PRIMARY_LOOKBACK})")
            res.to_csv(RESULTS_DIR / f"{name}_{period}_{suffix}.csv")
            print(f"\n{res.name}\n{res.to_string()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true",
                        help="include the held-out period (2024-10-03 onward). Run once.")
    main(parser.parse_args().final)
