"""Reproduce every number in the note.

    python data/download.py      # once
    python run_all.py            # in-sample only (development)
    python run_all.py --final    # adds the out-of-sample period; run once, at the end
    python run_all.py --holdout  # Round 3: untouched backcast + new-ETF holdouts; run once
"""
import argparse

import pandas as pd

from src.analysis import deflated_sharpe, h1_panel, h1_test, h3_test, h5a_test, summarize
from src.backtest import simulate
from src.config import (ASSET_CLASS, COST_BPS, COST_BPS_STRESS, IS_END, LOOKBACKS, OOS_START, PRIMARY_LOOKBACK,
                        RESULTS_DIR, SIZINGS)
from src import figures, robustness
from src.data import load_panel, load_rf
from src.signals import common_signal_dates, features, target_weights


def main(final: bool, holdout: bool = False) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    if holdout:
        # Round 3 untouched test sets (backcast + new ETFs). Evaluated once.
        from src.holdout import evaluate
        pd.set_option("display.width", 200, "display.float_format", "{:.3f}".format)
        for which in ("backcast", "new"):
            print(f"\n===== Holdout: {which} =====")
            for name, table in evaluate(which, RESULTS_DIR).items():
                print(f"\n--- {name} ---\n{table.to_string()}")
        return
    opens, closes = load_panel(final=final)
    feats = features(closes)
    rf = load_rf(closes.index)
    dates = common_signal_dates(closes, feats, max(LOOKBACKS))
    periods = {"IS": (None, IS_END)} | ({"OOS": (OOS_START, None)} if final else {})

    rows, daily_by_variant = [], {}
    for lookback in LOOKBACKS:
        for sizing in SIZINGS:
            w = target_weights(closes, feats, lookback, sizing, dates, rf, ASSET_CLASS)
            for cost in (COST_BPS, COST_BPS_STRESS):
                daily = simulate(opens, closes, w, cost, rf=rf)
                daily_by_variant[(lookback, sizing, cost)] = daily
                for period, (a, b) in periods.items():
                    rows.append({"lookback": lookback, "sizing": sizing, "cost_bps": cost,
                                 "period": period, **summarize(daily.loc[a:b])})
    table = pd.DataFrame(rows)

    # Deflated Sharpe over all strategy trials, in-sample, base cost, excess of cash.
    base = {k: v.loc[:IS_END, "excess"] for k, v in daily_by_variant.items() if k[2] == COST_BPS}
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
    print("All metrics are in excess of cash (3-month T-bill) unless the column says incl_cash_carry.")
    print(f"Deflated Sharpe hurdle from {len(trial_srs)} trials (annualized SR): {next(iter(dsr.values()))[1]:.3f}\n")
    print(table.drop(columns=["start", "end"]).to_string(index=False))

    for period, (a, b) in periods.items():
        panel = h1_panel(opens, closes, feats, dates, PRIMARY_LOOKBACK, rf).loc[a:b]
        for name, test in (("h1", h1_test), ("h3", h3_test), ("h5a", h5a_test)):
            res = pd.Series(test(panel), name=f"{name.upper()} ({period}, L={PRIMARY_LOOKBACK})")
            res.to_csv(RESULTS_DIR / f"{name}_{period}_{suffix}.csv")
            print(f"\n{res.name}\n{res.to_string()}")

    weights_fn = lambda lookback, sizing: target_weights(closes, feats, lookback, sizing, dates, rf, ASSET_CLASS)
    for period, bounds in periods.items():
        tables = robustness.run(opens, closes, rf, weights_fn, bounds, f"{period}_{suffix}", RESULTS_DIR)
        print(f"\n===== Robustness: {period} (final S3 vs benchmark S1, L={PRIMARY_LOOKBACK}) =====")
        for name, table in tables.items():
            print(f"\n--- {name} ---\n{table.to_string()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true",
                        help="include the held-out period (2024-10-03 onward). Run once.")
    parser.add_argument("--holdout", action="store_true",
                        help="Round 3 untouched holdouts (backcast + new ETFs). Run once.")
    args = parser.parse_args()
    main(args.final, args.holdout)
