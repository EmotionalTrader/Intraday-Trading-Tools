import argparse, pandas as pd
from pathlib import Path

def resample_3m(df1m: pd.DataFrame) -> pd.DataFrame:
    o = df1m["Open"].resample("3T").first()
    h = df1m["High"].resample("3T").max()
    l = df1m["Low"].resample("3T").min()
    c = df1m["Close"].resample("3T").last()
    v = df1m["Volume"].resample("3T").sum()
    out = pd.concat([o,h,l,c,v], axis=1).dropna()
    out.columns = ["Open","High","Low","Close","Volume"]
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to your local NinjaTrader 1m CSV")
    ap.add_argument("--rows", type=int, default=300, help="Number of 3-minute rows to include")
    args = ap.parse_args()

    # NinjaTrader format: "YYYYMMDD HHMMSS;Open;High;Low;Close;Volume"
    df = pd.read_csv(args.csv, sep=";", header=None,
                     names=["dt","Open","High","Low","Close","Volume"])
    df["DateTime"] = pd.to_datetime(df["dt"], format="%Y%m%d %H%M%S")
    df = df.drop(columns=["dt"]).set_index("DateTime").sort_index()

    df3 = resample_3m(df)
    sample = df3.head(args.rows)

    out_dir = Path("Python_Backtests/data/samples")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "MES_3m_SAMPLE.csv"
    sample.to_csv(out_path, index_label="DateTime")
    print(f"Wrote sample -> {out_path} ({len(sample)} rows)")

if __name__ == "__main__":
    main()
