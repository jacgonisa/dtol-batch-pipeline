#!/usr/bin/env python3
"""Filter a TSV by group or taxa fields.

Example:
  python3 scripts/filter_by_group.py \
    --tsv data/dtol_with_taxonomy.tsv \
    --out data/dtol_plants.tsv \
    --group plants
"""
import argparse
from pathlib import Path
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--group", default="")
    ap.add_argument("--taxa1", default="")
    ap.add_argument("--taxa2", default="")
    args = ap.parse_args()

    df = pd.read_csv(args.tsv, sep="\t")

    if args.group:
        df = df[df["group"].astype(str).str.contains(args.group, case=False, na=False)]
    if args.taxa1:
        df = df[df["taxa1"].astype(str).str.contains(args.taxa1, case=False, na=False)]
    if args.taxa2:
        df = df[df["taxa2"].astype(str).str.contains(args.taxa2, case=False, na=False)]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, sep="\t", index=False)
    print("[write]", out, "rows", len(df))


if __name__ == "__main__":
    main()
