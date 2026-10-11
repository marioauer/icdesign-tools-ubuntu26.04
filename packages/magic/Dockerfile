# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG MAGIC_REPO
ARG MAGIC_COMMIT
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN test -n "${MAGIC_COMMIT}" && git init /build/magic \
 && git -C /build/magic fetch --depth 1 "${MAGIC_REPO}" "${MAGIC_COMMIT}" \
 && git -C /build/magic checkout --detach FETCH_HEAD \
 && test "$(git -C /build/magic rev-parse HEAD)" = "${MAGIC_COMMIT}"
WORKDIR /build/magic

# Tcl/Tk supports both graphical editing and headless extraction/DRC.
# GCC 15+ defaults to C23, incompatible with upstream's K&R declarations.
RUN CFLAGS="-O2 -std=gnu17" ./configure --prefix="${PREFIX}" --with-tcl --with-opengl \
 && make -j"${JOBS}" \
 && make DESTDIR=/pkgroot install

RUN set -eu; \
    install -Dm0644 LICENSE /pkgroot/usr/share/doc/icdesign-magic/copyright; \
    version="$(tr -d '[:space:]' < VERSION)-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out debian; \
    printf 'Source: icdesign-magic\n\nPackage: icdesign-magic\nArchitecture: any\nDescription: Magic\n' > debian/control; \
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
      printf 'Package: icdesign-magic\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: Magic VLSI layout editor with extraction and design rule checking\n'; \
    } > /pkgroot/DEBIAN/control; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-magic_${version}_${arch}.deb"
