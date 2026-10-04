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

## Round 2: post-hoc follow-ups, pre-registered before running (6 more trials, 15 total)

Deflated Sharpe hurdle for 15 trials: 0.28. Net Sharpe at 5 bps (10 bps in brackets).

| Lookback | S1 vol target | S3 Bayesian (H4) | S4 calm tilt (H5) |
|---|---|---|---|
| 63d  | 0.46 (0.36) | 0.44 (0.34) | 0.48 (0.36) |
| 126d | 0.61 (0.54) | **0.65 (0.58)** | 0.64 (0.54) |
| 252d | 0.45 (0.39) | **0.49 (0.44)** | 0.46 (0.38) |

- **H3 (outcome rises continuously with ER in high-vol months): FAILED.** Slope −0.02,
  clustered t = −0.24, p = 0.81 (n = 1,092). Together with H1, there is no evidence that
  efficiency identifies information shocks in high-vol periods. The Round 1 mechanism is not supported.
- **H4 (Bayesian confidence sizing, S3): partly supported.** Turnover fell 35–37% at every lookback,
  as predicted. Sharpe beat S1 at 126d (+0.03) and 252d (+0.04) but not at 63d (−0.02), so by the
  pre-registered rule it fails at 1 of 3 lookbacks. The advantage grows when costs double (+0.05 at
  252d), consistent with the lower turnover. Drawdown relative to vol is lower at 252d (2.2× vs 2.7×),
  but skew is more negative.
- **H5 (calm efficient trends, S4): FAILED as a strategy.** Small Sharpe gains at 5 bps (+0.01 to +0.02)
  come with 30–50% more turnover and disappear at 10 bps (252d: 0.38 vs 0.39). Mechanism test H5a:
  calm efficient 0.035 vs calm inefficient 0.018, Welch p = 0.28, clustered p = 0.47; not significant.
- **Deflated Sharpe:** best is S3 at 126d with 0.93 probability; no variant clears 0.95.
