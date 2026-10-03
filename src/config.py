"""Pre-registered parameters. Every value here is fixed in HYPOTHESIS.md or DECISIONS.md."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
RESULTS_DIR = ROOT / "results"

UNIVERSE = {
    "Equities": ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "EWZ", "FXI"],
    "Bonds": ["SHY", "IEF", "TLT", "LQD", "HYG", "TIP"],
    "Commodities": ["GLD", "SLV", "DBC", "USO", "DBA"],
    "Currencies": ["UUP", "FXE", "FXY"],
    "Real estate": ["VNQ"],
}
TICKERS = [t for group in UNIVERSE.values() for t in group]
ASSET_CLASS = {t: g for g, ts in UNIVERSE.items() for t in ts}

SAMPLE_START = "2007-04-11"
IS_END = "2024-10-02"
OOS_START = "2024-10-03"

LOOKBACKS = [63, 126, 252]
SIZINGS = ["S0", "S1", "S2"]
PRIMARY_LOOKBACK = 252

TARGET_VOL = 0.10          # portfolio-level budget, split equally across assets
MAX_ABS_WEIGHT = 2.0       # per-asset cap, as a multiple of equity
VOL_SHORT = 60             # S1 sizing vol window
VOL_LONG = 252             # S2 sizing vol window on information shocks
STATE_VOL = 21             # vol-state window
STATE_PCTL = 0.75          # high-vol threshold (percentile of own trailing 252d)
ER_WINDOW = 21
ER_THRESHOLD = 0.44        # 2x the random-walk level 1/sqrt(21)

COST_BPS = 5.0
COST_BPS_STRESS = 10.0
