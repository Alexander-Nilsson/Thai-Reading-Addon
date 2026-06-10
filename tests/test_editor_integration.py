# ruff: noqa: E402
"""End-to-end integration tests for the editor reading generation flow.

These tests use a real headless Anki session (pytest-anki2) to mirror
actual user behavior: configuring the addon, opening a card in the editor,
and generating readings via the F9/button action.

The key bug being tested: the JavaScript fetchCText() function producing
  "Chinese Reading: Could not find the current field. Please click inside
   a field and try again."

Tests are forked by default (each test gets a fresh subprocess).
"""

import os

import pytest

pytest_anki = pytest.importorskip("pytest_anki", reason="pytest-anki2 not installed")
from pytest_anki import AnkiSession

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Config matching what a real user would set via Anki addon config ──

DEFAULT_CONFIG = {
    "MandarinTones12345": ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"],
    "CantoneseTones123456": ["#E60000", "#E68A00", "#00802B", "#005CE6", "#AC00E6", "gray"],
    "FontSize": 75,
    "ReadingType": "pinyin",
    "AutoCssJsGeneration": True,
    "ActiveFields": [],
    "Profiles": ["all"],
    "hanziConversion": "None",
    "readingConversion": "None",
    "SimplifiedField": "Simplified;overwrite",
    "TraditionalField": "Traditional;overwrite",
    "SimpTradField": "Traditional,Variant;overwrite",
    "traditionalIcons": False,
    "BopomofoTonesToNumber": True,
}

_ANKI_SESSION_PARAMS = dict(
    load_profile=False,
    unpacked_addons=[("chinese_reading", ROOT)],
    addon_configs=[("chinese_reading", DEFAULT_CONFIG)],
)

ADDON_NAME = "chinese_reading"

NOTETYPE_NAME = "Chinese Test"


def _create_notetype(col):
    notetype = col.models.new(NOTETYPE_NAME)
    col.models.add_field(notetype, col.models.new_field("Text"))
    col.models.add_field(notetype, col.models.new_field("Reading"))
    col.models.add_field(notetype, col.models.new_field("Simplified"))
    col.models.add_field(notetype, col.models.new_field("Traditional"))
    col.models.add_field(notetype, col.models.new_field("Variant"))
    template = col.models.new_template("Card 1")
    template["qfmt"] = "{{Text}}"
    template["afmt"] = "{{FrontSide}}<hr id=answer>{{Text}}"
    col.models.add_template(notetype, template)
    col.models.save(notetype)
    return notetype


def _find_addcards(max_wait=20):
    from PyQt6.QtWidgets import QApplication

    for _ in range(max_wait):
        QApplication.processEvents()
        result = next(
            (w for w in QApplication.topLevelWidgets() if type(w).__name__ == "AddCards"),
            None,
        )
        if result is not None:
            return result
    return None


# ── Tests ──────────────────────────────────────────────────────────


class TestEditorIntegration:
    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_finalize_readings_generates_pinyin(self, anki_session: AnkiSession) -> None:
        """finalizeReadings produces pinyin for Chinese text (no editor)."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            notetype = _create_notetype(col)
            note = col.new_note(notetype)
            note["Text"] = "你好世界"
            col.add_note(note, col.decks.current()["id"])
            col.save()

            result = mw.ChineseReading.finalizeReadings("你好世界", "Text", note)
            assert result is not None
            assert "ni3" in result

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_variants_populates_fields(self, anki_session: AnkiSession) -> None:
        """addVariants fills Simplified/Traditional fields with no editor."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            notetype = _create_notetype(col)
            note = col.new_note(notetype)
            note["Text"] = "你好世界"
            col.add_note(note, col.decks.current()["id"])
            col.save()

            handler = mw.ChineseReading
            handler.addVariants("你好世界", note)
            assert note["Simplified"], "Simplified should be populated"
            assert note["Traditional"], "Traditional should be populated"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_simp_trad_populates_when_simp_differs_from_trad(self, anki_session: AnkiSession) -> None:
        """addSimpTrad fills Variant when simplified != traditional."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            notetype = _create_notetype(col)
            note = col.new_note(notetype)
            note["Text"] = "你好世界"
            col.add_note(note, col.decks.current()["id"])
            col.save()

            handler = mw.ChineseReading
            handler.addVariants("汉语", note)
            handler.addSimpTrad("汉语", note)
            assert note["Variant"], "Variant should be populated when simp≠trad"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_bridge_reroute_handles_text_to_c_reading(self, anki_session: AnkiSession) -> None:
        """Simulate the JS bridge command: bridgeReroute -> finalizeReadings."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            notetype = _create_notetype(col)
            note = col.new_note(notetype)
            note["Text"] = "你好世界"
            col.add_note(note, col.decks.current()["id"])
            col.save()

            mw.onAddCard()
            anki_session.app.processEvents()
            add_cards = _find_addcards()
            assert add_cards is not None
            editor = add_cards.editor
            editor.set_note(note, focusTo=0)
            anki_session.app.processEvents()

            cmd = f"textToCReading:||:||:你好世界:||:||:0:||:||:{note.id}"

            from chinese_reading import main as addon_main

            addon_main.bridgeReroute(editor, cmd)

            reloaded = col.get_note(note.id)
            assert reloaded["Text"] == "你好世界"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_c_readings_js_generation(self, anki_session: AnkiSession) -> None:
        """addCReadings generates correct JS for both text-selected and
        no-text-selected paths. Uses a MagicMock editor so no QWebEngineView
        is needed."""
        from unittest.mock import MagicMock

        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw

            mock_editor = MagicMock()
            mock_editor.web.selectedText.return_value = ""
            captured_js: list[str] = []
            mock_editor.web.eval = lambda js: captured_js.append(js)

            notetype = mw.col.models.new(NOTETYPE_NAME)
            mw.col.models.add_field(notetype, mw.col.models.new_field("Text"))
            tmpl = mw.col.models.new_template("Card 1")
            tmpl["qfmt"] = "{{Text}}"
            tmpl["afmt"] = "{{FrontSide}}"
            mw.col.models.add_template(notetype, tmpl)
            mw.col.models.save(notetype)
            note = mw.col.new_note(notetype)
            note["Text"] = "你好世界"
            mw.col.add_note(note, mw.col.decks.current()["id"])
            note.id = 1611361324806

            mock_editor.note = note
            mw._lastFocusedFieldOrdinal = 0
            mw.ChineseReading.addCReadings(mock_editor)

            assert len(captured_js) >= 1
            last_js = captured_js[-1]
            assert "window.currentField" in last_js
            assert "getElementById('f0')" in last_js
            assert str(note.id) in last_js
            assert "fetchCText" in last_js

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_c_readings_with_text_selected(self, anki_session: AnkiSession) -> None:
        """When text IS selected, addCReadings skips currentField set."""
        from unittest.mock import MagicMock

        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw

            mock_editor = MagicMock()
            mock_editor.web.selectedText.return_value = "你好世界"
            captured_js: list[str] = []
            mock_editor.web.eval = lambda js: captured_js.append(js)

            mw.ChineseReading.addCReadings(mock_editor)

            assert len(captured_js) >= 1
            last_js = captured_js[-1]
            assert "window.currentField" not in last_js
            assert "fetchCText" in last_js

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_c_readings_no_focused_field(self, anki_session: AnkiSession) -> None:
        """When no field is focused, addCReadings logs warning and calls fetchCText."""
        from unittest.mock import MagicMock

        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw

            mock_editor = MagicMock()
            mock_editor.web.selectedText.return_value = ""
            captured_js: list[str] = []
            mock_editor.web.eval = lambda js: captured_js.append(js)

            mw._lastFocusedFieldOrdinal = None
            mw.ChineseReading.addCReadings(mock_editor)

            assert len(captured_js) >= 1
            last_js = captured_js[-1]
            assert "No focused field tracked" in last_js
            assert "fetchCText" in last_js


class TestConfigAndCatalog:
    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_real_catalog_discovers_default_notetypes(self, anki_session: AnkiSession) -> None:
        """The live catalog discovers actual note types from the collection."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            catalog = mw.ChineseReadingCatalog
            names = catalog.model_names("User 1")
            assert "Basic" in names, f"Catalog should list 'Basic'. Found: {names}"
            assert "Cloze" in names, f"Catalog should list 'Cloze'. Found: {names}"

            _create_notetype(col)
            from config.mutation import LiveModelCatalog

            rebuilt = LiveModelCatalog(mw)
            assert NOTETYPE_NAME in rebuilt.model_names("User 1"), (
                f"Rebuilt catalog should list {NOTETYPE_NAME}. Found: {rebuilt.model_names('User 1')}"
            )

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_mutation_validates_active_fields_real_catalog(self, anki_session: AnkiSession) -> None:
        """ConfigMutation validates ActiveFields against the real collection."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            _create_notetype(col)

            from config.mutation import ConfigDelta

            mutation = mw.ChineseReadingMutation
            valid = f"reading;all;{NOTETYPE_NAME};Card 1;Text;*;default"
            errors = mutation.validate(ConfigDelta(active_fields=(valid,)))
            assert not errors, f"Expected no errors, got: {errors}"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_addon_initializes_with_profile_load(self, anki_session: AnkiSession) -> None:
        """After profile load, all expected mw objects are set."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            expected = [
                "ChineseReading",
                "ChineseReadingConfig",
                "updateChineseReadingConfig",
                "chineseReadingSettings",
                "ChineseReadingCatalog",
                "ChineseReadingMutation",
            ]
            missing = [a for a in expected if not hasattr(mw, a)]
            assert not missing, f"Missing mw attributes: {missing}"
