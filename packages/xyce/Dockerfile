# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:base
FROM ${BASE_IMAGE}
ARG XYCE_REPO
ARG XYCE_COMMIT
ARG TRILINOS_REPO
ARG TRILINOS_COMMIT
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN test -n "${XYCE_COMMIT}" && git init /build/Xyce \
 && git -C /build/Xyce fetch --depth 1 "${XYCE_REPO}" "${XYCE_COMMIT}" \
 && git -C /build/Xyce checkout --detach FETCH_HEAD \
 && test "$(git -C /build/Xyce rev-parse HEAD)" = "${XYCE_COMMIT}" \
 && test -n "${TRILINOS_COMMIT}" && git init /build/Trilinos \
 && git -C /build/Trilinos fetch --depth 1 "${TRILINOS_REPO}" "${TRILINOS_COMMIT}" \
 && git -C /build/Trilinos checkout --detach FETCH_HEAD \
 && test "$(git -C /build/Trilinos rev-parse HEAD)" = "${TRILINOS_COMMIT}"

# Build a private, static Trilinos: the installed simulator must not depend on
# libraries left behind in the builder image. AMD uses Ubuntu's multiarch paths.
RUN libdir="/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)" \
 && cmake -S /build/Trilinos -B /build/trilinos-build \
      -C /build/Xyce/cmake/trilinos/trilinos-base.cmake \
      -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=/opt/trilinos-for-xyce \
      -D BUILD_SHARED_LIBS=OFF \
      -D AMD_LIBRARY_DIRS="${libdir}" \
      -D AMD_INCLUDE_DIRS=/usr/include/suitesparse \
      -D TPL_AMD_INCLUDE_DIRS=/usr/include/suitesparse \
      -D BLAS_LIBRARY_DIRS="${libdir}" \
      -D LAPACK_LIBRARY_DIRS="${libdir}" \
 && cmake --build /build/trilinos-build -j"${JOBS}" \
 && cmake --install /build/trilinos-build

RUN cmake -S /build/Xyce -B /build/xyce-build \
      -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX="${PREFIX}" \
      -D BUILD_SHARED_LIBS=OFF \
      -D Trilinos_ROOT=/opt/trilinos-for-xyce \
      -D FLEX_INCLUDE_DIR=/usr/include \
      -D CMAKE_DISABLE_FIND_PACKAGE_Git=TRUE \
 && cmake --build /build/xyce-build -j"${JOBS}" \
 && DESTDIR=/pkgroot cmake --install /build/xyce-build

# Keep integration helpers and documentation out of the common share namespace.
RUN set -eu; \
    xyce_share="/pkgroot${PREFIX}/share/xyce"; \
    mkdir -p "${xyce_share}"; \
    for entry in MatlabExamples PythonExamples Simulink SimulinkExamples \
      SetupPythonEnv.m XyceRest.py xyce_interface.py; do \
      if [[ -e "/pkgroot${PREFIX}/share/${entry}" ]]; then \
        mv "/pkgroot${PREFIX}/share/${entry}" "${xyce_share}/"; \
      fi; \
    done; \
    if [[ -d "/pkgroot${PREFIX}/doc" ]]; then \
      mkdir -p "/pkgroot${PREFIX}/share/doc"; \
      mv "/pkgroot${PREFIX}/doc" "/pkgroot${PREFIX}/share/doc/xyce"; \
    fi; \
    if [[ -f "${xyce_share}/SetupPythonEnv.m" ]]; then \
      sed -i "s|${PREFIX}/share|${PREFIX}/share/xyce|g" "${xyce_share}/SetupPythonEnv.m"; \
    fi

WORKDIR /build/Xyce
RUN set -eu; \
    install -Dm0644 COPYING "/pkgroot${PREFIX}/share/doc/icdesign-xyce/copyright"; \
    version="$(sed -n 's/^project(Xyce VERSION \([0-9.]*\).*/\1/p' CMakeLists.txt)+git$(git show -s --format=%cd --date=format:%Y%m%d HEAD).$(git rev-parse --short=8 HEAD)-1"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out debian; \
    printf 'Source: icdesign-xyce\n\nPackage: icdesign-xyce\nArchitecture: any\nDescription: Xyce simulator\n' > debian/control; \
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
      printf 'Package: icdesign-xyce\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: Xyce circuit simulator for the icdesign tool stack\n'; \
    } > /pkgroot/DEBIAN/control; \
    check-install-prefix /pkgroot "${PREFIX}" DEBIAN; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-xyce_${version}_${arch}.deb"
