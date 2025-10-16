#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.outdir = "results"
params.target_pdbs = "input/*.pdb"
params.ligand_csv = "input/ligands.csv"
params.boltz_template_force = false
params.boltz_template_threshold = 1.0
params.boltz_use_template = false
params.gpu_devices = null
params.gpu_allocation_detect_process_regex = null
params.use_msa_server = false
params.skip_dynamicbind = false
params.skip_boltz = false

include { DYNAMICBIND } from './modules/dynamicbind'
include { CREATE_BOLTZ_YAML_LIGAND ; BOLTZ_LIGAND } from './modules/boltz_ligand'

process ADD_INCHIKEY {
    tag "add_inchikey"
    // TODO: Make a new nf-binder-design-utils version with uv and rdkit installed
    // container 'ghcr.io/australian-protein-design-initiative/containers/nf-binder-design-utils:0.1.4'
    container 'ghcr.io/astral-sh/uv:python3.13-trixie-slim'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path ligands_csv

    output:
    path "ligands_with_inchikey.csv", emit: ligands_csv_with_inchikey

    script:
    """
    uv run ${projectDir}/bin/add_inchikey.py \
        "${ligands_csv}" \
        -o ligands_with_inchikey.csv \
        --smiles-column ligand \
        --shake256-fallback
    """
}

workflow {
    ch_target_pdbs = Channel.fromPath(params.target_pdbs)
    ch_input_ligand_csv = file(params.ligand_csv)

    // Add InChIKey column and parse augmented ligands CSV
    ch_ligand_csv = ADD_INCHIKEY(ch_input_ligand_csv)

    // Run DynamicBind (unless skipped)
    if (!params.skip_dynamicbind) {
        DYNAMICBIND(ch_target_pdbs, ch_ligand_csv, 20, 3, false)
    }

    // Run Boltz ligand prediction (unless skipped)
    if (!params.skip_boltz) {
        // Prepare target channel with metadata
        ch_targets = Channel.fromPath(params.target_pdbs)
            .map { pdb ->
                def name = pdb.baseName
                [[id: name], pdb]
            }

        // Parse augmented ligands CSV
        ch_ligands = ch_ligand_csv
            .splitCsv(header: true)
            .map { row ->
                def ligand_id = row.inchikey ?: row.ligand.take(20).replaceAll(/[^a-zA-Z0-9-]/, '_')
                [
                    id: ligand_id,
                    smiles: row.ligand,
                ]
            }

        // Create all target-ligand combinations
        ch_target_ligand_pairs = ch_targets
            .combine(ch_ligands)
            .map { target_meta, target_pdb, ligand_meta ->
                [target_meta, target_pdb, ligand_meta]
            }

        // Generate YAML files for each target-ligand pair
        CREATE_BOLTZ_YAML_LIGAND(ch_target_ligand_pairs)

        // Run Boltz predictions
        BOLTZ_LIGAND(CREATE_BOLTZ_YAML_LIGAND.out)
    }
}
