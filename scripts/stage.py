#!/usr/bin/env python3
"""Select release assets for one feed target.

The release artifacts are downloaded by the workflow into ``raw/<source>/``.
This script copies the packages that belong to one ``<arch>-<sdk>`` target
into ``stage/packages/`` and leaves signing/index generation to the SDK
container.

Selection rules are driven by ``feed-sources.json``:

* ``kind: zip``      - the zip name carries ``<arch>-<sdk>``; extract only
                       packages of the target package format.
* ``arch: all``      - architecture-independent packages (LuCI, themes).
* ``arch: filename`` - read the architecture from the package file name.
* ``arch: <name>``   - the source only publishes for that architecture.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path


def ipk_arch(name: str) -> str | None:
    """easytier-noweb_2.7.0_aarch64_cortex-a53.ipk -> aarch64_cortex-a53"""
    parts = name[: -len(".ipk")].split("_")
    if len(parts) < 3:
        return None
    return parts[-1]


def apk_arch(name: str) -> str | None:
    """easytier-noweb-2.7.0_aarch64_cortex-a53.apk -> aarch64_cortex-a53"""
    stem = name[: -len(".apk")]
    if "_" not in stem:
        return None
    candidate = stem.rsplit("_", 1)[1]
    if candidate == "all":
        return candidate
    # OpenWrt arch names contain letters, digits, '_' and '-'.
    if re.fullmatch(r"[a-z0-9][a-z0-9_-]*", candidate):
        return candidate
    return None


def package_arch(name: str, fmt: str) -> str | None:
    return ipk_arch(name) if fmt == "opkg" else apk_arch(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", required=True)
    parser.add_argument("--sdk", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--manifest", default=str(Path(__file__).resolve().parent.parent / "feed-sources.json"))
    parser.add_argument("--out", default="stage")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    fmt = "opkg" if args.sdk.startswith("24.10") else "apk"
    series = "24.10" if fmt == "opkg" else "25.12"
    suffix = ".ipk" if fmt == "opkg" else ".apk"

    out = Path(args.out) / "packages"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    raw_root = Path(args.raw)
    copied: dict[str, Path] = {}

    for source in manifest["sources"]:
        if not source.get("enabled", True):
            continue
        source_dir = raw_root / source["name"]
        if not source_dir.is_dir():
            print(f"[stage] skip {source['name']}: no downloads", file=sys.stderr)
            continue

        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue

            if source.get("kind") == "zip":
                if path.suffix.lower() != ".zip":
                    continue
                # fastfetch-2.70.0-aarch64_cortex-a53-24.10.6.zip
                if args.arch not in path.name:
                    continue
                if f"-{series}." not in path.name:
                    continue
                with zipfile.ZipFile(path) as archive:
                    for member in archive.namelist():
                        name = Path(member).name
                        if not name.endswith(suffix):
                            continue
                        (out / name).write_bytes(archive.read(member))
                        copied[name] = path
                continue

            if path.suffix.lower() != suffix:
                continue

            arch_rule = source.get("arch", "filename")
            if arch_rule == "all":
                take = True
            elif arch_rule == "filename":
                detected = package_arch(path.name, fmt)
                take = detected in (args.arch, "all")
            else:
                take = arch_rule == args.arch

            if take:
                target = out / path.name
                if target.exists():
                    print(f"[stage] duplicate {path.name}, keeping first", file=sys.stderr)
                    continue
                shutil.copy2(path, target)
                copied[path.name] = path

    print(f"[stage] {args.arch}-{args.sdk} ({fmt}): {len(copied)} packages")
    for name in sorted(copied):
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
