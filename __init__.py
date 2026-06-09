__version__ = "0.1.1"

try:
    from . import main
    from ._infra import updater
except ImportError:
    pass  # not running as a package (e.g. under pytest)
