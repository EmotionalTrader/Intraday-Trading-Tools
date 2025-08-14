# Intraday-Trading-Tools

A curated suite of intraday trading tools for TradingView. Includes EMA–VWAP crossover signals, Rolling VWAP suites, and Daily/Weekly VWAPs.

## Executive Summary

Intraday-Trading-Tools provides TradingView indicators and reproducible Python backtests for ES/MES 3-minute intraday trading.

**Validated EMA/VWAP Crossover Buy Signal (MES)**
- 3-min bars · 2025-06-01 → 2025-08-14 · 14:30–22:00 Europe/Stockholm  
- TP 10 pts / SL 7.5 pts  
- Result: **+65 pts** total · **58.3%** win · **Sharpe 3.07** · **MaxDD 30 pts**  
  [Report](reports/BUY_mes_TP10_SL7p5_1430-2200.md) · [Trades CSV](reports/BUY_mes_trades_TP10_SL7p5_1430-2200.csv)

<img src="https://raw.githubusercontent.com/EmotionalTrader/Intraday-Trading-Tools/main/reports/BUY_mes_TP10_SL7p5_1430-2200.png" alt="Equity curve — BUY TP10/SL7.5" width="900">


## Note on Code Origin
The Pine Script code was initially generated with help from large language models (LLMs) to speed up development. All trading algorithms, logic, and parameters are my own original work. Each indicator has been tested and deployed on TradingView, where it’s actively used and has been boosted by 50+ traders within the first days of release.

## Additional Information

### ⚠️ Disclaimer
This software and its indicators are provided for educational and informational purposes only and do not constitute financial advice. Trading involves significant risk, and many individuals lose money—especially in futures. Use these tools at your own risk, and consult a qualified financial advisor before making any trading decisions.

### Instrument Suitability
These indicators are primarily built for S&P 500 futures (ES and MES) but can be suitable for other instruments depending on your strategy and testing.

### Trading Recommendations
Trading based solely on indicators is not recommended. For better decision-making:
- Use **support and resistance levels** as your primary basis.
- Consider **price action and pattern breakouts** as a secondary basis.
- Use indicators (like those provided here) as a tertiary input.
- Before entering a position, check **RSI (Relative Strength Index)** to gauge overbought/oversold conditions.

## Future Updates
These are basic free versions. I’m working on more advanced algorithms, so watch this GitHub repository for future releases.

### 👤 Author — **EmotionalTrader**
- Futures trader, Python learner, aspiring asset trader  
- [GitHub](https://github.com/EmotionalTrader)

