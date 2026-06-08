__version__ = "0.1.0"

try:
    from . import main, miUpdater
except ImportError:
    pass  # not running as a package (e.g. under pytest)
