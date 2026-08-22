#!/usr/bin/env python
"""Build ligands.csv as all-against-all target PDBs × ligand SMILES."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def read_smiles(path: Path) -> list[str]:
    lines = path.read_text().splitlines()
    if not lines:
        return []

    if "," in lines[0]:
        reader = csv.DictReader(lines)
        for column in ("ligand", "smiles"):
            if reader.fieldnames and column in reader.fieldnames:
                return [
                    row[column].strip()
                    for row in reader
                    if row.get(column, "").strip()
                ]

    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


def protein_path_for(pdb: Path, output: Path, prefix: Path | None) -> str:
    if prefix is not None:
        return str(prefix / pdb.name)
    return str(pdb.resolve().relative_to(output.parent.resolve()))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-product of target PDB files and ligand SMILES into ligands.csv."
    )
    parser.add_argument(
        "targets",
        type=Path,
        help="Directory containing *.pdb target structures",
    )
    parser.add_argument(
        "ligands",
        type=Path,
        help="One SMILES per line, or CSV with a ligand column",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("ligands.csv"),
        help="Output CSV path (default: ligands.csv)",
    )
    parser.add_argument(
        "--prefix",
        type=Path,
        default=None,
        help="Fixed prefix for protein_path values (default: path relative to output directory)",
    )
    args = parser.parse_args()

    pdbs = sorted(args.targets.glob("*.pdb"))
    if not pdbs:
        sys.exit(f"No *.pdb files found in {args.targets}")

    smiles_list = read_smiles(args.ligands)
    if not smiles_list:
        sys.exit(f"No ligands read from {args.ligands}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["protein_path", "ligand"])
        for pdb in pdbs:
            protein_path = protein_path_for(pdb, args.output, args.prefix)
            for smiles in smiles_list:
                writer.writerow([protein_path, smiles])

    print(
        f"Wrote {len(pdbs) * len(smiles_list)} rows to {args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
