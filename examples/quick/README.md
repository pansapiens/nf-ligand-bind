# Quick start

Minimal pipeline demonstration using the
[DynamicBind tutorial](https://github.com/luwei0917/DynamicBind) example:
one target structure and four ligands.

Requires Nextflow, Apptainer or Docker, and a local NVIDIA GPU.

```bash
./run-local.sh
```

## Input

- [`input/target.pdb`](input/target.pdb) — cleaned receptor structure
- [`input/ligands.csv`](input/ligands.csv) — four target:ligand pairs

This is 1 target × 4 ligands = 4 Boltz-2 jobs plus DynamicBind screening.

Outputs land in `results/` (`affinity.csv`, `boltz/`, `dynamicbind/`, `pandamap/`).
