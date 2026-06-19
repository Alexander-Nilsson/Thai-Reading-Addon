# ruff: noqa: E402
"""Startup smoke tests for the Thai Reading addon.

Verifies that the addon loads, initialises, and hooks into Anki
without errors. Catches import-time failures, profile-load crashes,
and monkey-patch wiring issues.
"""

import os
import sys
from unittest.mock import patch

import pytest

pytest_anki = pytest.importorskip("pytest_anki", reason="pytest-anki2 not installed")
from pytest_anki import AnkiSession

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


@pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
def test_module_imports_cleanly(anki_session: AnkiSession) -> None:
    """Importing thai_reading.main must not raise at module level."""
    anki_session.load_addon(ADDON_NAME)
    with anki_session.profile_loaded():
        mod = sys.modules[f"{ADDON_NAME}.main"]
        assert mod is not None


@pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
def test_profile_load_sets_all_mw_attributes(anki_session: AnkiSession) -> None:
    """After profile_did_open fires, every expected mw attribute must be set."""
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


@pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
def test_profile_load_raises_no_error_dialogs(anki_session: AnkiSession) -> None:
    """No show_info / show_ask calls during profile load (which would indicate
    an error the user would see as a modal dialog)."""
    anki_session.load_addon(ADDON_NAME)
    with (
        patch(f"{ADDON_NAME}._infra.show_info") as mock_info,
        patch(f"{ADDON_NAME}._infra.show_ask") as mock_ask,
    ):
        with anki_session.profile_loaded():
            pass
        mock_info.assert_not_called()
        mock_ask.assert_not_called()


@pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
def test_bridge_cmd_wrapped(anki_session: AnkiSession) -> None:
    """Editor.onBridgeCmd must be wrapped by bridgeReroute."""
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
def test_config_editor_accept_wrapped(anki_session: AnkiSession) -> None:
    """ConfigEditor.accept must be wrapped by supportAccept."""
    anki_session.load_addon(ADDON_NAME)
    with anki_session.profile_loaded():
        import aqt.addons

        wrapped = aqt.addons.ConfigEditor.accept
        assert wrapped.__name__ == "supportAccept", (
            f"ConfigEditor.accept was not wrapped. Got {wrapped.__name__} instead of supportAccept"
        )
        addon_main = sys.modules[f"{ADDON_NAME}.main"]
        assert addon_main.ogAccept is not None, "main.ogAccept was not set"
