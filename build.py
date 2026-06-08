#!/usr/bin/env python3
"""
Build script for Chinese Reading Anki addon.

Usage:
    python build.py        # clean, build, and package (default)
    python build.py clean
    python build.py build
    python build.py package
"""

import json
import os
import shutil
import zipfile
from pathlib import Path


def get_version():
    try:
        import tomllib

        with open("pyproject.toml", "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "0.0.0"


def get_version_parts(v: str):
    parts = v.split(".")
    return [int(p) for p in parts]


def bump_version(v: str):
    parts = get_version_parts(v)
    parts[-1] += 1
    return ".".join(str(p) for p in parts)


def get_includes():
    return [
        "__init__.py",
        "main.py",
        "chineseHandler.py",
        "cssJSHandler.py",
        "dictdb.py",
        "settings.py",
        "updater.py",
        "utils.py",
        "Pyperclip.py",
        "js_registry.py",
        "addon_config.py",
        "anki_services.py",
        "manifest.json",
        "config.json",
        "js",
        "db",
        "lib",
        "urllib3",
    ]


def clean():
    build = Path("build")
    if build.exists():
        shutil.rmtree(build)
        print("  ✓ Removed build/")


def build_addon():
    version = get_version()
    print(f"  Version: {version}")

    build_dir = Path("build")
    addon_dir = build_dir / "chinese_reading"
    addon_dir.mkdir(parents=True)

    for item in get_includes():
        src = Path(item)
        if not src.exists():
            print(f"  ⚠  Skipped missing: {item}")
            continue
        dst = addon_dir / src.name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f"  ✓ Copied: {item}")

    # Generate fresh manifest with version
    manifest_path = addon_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"package": "Chinese Reading", "name": "Chinese Reading"}, f, indent=2)
    print("  ✓ Generated manifest.json")

    return addon_dir


def create_package():
    version = get_version()
    addon_dir = Path("build") / "chinese_reading"
    if not addon_dir.exists():
        print("  ❌ Build directory not found; run build first.")
        return None

    package_name = f"chinese_reading_v{version}.ankiaddon"
    package_path = Path("build") / package_name

    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(addon_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            arc_root = Path(root).relative_to(addon_dir)
            for f in files:
                zf.write(Path(root) / f, (arc_root / f).as_posix())

    print(f"  ✓ Package created: {package_path}")
    return package_path


def main():
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"

    if cmd == "clean":
        clean()
    elif cmd == "build":
        build_addon()
    elif cmd == "package":
        build_addon()
        create_package()
    elif cmd == "all":
        clean()
        build_addon()
        create_package()
        print("\n  Done.")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
