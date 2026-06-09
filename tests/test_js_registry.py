import os
import tempfile

from template.js_registry import JsRegistry


def test_load_returns_file_content():
    with tempfile.TemporaryDirectory() as td:
        js_file = os.path.join(td, "test.js")
        with open(js_file, "w") as f:
            f.write("console.log('hello');")

        reg = JsRegistry(td)
        content = reg.load("test.js")
        assert content == "console.log('hello');"


def test_load_caches_content():
    with tempfile.TemporaryDirectory() as td:
        js_file = os.path.join(td, "test.js")
        with open(js_file, "w") as f:
            f.write("original")

        reg = JsRegistry(td)
        first = reg.load("test.js")

        # mutate the file on disk
        with open(js_file, "w") as f:
            f.write("changed")

        # second load returns cached (original) content
        second = reg.load("test.js")
        assert first == second == "original"


def test_load_two_files():
    with tempfile.TemporaryDirectory() as td:
        for name, content in [("a.js", "aaa"), ("b.js", "bbb")]:
            with open(os.path.join(td, name), "w") as f:
                f.write(content)

        reg = JsRegistry(td)
        assert reg.load("a.js") == "aaa"
        assert reg.load("b.js") == "bbb"
        assert reg.load("a.js") == "aaa"


def test_load_missing_file_raises():
    with tempfile.TemporaryDirectory() as td:
        reg = JsRegistry(td)
        try:
            reg.load("nonexistent.js")
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass


def test_load_utf8():
    with tempfile.TemporaryDirectory() as td:
        js_file = os.path.join(td, "utf.js")
        with open(js_file, "w", encoding="utf-8") as f:
            f.write("// 中文注释\nvar x = 1;")

        reg = JsRegistry(td)
        content = reg.load("utf.js")
        assert "中文" in content
