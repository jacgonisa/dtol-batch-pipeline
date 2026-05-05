# Example: K-plexity on DToL genomes — full story

This documents the full k-plexity analysis on DToL chromosome-level assemblies from GoaT.
Two complementary runs were made: a high-quality tier (BUSCO ≥ 95 %) and a broader under-95 tier.

---

## Run 1 — High-quality tier (BUSCO ≥ 95 %)

### Background

Starting from the GoaT/DToL catalogue (4793 assemblies), two filters were applied:

1. `assembly_level == Chromosome` → 2653 assemblies
2. `busco_completeness ≥ 95 %` → 1754 assemblies (1683 unique species; 71 species appear
   twice because GoaT lists hap1 and hap2 phased assemblies separately under the same
   species name — only the first is processed, the second is auto-skipped via `--resume`).

After processing, 1671 species have complete k-plexity output. The 83-assembly gap breaks
down as: 71 phantom hap2 skips + 12 species sitting exactly at BUSCO = 95.0 that were
accidentally excluded by an off-by-one in the filter (`>` instead of `>=`; fixed in this
version of the script). Re-running with `--resume` recovers those 12.

### Input

`data/download_allgoatgenomehubs.tsv` — downloaded from GoaT, 4793 assemblies.

### Run command

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

Replace `/path/to/FASTK/Kplex` with the path to your compiled Kplex binary.

### Results

| Metric | Value |
|---|---|
| Eligible assemblies | 1754 |
| Unique species | 1683 |
| Successfully processed | 1671 |
| Failed (NCBI 502 errors) | ~33 |
| Clade breakdown | Invertebrates 1288 · Viridiplantae 227 · Vertebrates 135 · Fungi 20 · Protists 1 |

Clade representation is uneven: fungi are heavily under-represented because most fungal
assemblies in DToL have BUSCO completeness 90–95 %, just below the strict threshold.

---

## Run 2 — Under-BUSCO-95 tier (BUSCO < 95 % or no BUSCO data)

### Background

To recover species excluded by the 95 % threshold, a second run targets all
chromosome-level assemblies in GoaT with BUSCO < 95 % (and assemblies with no BUSCO
annotation at all — these are mostly bryophytes and algae where BUSCO is simply not
available, not a sign of poor quality).

Input TSV was pre-sorted so that 137 supervisor-curated priority species (from a
327-species reference set) appear first in the queue. If the run is interrupted, the
most scientifically important species are guaranteed to have been processed.

This run uses `--chr-only`, a new flag added to the pipeline that skips the
whole-genome (all-contigs) k-mer pass and only computes k-plexity on the
chromosome-filtered FASTA. This roughly halves compute time per species and keeps
output tidy — only `.chr.*` files are written, which is the biologically meaningful
quantity anyway.

### Input

`data/download_allgoatgenomehubs_underbusco95_chr.tsv` — 842 assemblies, chromosome-level,
BUSCO < 95 % or NaN, sorted by priority (supervisor species first).

BUSCO distribution of these 842 assemblies:

| BUSCO range | Count |
|---|---|
| NaN (no data) | 401 |
| 90–95 % | 243 |
| 85–90 % | 95 |
| 80–85 % | 60 |
| 50–80 % | 42 |
| < 50 % | 1 |

### Run command

```bash
python3 analysis/scripts/run_kplex_dtol_ncbi_with_kmc_deeptroubleshooting.py \
  --tsv data/download_allgoatgenomehubs_underbusco95_chr.tsv \
  --outdir analysis/results/dtol_kplex_chromosomes_only_underbusco95 \
  --kmer-tool fastk \
  --kplex /path/to/FASTK/Kplex \
  --k 5:151:1 \
  --h 1:10000000 \
  --threads 20 \
  --resume \
  --verbose \
  --min-busco 0 \
  --chr-only \
  --no-per-chromosome
```

Key flags:
- `--chr-only` — skip whole-genome pass; only produce `.chr.*` output files
- `--min-busco 0` — no BUSCO floor; the TSV is already pre-filtered to under-95
- `--no-per-chromosome` — no per-individual-chromosome breakdown

### Expected output

Per species in `analysis/results/dtol_kplex_chromosomes_only_underbusco95/`:
- `{Species_name}.chr.fastk.csv` — empirical k-plexity curve (`k`, `fraction_unique`)
- `{Species_name}.chr.theoretical.csv` — theoretical curve
- `{Species_name}.chr.fastk.png` / `.chr.theoretical.png` — curve plots
- `run_log.csv` — status per assembly

---

## Notes on `--chr-only`

By default the pipeline runs k-plexity **twice** per assembly:
1. On the full FASTA (all contigs, including unplaced scaffolds) → `.all.*` files
2. On the chromosome-filtered FASTA (sequences matching `chr|chromosome`) → `.chr.*` files

`--chr-only` skips step 1 entirely. The skip/resume logic is also updated: when
`--chr-only` is active, only the 4 `.chr.*` output files are checked for completion
(instead of all 8). This makes the flag safe to combine with `--resume`.

## Notes on hap1/hap2 pairs

71 species in the GoaT TSV have two assemblies (hap1 + hap2 phased). Because output
files are keyed by species name (not accession), the second assembly is auto-skipped by
`--resume` once the first is done. See
`analysis/results/dtol_kplex_chromosomes_only/haplotype_pairs.csv` for the full list
(141 rows; includes 4 suspicious pairs where "haplotypes" are actually different-ploidy
species: Rosa agrestis/canina, Karpatiosorbus bristoliensis, Holcus mollis).
