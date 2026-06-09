"""Smoke tests that load the addon inside a real headless Anki session."""

import os

import pytest
from pytest_anki import AnkiSession

pytest_anki = pytest.importorskip("pytest_anki", reason="pytest-anki not installed")

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


@pytest.mark.parametrize(
    "anki_session",
    [
        dict(
            load_profile=False,
            unpacked_addons=[("chinese_reading", ROOT)],
            addon_configs=[("chinese_reading", DEFAULT_CONFIG)],
        )
    ],
    indirect=True,
)
def test_addon_loads_and_sets_mw_attributes(anki_session: AnkiSession) -> None:
    """Importing the addon should register handlers and config on mw."""
    anki_session.load_addon("chinese_reading")

    assert hasattr(anki_session.mw, "ChineseReading")
    assert hasattr(anki_session.mw, "ChineseReadingConfig")
    assert hasattr(anki_session.mw, "updateChineseReadingConfig")
    assert hasattr(anki_session.mw, "chineseReadingSettings")


@pytest.mark.parametrize(
    "anki_session",
    [
        dict(
            load_profile=False,
            unpacked_addons=[("chinese_reading", ROOT)],
            addon_configs=[("chinese_reading", DEFAULT_CONFIG)],
        )
    ],
    indirect=True,
)
def test_addon_hooks_fire_on_profile_load(anki_session: AnkiSession) -> None:
    """Loading a profile should trigger the addon's profileLoaded hooks."""
    anki_session.load_addon("chinese_reading")

    with anki_session.profile_loaded():
        assert anki_session.collection is not None
        # Hooks should have fired without raising
        assert hasattr(anki_session.mw, "ChineseReading")
        assert hasattr(anki_session.mw, "ChineseReadingConfig")
