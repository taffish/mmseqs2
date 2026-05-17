FROM debian:12-slim

ARG MMSEQS2_TAG=18-8cc5c
ARG TARGETARCH

ENV DEBIAN_FRONTEND=noninteractive
ENV MMSEQS_HOME=/opt/mmseqs2
ENV PATH=/usr/local/bin:/opt/mmseqs2/bin:${PATH}

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      bash \
      curl \
      gawk \
      grep \
      libatomic1 \
      libbz2-1.0 \
      libgomp1 \
      libstdc++6 \
      zlib1g \
      wget \
      aria2 \
      tar \
      gzip \
      bzip2 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /root

RUN set -eux; \
    arch="${TARGETARCH:-$(dpkg --print-architecture)}"; \
    download_dir="/tmp/mmseqs2-download"; \
    install -d "${download_dir}" "${MMSEQS_HOME}"; \
    cd "${download_dir}"; \
    base_url="https://github.com/soedinglab/MMseqs2/releases/download/${MMSEQS2_TAG}"; \
    if [ "${arch}" = "amd64" ]; then \
      curl -fL "${base_url}/mmseqs-linux-sse2.tar.gz" -o mmseqs-linux-sse2.tar.gz; \
      echo "7f660ed8257adec1ddce885bb8a6acbe6acd703692146825e9fa9e9be06902af  mmseqs-linux-sse2.tar.gz" | sha256sum -c -; \
      tar -xzf mmseqs-linux-sse2.tar.gz; \
      cp -a mmseqs/. "${MMSEQS_HOME}/"; \
      install -m 0755 mmseqs/bin/mmseqs "${MMSEQS_HOME}/bin/mmseqs_sse2"; \
      rm -rf mmseqs; \
      curl -fL "${base_url}/mmseqs-linux-sse41.tar.gz" -o mmseqs-linux-sse41.tar.gz; \
      echo "0ece6a6af8f5d198bccabc98cb5fddfc9212ce04bb332e486bfdcc468c0d7b08  mmseqs-linux-sse41.tar.gz" | sha256sum -c -; \
      tar -xzf mmseqs-linux-sse41.tar.gz; \
      install -m 0755 mmseqs/bin/mmseqs "${MMSEQS_HOME}/bin/mmseqs_sse41"; \
      rm -rf mmseqs; \
      curl -fL "${base_url}/mmseqs-linux-avx2.tar.gz" -o mmseqs-linux-avx2.tar.gz; \
      echo "bd9b0234da5949ad528d5b5f9ea4cda9c1e23dce14b46c0791d4d919a76e61ce  mmseqs-linux-avx2.tar.gz" | sha256sum -c -; \
      tar -xzf mmseqs-linux-avx2.tar.gz; \
      install -m 0755 mmseqs/bin/mmseqs "${MMSEQS_HOME}/bin/mmseqs_avx2"; \
      rm -rf mmseqs; \
    elif [ "${arch}" = "arm64" ]; then \
      curl -fL "${base_url}/mmseqs-linux-arm64.tar.gz" -o mmseqs-linux-arm64.tar.gz; \
      echo "06c9a031331562e37eed3da79ef859d30a1a3ac5c5e334411dfaee5da5e9c0d0  mmseqs-linux-arm64.tar.gz" | sha256sum -c -; \
      tar -xzf mmseqs-linux-arm64.tar.gz; \
      cp -a mmseqs/. "${MMSEQS_HOME}/"; \
      install -m 0755 mmseqs/bin/mmseqs "${MMSEQS_HOME}/bin/mmseqs_arm64"; \
      rm -rf mmseqs; \
    else \
      echo "Unsupported TARGETARCH: ${arch}" >&2; \
      exit 1; \
    fi; \
    printf '%s\n' \
      '#!/bin/sh' \
      'arch="$(uname -m)"' \
      '' \
      'case "${arch}" in' \
      '  aarch64|arm64)' \
      '    binary="/opt/mmseqs2/bin/mmseqs_arm64"' \
      '    ;;' \
      '  x86_64|amd64)' \
      '    flags=""' \
      '    if [ -r /proc/cpuinfo ]; then' \
      '      flags="$(grep -m 1 "^flags" /proc/cpuinfo || true)"' \
      '    fi' \
      '    case "${flags}" in' \
      '      *avx2*) binary="/opt/mmseqs2/bin/mmseqs_avx2" ;;' \
      '      *sse4_1*) binary="/opt/mmseqs2/bin/mmseqs_sse41" ;;' \
      '      *) binary="/opt/mmseqs2/bin/mmseqs_sse2" ;;' \
      '    esac' \
      '    ;;' \
      '  *)' \
      '    echo "Unsupported runtime architecture: ${arch}" >&2' \
      '    exit 1' \
      '    ;;' \
      'esac' \
      '' \
      'exec "${binary}" "$@"' \
      > /usr/local/bin/mmseqs; \
    chmod 0755 /usr/local/bin/mmseqs; \
    ln -sf /usr/local/bin/mmseqs "${MMSEQS_HOME}/bin/mmseqs"; \
    rm -rf "${download_dir}"

RUN mmseqs version | grep -Fx "8cc5ce367b5638c4306c2d7cfc652dd099a4643f" >/dev/null \
 && mmseqs 2>&1 | grep -F "MMseqs2 Version: 8cc5ce367b5638c4306c2d7cfc652dd099a4643f" >/dev/null \
 && mmseqs easy-search 2>&1 | grep -F "usage: mmseqs easy-search" >/dev/null

ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=mmseqs2
