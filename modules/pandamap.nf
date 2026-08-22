process PANDAMAP {
    tag "${meta.id}"

    // Dependencies via conda recipe (PyPI packages through pip); enable with
    // `-profile conda`, or build a container from the same recipe with Wave
    // (`-profile wave`) when running with docker/apptainer.
    conda "${projectDir}/envs/pandamap.yml"

    publishDir "${params.outdir}/pandamap/${meta.target}/${meta.inchikey}", mode: 'copy'

    input:
    tuple val(meta), path(structure)

    output:
    path "interactions.png", emit: interactions_png
    path "interactions.csv", emit: interactions_csv
    path "report.txt", emit: report, optional: true
    path "plots.png", emit: plots_png, optional: true

    script:
    // Ligand auto-detected from HETATM records unless a resname is given
    def ligand_flag = params.pandamap_ligand_resname ? "--ligand ${params.pandamap_ligand_resname}" : ''
    """
    pandamap '${structure}' \\
        ${ligand_flag} \\
        -o interactions.png \\
        --report --report-file report.txt \\
        --csv interactions.csv \\
        --plots plots.png \\
        --dpi 200 \\
        -t '${meta.target} / ${meta.inchikey}'
    """
}
