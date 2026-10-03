"""Performance metrics, Deflated Sharpe Ratio, and the H1 mechanism test."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.backtest import forward_returns
from src.signals import trailing_return


def summarize(daily: pd.DataFrame, col: str = "net") -> dict:
    r = daily[col]
    years = len(r) / 252
    wealth = (1 + r).cumprod()
    monthly = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    return {
        "start": r.index[0].date(),
        "end": r.index[-1].date(),
        "ann_return": wealth.iloc[-1] ** (1 / years) - 1,
        "ann_vol": r.std() * np.sqrt(252),
        "sharpe": r.mean() / r.std() * np.sqrt(252),
        "max_drawdown": (wealth / wealth.cummax() - 1).min(),
        "turnover_per_yr": daily["turnover"].sum() / years,
        "worst_month": monthly.min(),
        "skew": stats.skew(r),
    }


def deflated_sharpe(r: pd.Series, trial_sharpes_daily: list[float]) -> tuple[float, float]:
    """Bailey & Lopez de Prado (2014). Returns (DSR probability, annualized SR hurdle from N trials)."""
    n_trials = len(trial_sharpes_daily)
    sr = r.mean() / r.std()
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    emc = 0.5772156649
    sr0 = np.sqrt(np.var(trial_sharpes_daily, ddof=1)) * (
        (1 - emc) * stats.norm.ppf(1 - 1 / n_trials)
        + emc * stats.norm.ppf(1 - 1 / (n_trials * np.e)))
    z = (sr - sr0) * np.sqrt(len(r) - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return float(stats.norm.cdf(z)), float(sr0 * np.sqrt(252))


def h1_panel(opens, closes, feats, dates, lookback) -> pd.DataFrame:
    """One row per asset-month: risk-scaled TSMOM outcome plus state labels."""
    sign = np.sign(trailing_return(closes, lookback)).loc[dates]
    outcome = sign * forward_returns(opens, dates) / feats["vol_short"].loc[dates]
    panel = pd.DataFrame({
        "outcome": outcome.stack(),
        "high_vol": feats["high_vol"].loc[dates].stack().astype(bool),
        "shock": feats["shock"].loc[dates].stack(),
    }).dropna()
    panel.index.names = ["date", "ticker"]
    return panel


def h1_test(panel: pd.DataFrame) -> dict:
    hv = panel[panel["high_vol"]]
    eff, ineff = hv.loc[hv["shock"], "outcome"], hv.loc[~hv["shock"], "outcome"]
    calm = panel.loc[~panel["high_vol"], "outcome"]
    welch = stats.ttest_ind(eff, ineff, equal_var=False)
    X = sm.add_constant(hv["shock"].astype(float))
    ols = sm.OLS(hv["outcome"], X).fit(
        cov_type="cluster", cov_kwds={"groups": hv.index.get_level_values("date").factorize()[0]})
    return {
        "n_high_vol_efficient": len(eff),
        "n_high_vol_inefficient": len(ineff),
        "n_calm": len(calm),
        "mean_high_vol_efficient": eff.mean(),
        "mean_high_vol_inefficient": ineff.mean(),
        "mean_calm": calm.mean(),
        "difference": eff.mean() - ineff.mean(),
        "welch_t": welch.statistic,
        "welch_p": welch.pvalue,
        "clustered_t": ols.tvalues["shock"],
        "clustered_p": ols.pvalues["shock"],
    }
