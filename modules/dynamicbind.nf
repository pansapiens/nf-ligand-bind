process DYNAMICBIND {
    publishDir "${params.outdir}/dynamicbind/${target_pdb.simpleName}", mode: 'copy'

    container "ghcr.io/australian-protein-design-initiative/containers/dynamicbind:latest"

    input:
    path target_pdb
    path ligand_csv
    val inference_steps
    val savings_per_complex
    val hts

    output:
    path "complete_affinity_prediction.csv", emit: complete_affinity_prediction_csv
    path "affinity_prediction.csv", emit: affinity_prediction_csv
    // Pose files are produced in non-HTS mode; HTS affinity screening may omit them.
    // Use rank* globs so DynamicBind's intermediate data/*.pdb is not published.
    path "*/rank*.pdb", emit: poses_pdb, optional: true
    path "*/rank*.sdf", emit: poses_sdf, optional: true
    
    script:
    def args = task.ext.args ?: ''
    def hts_flag = hts ? '--hts' : ''
    """
    mkdir -p data/esm2_output

    # DynamicBind HTS reads protein_path from the CSV; point it at the staged PDB
    python3 - <<'PY'
import csv
from pathlib import Path

src = Path("${ligand_csv}")
dst = Path("ligands_for_dynamicbind.csv")
pdb = Path("${target_pdb}").name

with src.open(newline="") as fin, dst.open("w", newline="") as fout:
    reader = csv.DictReader(fin)
    if not reader.fieldnames or "protein_path" not in reader.fieldnames:
        raise SystemExit("ligands CSV must have a protein_path column")
    writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        row["protein_path"] = pdb
        writer.writerow(row)
PY

    dynamicbind \
        ${target_pdb} \
        ligands_for_dynamicbind.csv \
      --savings_per_complex ${savings_per_complex} \
      --inference_steps ${inference_steps} \
      --num_workers ${task.cpus} \
      --results results_tmp \
      --header "" \
      ${hts_flag} \
      ${args}

    # Move CSV files to current dir
    mv results_tmp/*.csv .

    # Rename index directories to inchikeys based on CSV row order
    awk -F',' 'NR>1 {print \$NF}' ligands_for_dynamicbind.csv > inchikeys.txt

    idx=0
    while IFS= read -r inchikey; do
        src_dir="results_tmp/index\${idx}_idx_\${idx}"
        if [[ -d "\$src_dir" ]]; then
            mv "\$src_dir" "\${inchikey}"
        fi
        idx=\$((idx + 1))
    done < inchikeys.txt
    """
}
