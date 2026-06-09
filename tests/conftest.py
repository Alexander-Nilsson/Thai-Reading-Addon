import importlib
import importlib.util
import os
import sys
from unittest.mock import MagicMock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MOCK_MODULES = {
    "aqt": MagicMock(),
    "aqt.editor": MagicMock(),
    "aqt.utils": MagicMock(),
    "aqt.qt": MagicMock(),
    "aqt.qt.*": MagicMock(),
    "PyQt6": MagicMock(),
    "PyQt6.QtWidgets": MagicMock(),
    "PyQt6.QtGui": MagicMock(),
    "PyQt6.QtCore": MagicMock(),
    "dragonmapper": MagicMock(),
    "dragonmapper.transcriptions": MagicMock(),
}


@pytest.fixture(autouse=False)
def mock_anki_modules():
    original = {}
    for key, val in MOCK_MODULES.items():
        original[key] = sys.modules.get(key)
        sys.modules[key] = val
    yield
    for key, orig in original.items():
        if orig is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = orig


PKG_NAME = "chinese_reading_addon_test"


def _ensure_package():
    if PKG_NAME not in sys.modules:
        pkg = type(sys)(PKG_NAME)
        pkg.__path__ = [ROOT]
        pkg.__package__ = PKG_NAME
        sys.modules[PKG_NAME] = pkg


def _load_submodule(name, filepath):
    full_name = f"{PKG_NAME}.{name}"
    if full_name in sys.modules:
        return sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, filepath)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = PKG_NAME
    sys.modules[full_name] = module
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _install_mocks():
    saved = {}
    for key, val in MOCK_MODULES.items():
        saved[key] = sys.modules.get(key)
        sys.modules[key] = val
    return saved


def _restore_mocks(saved):
    for key in list(saved):
        if saved[key] is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = saved[key]


def _load_base_modules():
    _ensure_package()
    for name in ("addon_config", "utils", "dictdb", "js_registry", "text_utils"):
        filepath = os.path.join(ROOT, f"{name}.py")
        if os.path.exists(filepath):
            _load_submodule(name, filepath)


def import_css_js_handler():
    saved = _install_mocks()
    try:
        _load_base_modules()
        mod = _load_submodule("cssJSHandler", os.path.join(ROOT, "cssJSHandler.py"))
        return mod.CSSJSHandler
    finally:
        _restore_mocks(saved)


def import_chinese_handler():
    saved = _install_mocks()
    try:
        _load_base_modules()
        mod = _load_submodule("chineseHandler", os.path.join(ROOT, "chineseHandler.py"))
        return mod.ChineseHandler
    finally:
        _restore_mocks(saved)


@pytest.fixture
def db():
    from dictdb import DictDB

    d = DictDB(ROOT)
    yield d
    d.closeConnection()
