#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${SCRIPT_DIR}"

mkdir -p results/logs
DATESTAMP="$(date +%Y%m%d_%H%M%S)"

nextflow run "${PIPELINE_DIR}/main.nf" \
  --outdir results \
  --ligand_csv "input/ligands.csv" \
  --dynamicbind_output_poses \
  -w work \
  -profile local \
  -resume \
  -with-report "results/logs/report_${DATESTAMP}.html" \
  -with-trace "results/logs/trace_${DATESTAMP}.txt" \
  "$@"
