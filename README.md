# nf-ligand-bind

A Nextflow pipeline for prediction (high throughput) ligand binding

> Currently this pipeline facilitates running [DynamicBind](https://github.com/luwei0917/DynamicBind) in parallel. Additional small molecule docking and downstream summarization may be added in the future.

## Running

Get some example data:
```bash
mkdir -p input
curl https://raw.githubusercontent.com/luwei0917/DynamicBind/refs/heads/main/data/cleaned_input_proteinFile.pdb >input/target.pdb
curl https://raw.githubusercontent.com/luwei0917/DynamicBind/refs/heads/main/data/ligandFile_with_protein_path.csv >input/ligands.csv
```

Run:
```bash
nextflow run main.nf \
--outdir results \
--target_pdbs "./input/*.pdb" \
--ligand_csv "./input/ligands.csv" \
-resume
```

Results are output to `results/{target_name}/`, one subdirectory per target protein.
