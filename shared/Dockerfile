# syntax=docker/dockerfile:1
FROM ubuntu:26.04 AS base
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILD_DEPS
RUN test -n "$BUILD_DEPS" && apt-get update && apt-get install -y --no-install-recommends $BUILD_DEPS \
 && rm -rf /var/lib/apt/lists/*

# Only OpenVAF and VACASK need the Rust toolchain.
FROM base AS rust
RUN curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs \
      | sh -s -- -y --profile minimal
