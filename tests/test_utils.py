import inspect
from unittest.mock import MagicMock, patch


def _import_utils():
    with patch.dict(
        "sys.modules",
        {
            "aqt": MagicMock(),
            "aqt.qt": MagicMock(),
            "PyQt6": MagicMock(),
            "PyQt6.QtWidgets": MagicMock(),
            "PyQt6.QtGui": MagicMock(),
        },
    ):
        from _infra import show_ask, show_info

        return show_info, show_ask


class TestShowInfo:
    def test_is_callable_function(self):
        show_info, _ = _import_utils()
        assert callable(show_info)

    def test_signature_has_text_param(self):
        show_info, _ = _import_utils()
        sig = inspect.signature(show_info)
        params = list(sig.parameters.keys())
        assert "text" in params

    def test_signature_has_optional_params(self):
        show_info, _ = _import_utils()
        sig = inspect.signature(show_info)
        params = sig.parameters
        assert "parent" in params
        assert "level" in params
        assert "day" in params
        assert params["parent"].default is False
        assert params["level"].default == "msg"
        assert params["day"].default is True


class TestShowAsk:
    def test_is_callable_function(self):
        _, show_ask = _import_utils()
        assert callable(show_ask)

    def test_signature_has_text_param(self):
        _, show_ask = _import_utils()
        sig = inspect.signature(show_ask)
        params = list(sig.parameters.keys())
        assert "text" in params

    def test_signature_has_optional_params(self):
        _, show_ask = _import_utils()
        sig = inspect.signature(show_ask)
        params = sig.parameters
        assert "parent" in params
        assert "title" in params
        assert params["title"].default == "Chinese Reading"

    def test_show_info_level_variants(self):
        with patch.dict(
            "sys.modules",
            {
                "aqt": MagicMock(),
                "aqt.qt": MagicMock(),
                "PyQt6": MagicMock(),
                "PyQt6.QtWidgets": MagicMock(),
                "PyQt6.QtGui": MagicMock(),
            },
        ):
            from _infra import show_info

            src = inspect.getsource(show_info)
            assert '"wrn"' in src
            assert '"not"' in src
            assert '"err"' in src
