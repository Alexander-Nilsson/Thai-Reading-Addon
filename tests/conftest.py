import importlib
import importlib.util
import os
import sqlite3
import sys
import tempfile
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


PKG_NAME = "thai_reading_addon_test"

SUBPACKAGES = {
    "config": "config",
    "reading": "reading",
    "template": "template",
}


def _ensure_packages():
    if PKG_NAME not in sys.modules:
        pkg = type(sys)(PKG_NAME)
        pkg.__path__ = [ROOT]
        pkg.__package__ = PKG_NAME
        sys.modules[PKG_NAME] = pkg

    for short, subdir in SUBPACKAGES.items():
        full = f"{PKG_NAME}.{short}"
        if full not in sys.modules:
            subpkg = type(sys)(full)
            subpkg.__path__ = [os.path.join(ROOT, subdir)]
            subpkg.__package__ = full
            sys.modules[full] = subpkg

        if short not in sys.modules:
            sys.modules[short] = sys.modules[full]


def _load_submodule(name, filepath, subpackage=None):
    full_name = f"{PKG_NAME}.{name}"
    if full_name in sys.modules:
        return sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, filepath)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = f"{PKG_NAME}.{subpackage}" if subpackage else PKG_NAME
    sys.modules[full_name] = module
    if name not in sys.modules:
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
    _ensure_packages()
    modules = [
        ("config.config", "config/config.py", "config"),
        ("_infra", "_infra/__init__.py", "_infra"),
        ("reading.dictdb", "reading/dictdb.py", "reading"),
    ]
    for name, relpath, subpkg in modules:
        filepath = os.path.join(ROOT, relpath)
        if os.path.exists(filepath):
            _load_submodule(name, filepath, subpkg)


def import_css_js_handler():
    saved = _install_mocks()
    try:
        _load_base_modules()
        _load_submodule("config.config", os.path.join(ROOT, "config/config.py"), "config")
        _load_submodule("template.injector", os.path.join(ROOT, "template/injector.py"), "template")
        mod = _load_submodule("template.handler", os.path.join(ROOT, "template/handler.py"), "template")
        return mod.ThaiCssJsHandler
    finally:
        _restore_mocks(saved)


def import_thai_handler():
    saved = _install_mocks()
    try:
        _load_base_modules()
        _load_submodule("config.config", os.path.join(ROOT, "config/config.py"), "config")
        _load_submodule("reading.generator", os.path.join(ROOT, "reading/generator.py"), "reading")
        mod = _load_submodule("reading.handler", os.path.join(ROOT, "reading/handler.py"), "reading")
        return mod.ThaiHandler
    finally:
        _restore_mocks(saved)


@pytest.fixture
def db():
    _ensure_packages()
    _load_submodule("reading.dictdb", os.path.join(ROOT, "reading/dictdb.py"), "reading")
    from reading.dictdb import DictDB

    d = DictDB(ROOT)
    yield d
    d.close_connection()


def _create_test_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("CREATE TABLE words (word TEXT PRIMARY KEY, reading TEXT, tone_pattern TEXT, reading_ipa TEXT)")
    c.execute("CREATE INDEX iword ON words (word)")
    conn.commit()
    conn.close()


def _populate_test_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.executemany(
        "INSERT INTO words (word, reading, tone_pattern, reading_ipa) VALUES (?, ?, ?, ?)",
        [
            ("สวัสดี", "sa-wat-dii", "2-2-1", "sa.wat.dii"),
            ("ภาษาไทย", "pha-sa-thai", "1-1-1", "pha.sa.thai"),
            ("เรียนภาษาไทย", "rian-pha-sa-thai", "1-1-1-1", "rian.pha.sa.thai"),
        ],
    )
    conn.commit()
    conn.close()


@pytest.fixture
def test_db_path():
    with tempfile.TemporaryDirectory() as td:
        db_dir = os.path.join(td, "db")
        os.makedirs(db_dir)
        db_file = os.path.join(db_dir, "thai_dict.sqlite")
        _create_test_db(db_file)
        _populate_test_db(db_file)
        yield td


@pytest.fixture
def test_db(test_db_path):
    from reading.dictdb import DictDB

    d = DictDB(test_db_path)
    yield d
    d.close_connection()
