#!/usr/bin/env python3

import argparse
import yaml
import sys
import re
from pathlib import Path
from typing import Dict, Optional

import gemmi
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


def make_template_cif(pdb_file: str) -> str:
    """Convert a target PDB into a template-ready mmCIF.

    Boltz parses template structures through its mmCIF path, which aligns each
    chain against its entity full_sequence. PDBs without SEQRES (e.g. generated
    by modelling tools) produce entities with empty full_sequence and Boltz
    fails with IndexError. We set up entities and back-fill full_sequence from
    the observed polymer residues, then write mmCIF.
    """
    st = gemmi.read_structure(pdb_file)
    st.setup_entities()

    subchain_seq: Dict[str, list] = {}
    for chain in st[0]:
        polymer = chain.get_polymer()
        if len(polymer) == 0:
            continue
        subchain_seq[polymer[0].subchain] = [res.name for res in polymer]

    for entity in st.entities:
        if entity.entity_type != gemmi.EntityType.Polymer:
            continue
        if len(entity.full_sequence) > 0:
            continue
        for sub in entity.subchains:
            if sub in subchain_seq:
                entity.full_sequence = subchain_seq[sub]
                break

    stem = Path(pdb_file).with_suffix("").name + "_template.cif"
    doc = st.make_mmcif_document()
    doc.write_file(stem)
    print(f"Wrote template mmCIF: {stem}", file=sys.stderr)
    return stem


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

    # Always normalise the target to a template-ready mmCIF. Boltz template
    # parsing on raw PDBs without SEQRES crashes (empty entity full_sequence).
    template_cif = make_template_cif(args.target_pdb)

    # Add templates section (unless disabled)
    if not args.no_templates:
        template_entry = {"cif": template_cif}

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
