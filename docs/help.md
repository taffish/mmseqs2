taf-mmseqs2 18-r3

TAFFISH wrapper for MMseqs2, an ultra-fast search, clustering, and taxonomy
suite for protein and nucleotide datasets.

Usage:
  taf-mmseqs2 [TAF-APP-OPTION]
  taf-mmseqs2 [MMSEQS-CMD] [MMSEQS-ARGS...]
  taf-mmseqs2 [MMSEQS-OPTION] [MMSEQS-ARGS...]

TAF app options:
  -h, --help       Show this help text
  -v, --version    Show package and command version
  --compile        Print generated shell code instead of running it
  --               Stop parsing TAFFISH wrapper options

Help and version:
  taf-mmseqs2 -- -h
  taf-mmseqs2 -- --help
  taf-mmseqs2 mmseqs version
  taf-mmseqs2 mmseqs

Examples:
  taf-mmseqs2 mmseqs easy-search query.fa target.fa result.m8 tmp --threads 8 -s 5.7
  taf-mmseqs2 mmseqs createdb target.fa targetDB --threads 8
  taf-mmseqs2 mmseqs createindex targetDB tmp --threads 8
  taf-mmseqs2 mmseqs easy-search query.fa targetDB result.m8 tmp --threads 8
  taf-mmseqs2 mmseqs easy-cluster sequences.fa clusterRes tmp --min-seq-id 0.5 -c 0.8 --cov-mode 1
  taf-mmseqs2 mmseqs easy-linclust sequences.fa linclusterRes tmp --threads 8
  taf-mmseqs2 mmseqs search queryDB targetDB resultDB tmp --threads 8
  taf-mmseqs2 mmseqs convertalis queryDB targetDB resultDB result.m8
  taf-mmseqs2 mmseqs databases UniProtKB/Swiss-Prot swissprot tmp

Common modules:
  easy-search, easy-cluster, easy-linclust, easy-taxonomy, easy-rbh,
  createdb, createindex, search, map, rbh, cluster, linclust, taxonomy,
  convertalis, createtsv, convert2fasta, databases.

Notes:
  The TAFFISH package is named mmseqs2, but the upstream executable is mmseqs.
  Use taf-mmseqs2 mmseqs <module> for modules such as easy-search or createdb.
  Do not use taf-mmseqs2 easy-search ... as the normal form; command mode would
  treat easy-search as an executable.
  The -- separator is mainly for option-leading top-level mmseqs arguments,
  such as taf-mmseqs2 -- -h.
  Release 18 modules are available through taf-mmseqs2 mmseqs <module>.
  This is the CPU image. GPU and MPI workflows require a different build.
  The databases workflow may download large remote references and needs
  network, disk, and temporary-directory space.

Container:
  image: ghcr.io/taffish/mmseqs2:18-r3
  platforms: linux/amd64, linux/arm64
  upstream release: 18-8cc5c
  upstream binary commit: 8cc5ce367b5638c4306c2d7cfc652dd099a4643f

Upstream:
  source:  https://github.com/soedinglab/MMseqs2
  release: 18-8cc5c
  license: MIT
  citation: Steinegger and Soeding 2017; Mirdita et al. 2021
