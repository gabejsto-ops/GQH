# Variants and hypotheses tested

Every strategy variant or hypothesis test run, in order, including the ones that failed.
Full numbers: `results/variants_is.csv`, `results/h1_IS_is.csv` (reproduce with `python run_all.py`).

## Round 1: pre-registered set, in-sample 2008-05 to 2024-10 (9 trials)

Net Sharpe at 5 bps (10 bps in brackets). Deflated Sharpe hurdle for 9 trials: 0.27.

| Lookback | S0 sign only | S1 vol target | S2 conditional (ours) |
|---|---|---|---|
| 63d  | 0.20 (0.17) | 0.46 (0.36) | 0.46 (0.36) |
| 126d | 0.33 (0.31) | 0.61 (0.54) | 0.61 (0.54) |
| 252d | 0.08 (0.06) | 0.45 (0.39) | 0.45 (0.39) |

- **Vol targeting works:** S1 beats S0 at every lookback, as in the literature.
- **H2 (S2 beats S1): FAILED in-sample.** The Sharpe difference is ≤ 0.004 at every lookback. Only 104 of
  4,508 asset-months (2.3%) qualify as information shocks, so S2 rarely differs from S1.
- **H1 (shock months trend more): direction as predicted, not significant.** Risk-scaled next-month
  TSMOM outcome: 0.038 in high-vol efficient months vs 0.012 in high-vol inefficient months
  (Welch t = 0.61, p = 0.54; month-clustered t = 0.48). Calm months: 0.020. With 104 shock months
  the test can only detect a large effect.
- Best Deflated Sharpe: 126d S1 at 0.92 probability, below the conventional 0.95.
