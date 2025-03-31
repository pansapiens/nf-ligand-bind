#!/usr/bin/env nextflow
nextflow.enable.dsl=2

params.outdir = "results"
params.target_pdbs = "input/*.pdb"
params.ligand_csv = "input/ligands.csv"

include { DYNAMICBIND } from './modules/dynamicbind'

workflow {
    ch_target_pdbs = Channel.fromPath(params.target_pdbs)
    ch_ligand_csv = file(params.ligand_csv)

    DYNAMICBIND(ch_target_pdbs, ch_ligand_csv, 20, 3, false)
}
