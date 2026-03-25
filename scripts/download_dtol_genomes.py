#!/usr/bin/env python3
"""Download DToL genomes in batches using NCBI Datasets API.

Features:
- filters by BUSCO completeness and assembly level
- optional group/taxa filters
- resume support
- logs all downloads
"""
import argparse
import csv
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests


def ncbi_zip_url(acc: str) -> str:
    return (
        "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/"
        f"{acc}/download?include_annotation_type=GENOME_FASTA"
    )


def download(url: str, out_path: Path, api_key: str | None = None) -> None:
    headers = {}
    if api_key:
        headers["api-key"] = api_key
    r = requests.get(url, headers=headers, stream=True, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)


def extract_fasta(zip_path: Path, workdir: Path) -> Path | None:
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(workdir)
    for ext in ("*.fna", "*.fa", "*.fasta"):
        found = list(workdir.rglob(ext))
        if found:
            return found[0]
    return None


def ensure_fasta_ext(fasta_path: Path, workdir: Path) -> Path:
    # Some tools reject .fna; create .fasta symlink/copy
    if fasta_path.suffix in {".fa", ".fasta"}:
        return fasta_path
    target = workdir / "genome.fasta"
    try:
        if target.exists():
            target.unlink()
        os.symlink(str(fasta_path.resolve()), target)
        return target
    except Exception:
        import shutil
        shutil.copyfile(fasta_path, target)
        return target


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--min-busco", type=float, default=95.0)
    ap.add_argument("--require-chromosome", action="store_true")
    ap.add_argument("--group", default="")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--api-key", default="")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.tsv, sep="\t")
    # filters
    if args.group and "group" in df.columns:
        df = df[df["group"].astype(str).str.contains(args.group, case=False, na=False)]
    if "busco_completeness" in df.columns:
        df["busco_completeness"] = pd.to_numeric(df["busco_completeness"], errors="coerce")
        df = df[df["busco_completeness"] >= args.min_busco]
    if args.require_chromosome and "assembly_level" in df.columns:
        df = df[df["assembly_level"].astype(str).str.contains("Chromosome", na=False)]

    log_path = outdir / "run_log.csv"
    err_path = outdir / "run_errors.csv"
    wrote_header = log_path.exists()

    total = len(df)
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        row = row._asdict()
        acc = row.get("assembly_id")
        if not isinstance(acc, str) or not acc:
            continue
        sci = row.get("scientific_name") or acc
        safe = str(sci).strip().replace(" ", "_").replace("/", "_")

        fasta_out = outdir / f"{safe}.fasta"
        zip_path = outdir / f"{safe}.zip"
        workdir = outdir / f"tmp_{acc}"

        if args.resume and fasta_out.exists():
            if args.verbose:
                print(f"[{idx}/{total}] skip {acc}")
            continue

        status = "ok"
        err = ""
        try:
            url = ncbi_zip_url(acc)
            if args.verbose:
                print(f"[{idx}/{total}] download {acc}")
            download(url, zip_path, api_key=args.api_key or None)

            workdir.mkdir(parents=True, exist_ok=True)
            fasta = extract_fasta(zip_path, workdir)
            if fasta is None:
                raise RuntimeError("No FASTA found in download")
            fasta = ensure_fasta_ext(fasta, workdir)

            # move to output
            os.replace(fasta, fasta_out)

        except Exception as e:
            status = "error"
            err = str(e)
            print(f"[error] {acc}: {e}", file=sys.stderr)

        row_log = {
            "assembly_id": acc,
            "scientific_name": row.get("scientific_name"),
            "taxon_id": row.get("taxon_id"),
            "download_status": status,
            "error": err,
            "chromosome_count": row.get("chromosome_count"),
            "busco_completeness": row.get("busco_completeness"),
            "assembly_level": row.get("assembly_level"),
            "assembly_span": row.get("assembly_span"),
        }
        pd.DataFrame([row_log]).to_csv(log_path, mode="a", header=not wrote_header, index=False)
        wrote_header = True
        if status != "ok":
            pd.DataFrame([row_log]).to_csv(err_path, mode="a", header=not err_path.exists(), index=False)

        # cleanup
        try:
            if workdir.exists():
                import shutil
                shutil.rmtree(workdir, ignore_errors=True)
            if zip_path.exists():
                zip_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
