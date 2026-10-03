# Decision log

Every choice made after HYPOTHESIS.md was committed, in order. Changes to the strategy itself are
also counted as trials in VARIANTS.md.

## 2026-10-03: Data (before any returns or backtests were computed)

- **Source: Yahoo Finance adjusted daily bars (yfinance, `auto_adjust=True`) instead of the Webull
  OpenAPI.** Reason: reproducibility. Judges must be able to rerun the code, and Webull requires
  approved credentials (1–2 working days). Webull can be used as a cross-check later. Not a trial:
  the hypothesis allowed a cited fallback, and no results had been seen.
- **Sample:** 2007-04-11 (HYG inception, the last of the 23 to start trading) to 2026-10-02.
- **Out-of-sample cutoff:** 19.5 years of history; 20% would be 3.9 years, so the 2-year cap applies.
  **In-sample: 2007-04-11 → 2024-10-02. Out-of-sample: 2024-10-03 → 2026-10-02, evaluated once.**
  The first ~1 year of in-sample is warm-up for the 252-day signals.
- **Data checks** (`python data/download.py`): no missing closes in the sample. Four one-day moves
  above 25% were checked and are genuine: EWZ 2008-10-13, USO 2020-03-09 and 2020-04-21,
  SLV 2026-01-30. USO's 1-for-8 reverse split (2020-04-28) is correctly adjusted.
  Zero-volume days occur only before the sample start or in UUP's launch week (2007-03-15).
