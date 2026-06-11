# ruff: noqa: E402
import os
from unittest.mock import MagicMock

import pytest

# Skip if pytest_anki is not available
pytest_anki = pytest.importorskip("pytest_anki", reason="pytest-anki2 not installed")
from pytest_anki import AnkiSession

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Config with no active fields (set up manually per-test to avoid
# show_info blocking during profile load when note type doesn't exist yet)
SUBS2SRS_CONFIG = {
    "ReadingType": "pinyin",
    "ActiveFields": [],
    "Profiles": ["all"],
}


def _setup_wrapper_dict(handler, note_type="Subs2srs"):
    """Configure wrapperDict so addCReadings/cleanField can resolve fields."""
    handler.cssJSHandler.wrapperDict = {note_type: [["Card 1", "Expression", "front", "coloredhanzi", "pinyin"]]}


_ANKI_SESSION_PARAMS = dict(
    load_profile=False,
    unpacked_addons=[("chinese_reading", ROOT)],
    addon_configs=[("chinese_reading", SUBS2SRS_CONFIG)],
)

ADDON_NAME = "chinese_reading"


def _create_subs2srs_notetype(col):
    notetype = col.models.new("Subs2srs")
    col.models.add_field(notetype, col.models.new_field("Expression"))
    col.models.add_field(notetype, col.models.new_field("Meaning"))
    template = col.models.new_template("Card 1")
    template["qfmt"] = "{{Expression}}"
    template["afmt"] = "{{FrontSide}}<hr id=answer>{{Meaning}}"
    col.models.add_template(notetype, template)
    col.models.save(notetype)
    return notetype


@pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
def test_idempotent_reading_generation(anki_session: AnkiSession) -> None:
    """Verify that generating readings multiple times doesn't duplicate them."""
    anki_session.load_addon(ADDON_NAME)
    with anki_session.profile_loaded():
        mw = anki_session.mw
        col = mw.col

        # 1. Setup note with Subs2srs note type
        notetype = _create_subs2srs_notetype(col)
        note = col.new_note(notetype)
        note["Expression"] = "你好"
        col.add_note(note, col.decks.current()["id"])

        # Access the handler
        handler = mw.ChineseReading
        _setup_wrapper_dict(handler)

        # Mock editor
        mock_editor = MagicMock()
        mock_editor.note = note
        mock_editor.web.selectedText.return_value = ""  # No selection, use field resolution

        # 2. First generation
        handler.addCReadings(mock_editor)

        first_result = note["Expression"]
        assert "你好" in first_result
        assert "[ni3 hao3]" in first_result

        # 3. Second generation (should be identical, no duplication)
        handler.addCReadings(mock_editor)

        second_result = note["Expression"]
        assert second_result == first_result
        # Ensure we don't have [nǐ hǎo][nǐ hǎo]
        assert second_result.count("[ni3 hao3]") == 1


@pytest.mark.parametrize("anki_session", [_ANKI_SESSION_PARAMS], indirect=True)
def test_remove_reading_button(anki_session: AnkiSession) -> None:
    """Verify that the remove reading button works for configured fields."""
    anki_session.load_addon(ADDON_NAME)
    with anki_session.profile_loaded():
        mw = anki_session.mw
        col = mw.col

        # 1. Setup note with existing readings
        notetype = _create_subs2srs_notetype(col)
        note = col.new_note(notetype)
        note["Expression"] = "你好[nǐ hǎo]"
        col.add_note(note, col.decks.current()["id"])

        handler = mw.ChineseReading
        _setup_wrapper_dict(handler)
        mock_editor = MagicMock()
        mock_editor.note = note
        mock_editor.web.selectedText.return_value = ""

        # 2. Trigger removal
        handler.cleanField(mock_editor)

        # 3. Verify it was stripped
        assert note["Expression"] == "你好"
        # Verify it was saved to DB
        db_note = col.get_note(note.id)
        assert db_note["Expression"] == "你好"
        # Verify editor was told to reload
        mock_editor.loadNoteKeepingFocus.assert_called()
