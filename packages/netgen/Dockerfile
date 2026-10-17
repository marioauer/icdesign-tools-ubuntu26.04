# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG NETGEN_REPO
ARG NETGEN_COMMIT
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Open Circuit Design's LVS tool, not the unrelated netgen mesh generator.
RUN test -n "${NETGEN_COMMIT}" && git init /build/netgen \
 && git -C /build/netgen fetch --depth 1 "${NETGEN_REPO}" "${NETGEN_COMMIT}" \
 && git -C /build/netgen checkout --detach FETCH_HEAD \
 && test "$(git -C /build/netgen rev-parse HEAD)" = "${NETGEN_COMMIT}"
WORKDIR /build/netgen

# Retain pre-C23 semantics for upstream's legacy C declarations.
RUN CFLAGS="-O2 -std=gnu17" ./configure --prefix="${PREFIX}" --with-tcl \
 && make -j"${JOBS}" \
 && make DESTDIR=/pkgroot install

RUN set -eu; \
    install -Dm0644 Copying "/pkgroot${PREFIX}/share/doc/icdesign-netgen/copyright"; \
    version="$(tr -d '[:space:]' < VERSION)-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out debian; \
    printf 'Source: icdesign-netgen\n\nPackage: icdesign-netgen\nArchitecture: any\nDescription: Netgen LVS\n' > debian/control; \
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
      printf 'Package: icdesign-netgen\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: Open Circuit Design netgen layout versus schematic netlist comparator\n'; \
    } > /pkgroot/DEBIAN/control; \
    check-install-prefix /pkgroot "${PREFIX}" DEBIAN; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-netgen_${version}_${arch}.deb"
