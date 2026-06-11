"""Chinese Reading Addon for Anki"""

import sys

# Only do the real import when we're actually loaded as a package by Anki
if __spec__ is not None and __spec__.parent:
    from . import main
