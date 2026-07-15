#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pandas",
# ]
# ///
"""Parse Boltz affinity and confidence JSONs into a CSV with boltz2_ field prefixes."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

MODEL_RE = re.compile(r"_model_(\d+)\.json$")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open() as fh:
        return json.load(fh)


def flatten_with_prefix(data: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    flat = pd.json_normalize(data, sep="_").iloc[0].to_dict()
    return {f"{prefix}{key}": value for key, value in flat.items()}


def model_index_from_path(path: Path) -> Optional[int]:
    match = MODEL_RE.search(path.name)
    if not match:
        return None
    return int(match.group(1))


def parse_scores(
    affinity_json: Optional[Path],
    confidence_jsons: List[Path],
    protein_path: str,
    ligand: str,
    inchikey: str,
    target: Optional[str] = None,
) -> pd.DataFrame:
    affinity_fields: Dict[str, Any] = {}
    if affinity_json is not None:
        affinity_fields = flatten_with_prefix(load_json(affinity_json), "boltz2_")

    confidence_paths = sorted(confidence_jsons, key=lambda p: (model_index_from_path(p) is None, model_index_from_path(p) or 0, p.name))
    if not confidence_paths and not affinity_fields:
        raise ValueError("At least one of --affinity or --confidence is required")

    if not confidence_paths:
        row = {
            "protein_path": protein_path,
            "ligand": ligand,
            "inchikey": inchikey,
        }
        if target:
            row["target"] = target
        row.update(affinity_fields)
        return pd.DataFrame([row])

    rows: List[Dict[str, Any]] = []
    for conf_path in confidence_paths:
        row: Dict[str, Any] = {
            "protein_path": protein_path,
            "ligand": ligand,
            "inchikey": inchikey,
        }
        if target:
            row["target"] = target
        model_idx = model_index_from_path(conf_path)
        if model_idx is not None:
            row["boltz2_model"] = model_idx
        row.update(flatten_with_prefix(load_json(conf_path), "boltz2_"))
        row.update(affinity_fields)
        rows.append(row)

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse Boltz ligand affinity/confidence JSON into a boltz2_-prefixed CSV."
    )
    parser.add_argument(
        "--affinity",
        type=Path,
        help="Path to affinity_*.json",
    )
    parser.add_argument(
        "--confidence",
        type=Path,
        nargs="*",
        default=[],
        help="One or more confidence_*_model_N.json files",
    )
    parser.add_argument("--protein-path", required=True, help="Protein/target path or name")
    parser.add_argument("--ligand", required=True, help="Ligand SMILES")
    parser.add_argument("--inchikey", required=True, help="Ligand InChIKey")
    parser.add_argument("--target", default=None, help="Optional target id")
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output CSV path, or '-' for stdout (default)",
    )
    args = parser.parse_args()

    if args.affinity is None and not args.confidence:
        parser.error("Provide --affinity and/or --confidence")

    df = parse_scores(
        affinity_json=args.affinity,
        confidence_jsons=list(args.confidence),
        protein_path=args.protein_path,
        ligand=args.ligand,
        inchikey=args.inchikey,
        target=args.target,
    )

    # Stable column order: ids first, then boltz2_ fields
    id_cols = [c for c in ["protein_path", "ligand", "inchikey", "target", "boltz2_model"] if c in df.columns]
    other_cols = [c for c in df.columns if c not in id_cols]
    df = df[id_cols + other_cols]

    if args.output == "-":
        df.to_csv(sys.stdout, index=False, lineterminator="\n")
    else:
        df.to_csv(args.output, index=False, lineterminator="\n")
        logger.info("Wrote %d row(s) to %s", len(df), args.output)


if __name__ == "__main__":
    main()
