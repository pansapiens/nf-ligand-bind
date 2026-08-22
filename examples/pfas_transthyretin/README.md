# PFAS vs transthyretin (5JID)

Pipeline demonstration: six PFAS ligands against four multimeric states of
human transthyretin ([PDB 5JID](https://www.rcsb.org/structure/5JID),
co-crystallised PFOA removed).

Requires Nextflow, Apptainer or Docker, and a local NVIDIA GPU.

```bash
./run-local.sh
```

Extra Nextflow arguments are forwarded, for example `./run-local.sh --skip_dynamicbind`.

## Panel

C4/C6/C8 chain lengths, carboxyl vs sulfonyl head groups
([`input/pfas_panel.csv`](input/pfas_panel.csv)):

| name | CID | formula | head group |
|---|---|---|---|
| PFBA | 9777 | C4HF7O2 | carboxyl |
| PFHxA | 67542 | C6HF11O2 | carboxyl |
| PFOA | 9554 | C8HF15O2 | carboxyl |
| PFBS | 67815 | C4HF9O3S | sulfonyl |
| PFHxS | 67734 | C6HF13O3S | sulfonyl |
| PFOS | 74483 | C8HF17O3S | sulfonyl |

## Targets

Protein-only structures derived from 5JID (PFOA, waters and Na+ removed):

| file | chains | description |
|---|---|---|
| `5JID_monomer_A.pdb` | A | single monomer |
| `5JID_dimer_AB.pdb` | A, B | asymmetric-unit pair (functional dimer) |
| `5JID_dimer_BB.pdb` | B, D | chain B + crystallographic 2-fold mate |
| `5JID_tetramer.pdb` | A, B, C, D | full biological tetramer |

[`input/ligands.csv`](input/ligands.csv) lists all 24 target:ligand pairs
(4 targets × 6 ligands). To regenerate it from the panel metadata:

```bash
cd examples/pfas_transthyretin
python3 ../../bin/multiplex_ligands.py \
  input/target_pdbs input/pfas_panel.csv \
  -o input/ligands.csv
```

This is 24 Boltz-2 jobs, plus DynamicBind pose prediction and PandaMap on both
pose sets.

Outputs land in `results/` (`affinity.csv`, `boltz/`, `dynamicbind/`, `pandamap/`).
