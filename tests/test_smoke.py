# ruff: noqa: E402 — importorskip guard before Anki imports
"""Smoke tests that load the addon inside a real headless Anki session.

These tests verify that the addon initializes without errors during:
1. Module import (via __init__.py -> main.py)
2. Profile load (via profile_did_open -> _init_profile)
3. Hook registration (editor buttons, shortcuts, browser menu)
4. Critical wrappers (bridge cmd, config editor accept)

The addon's __init__.py catches Exception silently and prints to stderr,
which means import errors can be swallowed. The AnkiSession-based tests
verify that after a real Anki profile load, all expected objects exist.

pytest-anki2 creates a forked subprocess per test by default. If that's
not available (pytest-forked not installed), tests share a process, so
module-level state from one test may leak to the next.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

pytest_anki = pytest.importorskip("pytest_anki", reason="pytest-anki2 not installed")
from anki.hooks import runFilter
from pytest_anki import AnkiSession

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


# ── Tests that need a real AnkiSession ────────────────────────


class TestWithAnkiSession:
    """Tests that load the addon inside a real headless Anki session."""

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_profile_load_sets_all_mw_attributes(self, anki_session: AnkiSession) -> None:
        """After profile load, the addon must register all expected objects on mw."""
        anki_session.load_addon(ADDON_NAME)

        with anki_session.profile_loaded():
            mw = anki_session.mw
            expected_attrs = [
                "ChineseReading",
                "ChineseReadingConfig",
                "updateChineseReadingConfig",
                "chineseReadingSettings",
                "ChineseReadingCatalog",
                "ChineseReadingMutation",
            ]
            missing = [a for a in expected_attrs if not hasattr(mw, a)]
            assert not missing, f"mw attributes not set after profile load: {missing}"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_editor_buttons_registered(self, anki_session: AnkiSession) -> None:
        """setupEditorButtons hook adds F9/F10 buttons with correct commands."""
        anki_session.load_addon(ADDON_NAME)

        with anki_session.profile_loaded():
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
        """editor_did_init_shortcuts adds F9 and F10 shortcuts.

        The addon registers this via gui_hooks.editor_did_init_shortcuts,
        so the test fires the hook list directly (not runFilter).
        """
        anki_session.load_addon(ADDON_NAME)

        with anki_session.profile_loaded():
            from aqt import gui_hooks

            cuts: list = []
            editor = MagicMock()
            gui_hooks.editor_did_init_shortcuts(cuts, editor)

            keys = [c[0] for c in cuts]
            assert "F9" in keys, f"F9 shortcut not registered. Keys: {keys}"
            assert "F10" in keys, f"F10 shortcut not registered. Keys: {keys}"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_bridge_cmd_wrapped(self, anki_session: AnkiSession) -> None:
        """Editor.onBridgeCmd must be wrapped by the addon's bridgeReroute.

        Checks function name rather than identity because tests may share
        a process (if pytest-forked is not installed), meaning a previous
        test already replaced onBridgeCmd.

        Accesses ogReroute via sys.modules because importing 'main' as a
        top-level module would re-execute main.py (with broken relative imports).
        """
        anki_session.load_addon(ADDON_NAME)
        import aqt.editor

        wrapped = aqt.editor.Editor.onBridgeCmd
        assert wrapped.__name__ == "bridgeReroute", (
            f"Editor.onBridgeCmd was not wrapped. Got {wrapped.__name__} instead of bridgeReroute"
        )
        addon_main = sys.modules[f"{ADDON_NAME}.main"]
        assert addon_main.ogReroute is not None, "main.ogReroute was not set"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_config_editor_accept_wrapped(self, anki_session: AnkiSession) -> None:
        """ConfigEditor.accept must be wrapped by the addon's supportAccept.

        Checks function name rather than identity because tests may share
        a process (if pytest-forked is not installed), meaning a previous
        test already replaced ConfigEditor.accept.

        Accesses ogAccept via sys.modules because importing 'main' as a
        top-level module would re-execute main.py (with broken relative imports).
        """
        anki_session.load_addon(ADDON_NAME)
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
        from aqt import gui_hooks

        hook_names = [fn.__name__ for fn in gui_hooks.profile_did_open._hooks]
        assert "_init_profile" in hook_names, f"_init_profile not in profile_did_open hooks. Found: {hook_names}"
        assert "_rebuild_catalog" in hook_names, f"_rebuild_catalog not in profile_did_open hooks. Found: {hook_names}"

    @pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
    def test_browser_menu_hook(self, anki_session: AnkiSession) -> None:
        """browser_menus_did_init must have setupMenu registered."""
        anki_session.load_addon(ADDON_NAME)
        from aqt import gui_hooks

        hook_names = [fn.__name__ for fn in gui_hooks.browser_menus_did_init._hooks]
        assert "setupMenu" in hook_names, f"setupMenu not in browser_menus_did_init hooks. Found: {hook_names}"
