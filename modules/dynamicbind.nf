process DYNAMICBIND {
    publishDir "${params.outdir}/dynamicbind", mode: 'copy'

    container "ghcr.io/australian-protein-design-initiative/containers/dynamicbind:latest"

    input:
    path target_pdb
    path ligand_csv
    val inference_steps
    val savings_per_complex
    val hts
    
    output:
    path "${target_pdb.simpleName}/complete_affinity_prediction.csv", emit: complete_affinity_prediction_csv
    path "${target_pdb.simpleName}/affinity_prediction.csv", emit: affinity_prediction_csv
    path "${target_pdb.simpleName}/index*/*.pdb", emit: poses_pdb
    path "${target_pdb.simpleName}/index*/*.sdf", emit: poses_sdf
    path "${target_pdb.simpleName}/index*/*.pkl", emit: animation_pkl
    
    script:
    extra_args = ""
    if (hts) { extra_args = "--hts" }
    """
    mkdir -p data/esm2_output

    dynamicbind \
        ${target_pdb} \
        ${ligand_csv} \
      --savings_per_complex ${savings_per_complex} \
      --inference_steps ${inference_steps} \
      --num_workers ${task.cpus} \
      --results ${target_pdb.simpleName} \
      --header "" \
      ${extra_args}
    """
}
