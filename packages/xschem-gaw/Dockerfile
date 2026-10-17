# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG GAW_REPO
ARG GAW_COMMIT
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN test -n "${GAW_COMMIT}" && git init /build/xschem-gaw \
 && git -C /build/xschem-gaw fetch --depth 1 "${GAW_REPO}" "${GAW_COMMIT}" \
 && git -C /build/xschem-gaw checkout --detach FETCH_HEAD \
 && test "$(git -C /build/xschem-gaw rev-parse HEAD)" = "${GAW_COMMIT}"
WORKDIR /build/xschem-gaw

# Regenerate the bundled Automake 1.15 files for Ubuntu's current toolchain.
RUN autoreconf -fi \
 && CFLAGS="-O2 -std=gnu17" ./configure --prefix="${PREFIX}" \
 && make -j"${JOBS}" \
 && make DESTDIR=/pkgroot install

RUN set -eu; \
    install -Dm0644 LICENSE "/pkgroot${PREFIX}/share/doc/icdesign-xschem-gaw/copyright"; \
    version="1.0+git$(git show -s --format=%cd --date=format:%Y%m%d HEAD).$(git rev-parse --short=8 HEAD)-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out debian; \
    printf 'Source: icdesign-xschem-gaw\n\nPackage: icdesign-xschem-gaw\nArchitecture: any\nDescription: GAW waveform viewer\n' > debian/control; \
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
      printf 'Package: icdesign-xschem-gaw\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: GAW waveform viewer for the icdesign tool stack\n'; \
    } > /pkgroot/DEBIAN/control; \
    check-install-prefix /pkgroot "${PREFIX}" DEBIAN; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-xschem-gaw_${version}_${arch}.deb"
