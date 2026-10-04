# Devpost submission text

## Project name
Trading Like a Bayesian: A Risk-Premium Prior for Time-Series Momentum

## Tagline
Trend-following that thinks like a Bayesian: start from the risk premium, update on the trend, and bet in proportion to the evidence.

## Inspiration
Time-series momentum works because investors update their beliefs too slowly (conservatism), so prices drift after news.
But standard TSMOM is not very Bayesian itself: it bets full size on coin-flip trends and ignores the best-documented fact in
finance, that assets with a risk premium tend to go up. We asked what a trader who actually follows Bayes' rule would do.

## What it does
A monthly strategy on 23 liquid ETFs (equities, bonds, commodities, currencies, real estate). For each asset it combines a
prior (the asset class's long-run risk premium) with the evidence (its trailing 12-month Sharpe) and sizes the position by
the posterior probability that the asset's drift is positive. Premium assets stay long unless the trend is clearly negative;
weak trends get small bets; strong trends get full ones.

## How we built it
- Three rounds of pre-registered hypotheses in git, 18 strategy variants, every result reported, including the failures.
- Public data only (Yahoo Finance, Ken French Library, FRED); anyone can reproduce results with two commands.
- Next-day-open fills, 5 bps per side (10 bps tested), returns measured over cash.
- Held-out testing: after the original 2024–26 holdout was used up, we pre-registered two new untouched test sets (a
  2001–2007 backcast and 30 ETFs never used) and evaluated the final strategy on them once.
- Deflated Sharpe, block-bootstrap confidence intervals, a lookahead check, a lookback plateau, a long-only baseline, a
  matched-risk comparison, factor regression, square-root-impact capacity, and stress windows.

## Results
Excess-of-cash Sharpe, our strategy vs standard TSMOM vs long-only: development 0.45 / 0.37 / 0.33; 2024–26 0.46 / 0.25 / 0.36;
backcast 0.71 / 0.73 / 0.37; 30 new ETFs 0.38 / 0.18 / 0.36. Our strategy beats TSMOM in 3 of 4 test sets and long-only in all 4,
and keeps TSMOM's crash protection (COVID crash −3.1% vs −12.8% for long-only).

## Challenges we ran into
- Our first two ideas failed (de-risking only on noisy volatility; leaning into calm trends).
- Our second strategy's headline out-of-sample Sharpe of 1.08 turned out to be T-bill interest the engine credited without
  charging for cash. Measured properly, it was 0.21. That audit is what led us to the risk-premium prior.
- Using the original holdout for development meant designing fresh, untouched test sets to keep the evaluation honest.

## What we learned
- The improvement is real in 3 of 4 test sets but modest and not statistically significant: every confidence interval for
  "ours minus TSMOM" includes zero, and the strategy narrowly loses in the 2001–2007 backcast, where its long bias cost it
  the 2002 short-equity trend.
- The prior consistently helps a flat Bayesian sizing rule: 9 of 9 comparisons.
- Most of the strategy's apparent drawdown advantage comes from running at lower risk; at matched risk it is similar to TSMOM.

## What's next
Test on 1985+ futures for statistical power, estimate the prior from data (empirical Bayes), and backtest asset-class exposure caps.

## Built with
Python, pandas, NumPy, SciPy, statsmodels, matplotlib, yfinance

## Links
- Code: https://github.com/gabejsto-ops/GQH
- Quant note (PDF): note/quant_note.pdf in the repo (also uploaded here)
