# How to download lots of DToL genomes (Jacob's approach)

Short answer to the collaborator question:

1. Grab a DToL metadata TSV (GenomeHubs / DToL export) with assembly IDs, BUSCO, and assembly level.
2. Filter to the clade you care about (e.g., plants).
3. Use NCBI Datasets API to download assemblies in batches.
4. Resume after interruptions.
5. Run your tool (e.g., EDTA) per-genome.

Below is the exact workflow I used.

## Step 1: Get the DToL metadata TSV

You need a TSV with columns:
- `assembly_id`
- `scientific_name`
- `taxon_id`
- `assembly_level`
- `busco_completeness`
- (optional) `group`, `taxa1`, `taxa2`

## Step 2: Download genomes in batches

```bash
python3 scripts/download_dtol_genomes.py \
  --tsv data/download_allgoatgenomehubs.tsv \
  --outdir results/genomes_plants \
  --group plants \
  --min-busco 95 \
  --require-chromosome \
  --resume --verbose
```

This will write:
- `results/genomes_plants/*.fasta`
- `results/genomes_plants/run_log.csv`
- `results/genomes_plants/run_errors.csv`

## Step 3: Run EDTA (or other TE tool)

```bash
for fasta in results/genomes_plants/*.fasta; do
  EDTA.pl --genome "$fasta" --species others --step all --threads 8
  echo "done $fasta"
done
```

## Notes

- If the machine crashes, rerun with `--resume`.
- If a FASTA is partially downloaded, delete it and resume.
- Start with plants (or any group) to validate your pipeline before scaling to all DToL.

