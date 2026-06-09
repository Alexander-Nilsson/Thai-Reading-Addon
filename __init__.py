__version__ = "0.1.2"

try:
    from . import main  # type: ignore[import]  # ty:ignore[unresolved-import]
    from ._infra import updater  # type: ignore[import]  # ty:ignore[unresolved-import]
except ImportError:
    pass  # not running as a package (e.g. under pytest)
