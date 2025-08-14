# Data (local, not versioned)

This directory holds **raw market data** used for backtests. Large or licensed datasets are **intentionally excluded from Git** to keep the repository lean and to respect data licensing.

## Scope & provenance
- **Instrument:** MES (Micro E-mini S&P 500 Futures), CME.
- **Source:** NinjaTrader 8 historical data export (Minute bars).
- **Processing:** Resampled to **3-minute** bars for strategy evaluation.
- **Timezone policy:** Timestamps treated in **Europe/Stockholm**; analyses are session-filtered **09:00–22:00** local time unless noted.

## Expected files (local only)
Typical filenames (examples, not committed):
- `MES_1m_2025-06-16_2025-08-14.csv.txt`
- `MES_1m_2025-06-01_2025-06-16.csv.txt`

## Expected schema
- **Columns:** `DateTime, Open, High, Low, Close, Volume`
- **DateTime:** `YYYY-MM-DD HH:MM:SS`
- **Types:** `Open/High/Low/Close` = float, `Volume` = integer

## Verification artefacts (committed elsewhere in this repo)
- `reports/data_summary_*.txt` — dataset fingerprint (SHA256), row counts, date range, gap checks.
- `Python_Backtests/data/samples/MES_3m_SAMPLE.csv` — small 3-minute sample for schema review.
- `reports/mes_*` — strategy summaries and equity curves produced from the local dataset.

> Raw files remain local; only summaries, samples, and results are committed to demonstrate data lineage and reproducibility.
