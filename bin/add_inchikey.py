#!/usr/bin/env python
# /// script
# dependencies = [
#   "rdkit"
# ]
# ///
"""
Reads a CSV file, generates InChIKeys from a specified SMILES column,
and writes a new CSV with an added 'inchikey' column.
"""

import argparse
import csv
import sys
import logging
import io
import hashlib
from typing import Optional
from rdkit import Chem
from rdkit.Chem import inchi

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)


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
        logging.warning(f"Could not parse SMILES: {smiles}")
        return None
    try:
        key = inchi.MolToInchiKey(mol)
        return key
    except Exception as e:
        logging.warning(f"Could not generate InChIKey for SMILES {smiles}: {e}")
        return None


def smiles_to_shake256(smiles: str, length: int = 10) -> str:
    """Converts a SMILES string to SHAKE-256 hash.

    Args:
        smiles: The SMILES string to hash.
        length: Length of the hash in bytes (default: 10).

    Returns:
        SHAKE-256 hash as hexadecimal string.
    """
    if not smiles:
        return ""
    # SHAKE-256 produces a variable-length hash, we specify the output length
    return hashlib.shake_256(smiles.encode("utf-8")).hexdigest(length)


def main():
    """Main function to parse arguments and process the CSV."""
    parser = argparse.ArgumentParser(
        description="Add InChIKey column to a CSV based on SMILES strings."
    )
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to the output CSV file. Use '-' for stdout (default).",
    )
    parser.add_argument(
        "--smiles-column",
        default="ligand",
        help="Name of the column containing SMILES strings (default: 'ligand').",
    )
    parser.add_argument(
        "--shake256-fallback",
        action="store_true",
        help="Use SHAKE-256 hash of SMILES as fallback in inchikey column when InChIKey generation fails.",
    )

    args = parser.parse_args()

    try:
        # Handle input
        if args.input_csv == "-":
            logging.info("Reading from stdin...")
            input_stream = sys.stdin
        else:
            logging.info(f"Reading from file: {args.input_csv}")
            input_stream = open(args.input_csv, "r", newline="")

        # Handle output
        if args.output == "-":
            logging.info("Writing to stdout...")
            output_stream = sys.stdout
        else:
            logging.info(f"Writing to file: {args.output}")
            # Use io.StringIO for testing or if writing to a string is needed,
            # otherwise open the file directly.
            # For stdout, sys.stdout is used directly.
            output_stream = open(args.output, "w", newline="")

        reader = csv.reader(input_stream)
        writer = csv.writer(output_stream)

        # Process header
        try:
            header = next(reader)
        except StopIteration:
            logging.error("Input CSV is empty.")
            sys.exit(1)

        try:
            smiles_col_index = header.index(args.smiles_column)
        except ValueError:
            logging.error(
                f"SMILES column '{args.smiles_column}' not found in header: {header}"
            )
            sys.exit(1)

        # Write new header
        writer.writerow(header + ["inchikey"])

        # Process rows
        processed_count = 0
        for i, row in enumerate(reader):
            if len(row) <= smiles_col_index:
                logging.warning(
                    f"Row {i+2} is shorter than expected, skipping SMILES column {smiles_col_index}. Row: {row}"
                )
                smiles = ""  # Treat as empty
            else:
                smiles = row[smiles_col_index]

            inchikey = smiles_to_inchikey(smiles)
            # Use InChIKey if available, otherwise use 8-byte SHAKE-256 hash of SMILES as fallback
            if inchikey:
                identifier = inchikey
            elif args.shake256_fallback:
                identifier = smiles_to_shake256(smiles, 8)
            else:
                # If InChIKey generation fails and no fallback is enabled, exit with error
                logging.error(f"Failed to generate InChIKey for SMILES: {smiles}")
                logging.error(
                    "Use --shake256-fallback to enable SHAKE-256 hash fallback"
                )
                sys.exit(1)
            writer.writerow(row + [identifier])
            processed_count += 1
            if processed_count % 1000 == 0:
                logging.info(f"Processed {processed_count} records...")

        logging.info(f"Finished processing {processed_count} records.")

    except FileNotFoundError:
        logging.error(f"Input file not found: {args.input_csv}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        # Close files if they were opened
        if (
            "input_stream" in locals()
            and input_stream is not sys.stdin
            and not input_stream.closed
        ):
            input_stream.close()
        if (
            "output_stream" in locals()
            and output_stream is not sys.stdout
            and not output_stream.closed
        ):
            output_stream.close()


if __name__ == "__main__":
    # Note: RDKit needs to be installed in your environment.
    # You can typically install it using conda:
    # conda install -c conda-forge rdkit
    main()
