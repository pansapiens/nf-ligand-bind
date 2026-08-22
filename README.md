# nf-ligand-bind

A Nextflow pipeline for high-throughput ligand binding prediction.

It runs:

- [DynamicBind](https://github.com/luwei0917/DynamicBind) — pose prediction and affinity screening
- [Boltz-2](https://github.com/jwohlwend/boltz) — protein–ligand co-folding and affinity prediction
- [PandaMap](https://github.com/pritampanda15/PandaMap) — 2D/3D ligand–protein interaction plots on predicted poses

Each stage can be skipped with `--skip_dynamicbind`, `--skip_boltz`, or `--skip_pandamap`.

### Input

Provide a `ligands.csv` with one row per target:ligand pair. Paths in
`protein_path` are resolved relative to the CSV file location and staged into
the workflow as `path()` inputs:

```csv
protein_path,ligand
target.pdb,CC(=O)Nc1cc(NC(=O)c2c(Cl)cccc2Cl)ccn1
target.pdb,N#C[C@@H]1C[C@@H]1C(=O)Nc1cc(NC(=O)c2c(Cl)cccc2Cl)ccn1
target_pdbs/other_target.pdb,O=C(CO)Nc1cc(NC(=O)c2c(Cl)cccc2Cl)ccn1
```

Paths are resolved relative to the CSV file's directory (so in an example
under `examples/quick/input/ligands.csv`, use `target.pdb` not
`input/target.pdb`).

To build an all-against-all table from a folder of PDBs and a ligand list:

```bash
python3 bin/multiplex_ligands.py input/target_pdbs input/smiles.txt -o input/ligands.csv
```

`input/smiles.txt` can be one SMILES per line, or a CSV with a `ligand` column
(for example `input/pfas_panel.csv` from the PFAS example).

## Running

Ready-to-run examples:

| example | description |
|---|---|
| [`examples/quick`](examples/quick) | DynamicBind tutorial — 1 target, 4 ligands |
| [`examples/pfas_transthyretin`](examples/pfas_transthyretin) | PFAS panel vs transthyretin multimers (5JID) |

```bash
cd examples/quick
./run-local.sh
```

Or from the repo root with your own inputs:

```bash
nextflow run main.nf \
  --outdir results \
  --ligand_csv "./input/ligands.csv" \
  -resume
```

Results land in `--outdir` (`results/` by default): `affinity.csv`, `boltz/`, `dynamicbind/`, and `pandamap/{boltz,dynamicbind}/` (interaction plots, contact tables, and reports).
