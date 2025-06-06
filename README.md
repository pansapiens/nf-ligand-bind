# nf-ligand-bind

A Nextflow pipeline for prediction (high throughput) ligand binding

> Currently this pipeline facilitates running [DynamicBind](https://github.com/luwei0917/DynamicBind) in parallel. Additional small molecule docking and downstream summarization may be added in the future.

### Input

You'll need a directory containing target `.pdb` files, and a `ligand.csv` file like:

```csv
protein_path,ligand
target.pdb,CC(=O)Nc1cc(NC(=O)c2c(Cl)cccc2Cl)ccn1
target.pdb,N#C[C@@H]1C[C@@H]1C(=O)Nc1cc(NC(=O)c2c(Cl)cccc2Cl)ccn1
target.pdb,O=C(CO)Nc1cc(NC(=O)c2c(Cl)cccc2Cl)ccn1
target.pdb,O=C(Nc1ccnc(NC(=O)[C@H]2C[C@H]2Cl)c1)c1c(Cl)cccc1Cl
```

> NOTE: the `protein_path` column is currently unused and can be any value, including empty

## Running

Get some example data files:
```bash
mkdir -p input
curl https://raw.githubusercontent.com/luwei0917/DynamicBind/refs/heads/main/data/cleaned_input_proteinFile.pdb >input/target.pdb
curl https://raw.githubusercontent.com/luwei0917/DynamicBind/refs/heads/main/data/ligandFile_with_protein_path.csv >input/ligands.csv
```

Run:
```bash
nextflow run main.nf \
--outdir results \
--target_pdbs "./input_pdbs/" \
--ligand_csv "./input/ligands.csv" \
-resume
```

`--target_pdbs` is a directory containing `.pdb` files.

Results are output to `results/{target_name}/`, one subdirectory per target protein.
