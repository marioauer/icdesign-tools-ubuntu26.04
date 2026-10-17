# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG XSCHEM_REPO
ARG XSCHEM_COMMIT
ARG XSCHEM_VERSION=
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN test -n "${XSCHEM_COMMIT}" && git init /build/xschem \
 && git -C /build/xschem fetch --depth 1 "${XSCHEM_REPO}" "${XSCHEM_COMMIT}" \
 && git -C /build/xschem checkout --detach FETCH_HEAD \
 && test "$(git -C /build/xschem rev-parse HEAD)" = "${XSCHEM_COMMIT}"
WORKDIR /build/xschem

RUN if [[ ! -x ./configure && -f configure.ac ]]; then autoreconf -fi; fi \
 && ./configure --prefix="${PREFIX}" \
 && make -j"${JOBS}" \
 && make DESTDIR=/pkgroot install

RUN set -eu; \
    install -Dm0644 LICENSE "/pkgroot${PREFIX}/share/doc/icdesign-xschem/copyright"; \
    version="${XSCHEM_VERSION}"; \
    if [[ -z "${version}" ]]; then \
      version="0~git$(git show -s --format=%cd --date=format:%Y%m%d HEAD).$(git rev-parse --short=8 HEAD)"; \
    fi; \
    version="${version}-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out; \
    { \
      printf 'Package: icdesign-xschem\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s\n' "${RUNTIME_DEPS}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: xschem schematic editor\n'; \
    } > /pkgroot/DEBIAN/control; \
    check-install-prefix /pkgroot "${PREFIX}" DEBIAN; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-xschem_${version}_${arch}.deb"
