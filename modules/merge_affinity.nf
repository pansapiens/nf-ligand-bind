process MERGE_AFFINITY {
    tag "merge_affinity"
    container 'ghcr.io/australian-protein-design-initiative/containers/boltz:v2.2.1-2'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path boltz_csvs
    path dynamicbind_csvs

    output:
    path "affinity.csv", emit: affinity_csv
    path "boltz_affinity.csv", emit: boltz_affinity_csv, optional: true
    path "dynamicbind_affinity.csv", emit: dynamicbind_affinity_csv, optional: true

    script:
    // Lists of per-task CSVs; multimeric states emit different column counts
    // (pair_chains_iptm grows with chain number), so concatenation must be
    // column-aligned (pandas.concat) rather than text-based (collectFile).
    def boltz_args = boltz_csvs ? "--boltz " + boltz_csvs.collect { "'${it}'" }.join(" ") : ""
    def db_args = dynamicbind_csvs ? "--dynamicbind " + dynamicbind_csvs.collect { "'${it}'" }.join(" ") : ""
    """
    python3 ${projectDir}/bin/merge_affinity_tables.py \\
        ${boltz_args} \\
        ${db_args} \\
        --boltz-out boltz_affinity.csv \\
        --dynamicbind-out dynamicbind_affinity.csv \\
        -o affinity.csv
    """
}
