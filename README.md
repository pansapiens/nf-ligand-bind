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
--target_pdbs "./input/" \
--ligand_csv "./input/ligands.csv" \
-resume
```

`--target_pdbs` is a directory containing `.pdb` files.

Results are output to `results/{target_name}/`, one subdirectory per target protein.

## Options

Boltz-2 co-folds each target:ligand pair using the target structure as a template
with forced (restrained) backbone coordinates by default:

| Option | Default | Description |
|---|---|---|
| `--boltz_use_template` | `true` | pass the target PDB as a Boltz template |
| `--boltz_template_force` | `true` | apply template force restraints (keeps output close to input coordinates) |
| `--boltz_template_threshold` | `1.0` | template restraint distance threshold (Å) |
| `--flexible` | off | turn off template force restraints while keeping the template |
| `--use_msa_server` | off | fetch MSAs for Boltz (off by default; forced templates are usually sufficient) |
| `--dynamicbind_output_poses` | off | run DynamicBind in pose-output mode instead of HTS screening |
| `--skip_dynamicbind` / `--skip_boltz` | off | skip a predictor |
| `--skip_pandamap` | off | skip PandaMap interaction analysis of Boltz predictions |
| `--pandamap_ligand_resname` | auto | force PandaMap ligand residue name (default: auto-detect HETATM ligand) |

### PandaMap interaction analysis

Each Boltz-predicted complex (model_0) is passed to
[PandaMap](https://github.com/pritampanda15/PandaMap) for full analysis
(interaction diagram, contact CSV, text report, four-panel graphical report,
3D HTML viewer and empirical binding free energy estimate), publishing to
`results/pandamap/{target}/{inchikey}/`. Dependencies are declared as a conda
recipe with PyPI packages (`envs/pandamap.yml`: `pandamap[full]` plus rdkit
and dssp from conda-forge, pinned to dssp 4.5.3 - the 4.6.1 build ships a
broken mkdssp). Two execution modes:

- `-profile conda`: conda env built locally from the recipe.
- default (docker/apptainer): a container built from the same recipe by
  [Seqera Wave](https://docs.seqera.io/wave/cli/) is pinned in the module via
  its content-addressed tag. Rebuild with:
  `wave --conda-file envs/pandamap.yml --await --platform linux/amd64`
  and update the container directive in `modules/pandamap.nf`.

  Note: global `wave.enabled = true` (a `-profile wave`) is deliberately NOT
  used - it re-resolves every container reference through wave.seqera.io
  mirrors, re-pulling images already in the local apptainer cache. Two upstream quirks are worked around inside the
process: PandaMap calls the DSSP binary as `dssp` while conda-forge ships
`mkdssp` (a task-local symlink bridges this), and Boltz's 4-character `LIG1`
ligand residue name breaks the PDB temp file PandaMap feeds to DSSP (renamed
to `LIG` in the input CIF).

### Score merging

Per-task Boltz and DynamicBind score CSVs are merged column-aligned in
`MERGE_AFFINITY` (different multimeric states emit different numbers of
`boltz2_pair_chains_iptm_*` columns; text concatenation is not schema-safe).
Outputs `affinity.csv` plus column-aligned `boltz_affinity.csv` /
`dynamicbind_affinity.csv`.
