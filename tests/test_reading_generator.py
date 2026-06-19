from unittest.mock import MagicMock

import pytest

from config.config import AddonConfig
from reading.generator import ReadingGenerator


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


@pytest.fixture
def generator():
    return ReadingGenerator(db=MagicMock(), config=_make_config())


@pytest.fixture
def test_generator(test_db):
    return ReadingGenerator(db=test_db, config=_make_config())


# ── Segment and lookup ──────────────────────────────────────────


class TestSegmentAndLookup:
    def test_simple_rtgs(self, test_generator):
        result = test_generator._segment_and_lookup("สวัสดี", "rtgs")
        assert "สวัสดี" in result
        assert "[" in result
        assert "]" in result

    def test_rtgs_format(self, test_generator):
        result = test_generator._segment_and_lookup("สวัสดี", "rtgs")
        reading = result.split("[")[1].split("]")[0]
        assert reading == "sa-wat-dii", f"expected rtgs, got {reading!r}"

    def test_rtgs_multi_word(self, test_generator):
        result = test_generator._segment_and_lookup("ภาษาไทย", "rtgs")
        reading = result.split("[")[1].split("]")[0]
        assert reading == "pha-sa-thai", f"expected rtgs, got {reading!r}"

    def test_mixed_text_and_thai(self, test_generator):
        result = test_generator._segment_and_lookup("hello สวัสดี world", "rtgs")
        assert result.startswith("hello ")
        assert "สวัสดี" in result
        assert result.endswith(" world")

    def test_ipa(self, test_generator):
        result = test_generator._segment_and_lookup("ภาษาไทย", "ipa")
        assert "ภาษาไทย" in result
        assert "[" in result

    def test_unknown_char_passthrough(self, test_generator):
        result = test_generator._segment_and_lookup("hello", "rtgs")
        assert "[" not in result
        assert result == "hello"

    def test_brackets_stripped_from_input(self, test_generator):
        result = test_generator._segment_and_lookup("สวัสดี[old]", "rtgs")
        assert "old" not in result


# ── Generate ────────────────────────────────────────────────────


class TestGenerate:
    def test_returns_text_for_invalid_type(self, generator):
        result = generator.generate("สวัสดี", reading_type="invalid")
        assert result == "สวัสดี"

    def test_delegates_to_segment(self, test_generator):
        result = test_generator.generate("สวัสดี")
        assert "[" in result

    def test_generate_rtgs(self, test_generator):
        result = test_generator.generate("สวัสดี", reading_type="rtgs")
        assert "[" in result
        reading = result.split("[")[1].split("]")[0]
        assert reading == "sa-wat-dii"


# ── Phonetics ───────────────────────────────────────────────────


class TestPhonetics:
    def test_generate_phonetics(self, test_generator):
        result = test_generator.generate("สวัสดี", reading_type="phonetics")
        assert "[" in result
        reading = result.split("[")[1].split("]")[0]
        assert reading == "sà-wàt-dii", f"expected phonetics, got {reading!r}"

    def test_phonetics_multi_word(self, test_generator):
        result = test_generator.generate("ภาษาไทย", reading_type="phonetics")
        reading = result.split("[")[1].split("]")[0]
        assert reading == "paa-sǎa-thai", f"expected phonetics, got {reading!r}"

    def test_phonetics_fallback_to_rtgs(self, test_generator):
        """When phonetics is missing for a word, falls back to RTGS."""
        from unittest.mock import MagicMock

        test_generator._db.get_reading_phonetics = MagicMock(return_value=None)
        result = test_generator.generate("สวัสดี", reading_type="phonetics")
        reading = result.split("[")[1].split("]")[0]
        assert reading == "sa-wat-dii"
