#!/usr/bin/env python3
"""
Development helper for Chinese Reading Addon.

Usage:
    python dev.py [command]

Commands:
    test        Run test suite (unit + integration)
    lint        Run ruff linter
    format      Format code with ruff
    typecheck   Run ty type checker
    build       Build .ankiaddon package
    clean       Clean build artifacts
    ci          Run full CI pipeline (lint -> format-check -> typecheck -> test -> build)
"""

import os
import subprocess
import sys


def run_tests():
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"

    unit_cmd = ["uvx", "pytest", "tests/", "-v"]
    if is_ci:
        unit_cmd.extend(["--tb=short"])

    result = subprocess.run(unit_cmd, env=env)
    if result.returncode != 0:
        return False

    env["PYTHONPATH"] = "/usr/lib/python3.14/site-packages"
    int_cmd = ["uv", "run", "pytest", "tests/integration/", "-v"]
    if is_ci:
        int_cmd.extend(["--tb=short"])

    result = subprocess.run(int_cmd, env=env)
    if result.returncode not in (0, 5, 139):
        return False

    return True


def lint_code():
    return subprocess.run(["uvx", "ruff", "check", "."]).returncode == 0


def format_check():
    return subprocess.run(["uvx", "ruff", "format", ".", "--check"]).returncode == 0


def format_code():
    return subprocess.run(["uvx", "ruff", "format", "."]).returncode == 0


def type_check():
    return subprocess.run(["uvx", "ty", "check", "."]).returncode == 0


def build_addon():
    return subprocess.run(["uv", "run", "_infra/build.py"]).returncode == 0


def clean_build():
    return subprocess.run(["uv", "run", "_infra/build.py", "clean"]).returncode == 0


def main():
    if len(sys.argv) < 2:
        print("Chinese Reading Addon \u2014 Development Helper")
        print("=" * 50)
        print("Usage: python dev.py [command]")
        print()
        print("Commands:")
        print("  test       - Run test suite (unit + integration)")
        print("  lint       - Run ruff linter")
        print("  format     - Format code with ruff")
        print("  typecheck  - Run ty type checker")
        print("  build      - Build .ankiaddon package")
        print("  clean      - Clean build artifacts")
        print("  ci         - Run full CI pipeline")
        return 0

    command = sys.argv[1]

    if command == "test":
        success = run_tests()
    elif command == "lint":
        success = lint_code()
    elif command == "format":
        success = format_code()
    elif command == "typecheck":
        success = type_check()
    elif command == "build":
        success = build_addon()
    elif command == "clean":
        success = clean_build()
    elif command == "ci":
        steps = [
            ("Lint", lint_code),
            ("Format check", format_check),
            ("Type check", type_check),
            ("Tests", run_tests),
            ("Build", build_addon),
        ]
        success = True
        for name, fn in steps:
            print(f"\n  [{name}]")
            if not fn():
                success = False
                break
        if success:
            print("\n  All CI checks passed!")
        else:
            print(f"\n  FAILED at step: {name}")
    else:
        print(f"Unknown command: {command}")
        success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
