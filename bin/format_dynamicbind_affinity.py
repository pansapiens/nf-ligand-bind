#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pandas",
# ]
# ///
"""Format DynamicBind affinity_prediction.csv with inchikey metadata and dynamicbind_ prefixes."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

IDX_RE = re.compile(r"^(?:index)?(\d+)(?:_idx_\d+)?$|^idx_(\d+)$")


def row_index_from_name(name: str) -> int:
    text = str(name).strip()
    match = IDX_RE.match(text)
    if match:
        return int(match.group(1) or match.group(2))
    # Fallback: trailing integer
    digits = re.search(r"(\d+)$", text)
    if digits:
        return int(digits.group(1))
    raise ValueError(f"Cannot parse ligand index from DynamicBind name: {name!r}")


def format_affinity(affinity_csv: Path, ligands_csv: Path) -> pd.DataFrame:
    ligands = pd.read_csv(ligands_csv)
    required = {"protein_path", "ligand", "inchikey"}
    missing = required - set(ligands.columns)
    if missing:
        raise ValueError(f"Ligands CSV missing columns: {sorted(missing)}")

    affinity = pd.read_csv(affinity_csv)
    if "affinity" not in affinity.columns:
        raise ValueError(f"Affinity CSV missing 'affinity' column: {affinity_csv}")

    name_col = "name" if "name" in affinity.columns else affinity.columns[0]
    rows = []
    for _, pred in affinity.iterrows():
        idx = row_index_from_name(pred[name_col])
        if idx < 0 or idx >= len(ligands):
            raise ValueError(
                f"DynamicBind index {idx} out of range for ligands CSV with {len(ligands)} rows"
            )
        ligand_row = ligands.iloc[idx]
        row = {
            "protein_path": ligand_row["protein_path"],
            "ligand": ligand_row["ligand"],
            "inchikey": ligand_row["inchikey"],
            "dynamicbind_affinity": pred["affinity"],
        }
        # Keep any extra DynamicBind score columns with prefix
        for col, value in pred.items():
            if col in {name_col, "affinity"}:
                continue
            row[f"dynamicbind_{col}"] = value
        rows.append(row)

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add inchikey metadata and dynamicbind_ prefixes to DynamicBind affinity CSV."
    )
    parser.add_argument("affinity_csv", type=Path, help="DynamicBind affinity_prediction.csv")
    parser.add_argument(
        "--ligands-csv",
        type=Path,
        required=True,
        help="Ligands CSV with protein_path, ligand, inchikey (row order matches idx_N)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output CSV path, or '-' for stdout (default)",
    )
    args = parser.parse_args()

    df = format_affinity(args.affinity_csv, args.ligands_csv)
    if args.output == "-":
        df.to_csv(sys.stdout, index=False, lineterminator="\n")
    else:
        df.to_csv(args.output, index=False, lineterminator="\n")
        logger.info("Wrote %d row(s) to %s", len(df), args.output)


if __name__ == "__main__":
    main()
