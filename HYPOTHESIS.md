# Hypothesis: Not all volatility is noise

**Status: DRAFT — commit before any backtest is run. Any later change is logged in VARIANTS.md and counted as a trial.**

## 1. Economic hypothesis

Investors update their beliefs about fair value too slowly when news arrives (conservatism: they move
in the Bayesian direction but by less than the Bayesian amount, Edwards 1968; Barberis, Shleifer &
Vishny 1998). Prices therefore close only part of the gap on the day of the news, and the remainder
arrives as a predictable drift. Time-series momentum (Moskowitz, Ooi & Pedersen 2012) captures that drift.

In a Bayesian update, `new = old + k * (news - old)` with `k = σ0² / (σ0² + σs²)`. Under
underreaction the leftover gap is `(1 - λ) * k * (news - old)`. High volatility can come from two
different sources with opposite implications:

- **Information shock**: a large surprise `(news - old)` from a reliable signal (large `k`).
  The leftover gap is large, so the trend should continue.
- **Noise / disagreement**: an unreliable signal (large `σs²`, small `k`). There is little to absorb,
  moves alternate, and trends should reverse.

Standard TSMOM sizes positions by `target vol / recent vol`, cutting exposure in both cases.
Prior work (Barroso & Santa-Clara 2015; Moreira & Muir 2017) finds that cutting helps on average,
which is consistent with noise dominating high-volatility periods. We claim the average hides
information shocks, where cutting gives up the largest gaps.

**Who is on the other side:** investors anchored on pre-news valuations who sell into (or buy against)
the post-news drift, plus slow-moving institutional capital.
**Why it persists:** conservatism is a stable feature of human judgement, and the standard
risk-management practice of de-risking on volatility spikes pushes capital *away* from these episodes.

## 2. Measuring the two kinds of volatility (point-in-time only)

For each asset at each month-end `t`, using daily closes up to and including `t`:

- **High-vol state**: 21-day realized vol is above its own trailing 252-day 75th percentile.
- **Efficiency ratio (ER)** over the last 21 days: `|P_t - P_{t-21}| / Σ|P_i - P_{i-1}|`.
  Under a pure random walk, ER ≈ 1/√21 ≈ 0.22. **Efficient = ER > 0.44 (2× the noise level).**
  The threshold comes from random-walk theory, not from fitting the data.

## 3. Testable predictions

- **H1 (mechanism):** Among high-vol asset-months, the next-month TSMOM return (signal × next-month
  return) is higher for efficient than for inefficient months.
- **H2 (strategy):** Conditional sizing (S2 below) has a higher net Sharpe than standard vol targeting (S1).

**It fails if:** H1's difference is ≈ 0 or negative, or S2 does not beat S1 net of costs out of
sample. We will report the result either way.

## 4. Setup

- **Universe (fixed in advance, by rule):** the most liquid US-listed ETF for each distinct exposure
  across five asset classes, with inception before mid-2007, excluding leveraged/inverse products and
  UNG (its futures-roll losses dominate its returns). 23 assets:
  - Equities (8): SPY, QQQ, IWM, EFA, EEM, EWJ, EWZ, FXI
  - Bonds (6): SHY, IEF, TLT, LQD, HYG, TIP
  - Commodities (5): GLD, SLV, DBC, USO, DBA
  - Currencies (3): UUP, FXE, FXY
  - Real estate (1): VNQ

  Moskowitz, Ooi & Pedersen used 58 futures; we use ETFs because they are what a non-institutional
  investor can trade, at the cost of a shorter history and imperfect tracking for commodity ETFs.
  Breadth matters for the strategy (Grinold & Kahn's fundamental law: IR ≈ IC × √breadth) and for
  the statistical power of H1. Survivorship: all 23 still trade; the bias is limited to having
  picked ETFs that are liquid today, and we report results by asset class to show it is not
  driven by one group.
- **Data:** daily split- and dividend-adjusted bars; Webull OpenAPI (fallback cited if history is too short).
- **Signal:** sign of the trailing L-day return at month-end close; trade at the **next day's open**.
- **Sizing rules:**
  - S0: equal notional, ±1/N
  - S1: vol targeting, `w = (10% / N) / σ_60d` (annualized), capped at 2× per asset
  - S2: as S1, but in high-vol **and** efficient months size with `σ_252d` instead of `σ_60d`
    (no de-risking on information shocks); S1 sizing everywhere else
- **Costs:** 5 bps per side (commission + slippage) for liquid ETFs; also reported at 10 bps.
- **Out-of-sample:** the most recent 2 years (the 20% rule is longer for this history, so the 2-year
  cap applies). Held out until the end and evaluated once.

## 5. Planned variants (trial count = 9)

Lookback L ∈ {63, 126, 252} days × sizing ∈ {S0, S1, S2}. Primary specification: L = 252, S2 vs S1.
The ER window (21 days), threshold (0.44) and vol-state definition are fixed and are not varied.
Results reported for all 9 variants, with a Deflated Sharpe Ratio for N = 9.

---

# Round 2 (added after seeing Round 1 in-sample results; committed before running)

Round 1: H2 failed (S2 ≈ S1 because shocks are only 2.3% of asset-months) and H1 pointed the
predicted way but was not significant. These follow-ups were chosen *after* seeing those results,
so they are disclosed as post-hoc and every trial is counted. Thresholds and windows are unchanged.

## H3: continuous mechanism test (1 test, no new strategy)

The 0.44 cutoff in H1 discards information. If underreaction to information drives trends, the
next-month TSMOM outcome should rise *continuously* with the efficiency ratio.
**Test:** among high-vol asset-months (L = 252), regress the risk-scaled outcome on ER, with SEs
clustered by month. **Fails if** the slope is ≤ 0 or not significant.

## H4: trade like a Bayesian (sizing S3, 3 trials: L ∈ {63, 126, 252})

Conservative investors react late; a Bayesian keeps updating and bets in proportion to how sure it
is. With a flat prior, the posterior probability that an asset's drift is positive after L days is
Φ(z), where z = mean daily return / std × √L (the t-stat of the trend). A Bayesian therefore
sizes by confidence, not by the sign alone: **S3 = S1 × (2Φ(z) − 1)**, which runs from −1 to +1.
Weak, noisy trends near zero get small bets; clear trends get full ones.
**Predicts:** higher net Sharpe **and** lower turnover than S1 (fewer whipsaws on weak signals).
**Fails if** S3's net Sharpe ≤ S1's at the same lookback.

## H5: calm trends (sizing S4, 3 trials: L ∈ {63, 126, 252})

The mirror image of Round 1. In calm markets (not high-vol), news spreads gradually (Hong & Stein
1999, slow information diffusion), so a steady, efficient trend is the clearest sign of information
still being absorbed. **S4 = S1, with weight × 2 in calm months where ER > 0.44** (still subject to the
2× per-asset cap). The factor 2 is set a priori as the mirror of "do not de-risk"; it is not tuned.
**Predicts:** (a) among calm asset-months, efficient ones have a higher TSMOM outcome than inefficient
ones (Welch + month-clustered test, L = 252); (b) S4 net Sharpe > S1.
**Fails if** (a) is ≤ 0 / not significant, or S4 ≤ S1.

**Trial count after Round 2:** 9 + 3 + 3 = 15 strategy variants (Deflated Sharpe uses N = 15),
plus mechanism tests H1, H3, H5a.

---

# Round 3: a risk-premium prior (pre-registered after the 2024–2026 OOS was seen; committed before any code)

**Why a new round.** Rounds 1–2 showed (in-sample) that vol-targeted long-only earns about as much as TSMOM, and that
TSMOM's distinct value is crash protection (2008, 2020, 2022). S3 used a *flat* prior and so ignored the most
robust fact in asset pricing: assets with a risk premium drift up on average. A Bayesian should start from that.

## H6: risk-premium prior (sizing S5, 3 trials: L ∈ {63, 126, 252}; trial count becomes 18)

Work in annualized Sharpe units on returns in excess of cash. For each asset at each month-end:

- **Prior:** expected Sharpe m₀ by asset class, set a priori from the long-run risk-premium literature (Ilmanen 2011):
  **equities 0.3, bonds 0.3, real estate 0.3, commodities 0, currencies 0** (no reliable spot premium; roll costs).
  Prior strength: worth one lookback window of data, so the prior s.d. equals the data's standard error
  se = √(252 / L). Theory and evidence get equal weight; this is fixed, not tuned.
- **Evidence:** ŝ = trailing L-day mean excess return / s.d. × √252.
- **Posterior:** mean = (m₀ + ŝ) / 2, s.d. = se / √2, so P(drift > 0) = Φ(z₅) with z₅ = (m₀ + ŝ) / (√2 · se).
- **Position:** S5 = |S1 weight| × (2Φ(z₅) − 1). With m₀ = 0 this is S3 with a different (excess-return) z, so
  S3 is the flat-prior special case.

Effect: an asset with a premium stays long unless its trend is clearly negative (at L = 252, flip only if ŝ < −0.3);
assets without a premium are traded on trend alone.

**Predicts:** S5 has a higher excess Sharpe than S1 (original TSMOM) and S3, keeps most of TSMOM's crash protection,
and beats long-only. **Primary test: S5 vs S1 at L = 252 on the holdout sets below.** **Fails if** S5's holdout excess
Sharpe ≤ S1's. Secondary: S5 vs long-only and S3; crash-window behavior.

## Holdout design (the 2024–2026 window is spent; it is reported but labeled "already seen")

Evaluated **once**, after in-sample development, with `run_all.py --holdout`; the loader refuses these data otherwise.

1. **Backcast (time holdout):** dates **before 2007-04-11**, never loaded in any analysis. The universe is the original
   23 ETFs, each entering once it has a price history; the portfolio's vol budget is split across the assets available
   on each date. Evaluation runs from the first month-end with a 252-day history (at least 2 assets) to 2007-04-10.
2. **New ETFs (asset holdout):** a universe never used, chosen by the same rule (most liquid US ETF per distinct
   exposure, inception before mid-2007, no leveraged/inverse products), evaluated over 2008-06 → 2026-10:
   - Equities (country): EWG, EWU, EWC, EWA, EWY, EWT, EWH, EWW, EWQ, EWL
   - Equities (US sectors): XLE, XLF, XLK, XLU, XLV, XLP, XLI, XLB, XLY
   - Bonds: AGG, MBB, TLH, IEI
   - Commodities: DBB, DBE, DBP
   - Currencies: FXB, FXC, FXA, FXF
   Any ticker without clean data from mid-2007 is dropped by rule before any returns are computed.

All other settings (costs, timing, vol targeting, cap) are unchanged.
