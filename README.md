﻿# Intraday Trading Tools

I am building a focused set of indicators for **day trading**. Based on user requests, I am packaging the first release (**Dynamic Dynamic EMA x VWAP AlertsAlerts**) for **TradingView** (invite-only) and preparing a **NinjaTrader** port. My immediate priority is **usability and accuracy** (clear plots, one-shot alerts, minimal noise). After that, Iâ€™ll run a short **test-user validation** phase.

This repo is for **product updates and access logistics**.  
For access inquiries (waitlist), email **quantastic.analysis@gmail.com**.

---

## Dynamic Dynamic EMA x VWAP AlertsAlerts â€” What it does

**EMA selection**  
`Fast EMA`, `Medium EMA`, `Slow EMA (0 = off)`, `Cross mode (Double/Triple)`

**VWAP selection**  
`Daily Anchored VWAP` (Â±1s, Â±2s, Â±3s)  
`Weekly Anchored VWAP` (Â±1s, Â±2s, Â±3s)  
`Rolling VWAP` (Â±1s, Â±2s, Â±3s), `Rolling VWAP length (bars)`

**Alert Gates**  
`Gate Mode` (Single / AND (Both) / OR (Either))  
`Gate A Source` (Daily / Weekly / Rolling) Â· `Gate B Source` (Daily / Weekly / Rolling)  
`Buy Gate Level` (VWAP / -1s / -2s) Â· `Sell Gate Level` (VWAP / +1s / +2s)

**RVOL**  
`Lookback bars`, `Lookback days`, `Min RVOL`

**Deviation**  
`Activate deviation threshold`, `Deviation threshold (%)`

**ATR**  
`Activate ATR gate`, `ATR length`, `Minimum ATR (%)`, `Maximum ATR (%) (0 = off)`,  
`Relative regime (ATR vs baseline)`, `Baseline length`, `Min ratio Ã—`, `Max ratio Ã—`

**Time windows**  
`Activate Time Windows`, timezone selector, `Active window`,  
`Enable Blackout #1/#2/#3`, `Show blackout info (preview)`

**Other**  
`Price source` (HL2 / HLC3 / Close)

---

## Screenshots

**Intraday (unfiltered)** â€” raw EMA crosses with VWAP context.  
![Intraday (unfiltered)](reports/Dynamic_Dynamic EMA x VWAP Alerts_Alerts_Intraday_Unfiltered.png)

**Intraday (filtered)** â€” same chart with gates active to cut noise.  
![Intraday (filtered)](reports/Dynamic_Dynamic EMA x VWAP Alerts_Alerts_Intraday_Filtered.png)

**Swing example** â€” higher-timeframe usage for context.  
![Swing example](reports/Dynamic_Dynamic EMA x VWAP Alerts_Alerts_Swing.png)

---

## ðŸ§¾ Evidence (MES Â· 1m & 3m Â· long-only)

**Baseline (no gating):** ~13.5k trades, ~50.7% win, **+0.135 pts/trade** expectancy.  
**Calibrated ranking (OOS probs + post-training calibration)** isolates higher-quality subsets.

### Calibrated selection levels â€” credit-style grades (no thresholds shown)

**1-minute**

| Grade | Trades | Win % | Exp pts/trade |
|---|---:|---:|---:|
| **CCC** | 1325 | 64.15% | 3.20 |
| **CC**  | 832  | 67.19% | 3.75 |
| **C**   | 516  | 70.54% | 4.38 |
| **B**   | 310  | 72.58% | 4.65 |
| **A**   | 32   | 78.12% | 5.63 |
| **AA**  | 8    | 87.50% | 7.50 |
| **AAA** | 8    | 87.50% | 7.50 |

**3-minute**

| Grade | Trades | Win % | Exp pts/trade |
|---|---:|---:|---:|
| **CCC** | 793 | 69.74% | 4.67 |
| **CC**  | 520 | 76.15% | 5.77 |
| **C**   | 515 | 76.31% | 5.81 |
| **B**   | 195 | 90.77% | 8.46 |
| **BB**  | 195 | 90.77% | 8.46 |
| **BBB** | 182 | 91.76% | 8.68 |
| **A**   | 182 | 91.76% | 8.68 |
| **AA**  | 182 | 91.76% | 8.68 |
| **AAA** | 4   | 100.00% | 10.00 |

*Note:* Some adjacent grades share the same sample size due to gaps in the calibrated score distribution.

**Retention buckets (Top-K%)**  
A companion CSV lists **Top 50, 45, 40, 35, 30, 25, 20, 15, 10%** for **1m** and **3m** with columns:  
`timeframe, bucket_top_%, trades, win_%, exp_pts_per_trade`.  
See `reports/EVIDENCE_MES_long_retention_buckets.csv`.

---

## ðŸ§ª Initial Small Backtesting on Prototype Indicator

**Validated EMA/VWAP Crossover Buy Signal (MES)**  
- 3-min bars Â· 2025-06-01 â†’ 2025-08-14 Â· 14:30â€“22:00 Europe/Stockholm  
- TP 10 pts / SL 7.5 pts  
- Result: **+65 pts** total Â· **58.3% win** Â· **Sharpe 3.07** Â· **MaxDD 30 pts**  

<img src="reports/BUY_mes_TP10_SL7p5_1430-2200.png" alt="Equity curve â€” BUY TP10/SL7.5" width="900">

**Validated EMA/VWAP Crossover Sell Signal (MES)**  
- 3-min bars Â· 2025-06-01 â†’ 2025-08-14 Â· 14:30â€“22:00 Europe/Stockholm  
- TP 10 pts / SL 7.5 pts  
- Result: **+31.5 pts** total Â· **47.8% win** Â· **Sharpe 1.05** Â· **MaxDD 30 pts**  

<img src="reports/SELL_mes_TP10p0_SL7p5_1430-2200.png" alt="Equity curve â€” SELL TP10/SL7.5" width="900">

**Interpreting These Results**  
- Test period: quiet summer regime, slight bullish index near all-time highs.  
- Implication: more false signals and headwind for shorts.  
- The chosen bracket (TP 10 / SL 7.5) is intentionally conservative.

---

## ðŸ”­ Scope & Next Steps

- âœ… **Improving signal accuracy.**  
- âœ… **Expanding to more timeframes** (1m, 3m, 5m, 15m, 30m).  
- âœ… **Adapting to various market conditions** with deeper backtests on 2â€“5 years of historical data (incl. regime analysis).  
- âœ… **Adapting to multi-instrument use:** stocks, crypto, and commodities.  
- âœ… **Invite-only distribution via TradingView** (later: NinjaTrader port).  
- â³ **Short-side calibration evidence** (coming).  
- ðŸ”œ **Future updates:** quantitative analysis & ML modeling (feature selection, probability calibration, regime tagging), advanced futures & indicator modules, and **multi-year tick-data backtests** to sharpen accuracy and reduce overfitting.

âž¡ï¸ **Details & waitlist instructions:** see `products/Dynamic EMA x VWAP Alerts.md`

---

## ðŸ“¦ What this repo contains

- Product page(s) and reports/images  
- Announcements and updates  
- Contact instructions

---

## ðŸ“¬ Access / Buy

- **TradingView (indicator page):** _link_  
- **LemonSqueezy (checkout):** _link_  

**Status:** LemonSqueezy checkout is being finalized. **Join the waitlist** by emailing **quantastic.analysis@gmail.com** with your **TradingView username**.

---

## ðŸ“ Full reports / custom backtesting

For a **complete private report** or custom runs for other instruments/timeframes, **open a GitHub Issue** with your symbol(s), timeframe(s), and risk preferences.  
> We handle complete-report requests **via GitHub Issues only** (not DM/email).

---

## ðŸ‘¤ Author â€” EmotionalTrader

From emotional â†’ technical â†’ quant trader. Trading futures while building ML models in Python.  
- [GitHub](https://github.com/EmotionalTrader)

---

## âš–ï¸ Legal

Research & education only. Not investment advice. Markets involve risk; **past performance does not guarantee future results**. TradingView is not a party to any sale.

