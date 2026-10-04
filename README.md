# Trading Like a Bayesian: a risk-premium prior for time-series momentum

Gator Quant Hacks 2026, Systematic Trading Track. Quant note: [`note/quant_note.pdf`](note/quant_note.pdf).

Time-series momentum (TSMOM) sizes every trend the same and ignores that assets with a risk premium drift up on average.
We rebuild it as a Bayesian would: the **prior** is the asset's risk premium, the **evidence** is its trend, and each
position is sized by the posterior probability that the drift is positive (strategy **S5**). Every hypothesis was committed
before it was run (18 variants in three rounds, failures included), and S5 was evaluated once on two untouched holdouts.

| Excess-of-cash Sharpe, net of 5 bps, L = 252 | S5 (ours) | S1 standard TSMOM | Long-only |
|---|---|---|---|
| Development 2008–2024 (23 ETFs) | **0.45** | 0.37 | 0.33 |
| 2024–2026 (already seen) | **0.46** | 0.25 | 0.36 |
| Holdout: backcast 2001–2007 | 0.71 | **0.73** | 0.37 |
| Holdout: 30 never-used ETFs, 2008–2026 | **0.38** | 0.18 | 0.36 |

S5 beats standard TSMOM in 3 of 4 test sets and long-only in all 4. The edge is modest and not statistically significant
(all S5 − S1 confidence intervals include zero); the note's Results section takes it apart.

## Reproduce

Python 3.11+. No API keys are needed; all data is public.

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python data/download.py          # Yahoo ETF bars (incl. holdout ETFs), Ken French factors, FRED T-bill rate
python run_all.py --holdout      # Round 3 holdouts: backcast + 30 new ETFs
python run_all.py --final        # every other number, plus the figures in the note
```

Run `--holdout` before `--final` (figure 2 reads the holdout tables). `python run_all.py` with no flag runs the development
sample only: the loader drops every row after 2024-10-02, and holdout data is only loaded with `--holdout`. That is how
development was done. Outputs go to `results/` (CSV tables and run logs) and `note/figures/`. Each run takes a few minutes.

Yahoo's adjusted history is rescaled when new dividends are paid, so a later download can shift price levels slightly.
Returns, and therefore results, should match to rounding (a fresh clone matched to within 0.00003 Sharpe).

To rebuild the PDF from `note/quant_note.html`: `bash note/build_pdf.sh` (headless Edge or Chrome).

## What's where

| Path | Contents |
|---|---|
| `HYPOTHESIS.md` | Pre-registered hypotheses (Rounds 1–3 and the holdout design), each committed before it was run |
| `DECISIONS.md` | Every choice made after pre-registration, in order |
| `VARIANTS.md` | Every trial and test, including failures, with results |
| `run_all.py` | Single entry point: 18 variants × 2 cost levels, mechanism tests, robustness, holdouts, figures |
| `src/config.py` | All parameters (universes, windows, thresholds, prior Sharpe values, costs, dates) |
| `src/data.py` | Price, holdout and risk-free loaders; enforces the out-of-sample and holdout locks |
| `src/signals.py` | Signals and sizing rules S0–S5, including the risk-premium posterior |
| `src/backtest.py` | Daily simulator: month-end signals, next-open fills, drifting positions, costs, excess-of-cash returns |
| `src/analysis.py` | Metrics, Deflated Sharpe, block bootstrap, mechanism tests |
| `src/robustness.py` | Lag check, lookback sweep, matched-risk comparison, long-only baseline, factors, capacity, risk, stress windows |
| `src/holdout.py` | Round 3 holdout evaluation (backcast and new ETFs) |
| `src/figures.py` | The three figures in the note |
| `data/download.py` | Data download and coverage checks (raw data is not committed) |

## The strategy in one paragraph

At each month-end, for each ETF, compute the trailing 252-day Sharpe ratio of its returns over cash (ŝ). Combine it with a
prior expected Sharpe m₀ (0.3 for equities, bonds and real estate; 0 for commodities and currencies), with the prior given the
weight of one lookback window of data: z = (m₀ + ŝ) / (√2 · se), where se = √(252/L). The position is the standard TSMOM
vol-target weight (an equal share of a 10% vol budget) × (2Φ(z) − 1). Trades fill at the next day's open, with 5 bps per
side (10 bps tested).

## Sources

Yahoo Finance via `yfinance`; Kenneth R. French Data Library; FRED (DTB3). Method references are in the note.
AI tools were used for coding assistance; the team is responsible for all code and claims.
