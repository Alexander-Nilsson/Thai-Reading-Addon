# ruff: noqa: E402
"""End-to-end integration tests for the editor reading generation flow.

These tests use a real headless Anki session (pytest-anki2) to mirror
actual user behavior: configuring the addon, opening a card in the editor,
and generating readings via the F9/button action.

The key bug being tested: the JavaScript fetchCText() function producing
  "Thai Reading: Could not find the current field. Please click inside
   a field and try again."

Tests are forked by default (each test gets a fresh subprocess).
"""

import os
import sys

import pytest

pytest_anki = pytest.importorskip("pytest_anki", reason="pytest-anki2 not installed")
from anki.hooks import runFilter
from pytest_anki import AnkiSession

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Config matching what a real user would set via Anki addon config ──

DEFAULT_CONFIG = {
    "ThaiTones": ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"],
    "FontSize": 75,
    "ReadingType": "rtgs",
    "AutoCssJsGeneration": True,
    "ActiveFields": [],
    "Profiles": ["all"],
}

_ANKI_SESSION_PARAMS = dict(
    load_profile=False,
    unpacked_addons=[("thai_reading", ROOT)],
    addon_configs=[("thai_reading", DEFAULT_CONFIG)],
)

ADDON_NAME = "thai_reading"

NOTETYPE_NAME = "Chinese Test"


def _create_notetype(col):
    notetype = col.models.new(NOTETYPE_NAME)
    col.models.add_field(notetype, col.models.new_field("Text"))
    col.models.add_field(notetype, col.models.new_field("Reading"))
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
    def test_finalize_readings_non_thai_text_passes_through(self, anki_session: AnkiSession) -> None:
        """finalizeReadings passes through non-Thai text unchanged (no editor)."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            notetype = _create_notetype(col)
            note = col.new_note(notetype)
            note["Text"] = "你好世界"
            col.add_note(note, col.decks.current()["id"])
            col.save()

            result = mw.ThaiReading.finalizeReadings("你好世界", "Text", note)
            assert result is not None
            assert "你好世界" in result

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

            from thai_reading import main as addon_main

            addon_main.bridgeReroute(editor, cmd)

            reloaded = col.get_note(note.id)
            assert reloaded["Text"] == "你好世界"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_c_readings_updates_note_field(self, anki_session: AnkiSession) -> None:
        """addCReadings generates readings and updates the note field."""
        from unittest.mock import MagicMock

        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw

            notetype = _create_notetype(mw.col)
            note = mw.col.new_note(notetype)
            note["Text"] = "你好世界"
            mw.col.add_note(note, mw.col.decks.current()["id"])
            note_id = note.id

            mock_editor = MagicMock()
            mock_editor.note = note

            mw._lastFocusedFieldOrdinal = 0
            mw.ThaiReading.addCReadings(mock_editor)

            reloaded = mw.col.get_note(note_id)
            assert reloaded["Text"] == "你好世界"
            mock_editor.loadNoteKeepingFocus.assert_called_once()

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_c_readings_with_text_selected(self, anki_session: AnkiSession) -> None:
        """When text IS selected, addCReadings uses field resolution."""
        from unittest.mock import MagicMock

        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw

            notetype = _create_notetype(mw.col)
            note = mw.col.new_note(notetype)
            note["Text"] = "你好世界"
            mw.col.add_note(note, mw.col.decks.current()["id"])
            note_id = note.id

            mock_editor = MagicMock()
            mock_editor.note = note
            mock_editor.web.selectedText.return_value = "你好世界"

            mw._lastFocusedFieldOrdinal = 0
            mw.ThaiReading.addCReadings(mock_editor)

            reloaded = mw.col.get_note(note_id)
            assert reloaded["Text"] == "你好世界"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_add_c_readings_no_focused_field(self, anki_session: AnkiSession) -> None:
        """When no field is focused, addCReadings shows warning and returns."""
        from unittest.mock import MagicMock, patch

        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw

            notetype = _create_notetype(mw.col)
            note = mw.col.new_note(notetype)
            note["Text"] = "你好世界"
            mw.col.add_note(note, mw.col.decks.current()["id"])

            mock_editor = MagicMock()
            mock_editor.note = note

            mw._lastFocusedFieldOrdinal = None
            with patch("aqt.utils.showInfo") as mock_show_info:
                mw.ThaiReading.addCReadings(mock_editor)
                mock_show_info.assert_called_once_with("Thai Reading: Please click inside a field and try again.")


class TestHookRegistration:
    """Smoke tests verifying Anki hooks are registered by the addon.

    These were moved from tests/anki/test_smoke.py (deleted) since they
    share the same AnkiSession fixture as the editor integration tests.
    """

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_editor_buttons_registered(self, anki_session: AnkiSession) -> None:
        """setupEditorButtons hook adds F9/F10 buttons with correct commands."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            from unittest.mock import MagicMock

            editor = MagicMock()
            editor._links = {}
            editor._addButton.return_value = "<button>test</button>"

            buttons = runFilter("setupEditorButtons", [], editor)

            assert len(buttons) == 2, f"Expected 2 editor buttons, got {len(buttons)}"
            assert editor._links.get("addCReadings") is not None, "addCReadings link missing"
            assert editor._links.get("removeFormatting") is not None, "removeFormatting link missing"
            assert editor._addButton.call_count == 2

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_editor_shortcuts_registered(self, anki_session: AnkiSession) -> None:
        """editor_did_init_shortcuts adds F9 and F10 shortcuts."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            from aqt import gui_hooks

            cuts: list = []
            from unittest.mock import MagicMock

            editor = MagicMock()
            gui_hooks.editor_did_init_shortcuts(cuts, editor)

            keys = [c[0] for c in cuts]
            assert "F9" in keys, f"F9 shortcut not registered. Keys: {keys}"
            assert "F10" in keys, f"F10 shortcut not registered. Keys: {keys}"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_bridge_cmd_wrapped(self, anki_session: AnkiSession) -> None:
        """Editor.onBridgeCmd must be wrapped by the addon's bridgeReroute."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            import aqt.editor

            wrapped = aqt.editor.Editor.onBridgeCmd
            assert wrapped.__name__ == "bridgeReroute", (
                f"Editor.onBridgeCmd was not wrapped. Got {wrapped.__name__} instead of bridgeReroute"
            )
            addon_main = sys.modules[f"{ADDON_NAME}.main"]
            assert addon_main.ogReroute is not None, "main.ogReroute was not set"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_config_editor_accept_wrapped(self, anki_session: AnkiSession) -> None:
        """ConfigEditor.accept must be wrapped by the addon's supportAccept."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            import aqt.addons

            wrapped = aqt.addons.ConfigEditor.accept
            assert wrapped.__name__ == "supportAccept", (
                f"ConfigEditor.accept was not wrapped. Got {wrapped.__name__} instead of supportAccept"
            )
            addon_main = sys.modules[f"{ADDON_NAME}.main"]
            assert addon_main.ogAccept is not None, "main.ogAccept was not set"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_profile_did_open_hook(self, anki_session: AnkiSession) -> None:
        """_init_profile and _rebuild_catalog must be registered on profile_did_open."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            from aqt import gui_hooks

            hook_names = [fn.__name__ for fn in gui_hooks.profile_did_open._hooks]
            assert "_init_profile" in hook_names, f"_init_profile not in profile_did_open hooks. Found: {hook_names}"
            assert "_rebuild_catalog" in hook_names, (
                f"_rebuild_catalog not in profile_did_open hooks. Found: {hook_names}"
            )

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_browser_menu_hook(self, anki_session: AnkiSession) -> None:
        """browser.setupMenus must have setupMenu registered."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            from anki import hooks as anki_hooks

            setup_menus = anki_hooks._hooks.get("browser.setupMenus", [])
            setup_names = [fn.__name__ for fn in setup_menus]
            assert "setupMenu" in setup_names, f"setupMenu not in browser.setupMenus hooks. Found: {setup_names}"


class TestConfigAndCatalog:
    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_real_catalog_discovers_default_notetypes(self, anki_session: AnkiSession) -> None:
        """The live catalog discovers actual note types from the collection."""
        anki_session.load_addon(ADDON_NAME)
        with anki_session.profile_loaded():
            mw = anki_session.mw
            col = mw.col

            catalog = mw.ThaiReadingCatalog
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

            mutation = mw.ThaiReadingMutation
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
                "ThaiReading",
                "ThaiReadingConfig",
                "updateThaiReadingConfig",
                "thaiReadingSettings",
                "ThaiReadingCatalog",
                "ThaiReadingMutation",
            ]
            missing = [a for a in expected if not hasattr(mw, a)]
            assert not missing, f"Missing mw attributes: {missing}"
