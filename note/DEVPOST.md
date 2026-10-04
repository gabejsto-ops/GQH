# Devpost submission text

## Project name
Trading Like a Bayesian: Confidence-Weighted Time-Series Momentum

## Tagline
We tried to make trend-following smarter with Bayes' rule, tested 15 variants honestly, and took our own best-looking result apart.

## Inspiration
Time-series momentum works because investors update their beliefs too slowly when news arrives (conservatism), so prices drift
after information. If the market under-updates, a strategy that updates like a proper Bayesian should do better. We wanted to test that rather than assume it.

## What it does
A monthly trend-following strategy on 23 liquid ETFs (equities, bonds, commodities, currencies, real estate). Standard TSMOM takes
the sign of each asset's 12-month return and sizes it by volatility. Our version sizes each bet by the posterior probability that the
trend is real, (2Φ(z) − 1) where z is the trend's t-stat, so weak, noisy trends get small positions.

## How we built it
- Pre-registered every hypothesis in git before running it (Round 1: de-risk only on noisy volatility; Round 2: Bayesian sizing and a
  low-volatility mirror test). 15 strategy variants and 3 mechanism tests, all reported, including failures.
- Public data only (Yahoo Finance, Ken French Library, FRED), so anyone can reproduce results with `python run_all.py --final`.
- Next-day-open fills, 5 bps per side (10 bps tested), the last 2 years locked in code and evaluated once.
- Deflated Sharpe over 15 trials, block-bootstrap confidence intervals, delayed-fill lookahead check, lookback plateau, a long-only
  baseline, a matched-risk comparison, factor regression, square-root-impact capacity, and stress windows.

## Challenges we ran into
Our first out-of-sample result was a Sharpe of 1.08. Auditing it, we found the engine credited the interest that bond ETFs pay without
charging for cash, so much of the "edge" was the 4.5% T-bill rate. Measured over cash it is 0.21. We also found that our "37% less
turnover" came mostly from running smaller positions; at matched risk it is 10%.

## What we learned
- Most of our ideas failed: shock-aware de-risking, the continuous efficiency test, and calm-trend sizing all came out null.
- Bayesian sizing is statistically indistinguishable from standard TSMOM (Sharpe difference +0.02, CI −0.14 to 0.18).
- Trend-following barely beats simply holding the same vol-targeted portfolio over 2008–2026, but it protects in crashes:
  2008 0.0% vs −5.9%, the COVID crash −3.0% vs −12.8%, and 2022 +5.9% vs −11.0% (excess returns, trend vs long-only).
- Out of sample, the 2-year window is too short to confirm or reject a Sharpe of 0.4.

## What's next
Rerun on 1985+ futures for statistical power, backtest asset-class exposure caps as a separate pre-registered trial, and test a
trend/long-only blend for its crisis offset.

## Built with
Python, pandas, NumPy, SciPy, statsmodels, matplotlib, yfinance

## Links
- Code: https://github.com/gabejsto-ops/GQH
- Quant note (PDF): note/quant_note.pdf in the repo (also uploaded here)
