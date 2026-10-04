# Decision log

Every choice made after HYPOTHESIS.md was committed, in order. Changes to the strategy itself are
also counted as trials in VARIANTS.md.

## 2026-10-03: Data (before any returns or backtests were computed)

- **Source: Yahoo Finance adjusted daily bars (yfinance, `auto_adjust=True`) instead of the Webull
  OpenAPI.** Reason: reproducibility. Judges must be able to rerun the code, and Webull requires
  approved credentials (1–2 working days). Webull can be used as a cross-check later. Not a trial:
  the hypothesis allowed a cited fallback, and no results had been seen.
- **Sample:** 2007-04-11 (HYG inception, the last of the 23 to start trading) to 2026-10-02.
- **Out-of-sample cutoff:** 19.5 years of history; 20% would be 3.9 years, so the 2-year cap applies.
  **In-sample: 2007-04-11 → 2024-10-02. Out-of-sample: 2024-10-03 → 2026-10-02, evaluated once.**
  The first ~1 year of in-sample is warm-up for the 252-day signals.
- **Data checks** (`python data/download.py`): no missing closes in the sample. Four one-day moves
  above 25% were checked and are genuine: EWZ 2008-10-13, USO 2020-03-09 and 2020-04-21,
  SLV 2026-01-30. USO's 1-for-8 reverse split (2020-04-28) is correctly adjusted.
  Zero-volume days occur only before the sample start or in UUP's launch week (2007-03-15).

## 2026-10-03: Implementation details (code written before any backtest was run)

Points HYPOTHESIS.md left open, fixed here before seeing results:

- **High-vol state:** the asset's 21-day realized vol on the signal date is above the 75th percentile
  of its own 21-day vol over the trailing 252 trading days (including the signal date).
- **Timing:** signals use the close of the last trading day of each month; trades fill at the next
  day's open (adjusted). Positions drift with prices between rebalances (no daily rebalancing).
- **Costs:** charged on traded notional at each rebalance: 5 bps per side, plus a 10 bps run.
  No borrow cost on shorts and no interest on cash (limitation, see note).
- **Common start:** all 9 variants start on the same date, the first month-end where every input
  (252-day return, 252-day vol, the vol-state percentile) is available for all 23 assets.
- **H1 test:** unit = asset-month. Outcome = signal × next-month return (open-to-open between
  execution days), divided by the 60-day vol at the signal date. Among high-vol asset-months, compare
  efficient vs inefficient means: Welch t-test, and an OLS on an efficient dummy with standard errors
  clustered by month. Primary lookback L = 252.
- **Deflated Sharpe:** Bailey & López de Prado (2014), with N = 9 and the variance of the 9 variants'
  daily Sharpe ratios at the 5 bps cost level.

## 2026-10-03: Final strategy selected (after Round 2, before robustness tests and OOS)

- **Primary strategy: S3 (Bayesian confidence sizing) at L = 252. Benchmark: S1 at L = 252.**
- L = 252 is the lookback pre-registered as primary in HYPOTHESIS.md. S3 at 126d had the highest
  in-sample Sharpe, but choosing it would be selecting on results; it is reported as a variant only.
- No parameters change from here on. Robustness checks are diagnostics on this fixed specification.
