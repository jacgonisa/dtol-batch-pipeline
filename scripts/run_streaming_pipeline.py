#!/usr/bin/env python3
"""Streamed pipeline: download one genome, run command, delete, repeat.

This is the scalable mode for huge datasets.

Example:
  python3 scripts/run_streaming_pipeline.py \
    --tsv data/dtol_plants.tsv \
    --workdir results/streaming_run \
    --cmd "EDTA.pl --genome {fasta} --threads 8" \
    --min-busco 95 --require-chromosome --resume --verbose
"""
import argparse
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
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--cmd", required=True, help="Command template with {fasta}")
    ap.add_argument("--min-busco", type=float, default=95.0)
    ap.add_argument("--require-chromosome", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--api-key", default="")
    args = ap.parse_args()

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.tsv, sep="\t")
    if "busco_completeness" in df.columns:
        df["busco_completeness"] = pd.to_numeric(df["busco_completeness"], errors="coerce")
        df = df[df["busco_completeness"] >= args.min_busco]
    if args.require_chromosome and "assembly_level" in df.columns:
        df = df[df["assembly_level"].astype(str).str.contains("Chromosome", na=False)]

    log_path = workdir / "run_log.csv"
    err_path = workdir / "run_errors.csv"
    wrote_header = log_path.exists()

    done = set()
    if args.resume and log_path.exists():
        for line in log_path.read_text().splitlines():
            if line.startswith("DONE\t"):
                done.add(line.split("\t", 1)[1])

    total = len(df)
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        row = row._asdict()
        acc = row.get("assembly_id")
        if not isinstance(acc, str) or not acc:
            continue
        if args.resume and acc in done:
            continue

        sci = row.get("scientific_name") or acc
        safe = str(sci).strip().replace(" ", "_").replace("/", "_")
        zip_path = workdir / f"{safe}.zip"
        tmpdir = workdir / f"tmp_{acc}"

        status = "ok"
        err = ""
        try:
            url = ncbi_zip_url(acc)
            if args.verbose:
                print(f"[{idx}/{total}] download {acc}")
            download(url, zip_path, api_key=args.api_key or None)

            tmpdir.mkdir(parents=True, exist_ok=True)
            fasta = extract_fasta(zip_path, tmpdir)
            if fasta is None:
                raise RuntimeError("No FASTA found in download")
            fasta = ensure_fasta_ext(fasta, tmpdir)

            # run command
            cmd = args.cmd.format(fasta=str(fasta))
            if args.verbose:
                print(f"[{idx}/{total}] run {cmd}")
            import subprocess
            subprocess.check_call(cmd, shell=True)

            # mark done
            with open(log_path, "a") as log:
                log.write(f"DONE\t{acc}\n")

        except Exception as e:
            status = "error"
            err = str(e)
            print(f"[error] {acc}: {e}", file=sys.stderr)

        # append metadata log
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
        pd.DataFrame([row_log]).to_csv(log_path.with_suffix(".meta.csv"), mode="a", header=not wrote_header, index=False)
        wrote_header = True
        if status != "ok":
            pd.DataFrame([row_log]).to_csv(err_path, mode="a", header=not err_path.exists(), index=False)

        # cleanup
        try:
            if tmpdir.exists():
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
            if zip_path.exists():
                zip_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
