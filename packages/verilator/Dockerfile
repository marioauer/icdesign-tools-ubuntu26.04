# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG VERILATOR_REPO
ARG VERILATOR_COMMIT
ARG VERILATOR_VERSION=5.052
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN test -n "${VERILATOR_COMMIT}" && git init /build/verilator \
 && git -C /build/verilator fetch --depth 1 "${VERILATOR_REPO}" "${VERILATOR_COMMIT}" \
 && git -C /build/verilator checkout --detach FETCH_HEAD \
 && test "$(git -C /build/verilator rev-parse HEAD)" = "${VERILATOR_COMMIT}"
WORKDIR /build/verilator

# Install the compiler, wrappers, headers and makefiles used by --binary/--build.
RUN autoconf && ./configure --prefix="${PREFIX}" \
 && make -j"${JOBS}" \
 && make DESTDIR=/pkgroot install

RUN set -eu; \
    install -Dm0644 LICENSE "/pkgroot${PREFIX}/share/doc/icdesign-verilator/copyright"; \
    cp -a LICENSES "/pkgroot${PREFIX}/share/doc/icdesign-verilator/"; \
    version="${VERILATOR_VERSION}-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out debian; \
    printf 'Source: icdesign-verilator\n\nPackage: icdesign-verilator\nArchitecture: any\nDescription: Verilator\n' > debian/control; \
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
      printf 'Package: icdesign-verilator\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: Verilator Verilog and SystemVerilog compiler and simulator\n'; \
    } > /pkgroot/DEBIAN/control; \
    check-install-prefix /pkgroot "${PREFIX}" DEBIAN; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-verilator_${version}_${arch}.deb"
