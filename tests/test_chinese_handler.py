import os
from unittest.mock import MagicMock

import pytest
from conftest import import_chinese_handler

from addon_config import AddonConfig
from dictdb import DictDB
from text_utils import clean_spaces, html_remove, replace_html


def _make_config(**overrides):
    raw = {
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
    raw.update(overrides)
    return AddonConfig(_raw=raw)


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "chinese_dict.sqlite")


@pytest.fixture(scope="module")
def ChineseHandler():
    return import_chinese_handler()


def _make_handler(ChineseHandler, config=None, db=None):
    anki = MagicMock()
    anki.profile_name = "User 1"
    anki.col = None
    cfg = config or _make_config()
    handler = ChineseHandler.__new__(ChineseHandler)
    handler.mw = None
    handler.anki = anki
    handler.config = cfg
    handler.db = db
    handler.hanziRange = (
        "[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df"
        "\U0002a700-\U0002b73f\U0002b740-\U0002b81f"
        "\U0002b820-\U0002ceaf\U0002ceb0-\U0002ebef"
        "\uf900-\ufaff\U0002f800-\U0002fa1f]"
    )
    handler.toneToNumer = {"ˊ": "2", "ˇ": "3", "ˋ": "4", "˙": "5"}  # noqa: RUF001
    return handler


@pytest.fixture
def real_db():
    d = DictDB(os.path.dirname(os.path.dirname(__file__)))
    yield d
    d.closeConnection()


class TestRemoveBrackets:
    def test_simple_bracket_removal(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.removeBrackets("你好[nǐ hǎo]") == "你好"

    def test_multiple_brackets(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.removeBrackets("中国[zhōng guó]你好[nǐ hǎo]") == "中国你好"

    def test_no_brackets(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.removeBrackets("hello world") == "hello world"

    def test_preserves_sound_tags(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        result = handler.removeBrackets("[sound:file.mp3]")
        assert "[sound:file.mp3]" in result

    def test_preserves_number_brackets(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        result = handler.removeBrackets("[42]")
        assert "[42]" in result

    def test_removes_content_brackets_preserves_sound(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        result = handler.removeBrackets("你好[nǐ hǎo][sound:test.mp3]")
        assert "[sound:test.mp3]" in result
        assert "nǐ hǎo" not in result

    def test_return_sounds(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        text, sounds = handler.removeBrackets("[sound:file.mp3]你好[nǐ hǎo]", returnSounds=True)
        assert "[sound:file.mp3]" in sounds
        assert "nǐ hǎo" not in text

    def test_remove_audio(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        result = handler.removeBrackets("你好[nǐ hǎo][sound:file.mp3]", removeAudio=True)
        assert "[sound:file.mp3]" not in result
        assert "nǐ hǎo" not in result

    def test_html_preserved(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        text = "<b>你好</b>[nǐ hǎo]"
        result = handler.removeBrackets(text)
        assert "<b>" in result
        assert "nǐ hǎo" not in result

    def test_empty_string(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        result = handler.removeBrackets("")
        assert result == ""

    def test_preserves_spaces(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        result = handler.removeBrackets("你 好[nǐ hǎo]")
        assert "你 好" in result


class TestBopoToneToNumber:
    def test_tone2_converted(self, ChineseHandler):
        handler = _make_handler(ChineseHandler, config=_make_config(BopomofoTonesToNumber=True))
        assert handler.bopoToneToNumber("ㄊㄨㄥˊ") == "ㄊㄨㄥ2"

    def test_tone3_converted(self, ChineseHandler):
        handler = _make_handler(ChineseHandler, config=_make_config(BopomofoTonesToNumber=True))
        assert handler.bopoToneToNumber("ㄍㄨˇ") == "ㄍㄨ3"

    def test_tone4_converted(self, ChineseHandler):
        handler = _make_handler(ChineseHandler, config=_make_config(BopomofoTonesToNumber=True))
        assert handler.bopoToneToNumber("ㄉㄚˋ") == "ㄉㄚ4"

    def test_tone5_converted(self, ChineseHandler):
        handler = _make_handler(ChineseHandler, config=_make_config(BopomofoTonesToNumber=True))
        assert handler.bopoToneToNumber("ㄉㄜ˙") == "ㄉㄜ5"

    def test_tone1_appended(self, ChineseHandler):
        handler = _make_handler(ChineseHandler, config=_make_config(BopomofoTonesToNumber=True))
        assert handler.bopoToneToNumber("ㄇㄚ") == "ㄇㄚ1"

    def test_disabled(self, ChineseHandler):
        handler = _make_handler(ChineseHandler, config=_make_config(BopomofoTonesToNumber=False))
        assert handler.bopoToneToNumber("ㄊㄨㄥˊ") == "ㄊㄨㄥˊ"


class TestApplyOM:
    def test_overwrite(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.applyOM("Overwrite", "old dest", "new text") == "new text"
        assert handler.applyOM("Overwrite", "", "new text") == "new text"

    def test_if_empty_with_empty(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.applyOM("If Empty", "", "new text") == "new text"

    def test_if_empty_with_content(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.applyOM("If Empty", "existing", "new text") == "existing"

    def test_add_with_empty(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.applyOM("Add", "", "new text") == "new text"

    def test_add_with_content(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.applyOM("Add", "existing", "new text") == "existing<br>new text"

    def test_empty_text(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.applyOM("Overwrite", "dest", "") == "dest"

    def test_none_text(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        assert handler.applyOM("Overwrite", "dest", None) == "dest"
        assert handler.applyOM("Add", "dest", None) == "dest"
        assert handler.applyOM("If Empty", "dest", None) == "dest"


class TestSegmentAndLookup:
    def test_simple_pinyin(self, ChineseHandler, real_db):
        handler = _make_handler(ChineseHandler, db=real_db)
        result = handler._segment_and_lookup("你好", "pinyin")
        assert "你好" in result
        assert "[" in result
        assert "]" in result

    def test_mixed_text_and_chinese(self, ChineseHandler, real_db):
        handler = _make_handler(ChineseHandler, db=real_db)
        result = handler._segment_and_lookup("hello 你好 world", "pinyin")
        assert result.startswith("hello ")
        assert "你好" in result
        assert result.endswith(" world")

    def test_jyutping(self, ChineseHandler, real_db):
        handler = _make_handler(ChineseHandler, db=real_db)
        result = handler._segment_and_lookup("你好", "jyutping")
        assert "你好" in result
        assert "[" in result

    def test_unknown_char_passthrough(self, ChineseHandler, real_db):
        handler = _make_handler(ChineseHandler, db=real_db)
        result = handler._segment_and_lookup("hello", "pinyin")
        assert "[" not in result
        assert result == "hello"

    def test_brackets_stripped_from_input(self, ChineseHandler, real_db):
        handler = _make_handler(ChineseHandler, db=real_db)
        result = handler._segment_and_lookup("你好[nǐhǎo]", "pinyin")
        assert "nǐhǎo" not in result


class TestHtmlRemove:
    def test_removes_html_tags(self):
        finds, text = html_remove("<b>hello</b>")
        assert "--=HTML=--" in text
        assert finds == ["<b>", "</b>"]

    def test_replaces_html_back(self):
        finds, text = html_remove("<b>hello</b>")
        result = replace_html(text, finds)
        assert result == "<b>hello</b>"

    def test_no_html(self):
        finds, text = html_remove("plain text")
        assert text == "plain text"
        assert finds == []


class TestCleanSpaces:
    def test_removes_double_spaces(self):
        assert clean_spaces("hello  world") == "helloworld"

    def test_single_space_preserved(self):
        assert clean_spaces("hello world") == "hello world"


class TestEditorText:
    def test_returns_false_when_empty(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        mock_editor = MagicMock()
        mock_editor.web.selectedText.return_value = ""
        assert handler.editorText(mock_editor) is False

    def test_returns_text_when_selected(self, ChineseHandler):
        handler = _make_handler(ChineseHandler)
        mock_editor = MagicMock()
        mock_editor.web.selectedText.return_value = "selected text"
        result = handler.editorText(mock_editor)
        assert result == "selected text"
