process MERGE_AFFINITY {
    tag "merge_affinity"
    container 'ghcr.io/australian-protein-design-initiative/containers/boltz:v2.2.1-2'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path boltz_csv
    path dynamicbind_csv

    output:
    path "affinity.csv", emit: affinity_csv

    script:
    """
    python3 ${projectDir}/bin/merge_affinity_tables.py \\
        --boltz "${boltz_csv}" \\
        --dynamicbind "${dynamicbind_csv}" \\
        -o affinity.csv
    """
}
