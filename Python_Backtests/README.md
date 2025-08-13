# Python Backtests

This folder will contain Python translations of my TradingView Pine Script indicators for buy and sell signal testing.

By running these scripts, you can:
- Backtest the `EMA_VWAP_Buy_Signal` and `EMA_VWAP_Sell_Signal` logic on real historical intraday data.
- View cumulative returns, win rates, and trade frequencies.
- Experiment with different EMA periods, VWAP bands, and timeframes.

---

## 📊 Strategies Included

### 1. Buy Signals – `ema_vwap_buy_backtest.py`
- Low-risk, high-reward scalping setups.
- Optimized for **3-minute candles**.
- Entry when EMA9 crosses above EMA21 and price is above VWAP support.

### 2. Sell Signals – `ema_vwap_sell_backtest.py`
- Short setups for high-volatility conditions.
- Optimized for **3-minute candles**.
- Entry when EMA9 crosses below EMA21 and price is under VWAP resistance.

---

## ⚙️ Requirements / Installation

Make sure you have **Python 3.9+** installed.  
Install the dependencies with:

```bash
pip install pandas numpy matplotlib yfinance
pip install backtrader ta   # optional for advanced backtesting features
```

## 📂 Data Sources
- Free: yfinance for SPY, QQQ, and other ETFs.
- Paid: Polygon.io, IQFeed, or similar providers for MES/ES futures data (includes outside regular market hours).
