process PANDAMAP {
    tag "${meta.id}"

    // Wave-built container from envs/pandamap.yml (pandamap[full] + rdkit +
    // dssp=4.5.3 from conda-forge), built with the Wave CLI:
    //   wave --conda-file envs/pandamap.yml --await --platform linux/amd64
    // The tag is content-addressed by the recipe. The conda directive below
    // is used instead when running with -profile conda (container takes
    // precedence under docker/apptainer, conda wins with conda.enabled).
    container 'wave.seqera.io/wt/72fd15bd5001/wave/build:pandamap--196a145310186261'
    conda "${projectDir}/envs/pandamap.yml"

    publishDir "${params.outdir}/pandamap/${meta.target}/${meta.inchikey}", mode: 'copy'

    input:
    tuple val(meta), path(structure)

    output:
    path "interactions.png", emit: interactions_png
    path "interactions.csv", emit: interactions_csv
    path "interactions_3d.html", emit: interactions_3d_html, optional: true
    path "report.txt", emit: report, optional: true
    path "plots.png", emit: plots_png, optional: true
    path "deltaG.txt", emit: delta_g, optional: true

    script:
    // Ligand auto-detected from HETATM records (Boltz writes it as LIG1 in
    // chain X); override with --pandamap_ligand_resname for other resnames.
    def ligand_flag = params.pandamap_ligand_resname ? "--ligand ${params.pandamap_ligand_resname}" : ''
    """
    # PandaMap invokes DSSP by the name 'dssp' (its default), but conda-forge
    # dssp ships the binary as 'mkdssp'; provide a task-local alias on PATH.
    mkdir -p .local-bin
    ln -sf "\$(command -v mkdssp)" .local-bin/dssp
    export PATH="\$PWD/.local-bin:\$PATH"

    # Boltz names the ligand residue LIG1 (4 chars). BioPython's PDB writer,
    # used internally by PandaMap for its DSSP temp file, shifts columns on
    # 4-char residue names and mkdssp then rejects the file - so DSSP always
    # silently falls back to the geometric method. Rename to 3-char LIG.
    sed 's/LIG1/LIG /g' '${structure}' > pandamap_input.cif

    pandamap 'pandamap_input.cif' \\
        ${ligand_flag} \\
        -o interactions.png \\
        --report --report-file report.txt \\
        --csv interactions.csv \\
        --plots plots.png \\
        --3d --3d-output interactions_3d.html \\
        --deltaG \\
        --dpi 300 \\
        -t '${meta.target} / ${meta.inchikey}' \\
        2>&1 | tee pandamap.log

    # Extract the empirical binding free energy block into its own artefact
    grep -A6 'Estimated Binding Affinity' pandamap.log > deltaG.txt || true
    """
}
