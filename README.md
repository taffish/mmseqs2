# taf-mmseqs2

[MMseqs2 Release 20](https://github.com/soedinglab/MMseqs2/releases/tag/20-ae60e)
for TAFFISH: tool `mmseqs`, wrapper `taf-mmseqs2`, package `20-r1`,
image `ghcr.io/taffish/mmseqs2:20-r1`. CPU Linux amd64 and arm64.
The optional `mmseqs2-db` helper prepares independently versioned shared references;
ordinary local analysis does not need a shared library.

## Install and run

After publication:

```sh
taf update
taf install mmseqs2 20-r1
taf-mmseqs2 --help
taf-mmseqs2 --version
taf-mmseqs2 mmseqs version
taf-mmseqs2 mmseqs easy-search -h
```

Before publication, maintainers can install this checkout with `taf install --from .`.
Wrapper flags `--help`, `--version`, `--compile` belong to TAFFISH.
In command mode the first positional word is the executable: use
`taf-mmseqs2 mmseqs easy-search ...`, not `taf-mmseqs2 easy-search ...`.

```sh
taf-mmseqs2 mmseqs easy-search query.faa target.faa hits.tsv tmp-search --threads 4
taf-mmseqs2 mmseqs easy-cluster sequences.faa clusters tmp-cluster --threads 4
taf-mmseqs2 mmseqs easy-linclust sequences.faa linclusters tmp-lin --threads 4
taf-mmseqs2 mmseqs easy-rbh query.faa target.faa reciprocal.tsv tmp-rbh --threads 4
taf-mmseqs2 mmseqs createdb query.faa queryDB
taf-mmseqs2 mmseqs createdb target.faa targetDB
taf-mmseqs2 mmseqs search queryDB targetDB resultDB tmp-db --threads 4
taf-mmseqs2 mmseqs convertalis queryDB targetDB resultDB hits.tsv
taf-mmseqs2 mmseqs convert2fasta targetDB restored.faa
```

Inputs are protein/nucleotide FASTA/FASTQ or compatible MMseqs databases; compressed
FASTA gzip/bzip2 input is supported. Choose upstream search parameters for the data.
Default alignment TSV columns are query, target, identity, alignment length,
mismatches, gap openings, query/target coordinates, E-value and bit score.
Clustering writes `*_cluster.tsv`, `*_rep_seq.fasta` and `*_all_seqs.fasta`.
Use fresh output paths: upstream can overwrite outputs. Temporary search/index
files can be large; size RAM, threads and disk for the chosen analysis.
Docker runs as your UID/GID; Podman additionally uses keep-id. Apptainer retains
the invoking Linux user. Outputs therefore belong to the caller.

TAFFISH command-mode shell reconstruction requires **literal quotes** inside
arguments containing whitespace; outer shell quotes alone are not enough:

```sh
taf-mmseqs2 mmseqs easy-search "'query 1.faa'" "'target 1.faa'" "'hits 1.tsv'" "'tmp 1'" --threads 4
```

## Release 20 changes and compatibility

Release 20 fixes missing-partner rows from `pairaln` when exported with
`result2msa`: a dummy partner is an all-gap row instead of a spurious first
character followed by gaps. This is the upstream fix, not a TAFFISH algorithm
patch. The rest of the official source is unchanged from Release 19.

Since Release 19, protein Linclust defaults to upstream Linclust2. Results can differ from
Release 18; use `--linclust-version 1` for the old algorithm. Nucleotide
Linclust still uses version 1. Release 19 adds `cluster --cluster-version 2`,
`easy-proteomecluster` / `easy-proteomesearch`, consensus representatives and BLAST database
conversion; it changes CPU alignment/prefilter implementations and fixes several
upstream issues. See the official release notes before comparing scientific runs.
The obsolete `util/format_substitution_matrix.R` is replaced upstream by
`calculatelambda`. This packaging does not change algorithms or choose scientific
thresholds, taxonomic references or database versions.

## Native offline HTML

```sh
taf-mmseqs2 mmseqs easy-search query.faa target.faa alignments.html tmp-html --format-mode 3 --threads 4
taf-mmseqs2 mmseqs createtaxdb targetDB tmp-tax --ncbi-tax-dump taxonomy --tax-mapping-file mapping.tsv
taf-mmseqs2 mmseqs easy-taxonomy query.faa targetDB classification tmp-taxonomy --threads 4 --report-mode 1
cp classification_report classification.krona.html
```

Open the alignment HTML or taxonomy Krona HTML in the **host browser**.
The upstream taxonomy workflow names its report `classification_report` without
an extension; the copy above gives the unchanged page a browser-friendly name.
These are upstream-generated static visualizations with bundled assets, not a
new TAFFISH report service. Narrow windows may require horizontal scrolling for
long alignment graphics or sequences. No port or GUI server is started. The independent
[MMseqs2-App](https://github.com/soedinglab/MMseqs2-App) web/desktop companion is
not called by these CLI workflows and is not included.

The official Release 20 alignment exporter still inserts sequence IDs into JavaScript
without escaping. A quote can break the page and a script-ending name can inject
markup. This build applies the reviewed [HTML-only patch](docker/patches/html-escape.patch):
query and target names receive JSON/HTML-script encoding; long names are appended
without the former fixed name buffer. Decoded labels are unchanged. Search scores,
TSV, clustering, sequence storage and scientific code are unchanged. The same
HTML-output patch also replaces Krona's fixed label buffer with a sized string:
the upstream XML escaping is retained and long names no longer truncate or cause
an out-of-bounds output read. Taxonomy assignments/counts are unchanged. Original
source identity and the applied patch remain in the image. Do not treat arbitrary
HTML from untrusted third parties as safe just because it has an MMseqs filename.

## Resources and licenses

Reference families (UniProt/UniRef, NCBI NR/NT/taxonomy, GTDB, Pfam and other
upstream catalog entries) are selectable, often large and independently licensed.
No family is downloaded by default or embedded in this image. The smallest
reusable unit is an explicitly selected release's FASTA, complete prebuilt
MMseqs file set, or matching taxonomy/mapping files. Mixing releases can change
results. The helper never chooses a scientific resource or silently upgrades it.

Use the provider's official release distribution and permission terms.
[UniProt](https://www.uniprot.org/help/license) copyright content uses CC BY 4.0
with its stated third-party-rights caveats; [NCBI policies](https://www.ncbi.nlm.nih.gov/home/about/policies/)
do not remove possible third-party restrictions. Other catalog entries require
their own license review. The upstream **software** MIT license does not license
downloaded data. Do not store credentials or private URLs in recipes.

A recipe records trusted acquisition provenance, permission/attribution text,
release identity, exact byte sizes and SHA256. Mutable provider URLs can still
disappear or change: changed bytes fail rather than becoming a different resource.
Replace every placeholder in this example with reviewed facts:

```json
{
  "schema": "taffish.mmseqs2.recipe.v1",
  "id": "selected-proteins",
  "version": "FIXED_RELEASE",
  "source": "Official fixed release URL and attribution",
  "license": "Applicable permission and attribution notice",
  "files": [
    {
      "name": "proteins.faa.gz",
      "url": "https://PROVIDER/FIXED_RELEASE/proteins.faa.gz",
      "size": 123456,
      "sha256": "REPLACE_WITH_64_LOWERCASE_HEX_DIGITS"
    }
  ],
  "createdb": {"input": "proteins.faa.gz", "dbtype": 1}
}
```

`createdb` is optional; `dbtype` is 0 (automatic), 1 (protein) or 2 (nucleotide).
It produces a materialized, uncompressed `reference` database (no source symlinks).
For prebuilt sets, omit `createdb` and list **every** required flat file with its
checksum; compatibility with upstream MMseqs remains the user's responsibility.
For a fixed taxonomy tar archive, a file entry can add
`"extract": ["nodes.dmp", "names.dmp", "merged.dmp", "delnodes.dmp"]`.
Only these exact regular members are extracted; general archive trees are not accepted.

### Personal and system-wide preparation

Personal root:

```sh
DBROOT="$HOME/.local/share/taffish/databases/mmseqs2"
mkdir -p "$DBROOT"
chmod 755 "$DBROOT"
```

For a site root, an administrator can create one and assign it to the installer
account (run these as the intended installer with administrator permission):

```sh
DBROOT=/usr/local/share/taffish/databases/mmseqs2
sudo install -d -m 0755 -o "$(id -u)" -g "$(id -g)" "$DBROOT"
```

`/opt/taffish/databases/mmseqs2` is also supported. The installer must own the
physical root; no group/world writes. Published members are 0755/0644 so ordinary
users can reuse them read-only. Setup requires a real writable host bind; do not
prepare databases only in an ephemeral container.
This is an administrator-once installation followed by read-only ordinary-user reuse.

Choose **one** backend (recipe.json is in the current directory):

```sh
TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0 TAFFISH_CONTAINER_BACKEND=docker \
TAFFISH_DOCKER_RUN_ARGS="-v '$DBROOT:/db-install'" \
taf-mmseqs2 mmseqs2-db install --recipe recipe.json --db-root /db-install --rights-reviewed --dry-run

TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0 TAFFISH_CONTAINER_BACKEND=podman \
TAFFISH_PODMAN_RUN_ARGS="-v '$DBROOT:/db-install'" \
taf-mmseqs2 mmseqs2-db install --recipe recipe.json --db-root /db-install --rights-reviewed --dry-run

TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0 TAFFISH_CONTAINER_BACKEND=apptainer \
TAFFISH_APPTAINER_RUN_ARGS="--bind '$DBROOT:/db-install'" \
taf-mmseqs2 mmseqs2-db install --recipe recipe.json --db-root /db-install --rights-reviewed --dry-run
```

Review acquisition and redistribution rights before `--rights-reviewed`.
Replace `--dry-run` with `--source-dir sources` for already acquired files, or
`--allow-download` for explicit HTTPS acquisition. No missing source triggers
network access implicitly. `--reserve-gb` defaults to 10 extra GiB beyond payload
and missing cached bytes; increase it for large database builds or archive expansion.
The dry run reports fixed source/license, bytes, destination and intended network use.
For an Apptainer session whose site/isolation settings omit DNS configuration,
explicit downloads may need the additional read-only bind
`--bind /etc/resolv.conf:/etc/resolv.conf:ro` in `TAFFISH_APPTAINER_RUN_ARGS`.
This uses the host's existing resolver; offline analysis needs no network.

Installation verifies the **entire existing visible library** before adding a
member, holds an exclusive lock, preserves verified existing members, uses an
owned staging directory and atomically publishes only a complete verified member.
Same recipe and ID is an idempotent verification, not an overwrite. Rerun after
interruption to resume a matching partial download. Corrupt/oversize partials,
wrong identities, broken links, bad existing members or an active lock fail clearly.
Cache retirement checks the original directory and file identities and does not
follow a replaced parent. A retirement failure is reported even if the member
has already been published; that complete member and diagnostic cache are retained.

There is no `--force`. Inspect failures first; confirm no installer is running
before an administrator moves the exact damaged member/partial or stale lock to
a recoverable quarantine **outside the root**. Keep old resources and diagnostic
evidence. Never delete a whole root or a wildcard staging directory to recover.

### Discovery, reuse and manual binds

Discovery order: explicit absolute `TAFFISH_MMSEQS2_DB_PATH`, personal root,
`/usr/local/share/taffish/databases/mmseqs2`, then `/opt/taffish/databases/mmseqs2`.
A present but invalid selected root fails; it does not fall through or download.
Host Python 3 is required only for this verification. A valid directory symlink
override is resolved to its physical root; broken links fail.
All visible members, receipts, permissions and checksums must match. The verified
root is mounted read-only at `/resources/mmseqs2`; explicitly select a member:

```sh
taf-mmseqs2 mmseqs2-db list --db-root /resources/mmseqs2
UNIT=your-recipe-id--your-version
taf-mmseqs2 mmseqs2-db verify --db-root /resources/mmseqs2 --id "$UNIT"
taf-mmseqs2 mmseqs easy-search query.faa "/resources/mmseqs2/$UNIT/reference" hits.tsv tmp --threads 4
```

Disable discovery with `TAFFISH_MMSEQS2_DB_AUTO_MOUNT=0`. Manual read-only fallback:
replace the writable setup bind with `'$DBROOT:/db:ro'` using the same Docker,
Podman or Apptainer variable, then pass `/db/$UNIT/reference` or the selected source
filename. Data/cache remains in the host root; analysis outputs and temporary
files go in your writable project directory, never inside a shared member.

Upstream `mmseqs databases` remains an **explicit, unmanaged** catalog downloader.
Its rolling downloads are not a pinned shared-library install; acquire into a
separate project directory, audit license/versions, and use a fixed recipe for
shared publication. It is not an automatic resource fallback.
For `createtaxdb`, missing local taxonomy/mapping fails before implicit fetching.
To intentionally use the upstream rolling download behavior, explicitly pass
`TAFFISH_MMSEQS2_ALLOW_DOWNLOAD=1` **inside the container**:

```sh
taf-mmseqs2 env TAFFISH_MMSEQS2_ALLOW_DOWNLOAD=1 mmseqs createtaxdb targetDB tmp-tax
```

Do not use that opt-in for a repeatable scientific reference without subsequently
recording and verifying exactly what was acquired.

## Build and support boundary

Source commit `ae60ef6964f3de689139bcfe290d9fad18f70b06`;
source archive SHA256 `e15e9935e0ae3aebfd476e585a565cf309b0c0e0ec610abe2e87254470930883`.
The [Dockerfile](docker/Dockerfile) fixes source/base identities and applies only the
published HTML patch. The dependency-free upstream BlockAligner C API crate is
built offline. Compilers are excluded from the final image. Package inventories,
CMake configuration and patch are retained under `/opt/mmseqs2/build-records`;
upstream notices, examples, matrices, utilities and guide remain under
`/opt/mmseqs2`. The official fixed ARM64 archive supplies documentation only;
its unpatched executable is not installed.

amd64 retains AVX2 → SSE4.1 → SSE2 runtime dispatch; arm64 uses the native build.
Docker/Podman select the native image; Apptainer uses the same candidate's read-only
SIF on x86_64 Linux. Set `TAFFISH_CONTAINER_BACKEND=docker|podman|apptainer`.
CPU/OpenMP is supported; CUDA/ROCm/Metal, MPI and 64-bit database IDs are not enabled.
The companion server/desktop app and production-sized reference catalogs are
outside this packaging acceptance. Tiny synthetic tests verify functionality,
not biological accuracy or production capacity.

Source/base hashes do not freeze rolling Alpine indexes, package availability or
upstream download hosting. Drift is documented at installation points; never
silently replace a failed checksum. Packaging is Apache-2.0; MMseqs2 is MIT and
vendored dependencies retain their own notices. Cite the relevant upstream
papers listed in `taffish.toml`; the 2025 GPU paper is not a claim of GPU support.

## Packaging validation

The 20-r1 candidate passed native builds and runtime validation on ARM64
Docker/Podman and x86_64 Docker/Podman/Apptainer (the actual read-only SIF).
The checks cover declared offline commands, ordinary-user read-only operation,
actual wrappers, paired-MSA missing partners, resource failure/recovery/idempotence,
parent-link-safe cache retirement and read-only shared reuse. Native offline
reports were generated again; browser interactions and narrow windows were checked.
Their bytes match the previously verified directly opened offline pages.

Final local uncompressed image sizes are 98,528,134 bytes (ARM64) and
124,269,231 bytes (amd64), 5,446 bytes more than 19-r1 on each architecture.
Compiler/build trees and package indexes are excluded; the runtime includes the
resource helper's Python, native programs, documentation and license notices.
These are engine image sizes, not registry download sizes. No production catalog,
real site-wide database installation, biological accuracy or production capacity
is certified. Publication and public CI/registry/Index verification are separate.
