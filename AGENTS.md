# Repository conventions for agents

- Each `packages/<name>/dependencies.json` is the single manifest for that package. Keep its top-level keys in this order: `sources`, `build`, `runtime`.
- Dependency manifests, `shared/build-dependencies.json`, and `build-control.json` are JSON read by Python's standard-library `json` parser. Keep them valid JSON; `.github/workflows/pages.yml` is actual YAML.
- Put every `build` and `runtime` dependency on its own line. Do the same for `common` in `shared/build-dependencies.json`.
- Place package-specific build dependencies in the package manifest; `shared/build-dependencies.json` contains only dependencies common to every package. The build script computes the deduplicated union for selected packages. Inspect it with `python3 scripts/build.py --all --list-build-deps`.
- When changing pinned sources, keep VACASK's OpenVAF pin equal to the OpenVAF package pin, and update any corresponding package versions/minimum runtime dependency. Keep the Boost SHA-256 in the VACASK manifest in sync with its archive version.
- Run `make test` after changing manifests or build tooling. Full Docker package builds may require substantial time and network access.
- When adding one or more new packages, use `build-control.json` to build only those packages for faster verification.
