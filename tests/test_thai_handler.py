from unittest.mock import MagicMock

import pytest

from config.config import AddonConfig
from conftest import import_thai_handler
from reading.generator import ReadingGenerator, strip_brackets


def _make_config(**overrides):
    raw = {
        "ThaiTones": ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"],
        "FontSize": 75,
        "ReadingType": "rtgs",
        "AutoCssJsGeneration": True,
        "ActiveFields": [],
        "Profiles": ["all"],
    }
    raw.update(overrides)
    return AddonConfig(_raw=raw)


@pytest.fixture(scope="module")
def ThaiHandler():
    return import_thai_handler()


def _make_handler(ThaiHandler, config=None, db=None):
    anki = MagicMock()
    anki.profile_name = "User 1"
    anki.col = None
    cfg = config or _make_config()
    handler = ThaiHandler.__new__(ThaiHandler)
    handler.mw = None
    handler.anki = anki
    handler.config = cfg
    handler.db = db
    handler.reading_generator = ReadingGenerator(db, cfg)
    handler.cssJsHandler = MagicMock()
    return handler


class TestRemoveBrackets:
    def test_simple_bracket_removal(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.removeBrackets("สวัสดี[sa-wat-dii]") == "สวัสดี"

    def test_multiple_brackets(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.removeBrackets("ภาษาไทย[pha-sa-thai]สวัสดี[sa-wat-dii]") == "ภาษาไทยสวัสดี"

    def test_no_brackets(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.removeBrackets("hello world") == "hello world"

    def test_preserves_sound_tags(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        result = handler.removeBrackets("[sound:file.mp3]")
        assert "[sound:file.mp3]" in result

    def test_preserves_number_brackets(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        result = handler.removeBrackets("[42]")
        assert "[42]" in result

    def test_removes_content_brackets_preserves_sound(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        result = handler.removeBrackets("สวัสดี[sa-wat-dii][sound:test.mp3]")
        assert "[sound:test.mp3]" in result
        assert "sa-wat-dii" not in result

    def test_return_sounds(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        text, sounds = handler.removeBrackets("[sound:file.mp3]สวัสดี[sa-wat-dii]", returnSounds=True)
        assert "[sound:file.mp3]" in sounds
        assert "sa-wat-dii" not in text

    def test_remove_audio(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        result = handler.removeBrackets("สวัสดี[sa-wat-dii][sound:file.mp3]", removeAudio=True)
        assert "[sound:file.mp3]" in result  # sound tags preserved
        assert "sa-wat-dii" not in result

    def test_html_preserved(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        text = "<b>สวัสดี</b>[sa-wat-dii]"
        result = handler.removeBrackets(text)
        assert "<b>" in result
        assert "sa-wat-dii" not in result

    def test_empty_string(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        result = handler.removeBrackets("")
        assert result == ""

    def test_preserves_spaces(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        result = handler.removeBrackets("สวัส ดี[sa-wat-dii]")
        assert "สวัส ดี" in result


class TestApplyOM:
    def test_overwrite(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.applyOM("Overwrite", "old dest", "new text") == "new text"
        assert handler.applyOM("Overwrite", "", "new text") == "new text"

    def test_if_empty_with_empty(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.applyOM("If Empty", "", "new text") == "new text"

    def test_if_empty_with_content(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.applyOM("If Empty", "existing", "new text") == "existing"

    def test_add_with_empty(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.applyOM("Add", "", "new text") == "new text"

    def test_add_with_content(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.applyOM("Add", "existing", "new text") == "existing<br>new text"

    def test_empty_text(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.applyOM("Overwrite", "dest", "") == "dest"

    def test_none_text(self, ThaiHandler):
        handler = _make_handler(ThaiHandler)
        assert handler.applyOM("Overwrite", "dest", None) == "dest"
        assert handler.applyOM("Add", "dest", None) == "dest"
        assert handler.applyOM("If Empty", "dest", None) == "dest"


class TestStripBrackets:
    def test_simple_bracket_removal(self):
        assert strip_brackets("สวัสดี[sa-wat-dii]") == "สวัสดี"

    def test_multiple_brackets(self):
        assert strip_brackets("ภาษาไทย[pha-sa-thai]สวัสดี[sa-wat-dii]") == "ภาษาไทยสวัสดี"

    def test_no_brackets(self):
        assert strip_brackets("hello world") == "hello world"

    def test_preserves_sound_tags(self):
        assert "[sound:file.mp3]" in strip_brackets("[sound:file.mp3]")

    def test_preserves_number_brackets(self):
        result = strip_brackets("[42]")
        assert "[42]" in result

    def test_removes_content_brackets_preserves_sound(self):
        result = strip_brackets("สวัสดี[sa-wat-dii][sound:test.mp3]")
        assert "[sound:test.mp3]" in result
        assert "sa-wat-dii" not in result

    def test_return_sounds(self):
        text, sounds = strip_brackets("[sound:file.mp3]สวัสดี[sa-wat-dii]", return_sounds=True)
        assert "[sound:file.mp3]" in sounds
        assert "sa-wat-dii" not in text

    def test_remove_audio(self):
        result = strip_brackets("สวัสดี[sa-wat-dii][sound:file.mp3]", remove_audio=True)
        assert "[sound:file.mp3]" in result  # sound tags preserved
        assert "sa-wat-dii" not in result

    def test_html_preserved(self):
        text = "<b>สวัสดี</b>[sa-wat-dii]"
        result = strip_brackets(text)
        assert "<b>" in result
        assert "sa-wat-dii" not in result

    def test_empty_string(self):
        assert strip_brackets("") == ""

    def test_preserves_spaces(self):
        result = strip_brackets("สวัส ดี[sa-wat-dii]")
        assert "สวัส ดี" in result


class TestAddCReadingsNoTextSelected:
    def test_no_main_import_error_when_no_text_selected(self, ThaiHandler, test_db):
        """addCReadings should not fail with ModuleNotFoundError when no text selected."""
        handler = _make_handler(ThaiHandler, db=test_db)

        mock_editor = MagicMock()
        mock_editor.web.selectedText.return_value = ""

        try:
            handler.addCReadings(mock_editor)
        except ModuleNotFoundError as e:
            if "main" in str(e):
                pytest.fail(f"addCReadings raised ModuleNotFoundError for 'main': {e}")
            raise
