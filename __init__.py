"""Chinese Reading Addon for Anki"""

import tomllib
from pathlib import Path

__version__ = tomllib.loads(Path(__file__).with_name("pyproject.toml").read_text())["project"]["version"]

if __spec__ is not None:
    try:
        from . import main
    except ImportError:
        pass
