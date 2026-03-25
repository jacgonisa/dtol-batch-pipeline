#!/usr/bin/env python3
"""Build taxonomy annotations from a DToL TSV (taxon_id required).

This uses the NCBI taxdump (nodes.dmp, names.dmp) to map:
- group (superkingdom)
- taxa1 (phylum)
- taxa2 (order)
- genus
- species

Usage:
  python3 scripts/build_taxonomy_from_tsv.py \
    --tsv data/download_allgoatgenomehubs.tsv \
    --out data/dtol_with_taxonomy.tsv
"""
import argparse
import tarfile
from pathlib import Path
import requests
import pandas as pd

TAXDUMP_URL = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"


def download_taxdump(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(TAXDUMP_URL, stream=True, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)


def extract_taxdump(tar_path: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in ["nodes.dmp", "names.dmp"]:
            tar.extract(member, path=outdir)


def load_nodes(nodes_path: Path) -> dict[int, tuple[int, str]]:
    nodes = {}
    with open(nodes_path, "rt") as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            tax_id = int(parts[0])
            parent = int(parts[1])
            rank = parts[2]
            nodes[tax_id] = (parent, rank)
    return nodes


def load_names(names_path: Path) -> dict[int, str]:
    names = {}
    with open(names_path, "rt") as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            tax_id = int(parts[0])
            name_txt = parts[1]
            name_class = parts[3]
            if name_class == "scientific name":
                names[tax_id] = name_txt
    return names


def lineage(tax_id: int, nodes: dict[int, tuple[int, str]]) -> list[int]:
    path = []
    cur = tax_id
    seen = set()
    while cur in nodes and cur not in seen:
        seen.add(cur)
        path.append(cur)
        parent, _ = nodes[cur]
        if parent == cur:
            break
        cur = parent
    return path


def pick_rank(path: list[int], nodes: dict[int, tuple[int, str]], names: dict[int, str], rank: str) -> str:
    for tax_id in path:
        _, r = nodes.get(tax_id, (None, None))
        if r == rank:
            return names.get(tax_id, "")
    return ""


def map_group(superkingdom: str) -> str:
    if superkingdom == "Bacteria":
        return "eubacteria"
    if superkingdom == "Archaea":
        return "archaea"
    if superkingdom == "Eukaryota":
        return "eukaryote"
    return superkingdom.lower()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--taxdump-dir", default="data/ncbi_taxdump")
    ap.add_argument("--force-download", action="store_true")
    args = ap.parse_args()

    taxdir = Path(args.taxdump_dir)
    tar_path = taxdir / "taxdump.tar.gz"
    nodes_path = taxdir / "nodes.dmp"
    names_path = taxdir / "names.dmp"

    if args.force_download or not tar_path.exists():
        print("[download] taxdump")
        download_taxdump(tar_path)
    if not nodes_path.exists() or not names_path.exists():
        print("[extract] taxdump")
        extract_taxdump(tar_path, taxdir)

    print("[load] nodes/names")
    nodes = load_nodes(nodes_path)
    names = load_names(names_path)

    df = pd.read_csv(args.tsv, sep="\t")
    if "taxon_id" not in df.columns:
        raise RuntimeError("Input TSV must contain taxon_id")

    groups = []
    taxa1 = []
    taxa2 = []
    genus = []
    species = []

    for tax_id in df["taxon_id"].fillna(0).astype(int):
        if tax_id == 0:
            groups.append("")
            taxa1.append("")
            taxa2.append("")
            genus.append("")
            species.append("")
            continue
        path = lineage(tax_id, nodes)
        superkingdom = pick_rank(path, nodes, names, "superkingdom")
        groups.append(map_group(superkingdom))
        taxa1.append(pick_rank(path, nodes, names, "phylum"))
        taxa2.append(pick_rank(path, nodes, names, "order"))
        genus.append(pick_rank(path, nodes, names, "genus"))
        species.append(pick_rank(path, nodes, names, "species"))

    df["group"] = groups
    df["taxa1"] = taxa1
    df["taxa2"] = taxa2
    df["genus"] = genus
    df["species"] = species

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, sep="\t", index=False)
    print("[write]", out)


if __name__ == "__main__":
    main()
