# DToL Batch Download + Generic Pipeline Runner

This repo is a **tutorial-first** scaffold for downloading large batches of DToL genomes and running **any** downstream tool in a serial or batch fashion.

It is intentionally **tool-agnostic**: you plug in your own command and the runner applies it to each genome.

## What you can do

- Download thousands of DToL assemblies in batches
- Filter by clade or metadata (e.g., plants only)
- Keep only chromosome-level assemblies
- Resume after crashes
- Run any command per genome (EDTA, RepeatModeler, k-mer tools, etc.)

## Quick start

### 1) Build taxonomy annotations (optional, for clade filters)

```bash
python3 scripts/build_taxonomy_from_tsv.py \
  --tsv data/download_allgoatgenomehubs.tsv \
  --out data/dtol_with_taxonomy.tsv
```

### 2) Filter by clade (e.g., plants)

```bash
python3 scripts/filter_by_group.py \
  --tsv data/dtol_with_taxonomy.tsv \
  --out data/dtol_plants.tsv \
  --group plants
```

### 3) Download genomes (NCBI Datasets API)

```bash
python3 scripts/download_dtol_genomes.py \
  --tsv data/dtol_plants.tsv \
  --outdir results/genomes_plants \
  --min-busco 95 \
  --require-chromosome \
  --resume --verbose
```

This produces:
- `results/genomes_plants/*.fasta`
- `results/genomes_plants/run_log.csv`
- `results/genomes_plants/run_errors.csv`

### 4) Run any tool per genome

```bash
python3 scripts/run_generic_tool.py \
  --genomes results/genomes_plants \
  --cmd "YOUR_TOOL --genome {fasta} --threads 8" \
  --log results/genomes_plants/run_tool.log \
  --resume
```

Replace `YOUR_TOOL` with the command you want to run. The `{fasta}` placeholder is replaced by the genome file path.

## Input TSV format

Required columns:
- `assembly_id`
- `scientific_name`
- `taxon_id`
- `assembly_level`
- `busco_completeness`

Optional (for filtering):
- `group` (e.g., plants)
- `taxa1`, `taxa2`

## Tips

- If your machine crashes, just re-run with `--resume`.
- If a FASTA was partially written, delete it and resume.
- Start with a small subset (e.g. plants) before running the full DToL set.

## License

MIT
