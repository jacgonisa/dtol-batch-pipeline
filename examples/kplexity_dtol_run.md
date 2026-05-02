# Example: K-plexity on 1671 DToL genomes

This documents the full k-plexity run on the DToL chromosome-level assemblies from GoaT.

## Input

`data/download_allgoatgenomehubs.tsv` — downloaded from GoaT (https://goat.genomehubs.org), 4793 assemblies.

## Filters applied

- `assembly_level == Chromosome`
- `busco_completeness >= 95.0`

→ 1754 eligible entries (1683 unique species; 71 species have two assemblies due to hap1/hap2 phased assemblies sharing the same species name).

## Run command

```bash
python3 analysis/scripts/run_kplex_dtol_ncbi_with_kmc_deeptroubleshooting.py \
  --tsv data/download_allgoatgenomehubs.tsv \
  --outdir analysis/results/dtol_kplex_chromosomes_only \
  --kmer-tool fastk \
  --kplex /path/to/FASTK/Kplex \
  --k 5:151:1 \
  --h 1:10000000 \
  --threads 20 \
  --resume \
  --verbose \
  --min-busco 95.0 \
  --no-per-chromosome
```

Replace `/path/to/FASTK/Kplex` with the path to your compiled Kplex binary (see the FASTK subdirectory of the kplexity repo).

## Output

Per species in `analysis/results/dtol_kplex_chromosomes_only/`:
- `{Species_name}.chr.fastk.csv` — empirical k-plexity curve (`k`, `fraction_unique`)
- `{Species_name}.chr.theoretical.csv` — theoretical curve (`k`, `fraction_unique_theoretical`)
- `{Species_name}.chr.fastk.png` / `.chr.theoretical.png` — curve plots
- `run_log.csv` — status per assembly

## Results

| Metric | Value |
|---|---|
| Eligible assemblies | 1754 |
| Unique species | 1683 |
| Successfully processed | 1671 |
| Failed (NCBI 502 errors) | 33 |
| Clades | Invertebrates 1288, Viridiplantae 227, Vertebrates 135, Fungi 20, Protists 1 |

## Notes

- `--no-per-chromosome` means a single whole-genome k-mer count is used (chromosomes concatenated), not separate per-chromosome counts.
- `--resume` skips assemblies where all 8 expected output files already exist.
- 71 species appear twice in the TSV (phased hap1/hap2 assemblies). Since outputs are keyed by species name, the second entry is auto-skipped as already done.
- After the run, regenerate taxonomy: `python3 analysis/scripts/update_taxonomy_and_genome_sizes_like.py`
