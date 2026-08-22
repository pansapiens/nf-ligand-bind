#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pandas",
# ]
# ///
"""Join Boltz2 and DynamicBind affinity CSVs on protein_path + inchikey.

Accepts one or more per-task CSVs for each method. Different multimeric states
emit different numbers of columns (e.g. boltz2_pair_chains_iptm_N_M grows with
chain count), so per-task files are concatenated column-aligned with
pandas.concat rather than text concatenation - missing columns become NaN.

Writes:
  <output>                joined affinity table (outer merge on join keys)
  --boltz-out             column-aligned Boltz concatenation (optional)
  --dynamicbind-out       column-aligned DynamicBind concatenation (optional)
"""

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


def concat_aligned(paths: List[Path]) -> Optional[pd.DataFrame]:
    """Column-aligned concatenation of per-task CSVs (ragged schemas OK)."""
    frames = []
    for path in paths:
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # noqa: BLE001 - skip malformed per-task files
            logger.warning("Skipping unreadable CSV %s: %s", path, exc)
            continue
        if df.empty:
            continue
        frames.append(df)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True, sort=False)


def merge_tables(
    boltz_csvs: List[Path],
    dynamicbind_csvs: List[Path],
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

    boltz_df = concat_aligned(boltz_csvs) if boltz_csvs else None
    db_df = concat_aligned(dynamicbind_csvs) if dynamicbind_csvs else None

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
        description="Join per-task Boltz and DynamicBind affinity CSVs into affinity.csv"
    )
    parser.add_argument(
        "--boltz", type=Path, nargs="*", default=[],
        help="One or more per-task Boltz score CSVs",
    )
    parser.add_argument(
        "--dynamicbind", type=Path, nargs="*", default=[],
        help="One or more per-task DynamicBind score CSVs",
    )
    parser.add_argument(
        "--ligands",
        type=Path,
        default=None,
        help="Optional ligands_with_inchikey.csv used as the left-hand id table",
    )
    parser.add_argument(
        "--boltz-out", type=Path, default=None,
        help="Optional output path for the column-aligned Boltz concatenation",
    )
    parser.add_argument(
        "--dynamicbind-out", type=Path, default=None,
        help="Optional output path for the column-aligned DynamicBind concatenation",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output CSV path, or '-' for stdout (default)",
    )
    args = parser.parse_args()

    boltz_df = concat_aligned(args.boltz) if args.boltz else None
    if args.boltz_out and boltz_df is not None:
        boltz_df.to_csv(args.boltz_out, index=False, lineterminator="\n")
        logger.info("Wrote %d row(s) to %s", len(boltz_df), args.boltz_out)

    db_df = concat_aligned(args.dynamicbind) if args.dynamicbind else None
    if args.dynamicbind_out and db_df is not None:
        db_df.to_csv(args.dynamicbind_out, index=False, lineterminator="\n")
        logger.info("Wrote %d row(s) to %s", len(db_df), args.dynamicbind_out)

    df = merge_tables(args.boltz, args.dynamicbind, args.ligands)
    if args.output == "-":
        df.to_csv(sys.stdout, index=False, lineterminator="\n")
    else:
        df.to_csv(args.output, index=False, lineterminator="\n")
        logger.info("Wrote %d row(s) to %s", len(df), args.output)


if __name__ == "__main__":
    main()
