"""Robustness checks on the fixed final specification (S3, L = 252) and its benchmark (S1, L = 252).

These are diagnostics, not new trials: nothing here is used to change the strategy.
All returns are in excess of cash (3-month T-bill), see backtest.simulate.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis import bootstrap_sharpe, summarize
from src.backtest import simulate
from src.config import ASSET_CLASS, COST_BPS, PRIMARY_LOOKBACK, RAW_DIR, TICKERS

FINAL, BENCH, LONG_ONLY = "S3", "S1", "LongOnly"
SWEEP = [21, 42, 63, 84, 105, 126, 168, 210, 252]
AUM_GRID = [1e6, 1e7, 1e8, 1e9, 1e10, 1e11]
MATCHED_VOL = 0.10
STRESS_WINDOWS = {
    "GFC (2008-09 to 2009-03)": ("2008-09-01", "2009-03-31"),
    "Momentum crash rebound (2009-03 to 2009-06)": ("2009-03-09", "2009-06-30"),
    "Taper tantrum (2013-05 to 2013-06)": ("2013-05-01", "2013-06-30"),
    "COVID crash (2020-02-20 to 2020-03-23)": ("2020-02-20", "2020-03-23"),
    "COVID rebound (2020-03-24 to 2020-06-30)": ("2020-03-24", "2020-06-30"),
    "2022 rate shock (2022-01 to 2022-10)": ("2022-01-01", "2022-10-31"),
}


def _sharpe(r: pd.Series) -> float:
    return r.mean() / r.std() * np.sqrt(252)


def _hac(y: pd.Series, X: pd.DataFrame | None = None, lags: int = 10):
    X = pd.DataFrame({"const": 1.0}, index=y.index) if X is None else sm.add_constant(X)
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})


def lag_check(opens, closes, rf, weights_by_sizing, period):
    """Fill late. A real edge should degrade gradually; lookahead would collapse."""
    rows = []
    for sizing in (BENCH, FINAL):
        for lag in (1, 2, 5):
            daily = simulate(opens, closes, weights_by_sizing[sizing], COST_BPS, exec_lag=lag, rf=rf)
            rows.append({"sizing": sizing, "fill_delay_days": lag,
                         "sharpe": _sharpe(daily.loc[period[0]:period[1], "excess"])})
    return pd.DataFrame(rows)


def lookback_sweep(opens, closes, rf, weights_fn, period):
    rows = []
    for lookback in SWEEP:
        for sizing in (BENCH, FINAL):
            daily = simulate(opens, closes, weights_fn(lookback, sizing), COST_BPS, rf=rf)
            rows.append({"lookback": lookback, "sizing": sizing,
                         "sharpe": _sharpe(daily.loc[period[0]:period[1], "excess"])})
    return pd.DataFrame(rows).pivot(index="lookback", columns="sizing", values="sharpe")


def matched_risk(seg):
    """Scale each strategy's excess returns to the same 10% vol, so size does not drive comparisons."""
    rows = {}
    for s, d in seg.items():
        k = MATCHED_VOL / (d["excess"].std() * np.sqrt(252))
        r = d["excess"] * k
        wealth = (1 + r).cumprod()
        rows[s] = {"scale_factor": k, "ann_excess_return": r.mean() * 252,
                   "max_drawdown": (wealth / wealth.cummax() - 1).min(),
                   "turnover_per_yr": d["turnover"].sum() / (len(d) / 252) * k,
                   "cost_drag_per_yr_5bps": d["turnover"].sum() / (len(d) / 252) * k * COST_BPS / 1e4}
    return pd.DataFrame(rows)


def by_year(seg):
    return pd.DataFrame({s: (1 + d["excess"]).groupby(d.index.year).prod() - 1 for s, d in seg.items()})


def by_asset_class(detail, rf, years):
    """Annualized excess P&L contribution (fraction of equity per year) and Sharpe of each sleeve."""
    pos_prev = detail["positions"].shift(1).fillna(0)
    excess_pnl = detail["pnl"].sub(pos_prev.mul(rf.reindex(pos_prev.index), axis=0))
    pnl = excess_pnl.T.groupby(ASSET_CLASS).sum().T
    return pd.DataFrame({"ann_contribution": pnl.sum() / years, "sleeve_sharpe": pnl.apply(_sharpe)})


def sharpe_difference(final_r, bench_r):
    """Is S3 better than S1? Scale S3 to S1's vol, then a HAC t-test on the daily difference."""
    diff = final_r * bench_r.std() / final_r.std() - bench_r
    res = _hac(diff)
    alpha = _hac(final_r, bench_r.rename("S1"))
    return {"sharpe_final": _sharpe(final_r), "sharpe_bench": _sharpe(bench_r),
            "vol_matched_ann_return_gap": diff.mean() * 252,
            "gap_hac_t": res.tvalues["const"], "gap_hac_p": res.pvalues["const"],
            "corr_final_bench": final_r.corr(bench_r),
            "alpha_on_S1_ann": alpha.params["const"] * 252,
            "alpha_on_S1_t": alpha.tvalues["const"], "beta_on_S1": alpha.params["S1"]}


def factor_exposure(r: pd.Series):
    f = pd.read_csv(RAW_DIR / "french_factors.csv", index_col="Date", parse_dates=True)
    df = f.join(r.rename("strategy"), how="inner")
    res = _hac(df["strategy"], df[["Mkt-RF", "SMB", "HML", "Mom"]], lags=5)
    out = {f"beta_{k}": v for k, v in res.params.drop("const").items()}
    out |= {f"t_{k}": v for k, v in res.tvalues.drop("const").items()}
    out |= {"alpha_ann": res.params["const"] * 252, "alpha_t": res.tvalues["const"],
            "r_squared": res.rsquared, "n_days": len(df), "last_factor_date": df.index[-1].date()}
    return out


def capacity(detail, daily, closes, period, fixed_bps=COST_BPS):
    """Square-root impact: cost per trade = fixed + daily_vol * sqrt(trade $ / ADV $)."""
    volume = pd.DataFrame({t: pd.read_csv(RAW_DIR / f"{t}.csv", index_col="Date",
                                          parse_dates=True)["Volume"] for t in TICKERS})
    adv = (closes * volume.reindex(closes.index)).rolling(20).mean().shift(1)  # known before trading
    sigma_d = closes.pct_change().rolling(60).std().shift(1)
    traded = detail["traded"].loc[period[0]:period[1]]
    d = daily.loc[period[0]:period[1]]
    years = len(d) / 252
    equity = (1 + daily["net"]).cumprod().shift(1).fillna(1).loc[traded.index]
    trade_days = traded.index[traded.sum(axis=1) > 0]

    fixed_drag = d["turnover"].sum() / years * fixed_bps / 1e4
    gross_mean = d["excess"].mean() * 252 + fixed_drag
    vol = d["excess"].std() * np.sqrt(252)
    rows = []
    for aum in AUM_GRID:
        dollars = traded.loc[trade_days].mul(equity.loc[trade_days], axis=0) * aum
        participation = dollars / adv.loc[trade_days]
        impact = sigma_d.loc[trade_days] * np.sqrt(participation)
        impact_drag = (traded.loc[trade_days] * impact).sum().sum() / years
        rows.append({"aum": aum, "net_sharpe": (gross_mean - fixed_drag - impact_drag) / vol,
                     "impact_drag_ann": impact_drag,
                     "median_participation": float(np.nanmedian(participation.where(dollars > 0))),
                     "max_participation": float(np.nanmax(participation.values))})
    return pd.DataFrame(rows), gross_mean / vol


def risk_profile(detail, daily, period):
    pos = detail["positions"].loc[period[0]:period[1]]
    r = daily.loc[period[0]:period[1], "excess"]
    wealth = (1 + r).cumprod()
    underwater = wealth < wealth.cummax()
    spells = (underwater != underwater.shift()).cumsum()[underwater]
    var_1 = r.quantile(0.01)
    by_class_gross = pos.abs().T.groupby(ASSET_CLASS).sum().T
    return {"avg_gross_exposure": pos.abs().sum(axis=1).mean(),
            "max_gross_exposure": pos.abs().sum(axis=1).max(),
            "avg_net_exposure": pos.sum(axis=1).mean(),
            "max_single_position": pos.abs().max().max(),
            "max_single_position_ticker": pos.abs().max().idxmax(),
            "max_class_gross": by_class_gross.max().max(),
            "max_class_gross_name": by_class_gross.max().idxmax(),
            "daily_var_99": var_1, "daily_cvar_99": r[r <= var_1].mean(),
            "worst_day": r.min(), "worst_day_date": r.idxmin().date(),
            "longest_drawdown_days": int(spells.value_counts().max()) if len(spells) else 0}


def stress_windows(seg, closes, rf):
    spy = closes["SPY"].pct_change() - rf
    rows = []
    for name, (a, b) in STRESS_WINDOWS.items():
        row = {"window": name, "SPY": (1 + spy.loc[a:b]).prod() - 1}
        for s, d in seg.items():
            part = d.loc[a:b, "excess"]
            row[s] = (1 + part).prod() - 1 if len(part) else np.nan
        rows.append(row)
    return pd.DataFrame(rows).set_index("window")


def run(opens, closes, rf, weights_fn, period, label, results_dir):
    """Run every check for one period. Returns a dict of tables and writes them to CSV."""
    weights = {s: weights_fn(PRIMARY_LOOKBACK, s) for s in (BENCH, FINAL)}
    # Baseline: same vol targeting as S1, always long, no trend signal.
    weights[LONG_ONLY] = weights[BENCH].abs()
    sims = {s: simulate(opens, closes, w, COST_BPS, detail=True, rf=rf) for s, w in weights.items()}
    daily = {s: d for s, (d, _) in sims.items()}
    seg = {s: d.loc[period[0]:period[1]] for s, d in daily.items()}
    years = len(seg[FINAL]) / 252

    excess = pd.DataFrame({s: seg[s]["excess"] for s in (FINAL, BENCH, LONG_ONLY)})
    tables = {
        "summary": pd.DataFrame({s: summarize(d) for s, d in seg.items()}),
        "bootstrap_sharpe": bootstrap_sharpe(excess),
        "matched_risk": matched_risk(seg),
        "lag_check": lag_check(opens, closes, rf, weights, period),
        "lookback_sweep": lookback_sweep(opens, closes, rf, weights_fn, period),
        "by_year": by_year(seg),
        "by_asset_class": by_asset_class(
            {k: v.loc[period[0]:period[1]] for k, v in sims[FINAL][1].items()}, rf, years),
        "sharpe_difference": pd.Series(sharpe_difference(seg[FINAL]["excess"], seg[BENCH]["excess"])),
        "factor_exposure": pd.DataFrame({s: factor_exposure(d["excess"]) for s, d in seg.items()}),
        "risk_profile": pd.DataFrame({s: risk_profile(sims[s][1], daily[s], period) for s in sims}),
        "stress_windows": stress_windows(seg, closes, rf),
    }
    cap, gross_sharpe = capacity(sims[FINAL][1], daily[FINAL], closes, period)
    tables["capacity"] = cap
    tables["capacity_gross_sharpe"] = pd.Series({"gross_sharpe": gross_sharpe})

    for name, table in tables.items():
        table.to_csv(results_dir / f"robust_{name}_{label}.csv")
    return tables
