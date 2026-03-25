#!/usr/bin/env python3
"""Run any command on each downloaded genome (serial or batched).

Usage:
  python3 scripts/run_generic_tool.py \
    --genomes results/genomes_plants \
    --cmd "EDTA.pl --genome {fasta} --species others --step all --threads 8" \
    --log results/genomes_plants/run_tool.log

The {fasta} placeholder is replaced with the genome path.
"""
import argparse
import subprocess
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--genomes", required=True, help="Folder with .fasta genomes")
    ap.add_argument("--cmd", required=True, help="Command template with {fasta} placeholder")
    ap.add_argument("--log", default="run_tool.log", help="Log file path")
    ap.add_argument("--resume", action="store_true", help="Skip genomes already logged as done")
    args = ap.parse_args()

    genome_dir = Path(args.genomes)
    log_path = Path(args.log)

    done = set()
    if args.resume and log_path.exists():
        for line in log_path.read_text().splitlines():
            if line.startswith("DONE\t"):
                done.add(line.split("\t", 1)[1])

    with open(log_path, "a") as log:
        for fasta in sorted(genome_dir.glob("*.fasta")):
            if args.resume and str(fasta) in done:
                continue
            cmd = args.cmd.format(fasta=str(fasta))
            log.write(f"RUN\t{fasta}\t{cmd}\n")
            log.flush()
            try:
                subprocess.check_call(cmd, shell=True)
                log.write(f"DONE\t{fasta}\n")
            except subprocess.CalledProcessError as e:
                log.write(f"ERROR\t{fasta}\t{e}\n")
            log.flush()


if __name__ == "__main__":
    main()
