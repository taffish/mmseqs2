mmseqs2 20-r1

Purpose:
  Search, cluster and taxonomically classify protein or nucleotide sequences.

Usage:
  taf-mmseqs2 mmseqs easy-search query.faa target.faa hits.tsv tmp --threads 4
  taf-mmseqs2 mmseqs easy-cluster sequences.faa clusters tmp --threads 4
  taf-mmseqs2 mmseqs easy-linclust sequences.faa clusters tmp --threads 4
  taf-mmseqs2 mmseqs createdb sequences.faa sequenceDB
  taf-mmseqs2 mmseqs search queryDB targetDB resultDB tmp --threads 4
  taf-mmseqs2 mmseqs convertalis queryDB targetDB resultDB hits.tsv
  taf-mmseqs2 mmseqs convert2fasta sequenceDB restored.faa

Inputs and outputs:
  Supply FASTA/FASTQ or a matching MMseqs database; gzip and bzip2 input are supported.
  Search writes tabular hits; clustering writes memberships and representative FASTA.
  Use fresh output and temporary paths, and allow enough RAM/disk for your dataset.
  Protein Linclust defaults to version 2; add --linclust-version 1 for the old algorithm.
  Paths with spaces need literal quotes: "'query 1.faa'" "'hits 1.tsv'" "'tmp 1'".

Offline reports:
  taf-mmseqs2 mmseqs easy-search query.faa target.faa hits.html tmp --format-mode 3 --threads 4
  Open the HTML in your host browser. It is a single alignment viewer, not a server.
  For taxonomy, first prepare a matching local taxonomy-enabled target database:
    taf-mmseqs2 mmseqs createtaxdb targetDB tmp-tax --ncbi-tax-dump taxonomy --tax-mapping-file mapping.tsv
    taf-mmseqs2 mmseqs easy-taxonomy query.faa targetDB classification tmp-classify --threads 4 --report-mode 1
    cp classification_report classification.krona.html
  Taxonomy needs nodes.dmp, names.dmp, merged.dmp and delnodes.dmp plus accession mapping.
  Missing files fail without downloading. See README for explicit network setup.

Choose a backend:
  TAFFISH_CONTAINER_BACKEND=docker taf-mmseqs2 mmseqs version
  TAFFISH_CONTAINER_BACKEND=podman taf-mmseqs2 mmseqs version
  TAFFISH_CONTAINER_BACKEND=apptainer taf-mmseqs2 mmseqs version

Prepare reusable resources:
  Make a fixed recipe.json with source, license, filenames, sizes and SHA256; schema in README.
  DBROOT="$HOME/.local/share/taffish/databases/mmseqs2"
  mkdir -p "$DBROOT"
  Site alternatives: /usr/local/share/taffish/databases/mmseqs2 or /opt/taffish/databases/mmseqs2.
  The installer must own the root; do not allow group/world writes. Choose one backend:
    TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0 TAFFISH_CONTAINER_BACKEND=docker \
    TAFFISH_DOCKER_RUN_ARGS="-v '$DBROOT:/db-install'" \
    taf-mmseqs2 mmseqs2-db install --recipe recipe.json --db-root /db-install --rights-reviewed --dry-run
    TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0 TAFFISH_CONTAINER_BACKEND=podman \
    TAFFISH_PODMAN_RUN_ARGS="-v '$DBROOT:/db-install'" \
    taf-mmseqs2 mmseqs2-db install --recipe recipe.json --db-root /db-install --rights-reviewed --dry-run
    TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0 TAFFISH_CONTAINER_BACKEND=apptainer \
    TAFFISH_APPTAINER_RUN_ARGS="--bind '$DBROOT:/db-install'" \
    taf-mmseqs2 mmseqs2-db install --recipe recipe.json --db-root /db-install --rights-reviewed --dry-run
  Review acquisition and sharing rights. Replace --dry-run with --source-dir sources
  for offline installation, or --allow-download to explicitly fetch the fixed HTTPS files.
  --reserve-gb defaults to an extra 10 GiB. Repeat the same command after interruption.
  An active lock or damaged member fails; inspect it, do not overwrite/delete blindly.

Read-only reuse:
  Prepared roots are validated and mounted at /resources/mmseqs2:
    taf-mmseqs2 mmseqs2-db list --db-root /resources/mmseqs2
    UNIT=your-recipe-id--your-version
    taf-mmseqs2 mmseqs2-db verify --db-root /resources/mmseqs2 --id "$UNIT"
    taf-mmseqs2 mmseqs easy-search query.faa "/resources/mmseqs2/$UNIT/reference" hits.tsv tmp
  reference exists only when the recipe uses createdb; otherwise choose its supplied file.
  Discovery: TAFFISH_MMSEQS2_DB_PATH (absolute), then personal, /usr/local/share, /opt.
  Invalid selected roots fail. Discovery needs host Python 3.
  Disable it with TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0 for local inputs or manual binds.
  Manual fallback: use your backend's bind above with '$DBROOT:/db:ro', then read /db/$UNIT.

More help:
  https://github.com/taffish/mmseqs2#readme
  taf-mmseqs2 --help                  Wrapper help
  taf-mmseqs2 --version               Wrapper version
  taf-mmseqs2 mmseqs version          Upstream version
  taf-mmseqs2 mmseqs -h               Upstream command list
  taf-mmseqs2 mmseqs easy-search -h   Search options
  taf-mmseqs2 mmseqs2-db --help       Resource helper options
