import importlib
import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _mock_anki_deps():
    mocks = {
        "anki": MagicMock(),
        "anki.collection": MagicMock(),
        "anki.models": MagicMock(),
        "anki.notes": MagicMock(),
        "aqt": MagicMock(),
        "PyQt6": MagicMock(),
        "PyQt6.QtGui": MagicMock(),
        "PyQt6.QtWidgets": MagicMock(),
    }
    with pytest.MonkeyPatch.context() as m:
        m.setattr(sys, "modules", {**sys.modules, **mocks})
        yield


def _import_anki_services():
    from _infra import anki_services

    importlib.reload(anki_services)
    return anki_services.AnkiServices, anki_services.LiveAnkiServices


class TestAnkiServicesIsProtocol:
    def test_subclass_check(self):
        AnkiServices, _ = _import_anki_services()
        from typing import Protocol

        assert issubclass(AnkiServices, Protocol)

    def test_col_attribute_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "col" in dir(AnkiServices)

    def test_profile_name_attribute_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "profile_name" in dir(AnkiServices)

    def test_addon_folder_attribute_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "addon_folder" in dir(AnkiServices)

    def test_all_models_method_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "all_models" in dir(AnkiServices)

    def test_model_by_name_method_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "model_by_name" in dir(AnkiServices)

    def test_field_names_method_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "field_names" in dir(AnkiServices)

    def test_save_model_method_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "save_model" in dir(AnkiServices)

    def test_get_note_method_exists(self):
        AnkiServices, _ = _import_anki_services()
        assert "get_note" in dir(AnkiServices)

    def test_all_protocol_members(self):
        AnkiServices, _ = _import_anki_services()
        expected = [
            "col",
            "profile_name",
            "addon_folder",
            "all_models",
            "model_by_name",
            "field_names",
            "save_model",
            "get_note",
            "checkpoint",
            "reset",
            "process_events",
            "progress_finish",
            "progress_timer",
        ]
        for member in expected:
            assert member in dir(AnkiServices), f"Missing member: {member}"


class TestMockAnkiServices:
    def test_mock_implements_protocol(self):
        class MockAnkiServices:
            @property
            def col(self):
                return None

            @property
            def profile_name(self):
                return "User 1"

            @property
            def addon_folder(self):
                return "/tmp/addons21/chinese_reading"

            def all_models(self):
                return []

            def model_by_name(self, name):
                return None

            def field_names(self, model):
                return []

            def save_model(self, model):
                pass

            def get_note(self, nid):
                return None

            def checkpoint(self, name):
                pass

            def reset(self):
                pass

            def process_events(self):
                pass

            def progress_finish(self):
                pass

            def progress_timer(self, ms, callback, repeat):
                pass

        mock = MockAnkiServices()
        assert mock.profile_name == "User 1"
        assert mock.all_models() == []
        assert mock.model_by_name("test") is None
        assert mock.field_names({}) == []

    def test_mock_with_models(self):
        class MockAnkiServices:
            def __init__(self):
                self._models = [
                    {
                        "name": "Basic",
                        "flds": [{"name": "Front"}, {"name": "Back"}],
                        "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{BackSide}}"}],
                        "css": "",
                    }
                ]

            @property
            def col(self):
                return None

            @property
            def profile_name(self):
                return "User 1"

            @property
            def addon_folder(self):
                return "/tmp/addons21/chinese_reading"

            def all_models(self):
                return self._models

            def model_by_name(self, name):
                for m in self._models:
                    if m["name"] == name:
                        return m
                return None

            def field_names(self, model):
                return [f["name"] for f in model["flds"]]

            def save_model(self, model):
                pass

            def get_note(self, nid):
                return None

            def checkpoint(self, name):
                pass

            def reset(self):
                pass

            def process_events(self):
                pass

            def progress_finish(self):
                pass

            def progress_timer(self, ms, callback, repeat):
                pass

        mock = MockAnkiServices()
        models = mock.all_models()
        assert len(models) == 1
        assert models[0]["name"] == "Basic"
        assert mock.model_by_name("Basic") is not None
        assert mock.model_by_name("Missing") is None
        assert mock.field_names(models[0]) == ["Front", "Back"]


class TestLiveAnkiServicesAttributes:
    def test_has_all_protocol_methods(self):
        _, LiveAnkiServices = _import_anki_services()
        proto_methods = [
            "col",
            "profile_name",
            "addon_folder",
            "all_models",
            "model_by_name",
            "field_names",
            "save_model",
            "get_note",
            "checkpoint",
            "reset",
            "process_events",
            "progress_finish",
            "progress_timer",
        ]
        for attr in proto_methods:
            assert hasattr(LiveAnkiServices, attr), f"LiveAnkiServices missing: {attr}"
