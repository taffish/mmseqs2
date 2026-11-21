# Source, release documentation and the base image are content-pinned. Alpine
# branch repositories are rolling: packages may be replaced or removed later.
# A successful build records today's dependencies, not perpetual byte identity.
FROM alpine:3.24.4@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf AS build
ARG TARGETARCH
ARG BUILD_JOBS=2
RUN apk add --no-cache build-base cmake ninja cargo rust zlib-dev bzip2-dev curl ca-certificates patch
WORKDIR /build
RUN curl --fail --location --retry 5 --retry-all-errors \
      https://codeload.github.com/soedinglab/MMseqs2/tar.gz/ab57c0b9cd8893f1063e391c94cc845a3179bab1 -o source.tar.gz \
 && echo 'aa4e073836aa6ae7611a9aa74aedcf27817837a37322e77c522348410f18ef7c  source.tar.gz' | sha256sum -c - \
 && mkdir source && tar -xzf source.tar.gz --strip-components=1 -C source
COPY docker/patches/html-escape.patch /build/html-escape.patch
RUN cd source && patch --batch --fuzz=0 -p1 < /build/html-escape.patch
# Build the upstream dependency-free C API crate offline; never resolve the
# unrelated Rust development/test dependencies from its parent Cargo.toml.
RUN set -eu; \
    case "$TARGETARCH" in amd64) variants='sse2 sse41 avx2';; arm64) variants=arm64;; *) exit 64;; esac; \
    mkdir -p /out/bin /out/build-records; \
    apk info -vv > /out/build-records/build-packages.txt; \
    for variant in $variants; do \
      case "$variant" in sse2) simd=SSE2;; sse41) simd=SSE4_1;; avx2) simd=AVX2;; arm64) simd=ARM8;; esac; \
      cmake -S source -B "build-$variant" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DNATIVE_ARCH=0 "-DHAVE_$simd=1" \
        -DHAVE_TESTS=0 -DENABLE_WERROR=0 -DENABLE_CUDA=0 \
        -DVERSION_OVERRIDE=ab57c0b9cd8893f1063e391c94cc845a3179bab1; \
      cmake --build "build-$variant" --parallel "$BUILD_JOBS"; \
      cp "build-$variant/src/mmseqs" "/out/bin/mmseqs_$variant"; \
      strip "/out/bin/mmseqs_$variant"; \
      cp "build-$variant/CMakeCache.txt" "/out/build-records/CMakeCache-$variant.txt"; \
    done
# The fixed official release supplies architecture-independent documentation,
# examples, matrices and utilities. Its unpatched executable is not installed.
RUN curl --fail --location --retry 5 --retry-all-errors \
      https://github.com/soedinglab/MMseqs2/releases/download/19-ab57c/mmseqs-linux-arm64.tar.gz -o documentation.tar.gz \
 && echo '7319704b3eeb8e3e92fe0016afa55eb7e9d5d839d4a598fcd3bfafb5e8664f2c  documentation.tar.gz' | sha256sum -c - \
 && mkdir documentation && tar -xzf documentation.tar.gz -C documentation \
 && cp -a documentation/mmseqs/LICENSE.md documentation/mmseqs/README.md documentation/mmseqs/examples \
      documentation/mmseqs/matrices documentation/mmseqs/userguide.pdf documentation/mmseqs/util /out/ \
 && cp /build/html-escape.patch /out/build-records/ \
 && find source/lib -iname '*license*' -o -iname '*copying*' | sort > /out/build-records/license-paths.txt \
 && mkdir /out/third-party-licenses \
 && while read -r name; do \
      if test -f "$name"; then mkdir -p "/out/third-party-licenses/$(dirname "$name")"; cp "$name" "/out/third-party-licenses/$name" || exit 1; fi; \
    done < /out/build-records/license-paths.txt

FROM alpine:3.24.4@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf
# Runtime branch packages also drift; do not claim the base digest locks apk.
RUN apk add --no-cache bash bzip2 ca-certificates curl gawk grep gzip tar xz python3 libstdc++ libgomp libatomic zlib \
 && mkdir -p /opt/mmseqs2/build-records \
 && apk info -vv > /opt/mmseqs2/build-records/runtime-packages.txt \
 && find /var/cache/apk -maxdepth 1 -type f -name 'APKINDEX.*.tar.gz' -delete
COPY --from=build /out/ /opt/mmseqs2/
COPY docker/mmseqs /usr/local/bin/mmseqs
COPY docker/mmseqs2-db.py /usr/local/bin/mmseqs2-db
COPY docker/mmseqs2_transaction.py src/mmseqs2_validation.py /usr/local/bin/
COPY docker/check-taxonomy-inputs.py /opt/mmseqs2/check-taxonomy-inputs.py
COPY docker/smoke.py /opt/mmseqs2/smoke.py
ENV MMSEQS_HOME=/opt/mmseqs2 \
    PATH=/usr/local/bin:/opt/mmseqs2/bin:$PATH \
    TAFFISH_ENV=TAFFISH \
    TAFFISH_NAME=mmseqs2
RUN chmod 755 /usr/local/bin/mmseqs /usr/local/bin/mmseqs2-db \
 && ln -s /usr/local/bin/mmseqs /opt/mmseqs2/bin/mmseqs \
 && mmseqs version > /tmp/mmseqs-version \
 && grep -Fx ab57c0b9cd8893f1063e391c94cc845a3179bab1 /tmp/mmseqs-version \
 && test -r /opt/mmseqs2/userguide.pdf \
 && rm -f /tmp/mmseqs-version
# Functional, permissions, HTML and resource tests run outside image assembly.
WORKDIR /work
