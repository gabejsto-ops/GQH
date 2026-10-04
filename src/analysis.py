"""Performance metrics, Deflated Sharpe Ratio, and the H1 mechanism test."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.backtest import forward_returns
from src.config import ER_THRESHOLD
from src.signals import trailing_return


def summarize(daily: pd.DataFrame, col: str | None = None) -> dict:
    """Headline metrics on excess-of-cash returns when available (see simulate), else net returns."""
    col = col or ("excess" if "excess" in daily else "net")
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
        "sharpe_incl_cash_carry": daily["net"].mean() / daily["net"].std() * np.sqrt(252),
    }


def bootstrap_sharpe(returns: pd.DataFrame, n_boot: int = 2000, block: int = 21,
                     seed: int = 0) -> pd.DataFrame:
    """Moving-block bootstrap 95% intervals for the annualized Sharpe of each column, plus the
    difference between the first two columns (same resampled blocks, so the pairing is kept)."""
    rng = np.random.default_rng(seed)
    x = returns.dropna().values
    n = len(x)
    n_blocks = int(np.ceil(n / block))
    sharpes = np.empty((n_boot, x.shape[1]))
    for b in range(n_boot):
        starts = rng.integers(0, n - block + 1, n_blocks)
        sample = np.concatenate([x[s:s + block] for s in starts])[:n]
        sharpes[b] = sample.mean(0) / sample.std(0, ddof=1) * np.sqrt(252)
    point = x.mean(0) / x.std(0, ddof=1) * np.sqrt(252)
    out = pd.DataFrame({"sharpe": point, "ci_low": np.percentile(sharpes, 2.5, 0),
                        "ci_high": np.percentile(sharpes, 97.5, 0),
                        "p_sharpe_le_0": (sharpes <= 0).mean(0)}, index=returns.columns)
    if x.shape[1] >= 2:
        d = sharpes[:, 0] - sharpes[:, 1]
        out.loc[f"{returns.columns[0]} minus {returns.columns[1]}"] = [
            point[0] - point[1], np.percentile(d, 2.5), np.percentile(d, 97.5), (d <= 0).mean()]
    return out


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


def h1_panel(opens, closes, feats, dates, lookback, rf=None) -> pd.DataFrame:
    """One row per asset-month: risk-scaled TSMOM outcome (in excess of cash if rf) plus state labels."""
    sign = np.sign(trailing_return(closes, lookback)).loc[dates]
    outcome = sign * forward_returns(opens, dates, rf) / feats["vol_short"].loc[dates]
    panel = pd.DataFrame({
        "outcome": outcome.stack(),
        "high_vol": feats["high_vol"].loc[dates].stack().astype(bool),
        "shock": feats["shock"].loc[dates].stack(),
        "er": feats["er"].loc[dates].stack(),
    }).dropna()
    panel.index.names = ["date", "ticker"]
    return panel


def _clustered_ols(df: pd.DataFrame, regressor: pd.Series):
    X = sm.add_constant(regressor.astype(float))
    groups = df.index.get_level_values("date").factorize()[0]
    return sm.OLS(df["outcome"], X).fit(cov_type="cluster", cov_kwds={"groups": groups})


def h3_test(panel: pd.DataFrame) -> dict:
    """Round 2, H3: outcome rises continuously with ER among high-vol asset-months."""
    hv = panel[panel["high_vol"]]
    ols = _clustered_ols(hv, hv["er"])
    return {"n": len(hv), "slope_on_er": ols.params["er"],
            "clustered_t": ols.tvalues["er"], "clustered_p": ols.pvalues["er"]}


def h5a_test(panel: pd.DataFrame) -> dict:
    """Round 2, H5a: among calm asset-months, efficient (ER > threshold) trend more."""
    calm = panel[~panel["high_vol"]]
    efficient = calm["er"] > ER_THRESHOLD
    eff, ineff = calm.loc[efficient, "outcome"], calm.loc[~efficient, "outcome"]
    welch = stats.ttest_ind(eff, ineff, equal_var=False)
    ols = _clustered_ols(calm, efficient.rename("efficient"))
    return {"n_calm_efficient": len(eff), "n_calm_inefficient": len(ineff),
            "mean_calm_efficient": eff.mean(), "mean_calm_inefficient": ineff.mean(),
            "difference": eff.mean() - ineff.mean(), "welch_t": welch.statistic,
            "welch_p": welch.pvalue, "clustered_t": ols.tvalues["efficient"],
            "clustered_p": ols.pvalues["efficient"]}


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
