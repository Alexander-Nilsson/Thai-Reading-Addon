__version__ = "0.1.0"

try:
    from . import main, updater
except ImportError:
    pass  # not running as a package (e.g. under pytest)
