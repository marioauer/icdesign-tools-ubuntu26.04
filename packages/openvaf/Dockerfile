# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:rust
FROM ${BASE_IMAGE}
ARG OPENVAF_REPO
ARG OPENVAF_COMMIT
ARG OPENVAF_VERSION=24.0.2mob
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PATH="/root/.cargo/bin:/usr/lib/llvm-18/bin:${PATH}" \
    LLVM_SYS_181_PREFIX=/usr/lib/llvm-18 \
    CARGO_BUILD_JOBS=${JOBS} \
    CARGO_PROFILE_RELEASE_DEBUG=0

RUN test -n "${OPENVAF_COMMIT}" && git init /build/openvaf \
 && git -C /build/openvaf fetch --depth 1 "${OPENVAF_REPO}" "${OPENVAF_COMMIT}" \
 && git -C /build/openvaf checkout --detach FETCH_HEAD \
 && test "$(git -C /build/openvaf rev-parse HEAD)" = "${OPENVAF_COMMIT}"
WORKDIR /build/openvaf

# Only the compiler is packaged; workspace tests and VACASK are not built.
RUN cargo build --locked --release -p openvaf-driver --features llvm18

RUN set -eu; \
    install -Dm0755 target/release/openvaf-r "/pkgroot${PREFIX}/bin/openvaf-r"; \
    ln -s openvaf-r "/pkgroot${PREFIX}/bin/openvaf"; \
    install -Dm0644 LICENSE /pkgroot/usr/share/doc/icdesign-openvaf/copyright; \
    version="${OPENVAF_VERSION}-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out; \
    { \
      printf 'Package: icdesign-openvaf\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s\n' "${RUNTIME_DEPS}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: OpenVAF-Reloaded Verilog-A compiler (built from source)\n'; \
    } > /pkgroot/DEBIAN/control; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-openvaf_${version}_${arch}.deb"
