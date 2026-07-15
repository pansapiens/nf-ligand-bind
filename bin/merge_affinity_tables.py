#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pandas",
# ]
# ///
"""Join Boltz2 and DynamicBind affinity CSVs on protein_path + inchikey."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

JOIN_KEYS = ["protein_path", "inchikey"]
ID_COLS = ["protein_path", "ligand", "inchikey"]


def _is_usable(path: Optional[Path]) -> bool:
    if path is None or not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if not text:
        return False
    # Header-only files are treated as empty for joining
    return text.count("\n") >= 1 and len(text.splitlines()) > 1


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for key in JOIN_KEYS:
        if key not in df.columns:
            raise ValueError(f"{path} missing required join column '{key}'")
    return df


def merge_tables(
    boltz_csv: Optional[Path],
    dynamicbind_csv: Optional[Path],
    ligands_csv: Optional[Path] = None,
) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []

    if ligands_csv is not None and ligands_csv.exists():
        ligands = pd.read_csv(ligands_csv)
        for col in ID_COLS:
            if col not in ligands.columns:
                raise ValueError(f"Ligands CSV missing column '{col}'")
        # Prefer the target/protein path used by scoring tables when present later
        frames.append(ligands[ID_COLS].drop_duplicates())

    boltz_df = _read_csv(boltz_csv) if _is_usable(boltz_csv) else None
    db_df = _read_csv(dynamicbind_csv) if _is_usable(dynamicbind_csv) else None

    if boltz_df is None and db_df is None:
        if frames:
            logger.warning("No Boltz or DynamicBind scores to merge; writing ligand table only")
            return frames[0]
        raise ValueError("No usable Boltz or DynamicBind affinity CSV provided")

    if boltz_df is not None:
        frames.append(boltz_df)
    if db_df is not None:
        frames.append(db_df)

    merged = frames[0]
    for right in frames[1:]:
        # Avoid duplicate ligand column from right-hand tables
        right_cols = [
            c for c in right.columns if c == "ligand" and c in merged.columns
        ]
        right_merge = right.drop(columns=right_cols, errors="ignore")
        merged = merged.merge(right_merge, on=JOIN_KEYS, how="outer")

    # If ligand missing on some rows, fill from whichever side had it
    if "ligand" not in merged.columns and boltz_df is not None and "ligand" in boltz_df.columns:
        merged = merged.merge(
            boltz_df[JOIN_KEYS + ["ligand"]].drop_duplicates(),
            on=JOIN_KEYS,
            how="left",
        )
    if "ligand" not in merged.columns and db_df is not None and "ligand" in db_df.columns:
        merged = merged.merge(
            db_df[JOIN_KEYS + ["ligand"]].drop_duplicates(),
            on=JOIN_KEYS,
            how="left",
        )

    # Reorder columns
    first = [c for c in ID_COLS if c in merged.columns]
    boltz_cols = sorted(c for c in merged.columns if c.startswith("boltz2_"))
    db_cols = sorted(c for c in merged.columns if c.startswith("dynamicbind_"))
    other = [c for c in merged.columns if c not in first + boltz_cols + db_cols]
    return merged[first + boltz_cols + db_cols + other]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Join boltz_affinity.csv and dynamicbind_affinity.csv into affinity.csv"
    )
    parser.add_argument("--boltz", type=Path, default=None, help="boltz_affinity.csv")
    parser.add_argument(
        "--dynamicbind", type=Path, default=None, help="dynamicbind_affinity.csv"
    )
    parser.add_argument(
        "--ligands",
        type=Path,
        default=None,
        help="Optional ligands_with_inchikey.csv used as the left-hand id table",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output CSV path, or '-' for stdout (default)",
    )
    args = parser.parse_args()

    df = merge_tables(args.boltz, args.dynamicbind, args.ligands)
    if args.output == "-":
        df.to_csv(sys.stdout, index=False, lineterminator="\n")
    else:
        df.to_csv(args.output, index=False, lineterminator="\n")
        logger.info("Wrote %d row(s) to %s", len(df), args.output)


if __name__ == "__main__":
    main()
