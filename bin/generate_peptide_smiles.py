#!/usr/bin/env python
# /// script
# dependencies = [
#   "rdkit"
# ]
# ///
"""
Generates peptide sequences of a specified length and outputs their SMILES strings
and InChIKeys in various formats.
"""

import argparse
import itertools
import sys
import logging
import io
import csv
from typing import List, TextIO, Optional

from rdkit import Chem
from rdkit.Chem import inchi

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)

# Standard one-letter amino acid codes
STANDARD_AMINO_ACIDS: List[str] = [
    'A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I',
    'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V'
]

def generate_peptides(length: int, allowed_aas: List[str]) -> List[str]:
    """Generates all possible peptide sequences of a given length."""
    logging.info(f"Generating peptides of length {length} using {len(allowed_aas)} amino acids.")
    peptides = [''.join(p) for p in itertools.product(allowed_aas, repeat=length)]
    logging.info(f"Generated {len(peptides)} peptide sequences.")
    return peptides

def sequence_to_smiles(sequence: str) -> Optional[str]:
    """Converts a peptide sequence (string of 1-letter codes) to SMILES."""
    mol = Chem.MolFromSequence(sequence)
    if mol:
        return Chem.MolToSmiles(mol)
    else:
        logging.warning(f"Could not generate molecule for sequence: {sequence}")
        return None

def smiles_to_inchikey(smiles: str) -> Optional[str]:
    """Converts a SMILES string to an InChIKey using RDKit.

    Args:
        smiles: The SMILES string to convert.

    Returns:
        The corresponding InChIKey, or None if conversion fails.
    """
    if not smiles:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        # sequence_to_smiles should already warn if the sequence is bad,
        # but SMILES could be invalid for other reasons if generated elsewhere.
        # We log a lower level message here just in case.
        logging.debug(f"Could not parse SMILES for InChIKey generation: {smiles}")
        return None
    try:
        key = inchi.MolToInchiKey(mol)
        return key
    except Exception as e:
        logging.warning(f"Could not generate InChIKey for SMILES {smiles}: {e}")
        return None

def write_output(peptides: List[str], output_handle: TextIO, output_format: str) -> None:
    """Writes peptide sequences, SMILES, and InChIKeys to the output handle based on format."""

    delimiter = ','
    header = ['sequence', 'smiles', 'inchikey']
    protein_path = 'target.pdb' # Default for dynamic-bind-csv

    if output_format == 'tsv':
        delimiter = '\t'
    elif output_format == 'dynamic-bind-csv':
        header = ['protein_path', 'sequence', 'ligand', 'inchikey'] # Adjusted header
        delimiter = ',' # Explicitly set for clarity
    # Default 'csv' format uses the initial header and delimiter

    writer = csv.writer(output_handle, delimiter=delimiter)
    writer.writerow(header)

    count = 0
    skipped = 0
    for seq in peptides:
        smiles = sequence_to_smiles(seq)
        if smiles:
            inchikey = smiles_to_inchikey(smiles)
            if inchikey:
                row_data: List[str] = []
                if output_format == 'dynamic-bind-csv':
                    row_data = [protein_path, seq, smiles, inchikey]
                else: # csv or tsv
                    row_data = [seq, smiles, inchikey]
                writer.writerow(row_data)
                count += 1
            else:
                # SMILES was generated, but InChIKey failed
                logging.warning(f"Generated SMILES but failed to get InChIKey for sequence: {seq}")
                skipped += 1
        else:
            # SMILES generation failed (already logged in sequence_to_smiles)
            skipped += 1

        if (count + skipped) % 1000 == 0 and (count + skipped) > 0:
             logging.info(f"Processed {(count + skipped)} sequences...")

    logging.info(f"Successfully wrote {count} records.")
    if skipped > 0:
        logging.warning(f"Skipped {skipped} sequences due to conversion or InChIKey generation errors.")

def main():
    parser = argparse.ArgumentParser(description="Generate SMILES strings and InChIKeys for peptide sequences.")
    parser.add_argument(
        "--length",
        type=int,
        default=3,
        help="Length of the peptide sequences to generate (default: 3)."
    )
    parser.add_argument(
        "--exclude-aas",
        type=str,
        default='C',
        help="Comma-separated list of one-letter amino acid codes to exclude (default: 'C')."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default='-',
        help="Output file path for the CSV. Use '-' for stdout (default: '-')."
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=['csv', 'tsv', 'dynamic-bind-csv'],
        default='csv',
        help="Output format (default: 'csv'). 'dynamic-bind-csv' adds a 'protein_path' column and renames 'smiles' to 'ligand'."
    )

    args = parser.parse_args()

    excluded_aas = set(aa.strip().upper() for aa in args.exclude_aas.split(',') if aa.strip())
    allowed_aas = [aa for aa in STANDARD_AMINO_ACIDS if aa not in excluded_aas]

    if not allowed_aas:
        logging.error("No allowed amino acids remaining after exclusion.")
        sys.exit(1)

    logging.info(f"Allowed amino acids: {', '.join(allowed_aas)}")

    peptide_sequences = generate_peptides(args.length, allowed_aas)

    if args.output == '-':
        logging.info(f"Writing output to stdout in {args.format} format.")
        write_output(peptide_sequences, sys.stdout, args.format)
    else:
        logging.info(f"Writing output to file: {args.output} in {args.format} format.")
        try:
            with open(args.output, 'w', newline='') as f:
                write_output(peptide_sequences, f, args.format)
        except IOError as e:
            logging.error(f"Could not open output file {args.output}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
