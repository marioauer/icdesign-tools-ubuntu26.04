# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG IVERILOG_REPO
ARG IVERILOG_COMMIT
ARG IVERILOG_VERSION=13.0
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN test -n "${IVERILOG_COMMIT}" && git init /build/iverilog \
 && git -C /build/iverilog fetch --depth 1 "${IVERILOG_REPO}" "${IVERILOG_COMMIT}" \
 && git -C /build/iverilog checkout --detach FETCH_HEAD \
 && test "$(git -C /build/iverilog rev-parse HEAD)" = "${IVERILOG_COMMIT}"
WORKDIR /build/iverilog

# Includes iverilog, vvp, VPI modules and compiler target backends.
RUN sh autoconf.sh && ./configure --prefix="${PREFIX}" \
 && make -j"${JOBS}" \
 && make DESTDIR=/pkgroot install

RUN set -eu; \
    install -Dm0644 COPYING /pkgroot/usr/share/doc/icdesign-iverilog/copyright; \
    version="${IVERILOG_VERSION}-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out debian; \
    printf 'Source: icdesign-iverilog\n\nPackage: icdesign-iverilog\nArchitecture: any\nDescription: Icarus Verilog\n' > debian/control; \
    deps_args=(); \
    while IFS= read -r -d '' file; do \
      if readelf -h "${file}" 2>/dev/null | grep -Eq 'Type:.*(EXEC|DYN)'; then \
        strip --strip-unneeded "${file}"; deps_args+=("-e${file}"); \
      fi; \
    done < <(find "/pkgroot${PREFIX}" -type f -print0); \
    ((${#deps_args[@]} >= 1)); \
    deps="$(dpkg-shlibdeps -O "${deps_args[@]}" | sed -n 's/^shlibs:Depends=//p')"; \
    test -n "${deps}"; \
    { \
      printf 'Package: icdesign-iverilog\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: Icarus Verilog compiler and vvp simulation runtime\n'; \
    } > /pkgroot/DEBIAN/control; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-iverilog_${version}_${arch}.deb"
