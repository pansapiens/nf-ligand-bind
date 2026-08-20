process CREATE_BOLTZ_YAML_LIGAND {
    tag "${target_meta.id}_${ligand_meta.id}"

    container 'ghcr.io/australian-protein-design-initiative/containers/boltz:v2.2.1-2'

    input:
    tuple val(target_meta), path(target_pdb), val(ligand_meta)

    output:
    tuple val(meta), path(yaml_file), path(target_pdb)

    script:
    def target_name = target_meta.id
    def ligand_id = ligand_meta.id
    def id = "${target_name}_${ligand_id}"
    // --flexible turns off the template force restraints while keeping the template
    def use_force = params.boltz_template_force && !params.flexible
    def template_force_flag = use_force ? '--template-force' : ''
    def template_threshold_flag = params.boltz_template_threshold ? "--template-threshold ${params.boltz_template_threshold}" : ''
    def no_templates_flag = params.boltz_use_template ? '' : '--no-templates'

    meta = [
        id: id,
        target: target_name,
        protein_path: target_pdb.name,
        ligand: ligand_meta.smiles,
        inchikey: ligand_id,
    ]
    yaml_file = "${id}.yml"

    """
    python3 ${projectDir}/bin/create_boltz_yaml_ligand.py \
        --target-pdb '${target_pdb}' \
        --ligand-smiles '${ligand_meta.smiles}' \
        --output-yaml '${yaml_file}' \
        ${template_force_flag} \
        ${template_threshold_flag} \
        ${no_templates_flag}
    """
}

process BOLTZ_LIGAND {
    tag "${meta.id}"
    container 'ghcr.io/australian-protein-design-initiative/containers/boltz:v2.2.1-2'
    publishDir "${params.outdir}/boltz/${meta.target}", mode: 'copy'

    input:
    tuple val(meta), path(yaml_file), path(target_pdb)

    output:
    path ("${meta.inchikey}"), emit: results
    path ("${meta.id}_boltz_scores.csv"), emit: scores_csv
    tuple val(meta), path("${meta.inchikey}/predictions/${meta.id}/*.cif"), emit: predicted_structure, optional: true
    tuple val(meta), path("${meta.inchikey}/predictions/${meta.id}/confidence_${meta.id}_model_*.json"), emit: confidence_json, optional: true
    tuple val(meta), path("${meta.inchikey}/predictions/${meta.id}/affinity_*.json"), emit: affinity_json, optional: true

    script:
    def use_msa_server_flag = params.use_msa_server ? '--use_msa_server' : ''
    def args = task.ext.args ?: ''
    """
    # Find least-used GPU (by active processes and VRAM) and set CUDA_VISIBLE_DEVICES
    if [[ -n "${params.gpu_devices}" && "${params.gpu_devices}" != "null" ]]; then
        if [[ -f "${projectDir}/bin/find_available_gpu.py" ]]; then
            free_gpu=\$(${projectDir}/bin/find_available_gpu.py "${params.gpu_devices}" --verbose --exclude "${params.gpu_allocation_detect_process_regex}" --random-wait 2)
            export CUDA_VISIBLE_DEVICES="\$free_gpu"
            echo "Set CUDA_VISIBLE_DEVICES=\$free_gpu"
        else
            echo "Warning: find_available_gpu.py not found, skipping GPU selection"
        fi
    fi

    # Boltz model weights are stored in our container
    export BOLTZ_CACHE=\${BOLTZ_CACHE:-/app/boltz/cache}

    # Create various tmp/cache directories that are expected to be in \$HOME by default
    export NUMBA_CACHE_DIR="\$(pwd)/.numba_cache"
    mkdir -p \$NUMBA_CACHE_DIR
    export XDG_CONFIG_HOME="\$(pwd)/.config"
    mkdir -p \$XDG_CONFIG_HOME
    export TRITON_CACHE_DIR="\$(pwd)/.triton_cache"
    mkdir -p \$TRITON_CACHE_DIR

    # Prevent Python from using ~/.local/lib/ packages mounted inside the container
    export PYTHONNOUSERSITE=1

    boltz predict \
        ${args} \
        ${use_msa_server_flag} \
        --preprocessing-threads ${task.cpus} \
        --num_workers ${task.cpus} \
        --cache \$BOLTZ_CACHE \
        ${yaml_file}

    # Rename output folder from boltz_results_<id> to just the ligand inchikey
    mv "boltz_results_${meta.id}" "${meta.inchikey}"

    affinity_json=\$(ls ${meta.inchikey}/predictions/${meta.id}/affinity_*.json | head -n 1)
    python3 ${projectDir}/bin/parse_boltz_ligand_scores.py \
        --affinity "\$affinity_json" \
        --confidence ${meta.inchikey}/predictions/${meta.id}/confidence_${meta.id}_model_*.json \
        --protein-path '${meta.protein_path}' \
        --ligand '${meta.ligand}' \
        --inchikey '${meta.inchikey}' \
        --target '${meta.target}' \
        -o '${meta.id}_boltz_scores.csv'
    """
}
