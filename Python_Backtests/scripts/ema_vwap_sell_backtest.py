import argparse, math, re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------- helpers ----------
def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()

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

def vwap_bands(df: pd.DataFrame, tz: str, mult1=1.0, mult2=2.0, mode="stdev"):
    v = vwap_session(df, tz)
    sd = vwap_session_std(df, tz)
    basis = sd if mode.lower().startswith("stdev") else (v * 0.01)
    u1 = v + basis * mult1
    u2 = v + basis * mult2
    d1 = v - basis * mult1
    d2 = v - basis * mult2
    return v, (u1, u2, d1, d2)

def read_ninjatrader_csv(path: str) -> pd.DataFrame:
    # Format: YYYYMMDD HHMMSS;Open;High;Low;Close;Volume
    df = pd.read_csv(path, sep=";", header=None,
                     names=["dt","Open","High","Low","Close","Volume"])
    df["DateTime"] = pd.to_datetime(df["dt"], format="%Y%m%d %H%M%S")
    df = df.drop(columns=["dt"]).set_index("DateTime").sort_index()
    return df

def resample_3m(df1m: pd.DataFrame) -> pd.DataFrame:
    # use '3min' (no deprecation warnings)
    o = df1m["Open"].resample("3min").first()
    h = df1m["High"].resample("3min").max()
    l = df1m["Low"].resample("3min").min()
    c = df1m["Close"].resample("3min").last()
    v = df1m["Volume"].resample("3min").sum()
    out = pd.concat([o,h,l,c,v], axis=1).dropna()
    out.columns = ["Open","High","Low","Close","Volume"]
    return out

def filter_hours(df: pd.DataFrame, tz="Europe/Stockholm", start="14:30", end="22:00"):
    if df.index.tz is None:
        df = df.tz_localize(tz)
    else:
        df = df.tz_convert(tz)
    return df.between_time(start, end)

def hours_slug(hours: str) -> str:
    return re.sub(r"[^0-9\-]", "", hours.replace(":", ""))

# ---------- signal & backtest (SELL) ----------
def build_sell_signals(df3: pd.DataFrame, tz="Europe/Stockholm"):
    out = df3.copy()
    out["EMA9"]  = ema(out["Close"], 9)
    out["EMA21"] = ema(out["Close"], 21)
    vwap, (U1, U2, D1, D2) = vwap_bands(out, tz=tz, mult1=1.0, mult2=2.0, mode="stdev")
    out["VWAP"], out["U1"], out["U2"] = vwap, U1, U2

    cross_dn = (out["EMA9"].shift(1) >= out["EMA21"].shift(1)) & (out["EMA9"] < out["EMA21"])
    # resistance zone = between VWAP and upper bands
    resist = ((out["Close"] <= out["U1"]) & (out["Close"] >= out["VWAP"])) | \
             ((out["Close"] <= out["U2"]) & (out["Close"] >= out["VWAP"]))
    out["SELL_SIG"] = cross_dn & resist
    return out

def backtest_sell(df3: pd.DataFrame, tz="Europe/Stockholm", tp_pts=10.0, sl_pts=10.0):
    df = build_sell_signals(df3, tz=tz)
    trades = []
    in_pos = False
    entry_px = np.nan

    for i in range(1, len(df)):
        row_prev, row = df.iloc[i-1], df.iloc[i]
        ts = df.index[i]

        # entry next bar open
        if not in_pos and row_prev["SELL_SIG"]:
            in_pos = True
            entry_px = row["Open"]
            trades.append({"t_in": ts, "px_in": float(entry_px)})
            continue

        if in_pos:
            # short: SL triggers if High >= entry+SL ; TP triggers if Low <= entry-TP
            sl_hit = row["High"] >= entry_px + sl_pts
            tp_hit = row["Low"]  <= entry_px - tp_pts
            if sl_hit and tp_hit:
                px_out, reason = entry_px + sl_pts, "SL_samebar"
            elif sl_hit:
                px_out, reason = entry_px + sl_pts, "SL"
            elif tp_hit:
                px_out, reason = entry_px - tp_pts, "TP"
            else:
                px_out, reason = None, None

            if px_out is not None:
                in_pos = False
                pnl = entry_px - px_out  # short P&L in points
                trades[-1].update({"t_out": ts, "px_out": float(px_out), "pnl": float(pnl), "reason": reason})

    # close any open trade at last close
    if in_pos:
        last = df.iloc[-1]
        px_out = float(last["Close"])
        trades[-1].update({"t_out": df.index[-1], "px_out": px_out, "pnl": float(entry_px - px_out), "reason": "EOD"})

    tr = pd.DataFrame(trades)
    if tr.empty:
        return tr, {"trades": 0, "wins": 0, "winrate": 0.0, "total": 0.0, "sharpe": 0.0, "maxdd": 0.0}, pd.Series(dtype=float)

    wins = (tr["pnl"] > 0).sum()
    total = tr["pnl"].sum()
    # simple “per-trade” Sharpe (not annualized), ok for quick comparison
    sharpe = (tr["pnl"].mean() / (tr["pnl"].std() + 1e-9)) * math.sqrt(len(tr))
    eq = tr["pnl"].cumsum()
    rollmax = eq.cummax()
    maxdd = float((eq - rollmax).min())

    summary = {
        "trades": int(len(tr)),
        "wins": int(wins),
        "winrate": float(100.0 * wins / len(tr)),
        "total": float(total),
        "sharpe": float(sharpe),
        "maxdd": abs(maxdd),
    }
    return tr, summary, eq

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--from_date", default="2025-06-01")
    ap.add_argument("--to_date", default="2025-08-14")
    ap.add_argument("--tp", type=float, default=10.0)
    ap.add_argument("--sl", type=float, default=7.5)
    ap.add_argument("--tz", default="Europe/Stockholm")
    ap.add_argument("--hours", default="14:30-22:00")
    ap.add_argument("--plot", default="False")
    args = ap.parse_args()

    # load 1m, slice dates, resample 3m, filter session
    df1 = read_ninjatrader_csv(args.csv)
    df1 = df1.loc[(df1.index >= args.from_date) & (df1.index <= pd.to_datetime(args.to_date) + pd.Timedelta(days=1))]
    df3 = resample_3m(df1)
    start, end = args.hours.split("-")
    df3 = filter_hours(df3, tz=args.tz, start=start, end=end)

    # run backtest
    trades, summary, eq = backtest_sell(df3, tz=args.tz, tp_pts=args.tp, sl_pts=args.sl)

    # outputs (use stable names in /reports/)
    Path("reports").mkdir(exist_ok=True)
    stem = f"SELL_mes_TP{str(args.tp).replace('.', 'p')}_SL{str(args.sl).replace('.', 'p')}_{hours_slug(args.hours)}"
    report_md = Path("reports") / f"{stem}.md"
    trades_csv = Path("reports") / f"{stem.replace('SELL_', 'SELL_mes_trades_')}.csv"
    equity_png = Path("reports") / f"{stem}.png"

    trades.to_csv(trades_csv, index=False)

    # equity (local image saved into /reports so you can link it like with BUY)
    if len(eq) > 0:
        plt.figure(figsize=(10, 4))
        plt.plot(eq.values)
        plt.title("MES SELL – Cumulative P&L (points)")
        plt.xlabel("Trade #"); plt.ylabel("P&L")
        plt.tight_layout()
        plt.savefig(equity_png, dpi=144); plt.close()

    # summary markdown
    md = [
        f"# SELL – EMA/VWAP crossover (MES)",
        "",
        f"**Window:** {args.from_date} → {args.to_date} · **Session:** {args.hours} ({args.tz})",
        f"**Params:** TP {args.tp} / SL {args.sl}",
        "",
        "## Results",
        f"- Trades: {summary['trades']}  ·  Wins: {summary['wins']} ({summary['winrate']:.1f}%)",
        f"- Total P&L: {summary['total']:.1f} pts  ·  Sharpe: {summary['sharpe']:.2f}  ·  MaxDD: {summary['maxdd']:.1f} pts",
        "",
        f"_Artefacts:_ [Trades CSV]({trades_csv.name})" + (f" · [Equity PNG]({equity_png.name})" if equity_png.exists() else ""),
    ]
    report_md.write_text("\n".join(md), encoding="utf-8")

    print("Saved:")
    print(f"- summary MD  -> {report_md}")
    print(f"- trades CSV  -> {trades_csv}")
    if equity_png.exists():
        print(f"- equity PNG  -> {equity_png}")

if __name__ == "__main__":
    main()
