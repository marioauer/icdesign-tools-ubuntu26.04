# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG KLAYOUT_REPO
ARG KLAYOUT_COMMIT
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN test -n "${KLAYOUT_COMMIT}" && git init /build/klayout \
 && git -C /build/klayout fetch --depth 1 "${KLAYOUT_REPO}" "${KLAYOUT_COMMIT}" \
 && git -C /build/klayout checkout --detach FETCH_HEAD \
 && test "$(git -C /build/klayout rev-parse HEAD)" = "${KLAYOUT_COMMIT}"
WORKDIR /build/klayout

# Match upstream's Ubuntu 26 build: Qt5, Ruby, Python and libgit2 support.
# Stage separately so no /pkgroot or /build paths survive in the runtime RPATH.
RUN ./build.sh -release -j"${JOBS}" -qmake /usr/bin/qmake \
      -ruby /usr/bin/ruby -python /usr/bin/python3 \
      -bin /build/klayout-bin -build /build/klayout-build \
      -rpath "${PREFIX}/lib/klayout"

# Follow upstream's binary/library/plugin layout under our private prefix.
RUN set -eu; \
    mkdir -p "/pkgroot${PREFIX}/bin" "/pkgroot${PREFIX}/lib/klayout"; \
    cp -a /build/klayout-bin/klayout /build/klayout-bin/strm* "/pkgroot${PREFIX}/bin/"; \
    cp -a /build/klayout-bin/lib*.so* /build/klayout-bin/db_plugins \
      /build/klayout-bin/lay_plugins /build/klayout-bin/pymod "/pkgroot${PREFIX}/lib/klayout/"; \
    install -Dm0644 LICENSE /pkgroot/usr/share/doc/icdesign-klayout/copyright; \
    install -Dm0644 etc/logo.png /pkgroot/usr/share/pixmaps/icdesign-klayout.png; \
    mkdir -p /pkgroot/usr/share/applications; \
    sed -e "s|^Exec=.*|Exec=${PREFIX}/bin/klayout -e %f|" \
        -e 's|^Icon=.*|Icon=icdesign-klayout|' etc/klayout.desktop \
      > /pkgroot/usr/share/applications/icdesign-klayout.desktop

# Inspect every executable, private library and plugin, not just the GUI binary.
# Local shlibs metadata lets dpkg-shlibdeps resolve bundled libraries without
# hiding missing dependency information for system libraries.
RUN set -eu; \
    source ./version.sh; \
    version="${KLAYOUT_VERSION}-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out debian; \
    printf 'Source: icdesign-klayout\n\nPackage: icdesign-klayout\nArchitecture: any\nDescription: KLayout layout editor\n' > debian/control; \
    mapfile -d '' binaries < <(find "/pkgroot${PREFIX}" -type f \
      \( -name klayout -o -name 'strm*' -o -name '*.so*' \) -print0); \
    ((${#binaries[@]} >= 1)); \
    deps_args=(); \
    for binary in "${binaries[@]}"; do \
      strip --strip-unneeded "${binary}"; \
      deps_args+=("-e${binary}"); \
      objdump -p "${binary}" | awk '$1 == "SONAME" && $2 ~ /^libklayout_.*\.so\./ { \
        split($2, parts, /\.so\./); print parts[1], parts[2], "icdesign-klayout" \
      }' >> debian/shlibs.local; \
    done; \
    deps="$(dpkg-shlibdeps -O -xicdesign-klayout \
      -l"/pkgroot${PREFIX}/lib/klayout" "${deps_args[@]}" | sed -n 's/^shlibs:Depends=//p')"; \
    test -n "${deps}"; \
    { \
      printf 'Package: icdesign-klayout\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: KLayout chip layout viewer and editor with Python and Ruby scripting\n'; \
    } > /pkgroot/DEBIAN/control; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-klayout_${version}_${arch}.deb"
