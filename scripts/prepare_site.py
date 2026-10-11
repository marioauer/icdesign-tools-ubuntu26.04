#!/usr/bin/env python3
"""Publish new builds while retaining disabled packages from the previous Pages site."""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("ngspice", "openvaf", "vacask", "xschem", "klayout",
            "verilator", "iverilog", "magic", "netgen", "xyce", "xschem-gaw")


def valid(name, package):
    return isinstance(name, str) and bool(re.fullmatch(rf"icdesign-{package}_[A-Za-z0-9.+:~_-]+_[A-Za-z0-9_-]+\.deb", name)) and "/" not in name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-url", help="existing GitHub Pages site URL; omit on first publish")
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--site", type=Path, default=ROOT / "site")
    args = parser.parse_args()
    if args.site.exists():
        shutil.rmtree(args.site)
    args.site.mkdir(parents=True)
    previous = {}
    if args.previous_url:
        base = args.previous_url.rstrip("/") + "/"
        try:
            with urllib.request.urlopen(base + "manifest.json", timeout=30) as r:
                previous = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        if not isinstance(previous, dict):
            raise ValueError("invalid prior manifest")
    manifest = {}
    for p in PACKAGES:
        files = list(args.dist.glob(f"icdesign-{p}_*.deb"))
        if len(files) > 1:
            raise ValueError(f"multiple builds for {p} in dist")
        if files:
            name = files[0].name
            if not valid(name, p):
                raise ValueError(f"invalid filename: {name}")
            shutil.copy2(files[0], args.site / name)
        elif p in previous:
            name = previous[p]
            if not valid(name, p):
                raise ValueError(f"invalid previous filename for {p}")
            with urllib.request.urlopen(base + name, timeout=120) as r, (args.site / name).open("wb") as f:
                shutil.copyfileobj(r, f)
        else:
            continue
        manifest[p] = name
    if not manifest:
        raise ValueError("no packages available to publish")
    (args.site / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    links = "\n".join(f'<li><a href="{html.escape(name)}">{html.escape(p)}</a></li>' for p, name in manifest.items())
    (args.site / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>IC design tools — Ubuntu 26.04</title>'
        '<h1>IC design tools — Ubuntu 26.04</h1><ul>\n' + links + '\n</ul></html>\n'
    )
    print("Publishing:", ", ".join(manifest))


if __name__ == "__main__":
    main()
