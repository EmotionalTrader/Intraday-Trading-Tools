import argparse
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# Helpers: indicators & VWAP bands
# -------------------------

def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).ewm(alpha=1/length, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/length, adjust=False).mean()
    rs = up / down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def session_id(index: pd.DatetimeIndex, tz: str) -> pd.Series:
    idx = index if index.tz is not None else index.tz_localize(tz)
    idx = idx.tz_convert(tz)
    return pd.Series(idx.date, index=index)

def vwap_session(df: pd.DataFrame, tz: str) -> pd.Series:
    hlc3 = df[["High","Low","Close"]].mean(axis=1)
    sid = session_id(df.index, tz)
    pv = (hlc3 * df["Volume"]).groupby(sid).cumsum()
    vv = df["Volume"].groupby(sid).cumsum()
    return pv / vv.replace(0, np.nan)

def vwap_session_std(df: pd.DataFrame, tz: str) -> pd.Series:
    hlc3 = df[["High","Low","Close"]].mean(axis=1)
    vwap = vwap_session(df, tz)
    w = df["Volume"]
    sid = session_id(df.index, tz)
    ex2 = (hlc3.pow(2) * w).groupby(sid).cumsum() / w.groupby(sid).cumsum().replace(0, np.nan)
    var = (ex2 - vwap.pow(2)).clip(lower=0)
    return np.sqrt(var)

def vwap_bands(df: pd.DataFrame, tz: str, mults=(1.0, 2.0, 3.0), mode="stdev"):
    v = vwap_session(df, tz)
    sd = vwap_session_std(df, tz)
    basis = sd if mode.lower().startswith("stdev") else (v * 0.01)
    bands = {f"U{i}": v + basis*m for i, m in enumerate(mults, 1)}
    bands.update({f"D{i}": v - basis*m for i, m in enumerate(mults, 1)})
    return v, bands

# -------------------------
# IO & resampling
# -------------------------

def read_ninjatrader_csv(path: str) -> pd.DataFrame:
    """
    NinjaTrader export:
    YYYYMMDD HHMMSS;Open;High;Low;Close;Volume
    """
    df = pd.read_csv(path, sep=";", header=None,
                     names=["dt","Open","High","Low","Close","Volume"])
    df["DateTime"] = pd.to_datetime(df["dt"], format="%Y%m%d %H%M%S")
    df = df.drop(columns=["dt"]).set_index("DateTime").sort_index()
    return df

def resample_3m(df1m: pd.DataFrame) -> pd.DataFrame:
    # '3min' avoids the deprecation warning for 'T'
    o = df1m["Open"].resample("3min").first()
    h = df1m["High"].resample("3min").max()
    l = df1m["Low"].resample("3min").min()
    c = df1m["Close"].resample("3min").last()
    v = df1m["Volume"].resample("3min").sum()
    out = pd.concat([o,h,l,c,v], axis=1).dropna()
    out.columns = ["Open","High","Low","Close","Volume"]
    return out

def filter_hours(df: pd.DataFrame, tz="Europe/Stockholm", start="09:00", end="22:00"):
    if df.index.tz is None:
        df = df.tz_localize(tz)
    else:
        df = df.tz_convert(tz)
    return df.between_time(start, end)

# -------------------------
# Strategy logic (BUY side)
# -------------------------

def build_signals(df3: pd.DataFrame, tz="Europe/Stockholm",
                  ema_fast=9, ema_slow=21, mults=(1.0,2.0,3.0), mode="stdev"):
    out = df3.copy()
    out["EMA_F"] = ema(out["Close"], ema_fast)
    out["EMA_S"] = ema(out["Close"], ema_slow)
    out["RSI"]   = rsi(out["Close"])

    vwap, bands = vwap_bands(out, tz=tz, mults=mults, mode=mode)
    out["VWAP"] = vwap
    out["L1"], out["L2"], out["L3"] = bands["D1"], bands["D2"], bands["D3"]

    cross_up = (out["EMA_F"].shift(1) <= out["EMA_S"].shift(1)) & (out["EMA_F"] > out["EMA_S"])
    support  = ((out["Close"] >= out["L3"]) & (out["Close"] <= out["VWAP"])) | \
               ((out["Close"] >= out["L1"]) & (out["Close"] <= out["VWAP"]))
    out["BUY_SIG"] = cross_up & support
    return out

def backtest_buy(df3: pd.DataFrame, tz="Europe/Stockholm", tp_pts=10.0, sl_pts=10.0):
    df = build_signals(df3, tz=tz)
    trades = []
    in_pos = False
    entry_px = np.nan
    entry_rsi = np.nan

    for i in range(1, len(df)):
        row_prev, row = df.iloc[i-1], df.iloc[i]
        ts = df.index[i]

        if not in_pos and row_prev["BUY_SIG"]:
            in_pos = True
            entry_px = row["Open"]
            entry_rsi = row["RSI"]
            trades.append({"t_in": ts, "px_in": float(entry_px), "rsi_in": float(entry_rsi)})
            continue

        if in_pos:
            tp_hit = row["High"] >= entry_px + tp_pts
            sl_hit = row["Low"]  <= entry_px - sl_pts
            if tp_hit and sl_hit:
                px_out, reason = entry_px - sl_pts, "SL_samebar"
            elif tp_hit:
                px_out, reason = entry_px + tp_pts, "TP"
            elif sl_hit:
                px_out, reason = entry_px - sl_pts, "SL"
            else:
                px_out, reason = None, None

            if px_out is not None:
                in_pos = False
                trades[-1].update({"t_out": ts, "px_out": float(px_out), "rsi_out": float(row["RSI"]), "reason": reason})

    if in_pos:
        last = df.iloc[-1]
        trades[-1].update({"t_out": df.index[-1], "px_out": float(last["Close"]), "rsi_out": float(last["RSI"]), "reason": "EOD"})

    tr = pd.DataFrame(trades)
    if tr.empty:
        return tr, {"trades": 0, "win_rate": 0, "pnl_sum": 0, "avg_pnl": 0, "exp": 0, "max_dd": 0, "sharpe": 0, "freq_per_day": 0}, pd.Series(dtype=float)

    tr["pnl"] = tr["px_out"] - tr["px_in"]
    eq = tr["pnl"].cumsum()

    daily = tr.set_index("t_out").resample("1D")["pnl"].sum().fillna(0.0)
    sharpe = 0.0
    if daily.std() != 0:
        sharpe = float((daily.mean() / daily.std()) * np.sqrt(252))

    cum = eq.values
    roll_max = np.maximum.accumulate(cum)
    dd = roll_max - cum
    max_dd = float(dd.max()) if len(dd) else 0.0

    days = pd.Series(df.index.tz_convert("Europe/Stockholm").date).nunique()
    freq = float(len(tr) / max(1, days))

    summary = {
        "trades": int(len(tr)),
        "win_rate": float((tr["pnl"] > 0).mean()),
        "pnl_sum": float(tr["pnl"].sum()),
        "avg_pnl": float(tr["pnl"].mean()),
        "exp": float(tr["pnl"].mean()),
        "max_dd": max_dd,
        "sharpe": sharpe,
        "freq_per_day": freq,
    }
    return tr, summary, eq

# -------------------------
# Filenames for scenario artefacts
# -------------------------

def fmt_num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x).replace(".", "p")

def hours_slug(hours: str) -> str:
    # "14:30-22:00" -> "1430-2200"
    return re.sub(r"[^0-9\-]", "", hours.replace(":", ""))

def stem_name(tp: float, sl: float, hours: str, side: str = "BUY") -> str:
    return f"{side}_mes_TP{fmt_num(tp)}_SL{fmt_num(sl)}_{hours_slug(hours)}"

# -------------------------
# CLI
# -------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to NinjaTrader 1m export (.csv or .csv.txt)")
    ap.add_argument("--from_date", default=None, help="YYYY-MM-DD (optional)")
    ap.add_argument("--to_date", default=None, help="YYYY-MM-DD (optional)")
    ap.add_argument("--tp", type=float, default=10.0)
    ap.add_argument("--sl", type=float, default=10.0)
    ap.add_argument("--tz", default="Europe/Stockholm")
    ap.add_argument("--hours", default="14:30-22:00")  # default to your published session
    ap.add_argument("--plot", type=lambda s: s.lower()=="true", default=True)
    args = ap.parse_args()

    df1 = read_ninjatrader_csv(args.csv)
    if args.from_date:
        df1 = df1[df1.index >= pd.Timestamp(args.from_date)]
    if args.to_date:
        df1 = df1[df1.index <= pd.Timestamp(args.to_date) + pd.Timedelta(days=1)]

    df3 = resample_3m(df1)

    start, end = args.hours.split("-")
    df3 = filter_hours(df3, tz=args.tz, start=start, end=end)

    trades, summary, eq = backtest_buy(df3, tz=args.tz, tp_pts=args.tp, sl_pts=args.sl)

    Path("reports").mkdir(exist_ok=True)

    stem = stem_name(args.tp, args.sl, args.hours, side="BUY")
    trades_csv = Path("reports") / f"{stem.replace('BUY_', 'BUY_mes_trades_')}.csv"
    summary_md = Path("reports") / f"{stem}.md"
    equity_png = Path("reports") / f"{stem}.png"

    # Save trades (now in /reports so it can be linked)
    trades.to_csv(trades_csv, index=False)

    # Save equity plot (optional)
    if args.plot and not eq.empty:
        plt.figure(figsize=(10, 4))
        eq.plot()
        plt.title("MES Buy Strategy – Cumulative P&L (points)")
        plt.xlabel("Time"); plt.ylabel("P&L")
        plt.tight_layout()
        plt.savefig(equity_png, dpi=144)
        plt.close()

    start_dt = df3.index.min()
    end_dt = df3.index.max()
    md = [
        "# MES Buy Backtest Summary",
        "",
        f"**Data window used:** {start_dt} → {end_dt}",
        f"**Session (Stockholm):** {args.hours}",
        f"**Bars:** 3-minute OHLCV",
        f"**Rules:** Entry = EMA(9) cross above EMA(21) with VWAP support; TP +{args.tp} pts / SL -{args.sl} pts; one position at a time",
        "",
        "## Results",
        f"- Trades: {summary['trades']}",
        f"- Win rate: {summary['win_rate']*100:.1f}%",
        f"- Total P&L (pts): {summary['pnl_sum']:.2f}",
        f"- Avg P&L per trade (pts): {summary['avg_pnl']:.2f}",
        f"- Expectancy (pts): {summary['exp']:.2f}",
        f"- Max Drawdown (pts): {summary['max_dd']:.2f}",
        f"- Sharpe (daily, points): {summary['sharpe']:.2f}",
        f"- Trades per day: {summary['freq_per_day']:.2f}",
        "",
        f"_Artefacts:_ [Trades CSV]({trades_csv.name}) · "
        + (f"[Equity PNG]({equity_png.name})" if equity_png.exists() else "Equity PNG (not generated)"),
    ]
    summary_md.write_text("\n".join(md), encoding="utf-8")

    print("Saved:")
    print(f"- trades CSV  -> {trades_csv}")
    print(f"- summary MD  -> {summary_md}")
    if equity_png.exists():
        print(f"- equity PNG  -> {equity_png}")

if __name__ == "__main__":
    main()
