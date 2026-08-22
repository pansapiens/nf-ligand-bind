#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.outdir = "results"
params.target_pdbs = "input/*.pdb"
params.ligand_csv = "input/ligands.csv"
// Boltz templates: the target structure is passed as a template with a forced
// (restrained) backbone by default; --flexible relaxes the force restraints.
params.boltz_template_force = true
params.boltz_template_threshold = 1.0
params.boltz_use_template = true
params.flexible = false
params.gpu_devices = null
params.gpu_allocation_detect_process_regex = null
params.use_msa_server = false
params.skip_dynamicbind = false
params.skip_boltz = false
params.dynamicbind_output_poses = false
params.skip_pandamap = false
params.pandamap_ligand_resname = null

include { DYNAMICBIND } from './modules/dynamicbind'
include { CREATE_BOLTZ_YAML_LIGAND ; BOLTZ_LIGAND } from './modules/boltz_ligand'
include { PANDAMAP } from './modules/pandamap'
include { MERGE_AFFINITY } from './modules/merge_affinity'

process ADD_INCHIKEY {
    tag "add_inchikey"
    // boltz image has rdkit + /usr/bin/ps (needed for Nextflow metrics under --cleanenv)
    container 'ghcr.io/australian-protein-design-initiative/containers/boltz:v2.2.1-2'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path ligands_csv

    output:
    path "ligands_with_inchikey.csv", emit: ligands_csv_with_inchikey

    script:
    """
    python3 ${projectDir}/bin/add_inchikey.py \
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

    ch_boltz_scores = Channel.empty()
    ch_dynamicbind_scores = Channel.empty()

    // Run DynamicBind (unless skipped)
    if (!params.skip_dynamicbind) {
        DYNAMICBIND(ch_target_pdbs, ch_ligand_csv, 20, 3, params.dynamicbind_output_poses)
        ch_dynamicbind_scores = DYNAMICBIND.out.scores_csv
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
        ch_boltz_scores = BOLTZ_LIGAND.out.scores_csv

        // PandaMap interaction analysis on predicted Boltz structures
        if (!params.skip_pandamap) {
            PANDAMAP(BOLTZ_LIGAND.out.predicted_structure)
        }
    }

    // Collect per-task score CSVs as file lists. Column-aligned concatenation
    // happens in MERGE_AFFINITY: different multimeric states emit different
    // column counts (boltz2_pair_chains_iptm_* grows with chain number), which
    // breaks naive text concatenation (collectFile keepHeader).
    ch_boltz_affinity = ch_boltz_scores
        .collect()
        .ifEmpty([])

    ch_dynamicbind_affinity = ch_dynamicbind_scores
        .collect()
        .ifEmpty([])

    // Join Boltz2 + DynamicBind into a single master affinity table
    MERGE_AFFINITY(ch_boltz_affinity, ch_dynamicbind_affinity)
}
