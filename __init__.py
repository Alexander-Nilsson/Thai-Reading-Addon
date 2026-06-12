"""Chinese Reading Addon for Anki"""

import sys
import tomllib
from pathlib import Path

__version__ = tomllib.loads(Path(__file__).with_name("pyproject.toml").read_text())["project"]["version"]

# Only do the real import when we're actually loaded as a package by Anki
if __spec__ is not None and __spec__.parent:
    from . import main
