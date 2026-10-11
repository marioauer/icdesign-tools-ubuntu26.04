# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG NGSPICE_REPO
ARG NGSPICE_COMMIT
ARG NGSPICE_VERSION=47
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Fetch the immutable commit, not the potentially moving ref.
RUN test -n "${NGSPICE_COMMIT}" && git init /build/ngspice \
 && git -C /build/ngspice fetch --depth 1 "${NGSPICE_REPO}" "${NGSPICE_COMMIT}" \
 && git -C /build/ngspice checkout --detach FETCH_HEAD \
 && test "$(git -C /build/ngspice rev-parse HEAD)" = "${NGSPICE_COMMIT}"
WORKDIR /build/ngspice

RUN if [[ -x ./autogen.sh ]]; then ./autogen.sh; \
    elif [[ -f configure.ac ]]; then autoreconf -fi; fi \
 && ./configure --with-x --enable-xspice --disable-debug --enable-cider \
      --with-readline=yes --enable-openmp --enable-predictor --enable-osdi \
      --prefix="${PREFIX}" \
 && make -j"${JOBS}" \
 && make DESTDIR=/pkgroot install

RUN set -eu; \
    install -Dm0644 COPYING /pkgroot/usr/share/doc/icdesign-ngspice/copyright; \
    version="${NGSPICE_VERSION}-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out; \
    { \
      printf 'Package: icdesign-ngspice\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s\n' "${RUNTIME_DEPS}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: ngspice circuit simulator\n'; \
    } > /pkgroot/DEBIAN/control; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-ngspice_${version}_${arch}.deb"
