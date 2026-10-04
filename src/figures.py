"""Figures for the quant note. Written to note/figures/ by `python run_all.py --final`
(figure 2 also reads the holdout tables written by `python run_all.py --holdout`)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.backtest import simulate
from src.config import COST_BPS, IS_END, OOS_START, PRIMARY_LOOKBACK, RESULTS_DIR, ROOT

FIG_DIR = ROOT / "note" / "figures"
# Reference categorical palette, slots 1-3 (validated all-pairs); text in ink tokens.
COLORS = {"S5": "#2a78d6", "S1": "#eb6834", "LongOnly": "#1baf7a"}
NAMES = {"S5": "S5 risk-premium prior (ours)", "S1": "S1 standard TSMOM", "LongOnly": "Long-only, no signal"}
SHORT = {"S5": "S5 prior (ours)", "S1": "S1 TSMOM", "LongOnly": "Long-only"}
ORDER = ("S5", "S1", "LongOnly")
INK, INK_2, GRID, OOS_FILL = "#0b0b0b", "#52514e", "#e4e3df", "#f1f0ec"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def equity_curves(opens, closes, rf, weights_fn):
    """Growth of $1 in excess of cash, each scaled to 10% vol using in-sample vol only."""
    w = {s: weights_fn(PRIMARY_LOOKBACK, s) for s in ("S1", "S5")}
    w["LongOnly"] = w["S1"].abs()
    fig, ax = plt.subplots(figsize=(6.8, 2.4))
    end_values = {}
    for s in ("LongOnly", "S1", "S5"):
        r = simulate(opens, closes, w[s], COST_BPS, rf=rf)["excess"]
        k = 0.10 / (r.loc[:IS_END].std() * np.sqrt(252))
        wealth = (1 + k * r).cumprod()
        ax.plot(wealth.index, wealth, color=COLORS[s], lw=1.4 if s == "S5" else 1.1, label=NAMES[s])
        end_values[s] = wealth
    ax.axvspan(pd.Timestamp(OOS_START), wealth.index[-1], color=OOS_FILL, zorder=0)
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator([0.8, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:.2f}"))
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_ylabel("Growth of $1 over cash")
    ax.set_xlim(wealth.index[0], wealth.index[-1] + pd.Timedelta(days=900))
    ax.text(pd.Timestamp(OOS_START) + pd.Timedelta(days=20), ax.get_ylim()[0] * 1.03,
            "2024–26\n(already seen)", va="bottom", ha="left", color=INK_2, fontsize=7)
    # Direct labels at line ends, spread by rank so they never collide.
    order = sorted(end_values, key=lambda k: end_values[k].iloc[-1], reverse=True)
    for rank, s in enumerate(order):
        wealth = end_values[s]
        ax.annotate(SHORT[s], (wealth.index[-1], wealth.iloc[-1]), xytext=(5, 9 - 9 * rank),
                    textcoords="offset points", color=INK, fontsize=7.5, va="center")
    ax.legend(loc="upper left", ncol=1, fontsize=7.5, handlelength=1.6)
    fig.savefig(FIG_DIR / "fig1_equity.png")
    plt.close(fig)


def _panel_data():
    """(title, {strategy: (sharpe, lo, hi, naive)}) for each of the four test sets."""
    panels = []
    for period, title in (("IS", "Development\n2008–2024"), ("OOS", "2024–2026\n(already seen)")):
        boot = pd.read_csv(RESULTS_DIR / f"robust_bootstrap_sharpe_{period}_final.csv", index_col=0)
        summ = pd.read_csv(RESULTS_DIR / f"robust_summary_{period}_final.csv", index_col=0)
        panels.append((title, {s: (*boot.loc[s, ["sharpe", "ci_low", "ci_high"]],
                                   float(summ.loc["sharpe_incl_cash_carry", s])) for s in ORDER}))
    for which, title in (("backcast", "Holdout: backcast\n2001–2007"), ("new", "Holdout: 30 new ETFs\n2008–2026")):
        boot = pd.read_csv(RESULTS_DIR / f"holdout_{which}_bootstrap_sharpe.csv", index_col=0)
        var = pd.read_csv(RESULTS_DIR / f"holdout_{which}_variants.csv", index_col=0)
        var = var[(var.lookback == PRIMARY_LOOKBACK) & (var.cost_bps == COST_BPS)].set_index("sizing")
        panels.append((title, {s: (*boot.loc[s, ["sharpe", "ci_low", "ci_high"]],
                                   float(var.loc[s, "sharpe_incl_cash_carry"])) for s in ORDER}))
    return panels


def sharpe_intervals():
    """Dot-and-whisker per test set: excess Sharpe with 95% bootstrap CI; hollow = naive incl. cash carry."""
    panels = _panel_data()
    fig, axes = plt.subplots(1, 4, figsize=(6.8, 1.9), sharex=True, sharey=True)
    for ax, (title, vals) in zip(axes, panels):
        for i, s in enumerate(ORDER):
            y = 2 - i
            pt, lo, hi, naive = vals[s]
            ax.plot([lo, hi], [y, y], color=COLORS[s], lw=1.5, solid_capstyle="round")
            ax.plot(naive, y, "o", ms=4.5, mfc="white", mec=COLORS[s], mew=1.1, zorder=3)
            ax.plot(pt, y, "o", ms=5, color=COLORS[s], mec="white", mew=1.0, zorder=4)
            ax.text(pt, y + 0.3, f"{pt:.2f}", ha="center", color=INK, fontsize=7)
        ax.axvline(0, color=INK_2, lw=0.8)
        ax.set_title(title, fontsize=7.5, color=INK, loc="left")
        ax.grid(axis="y", visible=False)
        ax.set_ylim(-0.6, 2.75)
        ax.set_xlim(-0.8, 1.9)
        ax.set_xticks([0, 1.0])
    axes[0].set_yticks([2, 1, 0], [SHORT[s] for s in ORDER])
    fig.supxlabel("Annualized Sharpe over cash, net of 5 bps (L = 252)", fontsize=8, color=INK_2, y=-0.06)
    fig.text(0.0, -0.17, "●  excess of cash, 95% block-bootstrap CI     ○  naive Sharpe incl. T-bill carry",
             color=INK_2, fontsize=7.5)
    fig.savefig(FIG_DIR / "fig2_sharpe_ci.png")
    plt.close(fig)


def lookback_plateau():
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 1.7), sharey=True)
    for ax, period in zip(axes, ("IS", "OOS")):
        sweep = pd.read_csv(RESULTS_DIR / f"robust_lookback_sweep_{period}_final.csv", index_col=0)
        for s in ("S1", "S5"):
            ax.plot(sweep.index, sweep[s], color=COLORS[s], lw=1.4, marker="o", ms=3.5, label=SHORT[s])
        ax.axvline(PRIMARY_LOOKBACK, color=INK_2, lw=0.8, ls=":")
        ax.axhline(0, color=INK_2, lw=0.8)
        ax.set_title({"IS": "Development 2008–2024", "OOS": "2024–2026 (already seen)"}[period],
                     fontsize=8.5, color=INK, loc="left")
    fig.supxlabel("Lookback (trading days); dotted line = pre-registered 252",
                  fontsize=8.5, color=INK_2, y=-0.14)
    axes[0].set_ylabel("Excess Sharpe")
    axes[0].legend(loc="lower right", fontsize=7.5)
    fig.savefig(FIG_DIR / "fig3_plateau.png")
    plt.close(fig)


def policy_curves():
    """Position (fraction of the vol-target weight) vs trailing 12-month Sharpe, L = 252 (se = 1)."""
    from scipy.stats import norm
    s = np.linspace(-3, 3, 601)
    curves = {
        "S1 TSMOM: sign": (np.sign(s), COLORS["S1"], "-"),
        "S3 flat prior": (2 * norm.cdf(s) - 1, "#4a3aa7", "-"),   # palette slot 7; aqua means long-only elsewhere
        "S5, no-premium asset (m₀ = 0)": (2 * norm.cdf(s / np.sqrt(2)) - 1, COLORS["S5"], "--"),
        "S5, premium asset (m₀ = 0.3)": (2 * norm.cdf((s + 0.3) / np.sqrt(2)) - 1, COLORS["S5"], "-"),
    }
    fig, ax = plt.subplots(figsize=(6.8, 2.0))
    ax.axhline(0, color=INK_2, lw=0.8)
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.axhline(1, color=INK_2, lw=0.8, ls=":")
    ax.text(-2.95, 1.04, "long-only", color=INK_2, fontsize=7, va="bottom")
    for label, (y, color, ls) in curves.items():
        ax.plot(s, y, color=color, ls=ls, lw=1.6 if "premium asset" in label else 1.2, label=label)
    ax.annotate("S5 turns short only below −0.3", xy=(-0.3, 0), xytext=(-2.9, 0.45), fontsize=7.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.7))
    ax.set_xlabel("Trailing 12-month Sharpe of the asset (the evidence)")
    ax.set_ylabel("Position")
    ax.set_xlim(-3, 3)
    ax.set_ylim(-1.15, 1.25)
    ax.legend(loc="lower right", fontsize=7.5, handlelength=2.2)
    fig.savefig(FIG_DIR / "fig0_policy.png")
    plt.close(fig)


def make_all(opens, closes, rf, weights_fn):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    policy_curves()
    equity_curves(opens, closes, rf, weights_fn)
    sharpe_intervals()
    lookback_plateau()
