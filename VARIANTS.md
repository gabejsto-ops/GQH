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

## Robustness diagnostics on the final spec (S3 vs S1, L = 252, in-sample, 5 bps)

Diagnostics only; nothing here changed the strategy. The lookback sweep (9 lookbacks × 2 sizings)
is disclosed, but it was not used for selection. Tables: `results/robust_*_IS_is.csv`.

- **Lookahead check:** filling 1 or 4 extra days late lowers S3's Sharpe gradually (0.49 → 0.47 → 0.46),
  with no collapse. That is consistent with no lookahead.
- **Plateau:** S3 Sharpe is 0.50–0.65 across 84–252d lookbacks and beats S1 at every lookback ≥ 126d,
  but not at 42–105d. Bayesian sizing helps slow trend signals, not fast ones. 21d fails for both.
- **S3 vs S1 is NOT statistically significant:** vol-matched return gap +0.2%/yr, HAC t = 0.56,
  p = 0.57; correlation 0.95. The defensible gains are lower turnover (3.2× vs 5.1×/yr), a smaller
  max drawdown relative to vol, and a shorter longest drawdown (840 vs 1,047 days). Skew is worse (−0.68 vs −0.43).
- **By year:** S3 is positive in 12 of 17 years. Its losses are smaller than S1's in each of S1's 4 worst
  years, and its gains are smaller in the best ones. No single year drives the result.
- **By asset class:** bonds contribute ~60% of P&L (sleeve Sharpe 0.66); the other classes are 0.15–0.24.
  The result leans on the 2008–2021 bond rally and the 2022 sell-off (regime dependence).
- **Factors (Fama-French 3 + momentum):** small but significant loadings. The largest is momentum
  (β = 0.09, t = 19); market β is 0.035; R² = 0.25. Alpha is 1.2%/yr at 3.1% vol, t = 1.73: not
  significant at 5%.
- **Stress:** GFC flat (+0.1% vs SPY −37%); 2022 +5.4% (SPY −18%); loses in the March–June 2009
  momentum-crash rebound (−3.1%) and the COVID crash (−2.9%). S3 gives up some of S1's crisis gains.
- **Risk concentration:** vol targeting levers low-vol bonds. SHY reaches 164% of equity and the bond
  sleeve 192% gross. Average gross exposure is 0.80×, the maximum 2.14×.
- **Capacity (square-root impact):** net Sharpe 0.49 at $1M, 0.44 at $100M, 0.31 at $1B, and below zero
  near $10B (gross 0.55). Binding names today are the currency and commodity ETFs (2024 median ADV:
  FXY $10M, DBC $22M, UUP $22M); in 2008, HYG traded only $3.6M a day.

## Out-of-sample: 2024-10-03 to 2026-10-02, run once (`python run_all.py --final`, log in `results/final_run_log.txt`)

| L = 252, net of 5 bps (10 bps) | In-sample | Out-of-sample |
|---|---|---|
| S3 Sharpe | 0.49 (0.44) | **1.08 (1.05)** |
| S1 Sharpe | 0.45 (0.39) | 1.06 (1.02) |
| S3 max drawdown | −6.8% | −3.3% |
| S3 turnover / yr | 3.2× | 2.6× (S1: 3.9×) |

- **The strategy held up out of sample.** Both versions did better than in-sample. With only 2 years
  of data the Sharpe estimate has a standard error of ~0.9, so this is consistent with the in-sample
  result, not proof of a stronger edge.
- **S3 vs S1 OOS:** again nearly identical risk-adjusted (gap t = 0.18, correlation 0.98), with 33% less
  turnover and a smaller drawdown. Same conclusion as in-sample.
- **Different sources than in-sample:** OOS profit came from commodities (sleeve Sharpe 1.5) and
  equities (0.9), not mainly bonds. Market beta rose to 0.12 (t = 9.8) with average net exposure 0.81×
  long: part of the OOS result is being long trending equity and gold markets.
- **Mechanism tests OOS:** H3's slope is positive and significant OOS (p = 0.003, n = 133), the reverse of
  in-sample (p = 0.81, n = 1,092). H1 has only 5 shock months OOS. H5a: no effect (p = 0.86). Given the
  in-sample failure, the small sample, and the number of tests run, we treat the H3 OOS result as
  probably chance or regime-specific. We do not claim it.

## Post-OOS audit: cash carry inflates the reported Sharpe (correction, no strategy change)

The engine credits each ETF's total return (including the interest that bond ETFs such as SHY pay)
but neither pays interest on idle cash nor charges financing on leverage. The reported return
therefore includes roughly rf × net exposure. Measured over cash, as in the TSMOM literature
(Σ wᵢ(rᵢ − rf), with rf from the Ken French library; OOS runs only to 2026-08-31, the last rf date):

| Sharpe | Reported | Excess of cash |
|---|---|---|
| S3 IS | 0.49 | 0.39 |
| S3 OOS | 1.20 | **0.23** |
| S1 IS | 0.45 | 0.38 |
| S1 OOS | 1.26 | **0.35** |

OOS, T-bills paid ~4.5%/yr and S3 averaged ~0.8× net long, so 3.6 points of S3's 4.5%/yr OOS return were
cash carry. **The OOS improvement over in-sample is an artifact of high interest rates.** Measured over
cash, S3 is weaker than S1 OOS. All headline numbers in the note will be reported in excess of cash.
