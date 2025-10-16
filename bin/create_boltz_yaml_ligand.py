#!/usr/bin/env python

import argparse
import yaml
import sys
import re
from typing import Dict
from Bio import PDB
from Bio.PDB.Polypeptide import protein_letters_3to1, is_aa


def sanitize_for_filename(text: str) -> str:
    """Removes characters that are not filename-friendly."""
    return re.sub(r"[^a-zA-Z0-9_\-.]", "_", text)


def get_all_chain_sequences(pdb_file: str) -> Dict[str, str]:
    """Extract sequences from all protein chains in a PDB file.

    Returns:
        dict: {chain_id: sequence}
    """
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("structure", pdb_file)

    sequences = {}

    for chain in structure.get_chains():
        cid = chain.id.strip()
        if not cid:
            continue

        # Extract amino acid sequence
        sequence = ""
        for residue in chain:
            if is_aa(residue):
                try:
                    res_name = residue.get_resname().upper()
                    one_letter = protein_letters_3to1.get(res_name, "X")
                    sequence += one_letter
                except (KeyError, AttributeError):
                    sequence += "X"

        if sequence:
            sequences[cid] = sequence

    if not sequences:
        raise ValueError(f"No valid protein chains found in {pdb_file}")

    return sequences


def main():
    parser = argparse.ArgumentParser(
        description="Create a YAML file for BOLTZ ligand affinity prediction."
    )
    parser.add_argument("--target-pdb", required=True, help="Path to target PDB file.")
    parser.add_argument(
        "--ligand-smiles", required=True, help="SMILES string for the ligand."
    )
    parser.add_argument(
        "--output-yaml", required=True, help="Path to the output YAML file."
    )
    parser.add_argument(
        "--template-force",
        action="store_true",
        help="Force template constraint with potential.",
    )
    parser.add_argument(
        "--template-threshold",
        type=float,
        default=None,
        help="Distance threshold for template (in Angstroms).",
    )
    parser.add_argument(
        "--no-templates", action="store_true", help="Skip adding templates section."
    )

    args = parser.parse_args()

    # Extract all protein sequences from PDB
    try:
        chain_sequences = get_all_chain_sequences(args.target_pdb)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Found {len(chain_sequences)} protein chain(s) in {args.target_pdb}: {', '.join(sorted(chain_sequences.keys()))}",
        file=sys.stderr,
    )

    # Build sequences list - all protein chains first
    sequences_list = []

    for chain_id in sorted(chain_sequences.keys()):
        sequences_list.append(
            {
                "protein": {
                    "id": [chain_id],
                    "sequence": chain_sequences[chain_id],
                    "msa": "empty",
                }
            }
        )

    # Add ligand as chain X
    sequences_list.append({"ligand": {"id": ["X"], "smiles": args.ligand_smiles}})

    data = {
        "version": 1,
        "sequences": sequences_list,
    }

    # Add templates section (unless disabled)
    if not args.no_templates:
        # Use 'pdb' key for PDB files, 'cif' for CIF files
        if args.target_pdb.lower().endswith(".pdb"):
            template_entry = {"pdb": args.target_pdb}
        else:
            template_entry = {"cif": args.target_pdb}

        if args.template_force:
            template_entry["force"] = True
        if args.template_threshold is not None:
            template_entry["threshold"] = args.template_threshold

        data["templates"] = [template_entry]

    # Add properties section for affinity prediction
    # Ligand is always chain X
    data["properties"] = [{"affinity": {"binder": "X"}}]

    # Write YAML
    with open(args.output_yaml, "w") as f:
        yaml.dump(data, f, sort_keys=False)

    print(f"Created YAML file: {args.output_yaml}", file=sys.stderr)


if __name__ == "__main__":
    main()
