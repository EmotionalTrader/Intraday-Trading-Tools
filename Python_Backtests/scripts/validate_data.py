import argparse, hashlib, pandas as pd
from pathlib import Path

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)              # local NinjaTrader export (1m)
    ap.add_argument("--out", default="reports/data_summary.txt")
    args = ap.parse_args()

    p = Path(args.csv)
    sha = sha256_of_file(p)

    # NinjaTrader format: "YYYYMMDD HHMMSS;Open;High;Low;Close;Volume"
    df = pd.read_csv(p, sep=";", header=None,
                     names=["dt","Open","High","Low","Close","Volume"])
    df["DateTime"] = pd.to_datetime(df["dt"], format="%Y%m%d %H%M%S")
    df = df.drop(columns=["dt"]).set_index("DateTime").sort_index()

    # gaps > 1 minute
    diffs = df.index.to_series().diff().dropna()
    gaps_over_1m = int((diffs > pd.Timedelta(minutes=1)).sum())
    largest_gap = diffs.max() if not diffs.empty else pd.Timedelta(0)

    summary = f"""File: {p.name}
SHA256: {sha}

Rows: {len(df):,}
First timestamp: {df.index.min()}
Last  timestamp: {df.index.max()}

Gaps > 1m: {gaps_over_1m}
Largest gap: {largest_gap}

Head:
{df.head(3).to_string()}

Tail:
{df.tail(3).to_string()}
"""

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary, encoding="utf-8")
    print(f"Wrote summary -> {out}")

if __name__ == "__main__":
    main()
