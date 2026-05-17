# taf-mmseqs2

TAFFISH wrapper for [MMseqs2](https://github.com/soedinglab/MMseqs2), an ultra-fast sequence search, clustering, and taxonomy suite for protein and nucleotide datasets.

This repository packages upstream MMseqs2 release `18-8cc5c` as the TAFFISH
package version `18-r1`. The short TAFFISH version keeps package names stable
and readable, while the Dockerfile, upstream metadata, and smoke tests pin the
exact upstream release tag and binary commit.

## Installation

Install from the public TAFFISH Hub index:

```sh
taf update
taf install mmseqs2
```

Install the exact release:

```sh
taf install mmseqs2 18-r1
```

For local testing before the app is published to the public index:

```sh
taf install --from .
```

## Usage

Show TAFFISH app help:

```sh
taf-mmseqs2 --help
```

Show the TAFFISH package version:

```sh
taf-mmseqs2 --version
```

Show upstream MMseqs2 version:

```sh
taf-mmseqs2 mmseqs version
```

Show upstream command help:

```sh
taf-mmseqs2 mmseqs
taf-mmseqs2 mmseqs easy-search
taf-mmseqs2 mmseqs createdb
```

Run an easy protein search directly from FASTA files:

```sh
taf-mmseqs2 mmseqs easy-search query.fa target.fa result.m8 tmp --threads 8 -s 5.7
```

Create and index a reusable target database:

```sh
taf-mmseqs2 mmseqs createdb target.fa targetDB --threads 8
taf-mmseqs2 mmseqs createindex targetDB tmp --threads 8
taf-mmseqs2 mmseqs easy-search query.fa targetDB result.m8 tmp --threads 8
```

Cluster sequences:

```sh
taf-mmseqs2 mmseqs easy-cluster sequences.fa clusterRes tmp --min-seq-id 0.5 -c 0.8 --cov-mode 1 --threads 8
taf-mmseqs2 mmseqs easy-linclust sequences.fa linclusterRes tmp --threads 8
```

Convert database-format search output to a tabular alignment file:

```sh
taf-mmseqs2 mmseqs createdb query.fa queryDB
taf-mmseqs2 mmseqs createdb target.fa targetDB
taf-mmseqs2 mmseqs search queryDB targetDB resultDB tmp --threads 8
taf-mmseqs2 mmseqs convertalis queryDB targetDB resultDB result.m8
```

Download one of the reference databases supported by the upstream `databases`
workflow:

```sh
taf-mmseqs2 mmseqs databases UniProtKB/Swiss-Prot swissprot tmp
taf-mmseqs2 mmseqs easy-search query.fa swissprot result.m8 tmp --threads 8
```

Because this is a command-mode TAFFISH tool, the first non-option argument is
the in-container command. MMseqs2's actual executable is named `mmseqs`, so
the clearest form is:

```sh
taf-mmseqs2 mmseqs easy-search ...
taf-mmseqs2 mmseqs easy-cluster ...
taf-mmseqs2 mmseqs createdb ...
```

Do not use `taf-mmseqs2 easy-search ...` as the normal form. In command mode,
TAFFISH will interpret `easy-search` as an executable inside the container, not
as a subcommand of `mmseqs`.

The `--` separator is only useful for option-leading arguments to the default
`mmseqs` command:

```sh
taf-mmseqs2 -- -h
taf-mmseqs2 -- --help
```

For MMseqs2 modules such as `version`, `easy-search`, or `createdb`, use the
explicit `taf-mmseqs2 mmseqs <module> ...` form.

This README lists common usage patterns, not the full upstream manual. The
TAFFISH wrapper calls the upstream `mmseqs` command directly, so official
MMseqs2 modules and options are available as upstream implements them. Use
`taf-mmseqs2 mmseqs` or the upstream user guide for the complete module list.
Release 18 modules such as `fwbw`, `pairaln`, `taxonomyreport`, and
`createdmptaxonomy` are available through the same `taf-mmseqs2 mmseqs ...`
form even though they are not expanded in the common examples above.

## Package

```text
name: mmseqs2
command: taf-mmseqs2
version: 18-r1
kind: tool
image: ghcr.io/taffish/mmseqs2:18-r1
upstream release: 18-8cc5c
upstream binary commit: 8cc5ce367b5638c4306c2d7cfc652dd099a4643f
```

## Container

The container image is built from `docker/Dockerfile`. It starts from
`debian:12-slim`, downloads official MMseqs2 release binaries from GitHub, and
verifies every downloaded archive with the upstream GitHub release sha256
digests.

For `linux/amd64`, the image installs the official `sse2`, `sse41`, and `avx2`
CPU binaries. The `/usr/local/bin/mmseqs` launcher selects the fastest
available binary at runtime based on `/proc/cpuinfo`, falling back to SSE2 on
older CPUs.

For `linux/arm64`, the image installs the official `mmseqs-linux-arm64`
binary. The upstream matrices, examples, README, license, bash-completion
script, and user guide are kept under `/opt/mmseqs2`.

The image includes these user-facing commands and runtime tools:

```text
mmseqs
bash
gawk
grep
curl
wget
aria2c
tar
gzip
bzip2
```

The downloader and shell tools are included because upstream workflows such as
`mmseqs databases` and taxonomy database setup can call external download,
archive, and text-processing utilities. The core search and clustering
workflows are provided by the upstream `mmseqs` binary itself.

This first TAFFISH package is a CPU MMseqs2 build. Upstream release
`18-8cc5c` also publishes GPU archives, but those CUDA-enabled binaries are
not bundled in this image. `--gpu 1` workflows require a future GPU-specific
TAFFISH app or a custom image with the upstream GPU binary and backend GPU
runtime options.

The official precompiled static binaries do not include MPI support. Use a
custom MPI build if you need the upstream multi-node `RUNNER=mpirun ...`
execution mode.

The image is built and validated for:

```text
linux/amd64
linux/arm64
```

The TAFFISH metadata declares a Docker smoke check:

```text
exist: mmseqs, bash, gawk, grep, curl, wget, aria2c, tar, gzip, bzip2
test:  mmseqs version reports the pinned upstream binary commit
test:  top-level MMseqs2 help is available
test:  easy-search, createdb, and databases help surfaces are available
test:  selected release 18 and taxonomy-related module help surfaces are available
test:  shell runtime is usable
test:  createdb accepts gzip and bzip2 FASTA inputs
test:  a tiny easy-search produces a tabular hit
test:  a tiny easy-cluster produces a cluster TSV
test:  tiny easy-linclust and easy-rbh workflows run
test:  createdb, search, convertalis, createtsv, and convert2fasta run as a DB workflow
```

During TAFFISH Hub indexing, this smoke metadata verifies that the published
image exposes the expected command surface, reports the pinned upstream binary
commit, includes the helper runtime tools needed by upstream workflows, and
can run representative local sequence search and clustering tasks. It does not
download remote databases or exhaustively validate every MMseqs2 module.

Each smoke command is self-contained because the public index runs every
`[smoke].test` entry in a fresh temporary container. No smoke entry depends on
files created by an earlier entry.

## Upstream

- Project: MMseqs2
- Source: <https://github.com/soedinglab/MMseqs2>
- Release: <https://github.com/soedinglab/MMseqs2/releases/tag/18-8cc5c>
- Upstream license: MIT
- Citation:
  - Steinegger and Soeding 2017, DOI: `10.1038/nbt.3988`
  - Steinegger and Soeding 2018, DOI: `10.1038/s41467-018-04964-5`
  - Mirdita et al. 2019, DOI: `10.1093/bioinformatics/bty1057`
  - Mirdita et al. 2021, DOI: `10.1093/bioinformatics/btab184`
  - Kallenborn et al. 2024, DOI: `10.1101/2024.11.13.623350`

## Maintainer Notes

Useful checks before publishing:

```sh
taf check
taf compile -- mmseqs version
taf publish --release --dry-run
docker build -t ghcr.io/taffish/mmseqs2:18-r1 -f docker/Dockerfile .
docker build --platform linux/amd64 -t ghcr.io/taffish/mmseqs2:18-r1-amd64-test -f docker/Dockerfile .
docker build --platform linux/arm64 -t ghcr.io/taffish/mmseqs2:18-r1-arm64-test -f docker/Dockerfile .
docker run --rm ghcr.io/taffish/mmseqs2:18-r1 mmseqs version
docker run --rm ghcr.io/taffish/mmseqs2:18-r1 mmseqs easy-search
```

The repository wrapper files are licensed under Apache-2.0. Upstream MMseqs2
is distributed under the MIT license, and bundled third-party components
remain under their own upstream licenses.
