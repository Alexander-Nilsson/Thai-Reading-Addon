import os
from unittest.mock import MagicMock

import pytest

from config.config import AddonConfig
from reading.dictdb import DictDB
from reading.generator import ReadingGenerator, bopoToneToNumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


@pytest.fixture
def real_db():
    d = DictDB(ROOT)
    yield d
    d.closeConnection()


@pytest.fixture
def generator():
    return ReadingGenerator(db=MagicMock(), config=_make_config())


@pytest.fixture
def real_generator(real_db):
    return ReadingGenerator(db=real_db, config=_make_config())


# ── bopoToneToNumber ────────────────────────────────────────────


class TestBopoToneToNumber:
    def test_tone2_converted(self):
        assert bopoToneToNumber("ㄊㄨㄥˊ", enabled=True) == "ㄊㄨㄥ2"

    def test_tone3_converted(self):
        assert bopoToneToNumber("ㄍㄨˇ", enabled=True) == "ㄍㄨ3"

    def test_tone4_converted(self):
        assert bopoToneToNumber("ㄉㄚˋ", enabled=True) == "ㄉㄚ4"

    def test_tone5_converted(self):
        assert bopoToneToNumber("ㄉㄜ˙", enabled=True) == "ㄉㄜ5"

    def test_tone1_appended(self):
        assert bopoToneToNumber("ㄇㄚ", enabled=True) == "ㄇㄚ1"

    def test_disabled(self):
        assert bopoToneToNumber("ㄊㄨㄥˊ", enabled=False) == "ㄊㄨㄥˊ"


# ── Segment and lookup ──────────────────────────────────────────


class TestSegmentAndLookup:
    def test_simple_pinyin(self, real_generator):
        result = real_generator._segment_and_lookup("你好", "pinyin")
        assert "你好" in result
        assert "[" in result
        assert "]" in result

    def test_mixed_text_and_chinese(self, real_generator):
        result = real_generator._segment_and_lookup("hello 你好 world", "pinyin")
        assert result.startswith("hello ")
        assert "你好" in result
        assert result.endswith(" world")

    def test_jyutping(self, real_generator):
        result = real_generator._segment_and_lookup("你好", "jyutping")
        assert "你好" in result
        assert "[" in result

    def test_unknown_char_passthrough(self, real_generator):
        result = real_generator._segment_and_lookup("hello", "pinyin")
        assert "[" not in result
        assert result == "hello"

    def test_brackets_stripped_from_input(self, real_generator):
        result = real_generator._segment_and_lookup("你好[nǐhǎo]", "pinyin")
        assert "nǐhǎo" not in result


# ── Generate ────────────────────────────────────────────────────


class TestGenerate:
    def test_returns_text_for_invalid_type(self, generator):
        result = generator.generate("你好", reading_type="invalid")
        assert result == "你好"

    def test_delegates_to_segment(self, real_generator):
        result = real_generator.generate("你好")
        assert "[" in result
