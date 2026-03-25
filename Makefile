.PHONY: help download run-tool

help:
	@echo "Targets:"
	@echo "  download   Download genomes from data/download_allgoatgenomehubs.tsv"
	@echo "  run-tool   Run a generic command on each genome"

# Example: make download OUTDIR=results/genomes_plants GROUP=plants BUSCO=95

download:
	python3 scripts/download_dtol_genomes.py \
		--tsv data/download_allgoatgenomehubs.tsv \
		--outdir $(OUTDIR) \
		--min-busco $(BUSCO) \
		$(if $(GROUP),--group $(GROUP),) \
		--require-chromosome --resume --verbose

# Example: make run-tool GENOMES=results/genomes_plants CMD="YOUR_TOOL --genome {fasta}"

run-tool:
	python3 scripts/run_generic_tool.py \
		--genomes $(GENOMES) \
		--cmd $(CMD) \
		--log $(GENOMES)/run_tool.log \
		--resume
