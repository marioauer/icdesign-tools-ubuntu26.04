# syntax=docker/dockerfile:1
ARG BASE_IMAGE=icdesign-build-ubuntu26.04:rust
FROM ${BASE_IMAGE}
ARG VACASK_REPO
ARG VACASK_COMMIT
ARG VACASK_VERSION=0.3.4
ARG OPENVAF_REPO
ARG OPENVAF_COMMIT
ARG BOOST_VERSION
ARG BOOST_SHA256
ARG PREFIX=/opt/icdesign/tools
ARG JOBS=2
ARG MAINTAINER="icdesign build <noreply@example.invalid>"
ARG RUNTIME_DEPS

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# OpenVAF-Reloaded (OSDI 0.4) compiles VACASK's built-in Verilog-A models.
ENV PATH="/root/.cargo/bin:/usr/lib/llvm-18/bin:${PATH}" \
    LLVM_SYS_181_PREFIX=/usr/lib/llvm-18
RUN test -n "${OPENVAF_COMMIT}" && git init /build/openvaf \
 && git -C /build/openvaf fetch --depth 1 "${OPENVAF_REPO}" "${OPENVAF_COMMIT}" \
 && git -C /build/openvaf checkout --detach FETCH_HEAD \
 && test "$(git -C /build/openvaf rev-parse HEAD)" = "${OPENVAF_COMMIT}"
WORKDIR /build/openvaf
RUN CARGO_BUILD_JOBS="${JOBS}" cargo build --locked --release -p openvaf-driver --features llvm18

# Keep the verified Boost 1.88 source pin for VACASK's Process library.
RUN set -eu; \
    boost_dir="boost_${BOOST_VERSION//./_}"; \
    curl -fL "https://archives.boost.io/release/${BOOST_VERSION}/source/${boost_dir}.tar.gz" -o /tmp/boost.tar.gz; \
    echo "${BOOST_SHA256}  /tmp/boost.tar.gz" | sha256sum -c -; \
    mkdir -p /build; tar -xf /tmp/boost.tar.gz -C /build; rm /tmp/boost.tar.gz; \
    cd "/build/${boost_dir}"; \
    ./bootstrap.sh; \
    ./b2 -j"${JOBS}" --with-filesystem --with-process --with-asio \
      link=static variant=release stage

RUN test -n "${VACASK_COMMIT}" && git init /build/vacask \
 && git -C /build/vacask fetch --depth 1 "${VACASK_REPO}" "${VACASK_COMMIT}" \
 && git -C /build/vacask checkout --detach FETCH_HEAD \
 && test "$(git -C /build/vacask rev-parse HEAD)" = "${VACASK_COMMIT}"
WORKDIR /build/vacask
RUN cmake -S . -B /build/vacask-build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="${PREFIX}" \
      -DOPENVAF_DIR=/build/openvaf/target/release \
      -DBoost_ROOT="/build/boost_${BOOST_VERSION//./_}/stage" \
      -DSuiteSparse_DIR=/usr \
      -DFLEX_INCLUDE_DIR=/usr/include \
      -DCADNIP_PARSERS=OFF \
 && cmake --build /build/vacask-build --parallel "${JOBS}" \
 && DESTDIR=/pkgroot cmake --install /build/vacask-build

# Upstream installs openvaf-r alongside vacask; the separate icdesign-openvaf
# package owns that path, so do not ship a duplicate. Keep the compiled models.
RUN set -eu; \
    rm -f "/pkgroot${PREFIX}/bin/openvaf-r"; \
    install -Dm0644 LICENSE "/pkgroot${PREFIX}/share/doc/icdesign-vacask/copyright"; \
    version="${VACASK_VERSION}-2"; \
    dpkg --validate-version "${version}"; \
    arch="$(dpkg --print-architecture)"; \
    mkdir -p /pkgroot/DEBIAN /out; \
    { \
      printf 'Package: icdesign-vacask\n'; \
      printf 'Version: %s\n' "${version}"; \
      printf 'Section: electronics\nPriority: optional\n'; \
      printf 'Architecture: %s\n' "${arch}"; \
      printf 'Maintainer: %s\n' "${MAINTAINER}"; \
      printf 'Description: VACASK Verilog-A circuit simulator\n'; \
    } > /pkgroot/DEBIAN/control; \
    mapfile -d '' binaries < <(find "/pkgroot${PREFIX}/bin" "/pkgroot${PREFIX}/lib/vacask/mod" \
      -type f \( -name vacask -o -name '*.osdi' \) -print0); \
    deps_args=(); for binary in "${binaries[@]}"; do deps_args+=("-e${binary}"); done; \
    ((${#deps_args[@]} >= 1)); \
    mkdir -p debian; printf 'Source: icdesign-vacask\n\n' > debian/control; \
    printf 'Package: icdesign-vacask\nArchitecture: any\nDescription: VACASK simulator\n' >> debian/control; \
    deps="$(dpkg-shlibdeps -O "${deps_args[@]}" | sed -n 's/^shlibs:Depends=//p')"; \
    test -n "${deps}"; \
    printf 'Depends: %s, %s\n' "${RUNTIME_DEPS}" "${deps}" >> /pkgroot/DEBIAN/control; \
    check-install-prefix /pkgroot "${PREFIX}" DEBIAN; \
    dpkg-deb --root-owner-group --build /pkgroot "/out/icdesign-vacask_${version}_${arch}.deb"
