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

## Corrected headline results (excess of cash) and the final teardown

Net of 5 bps, in excess of 3-month T-bills, L = 252. 95% intervals from a 21-day block bootstrap
(2,000 draws). Tables: `results/robust_*_final.csv`.

| Sharpe [95% CI] | In-sample 2008–2024 | Out-of-sample 2024–2026 |
|---|---|---|
| S3 (final) | 0.39 [−0.09, 0.87] | 0.21 [−0.72, 1.58] |
| S1 (standard TSMOM) | 0.37 [−0.10, 0.84] | 0.25 [−0.69, 1.65] |
| Long-only, same vol targeting, no signal | 0.33 [−0.19, 0.85] | 0.36 [−0.45, 1.86] |
| S3 − S1 | +0.02 [−0.14, +0.18] | −0.04 [−0.26, +0.15] |

- **No strategy's Sharpe is distinguishable from zero** at 95%, in or out of sample. The best IS
  Deflated Sharpe (excess) is 0.89 (126d S3/S4); none passes 0.95.
- **The trend signal barely beats just being long.** In-sample S1 0.37 vs long-only 0.33; out of sample,
  long-only did better (0.36 vs 0.25). Over 2008–2026, most of the Sharpe comes from holding a
  vol-targeted, diversified ETF portfolio, not from timing it.
- **Bayesian sizing adds nothing measurable.** At matched 10% vol: turnover −10% (10.5× vs 11.6×/yr),
  max drawdown −22% vs −25% in-sample; OOS the excess Sharpe is slightly lower than S1.
- **Where the trend signal does earn its keep: crises.** Excess returns, S3 / S1 / long-only:
  GFC 0.0% / +2.4% / −5.9%; COVID crash −3.0% / −2.3% / −12.8%; 2022 +5.9% / +9.9% / −11.0%. It pays
  for that in rebounds: March–June 2009 −3.1% / −5.2% / +4.6%. This is the crisis-diversification
  profile documented for trend-following, at a similar long-run Sharpe to long-only.
- **Regime dependence confirmed:** the bond sleeve had a Sharpe of 0.52 in-sample and −0.93 out of sample.
  OOS profits came from commodities (1.32) and equities (0.66).
- **Capacity (excess):** S3 Sharpe 0.39 → 0.33 at $100M → 0.20 at $1B → negative by $10B.
- **H3 OOS** remains significant (p = 0.006) after the correction, and in-sample remains null
  (p = 0.82). Treated as probably chance or regime-specific; not claimed.

## Round 3: risk-premium prior (S5), in-sample 2008–2024, 3 more trials (18 total)

Pre-registered in HYPOTHESIS.md (Round 3) and coded before running. Excess-of-cash Sharpe, 5 bps (10 bps):

| Lookback | S1 TSMOM | S3 flat prior | **S5 risk-premium prior** |
|---|---|---|---|
| 63d  | 0.38 (0.28) | 0.35 (0.26) | 0.38 (0.28) |
| 126d | 0.52 (0.44) | 0.54 (0.47) | **0.55 (0.48)** |
| 252d | 0.37 (0.31) | 0.39 (0.34) | **0.45 (0.40)** |

- At L = 252: S5 Sharpe 0.45 [95% CI −0.02, 0.95], P(Sharpe ≤ 0) = 0.032, the first variant below 5%.
  S5 − S1 = +0.07 [−0.13, +0.29], not significant. Deflated Sharpe 0.80 (N = 18, hurdle 0.23); below 0.95.
- Lowest turnover of any vol-targeted variant (2.7×/yr vs 5.1× for S1). Its lead grows with doubled costs (+0.08).
- Crash profile kept, smaller: GFC −0.5% (long-only −5.9%), COVID crash −3.1% (−12.8%), 2022 +3.6% (S1 +9.9%,
  long-only −11.0%). Smaller loss in the 2009 rebound (−1.8% vs S1 −5.2%). Skew worse (−0.77).
- Correlation with S1 0.90 and with long-only 0.51: a genuine blend of the two, as designed.
- Beats S1 at 2 of 3 lookbacks in-sample (tie at 63d). The pre-registered verdict comes from the holdouts.

## Round 3 holdouts, evaluated once (`python run_all.py --holdout`, log in `results/holdout_run_log.txt`)

Excess-of-cash Sharpe, 5 bps. Primary pre-registered test: S5 vs S1 at L = 252.

| Test set | S5 prior | S1 TSMOM | S3 flat | Long-only | S5 − S1 [95% CI] | Verdict |
|---|---|---|---|---|---|---|
| Backcast 2001-01 → 2007-04 (original ETFs as they launch, 5→22) | 0.71 | **0.73** | 0.62 | 0.37 | −0.02 [−0.38, +0.44] | **Fail** (narrowly) |
| New ETFs 2008-04 → 2026-10 (30 never-used ETFs) | **0.38** | 0.18 | 0.28 | 0.36 | +0.20 [−0.01, +0.40] | **Pass** |

- **Across lookbacks** (63/126/252): S5 beats S1 in 2 of 3 in the backcast (0.50 vs 0.50, 0.38 vs 0.36, 0.71 vs 0.73)
  and in 2 of 3 on new ETFs (0.22 vs 0.25, 0.34 vs 0.21, 0.38 vs 0.18).
- **S5 beats the flat-prior S3 in all 6 holdout cases**, and in all 3 in-sample: the prior improves the Bayesian
  sizing every time it has been tested (9 of 9).
- **Why the backcast fails:** in the 2002 bear market S1 was short equities and made +13.5%; S5's prior kept it closer
  to long and it made +1.8%. That is the price of the prior: it gives up some of the largest short-trend wins.
- Long-only on the new ETFs (0.36) is close to S5 (0.38). S5's drawdown is about half of S1's (−8.8% vs −15.5%), but at
  lower vol; relative to vol it is only slightly smaller (2.8× vs 3.0×). S5's skew is the most negative of any variant (−1.10).
- Crash profile on new ETFs (S5 / S1 / long-only): GFC +1.2% / +5.9% / −8.5%; COVID crash −3.5% / −2.2% / −18.2%;
  2022 +1.5% / +4.5% / −10.0%.
