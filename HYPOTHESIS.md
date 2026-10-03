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
