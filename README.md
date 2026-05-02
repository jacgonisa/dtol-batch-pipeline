# DToL Batch Download + Generic Pipeline Runner

This repo is a **tutorial-first** scaffold for downloading large batches of DToL genomes and running **any** downstream tool in a serial or batch fashion.

It is intentionally **tool-agnostic**: you plug in your own command and the runner applies it to each genome.

## Two modes

1. **Batch download → run tools later**
2. **Streaming** (download one genome → run tool → delete → repeat)

## Quick start (streaming mode)

This is the scalable approach for thousands of genomes.

```bash
python3 scripts/run_streaming_pipeline.py \
  --tsv data/dtol_plants.tsv \
  --workdir results/streaming_run \
  --cmd "YOUR_TOOL --genome {fasta} --threads 8 --outdir {outdir}" \
  --min-busco 95 --require-chromosome --resume --verbose
```

## 1) Build taxonomy annotations (optional, for clade filters)

```bash
python3 scripts/build_taxonomy_from_tsv.py \
  --tsv data/download_allgoatgenomehubs.tsv \
  --out data/dtol_with_taxonomy.tsv
```

## 2) Filter by clade (e.g., plants)

```bash
python3 scripts/filter_by_group.py \
  --tsv data/dtol_with_taxonomy.tsv \
  --out data/dtol_plants.tsv \
  --group plants
```

## 3) Batch download (optional)

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

## 4) Run any tool per genome (batch mode)

```bash
python3 scripts/run_generic_tool.py \
  --genomes results/genomes_plants \
  --cmd "YOUR_TOOL --genome {fasta} --threads 8" \
  --log results/genomes_plants/run_tool.log \
  --resume
```

Replace `YOUR_TOOL` with the command you want to run. The `{fasta}` placeholder is replaced by the genome file path.

Available placeholders in `--cmd`:
- `{fasta}`: FASTA path passed to the tool
- `{outdir}`: per-genome output directory inside `WORKDIR/outputs/`
- `{assembly_id}`: NCBI assembly accession
- `{scientific_name}`: species name from the TSV
- `{species_slug}`: species name converted into a filesystem-safe form
- `{taxon_id}`: NCBI taxon ID

## Chromosome-only FASTA mode

`--require-chromosome` filters the TSV to chromosome-level assemblies, but those assemblies can still contain unplaced scaffolds.

If you want the downstream tool to see only FASTA records whose headers look like chromosomes, add:

```bash
--chromosomes-only-fasta
```

By default this keeps records matching:

```text
(?i)chromosome|\bchr\b
```

You can override that with `--chromosome-regex`.

## ANIANNS pattern

If you want to stream DToL genomes through ANIANNS one by one, the pattern is:

```bash
python3 scripts/run_streaming_pipeline.py \
  --tsv data/dtol_plants.tsv \
  --workdir results/anianns_plants \
  --min-busco 95 \
  --require-chromosome \
  --chromosomes-only-fasta \
  --resume --verbose \
  --cmd "bash -lc 'cd /path/to/anianns && YOUR_ANIANNS_COMMAND --input {fasta} --output {outdir}'"
```


python3 scripts/run_streaming_pipeline.py  --tsv data/download_allgoatgenomehubs.tsv  --workdir ../analysis/results/annianns --min-busco 95  --require-chromosome  --chromosomes-only-fasta  --resume --verbose  --cmd "bash -lc 'anianns annotate -f {fasta} -d {outdir}'"


This does:
- download one assembly
- extract the genome FASTA
- subset to chromosome-like records only
- run your ANIANNS command on that one FASTA
- keep outputs in `results/anianns_plants/outputs/<species>/`
- delete the downloaded assembly and move to the next genome

You need to replace `YOUR_ANIANNS_COMMAND` with the actual command used by your local ANIANNS checkout.

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
