# Python Backtests 

Reproducible backtests for the EMA + VWAP TradingView indicators in this repo:

EMA_VWAP_Buy_Signal → scripts/ema_vwap_buy_backtest.py

EMA_VWAP_Sell_Signal → scripts/ema_vwap_sell_backtest.py

The goal is to show clear, minimal, end-to-end workflow:
export 1-minute data → resample to 3-minutes → apply rules → produce metrics + equity curve + trade log.

### Repo layout (relevant to backtests)

```bash
Intraday-Trading-Tools/
├─ Python_Backtests/
│  ├─ scripts/
│  │  ├─ validate_data.py            # sanity-check CSV → reports/
│  │  ├─ make_3m_sample.py           # build tiny 3-min sample → data/samples/
│  │  ├─ ema_vwap_buy_backtest.py    # BUY logic backtest (EMA+VWAP)
│  │  ├─ ema_vwap_sell_backtest.py   # SELL logic backtest (EMA+VWAP)
│  │  ├─ extract_sell_rsi.py         # RSI at SELL entries → markdown
│  │  └─ extract_sell_rsi_outcome.py # RSI at SELL entries + outcome
│  └─ data/
│     ├─ PLACEHOLDER.md              # explains why raw data stays local
│     └─ samples/                    # tiny demo CSVs (safe to commit)
└─ reports/                           # small, curated artefacts (PNG/CSV/MD)
```

### What’s included

```bash
# Backtest components
- BUY backtest (ema_vwap_buy_backtest.py)
- SELL backtest (ema_vwap_sell_backtest.py)
- Data validator (validate_data.py)
- 3-minute sampler (make_3m_sample.py)

```

### Input data 

```bash
- Source: NinjaTrader 1-minute exports
- Format: YYYYMMDD HHMMSS;Open;High;Low;Close;Volume
- Files are kept local (ignored by Git). A tiny sample can live in data/samples/.

```

### Quick start (Windows/CMD)


```bash
cd "C:\Users\documents\Intraday-Trading-Tools"

:: 1) Provenance (optional but recommended)
python Python_Backtests\scripts\validate_data.py ^
  --csv "Python_Backtests\Data\MES_1m_2025-06-01_2025-08-14_combined.csv.txt" ^
  --out "reports\data_summary_MES_2025-06-01_2025-08-14.txt"

:: 2) BUY backtest (public setting used in the main README)
python Python_Backtests\scripts\ema_vwap_buy_backtest.py ^
  --csv "Python_Backtests\Data\MES_1m_2025-06-01_2025-08-14_combined.csv.txt" ^
  --from_date 2025-06-01 --to_date 2025-08-14 ^
  --tp 10 --sl 7.5 ^
  --tz Europe/Stockholm --hours 14:30-22:00 ^
  --plot True

:: 3) SELL backtest (baseline public setting)
python Python_Backtests\scripts\ema_vwap_sell_backtest.py ^
  --csv "Python_Backtests\Data\MES_1m_2025-06-01_2025-08-14_combined.csv.txt" ^
  --from_date 2025-06-01 --to_date 2025-08-14 ^
  --tp 10 --sl 7.5 ^
  --tz Europe/Stockholm --hours 14:30-22:00 ^
  --plot False
```

### Outputs (written to reports/)
- BUY_mes_TP10_SL7p5_1430-2200.md – summary metrics
- BUY_mes_TP10_SL7p5_1430-2200.png – equity curve (points)
- BUY_mes_trades_TP10_SL7p5_1430-2200.csv – trades log
- SELL_mes_TP10p0_SL7p5_1430-2200.md/.png/.csv – analogous SELL artefacts
- data_summary_*.txt – data window + SHA256 (provenance)

### Reproducibility note

Backtests reference a local NinjaTrader CSV (not committed).
validate_data.py writes a small data_summary_*.txt with row counts, date range, and SHA256 so reviewers can match against the author’s run.
