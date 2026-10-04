# Trading Like a Bayesian: confidence-weighted time-series momentum

Gator Quant Hacks 2026, Systematic Trading Track. Quant note: [`note/quant_note.pdf`](note/quant_note.pdf).

We tested whether Bayesian reasoning improves time-series momentum (TSMOM) on 23 liquid ETFs from 2008 to 2026.
Every hypothesis was committed before it was run (15 strategy variants, 3 mechanism tests), the last two years were
held out and evaluated once, and the result is reported as it came out: the Bayesian sizing is indistinguishable from
standard TSMOM, and both barely beat holding the same vol-targeted portfolio, except in crashes.

| Excess-of-cash Sharpe, net of 5 bps | In-sample 2008–2024 | Out-of-sample 2024–2026 |
|---|---|---|
| S3 Bayesian sizing (final) | 0.39 [−0.09, 0.87] | 0.21 [−0.72, 1.58] |
| S1 standard TSMOM | 0.37 | 0.25 |
| Long-only, same vol targeting | 0.33 | 0.36 |

## Reproduce

Python 3.11+. No API keys are needed; all data is public.

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python data/download.py          # Yahoo ETF bars, Ken French factors, FRED T-bill rate -> data/raw/
python run_all.py --final        # every number and figure in the note
```

`python run_all.py` without `--final` runs in-sample only: the loader drops every row after 2024-10-02, which is how
development was done. `--final` adds the held-out period. Outputs go to `results/` (CSV tables, plus
`final_run_log.txt`) and `note/figures/`. A full run takes a few minutes.

Yahoo's adjusted history is rescaled when new dividends are paid, so a later download can shift price levels slightly.
Returns, and therefore results, should match to rounding.

To rebuild the PDF from `note/quant_note.html`: `bash note/build_pdf.sh` (headless Edge or Chrome).

## What's where

| Path | Contents |
|---|---|
| `HYPOTHESIS.md` | Pre-registered hypotheses (Round 1, then Round 2), committed before each was run |
| `DECISIONS.md` | Every choice made after pre-registration, in order |
| `VARIANTS.md` | Every trial and test, including failures, with results |
| `run_all.py` | Single entry point: 15 variants × 2 cost levels, mechanism tests, robustness, figures |
| `src/config.py` | All parameters (universe, windows, thresholds, costs, out-of-sample date) |
| `src/data.py` | Price and risk-free loaders; enforces the out-of-sample lock |
| `src/signals.py` | Signals, vol state, efficiency ratio, sizing rules S0–S4 |
| `src/backtest.py` | Daily simulator: month-end signals, next-open fills, drifting positions, costs, excess-of-cash returns |
| `src/analysis.py` | Metrics, Deflated Sharpe, block bootstrap, mechanism tests H1/H3/H5a |
| `src/robustness.py` | Lag check, lookback sweep, matched-risk comparison, long-only baseline, factors, capacity, risk, stress windows |
| `src/figures.py` | The three figures in the note |
| `data/download.py` | Data download and coverage checks (raw data is not committed) |

## Strategy in one paragraph

Each month-end, for each ETF, take the sign of its trailing 252-day return and size it to an equal share of a 10% vol
budget (S1, standard TSMOM). S3 multiplies that position by 2Φ(z) − 1, where z is the t-stat of the trailing mean
return. That is the posterior probability (flat prior) that the drift is positive, rescaled to [−1, 1]: weak trends get
small bets. Trades fill at the next day's open, with 5 bps per side (10 bps tested).

## Sources

Yahoo Finance via `yfinance`; Kenneth R. French Data Library; FRED (DTB3). Method references are in the note.
AI tools were used for coding assistance; the team is responsible for all code and claims.
