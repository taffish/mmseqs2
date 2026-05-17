taf-mmseqs2 18-r1

TAFFISH wrapper for MMseqs2, an ultra-fast sequence search, clustering, and
taxonomy suite for protein and nucleotide datasets.

Usage:
  taf-mmseqs2 [TAF-APP-OPTION]
  taf-mmseqs2 [MMSEQS-CMD] [MMSEQS-ARGS...]
  taf-mmseqs2 [MMSEQS-OPTION] [MMSEQS-ARGS...]

TAF app options:
  -h, --help       Show this help text
  -v, --version    Show package and command version
  --compile        Print generated shell code instead of running it
  --               Stop parsing TAFFISH wrapper options

Upstream option calls:
  taf-mmseqs2 -- -h
  taf-mmseqs2 -- --help

Upstream commands:
  taf-mmseqs2 mmseqs version
  taf-mmseqs2 mmseqs
  taf-mmseqs2 mmseqs easy-search
  taf-mmseqs2 mmseqs createdb

Recommended examples:
  taf-mmseqs2 --version
  taf-mmseqs2 mmseqs version
  taf-mmseqs2 -- -h
  taf-mmseqs2 mmseqs easy-search query.fa target.fa result.m8 tmp --threads 8 -s 5.7
  taf-mmseqs2 mmseqs createdb target.fa targetDB --threads 8
  taf-mmseqs2 mmseqs createindex targetDB tmp --threads 8
  taf-mmseqs2 mmseqs easy-search query.fa targetDB result.m8 tmp --threads 8
  taf-mmseqs2 mmseqs easy-cluster sequences.fa clusterRes tmp --min-seq-id 0.5 -c 0.8 --cov-mode 1
  taf-mmseqs2 mmseqs easy-linclust sequences.fa linclusterRes tmp --threads 8
  taf-mmseqs2 mmseqs search queryDB targetDB resultDB tmp --threads 8
  taf-mmseqs2 mmseqs convertalis queryDB targetDB resultDB result.m8
  taf-mmseqs2 mmseqs databases UniProtKB/Swiss-Prot swissprot tmp

Common MMseqs2 modules:
  easy-search       Search FASTA/FASTQ queries against FASTA/FASTQ or MMseqs DB targets
  easy-cluster      Sensitive clustering directly from FASTA/FASTQ
  easy-linclust     Fast linear-time clustering for large sequence sets
  easy-taxonomy     Taxonomic assignment against taxonomy-aware databases
  easy-rbh          Reciprocal best-hit workflow
  createdb          Convert FASTA/FASTQ input to MMseqs2 database format
  createindex       Precompute a target database index
  search            Database-format sensitive homology search
  map               Very similar sequence mapping
  rbh               Database-format reciprocal best-hit search
  cluster           Database-format sensitive clustering
  linclust          Database-format fast clustering
  taxonomy          Database-format taxonomic classification
  convertalis       Convert alignment DB to BLAST-tab, SAM, or custom formats
  createtsv         Convert result DB to tab-separated text
  convert2fasta     Convert sequence DB back to FASTA
  databases         List and download supported public reference databases

Notes:
  - This command runs MMseqs2 inside the TAFFISH container image.
  - The TAFFISH package is named mmseqs2, but the upstream executable is named
    mmseqs. The clearest command-mode form is taf-mmseqs2 mmseqs ...
  - taf-mmseqs2 --help and taf-mmseqs2 --version are handled by the TAFFISH
    command wrapper. Use taf-mmseqs2 mmseqs version for the upstream binary
    commit.
  - The -- separator is mainly useful for option-leading top-level mmseqs
    arguments such as taf-mmseqs2 -- -h. MMseqs2 modules such as version,
    easy-search, and createdb should be called as taf-mmseqs2 mmseqs <module>.
  - Do not use taf-mmseqs2 easy-search ... as the normal form. In command mode,
    easy-search would be interpreted as an executable, not as a subcommand of
    mmseqs.
  - The wrapper calls the upstream mmseqs binary directly. Official MMseqs2
    modules and options are available as upstream implements them.
  - Release 18 modules such as fwbw, pairaln, taxonomyreport, and
    createdmptaxonomy are available through taf-mmseqs2 mmseqs <module>.
  - The image includes official CPU binaries. On linux/amd64 it dispatches to
    AVX2, SSE4.1, or SSE2 at runtime; on linux/arm64 it uses the official ARM64
    binary.
  - GPU archives from upstream release 18-8cc5c are not bundled in this CPU
    image. GPU workflows require a GPU-specific build and container backend GPU
    runtime options.
  - The official precompiled static binaries do not include MPI support.
  - Workflows such as databases may download large remote reference databases
    and need sufficient network, disk, and temporary-directory space.
  - Input, output, and tmp paths should be accessible from the current working
    directory or mounted user paths. Large searches and clustering jobs can
    require substantial temporary disk space and memory.

Container:
  image: ghcr.io/taffish/mmseqs2:18-r1
  supported backends: apptainer, podman, docker
  supported platforms: linux/amd64, linux/arm64
  upstream release: 18-8cc5c
  upstream binary commit: 8cc5ce367b5638c4306c2d7cfc652dd099a4643f

Upstream:
  project: MMseqs2
  source:  https://github.com/soedinglab/MMseqs2
  release: https://github.com/soedinglab/MMseqs2/releases/tag/18-8cc5c
  license: MIT
  citation: Steinegger and Soeding 2017; Steinegger and Soeding 2018; Mirdita et al. 2019; Mirdita et al. 2021; Kallenborn et al. 2024
  doi: 10.1038/nbt.3988; 10.1038/s41467-018-04964-5; 10.1093/bioinformatics/bty1057; 10.1093/bioinformatics/btab184; 10.1101/2024.11.13.623350
