__version__ = "0.1.3"

try:
    from . import main  # type: ignore[import]  # ty:ignore[unresolved-import]
except Exception:
    import traceback

    traceback.print_exc()

try:
    from ._infra import updater  # type: ignore[import]  # ty:ignore[unresolved-import]
except Exception:
    pass
