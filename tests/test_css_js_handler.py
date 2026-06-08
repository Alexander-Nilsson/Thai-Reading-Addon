import os
import re
from unittest.mock import patch

import pytest
from conftest import import_css_js_handler

from addon_config import AddonConfig

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


class _MockAnkiServices:
    def __init__(self, profile_name="User 1"):
        self._profile_name = profile_name
        self._models = []

    @property
    def profile_name(self):
        return self._profile_name

    @property
    def col(self):
        return None

    @property
    def addon_folder(self):
        return "/tmp/addons21/chinese_reading"

    def all_models(self):
        return self._models


@pytest.fixture(scope="module")
def CSSJSHandler():
    return import_css_js_handler()


@pytest.fixture
def handler(CSSJSHandler):
    return CSSJSHandler(mw=None, anki_services=_MockAnkiServices(), path=ROOT, config=_make_config())


@pytest.fixture
def handler_custom_font(CSSJSHandler):
    return CSSJSHandler(
        mw=None,
        anki_services=_MockAnkiServices(),
        path=ROOT,
        config=_make_config(FontSize=100),
    )


class TestCSSPattern:
    def test_pattern_matches_generated_css(self, handler):
        css = handler.getChineseCss()
        match = re.search(handler.chineseCSSPattern, css, re.DOTALL)
        assert match is not None

    def test_pattern_does_not_match_random_text(self, handler):
        text = "body { color: red; }"
        match = re.search(handler.chineseCSSPattern, text, re.DOTALL)
        assert match is None


class TestGetChineseCss:
    def test_contains_tone_classes(self, handler):
        css = handler.getChineseCss()
        assert ".tone1" in css
        assert ".tone5" in css
        assert "#E60000" in css

    def test_contains_cantonese_tone_classes(self, handler):
        css = handler.getChineseCss()
        assert ".canTone1" in css
        assert ".canTone6" in css

    def test_contains_header_and_footer(self, handler):
        css = handler.getChineseCss()
        assert "###CHINESE READING CSS STARTS###" in css
        assert "###CHINESE READING CSS ENDS###" in css

    def test_contains_ruby_font_size(self, handler):
        css = handler.getChineseCss()
        assert ".pinyin-ruby" in css
        assert "font-size:75%" in css

    def test_font_size_custom(self, handler_custom_font):
        css = handler_custom_font.getChineseCss()
        assert "font-size:100%" in css

    def test_hover_classes(self, handler):
        css = handler.getChineseCss()
        assert ".unhovered-word .hanzi-ruby" in css
        assert ".unhovered-word .pinyin-ruby" in css

    def test_night_mode_mandarin_tones(self, handler):
        css = handler.getChineseCss()
        assert ".nightMode .tone1" in css

    def test_night_mode_cantonese_tones(self, handler):
        css = handler.getChineseCss()
        assert ".nightMode .canTone1" in css


class TestEditChineseCss:
    def test_adds_css_to_empty(self, handler):
        result = handler.editChineseCss("")
        assert "###CHINESE READING CSS STARTS###" in result

    def test_adds_css_to_existing(self, handler):
        result = handler.editChineseCss("body { color: black; }")
        assert "body { color: black; }" in result
        assert "###CHINESE READING CSS STARTS###" in result

    def test_replaces_existing_css(self, handler):
        old_css = handler.getChineseCss()
        result = handler.editChineseCss(old_css)
        assert "###CHINESE READING CSS STARTS###" in result

    def test_remove_chinese_css(self, handler):
        css = "before" + handler.getChineseCss() + "after"
        result = handler.removeChineseCss(css)
        assert "###CHINESE READING CSS STARTS###" not in result
        assert "before" in result
        assert "after" in result


class TestInjectWrapperElement:
    def test_injects_wrapper_around_field(self, handler):
        text = "some text {{MyField}} more text"
        result = handler.injectWrapperElement(text, "MyField", "hover", "pinyin")
        assert 'class="wrapped-chinese"' in result
        assert 'display-type="hover"' in result
        assert 'reading-type="pinyin"' in result
        assert "{{MyField}}" in result

    def test_does_not_double_wrap(self, handler):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = handler.injectWrapperElement(text, "MyField", "hover", "pinyin")
        assert result == text


class TestOverwriteWrapperElement:
    def test_changes_display_type(self, handler):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = handler.overwriteWrapperElement(text, "MyField", "coloredhover", "pinyin")
        assert 'display-type="coloredhover"' in result
        assert result.count("wrapped-chinese") == 1

    def test_changes_reading_type(self, handler):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = handler.overwriteWrapperElement(text, "MyField", "hover", "bopomofo")
        assert 'reading-type="bopomofo"' in result

    def test_no_change_when_same(self, handler):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = handler.overwriteWrapperElement(text, "MyField", "hover", "pinyin")
        assert result == text


class TestRemoveWrappers:
    def test_removes_single_wrapper(self, handler):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = handler.removeWrappers(text)
        assert result == "{{MyField}}"

    def test_removes_multiple_wrappers(self, handler):
        text = (
            '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{Field1}}</div>'
            " and "
            '<div reading-type="jyutping" display-type="coloredhover" class="wrapped-chinese">{{Field2}}</div>'
        )
        result = handler.removeWrappers(text)
        assert result == "{{Field1}} and {{Field2}}"

    def test_preserves_plain_text(self, handler):
        text = "no wrappers here"
        assert handler.removeWrappers(text) == text


class TestTemplateInModelDict:
    def test_matching_template(self, handler):
        model_dict = [["Card 1", "Field1", "front", "hover", "pinyin"]]
        assert handler.templateInModelDict("Card 1", model_dict) is True

    def test_non_matching_template(self, handler):
        model_dict = [["Card 1", "Field1", "front", "hover", "pinyin"]]
        assert handler.templateInModelDict("Card 2", model_dict) is False


class TestTemplateFilteredDict:
    def test_filters_by_template(self, handler):
        model_dict = [
            ["Card 1", "Field1", "front", "hover", "pinyin"],
            ["Card 1", "Field2", "back", "coloredhover", "bopomofo"],
            ["Card 2", "Field1", "both", "reading", "pinyin"],
        ]
        result = handler.templateFilteredDict(model_dict, "Card 1")
        assert len(result) == 2
        assert result[0][0] == "Card 1"
        assert result[1][0] == "Card 1"


class TestCheckProfile:
    def test_all_profile_matches(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(Profiles=["all"]),
        )
        assert handler.checkProfile() is True

    def test_matching_named_profile(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices("User 1"),
            path=ROOT,
            config=_make_config(Profiles=["User 1"]),
        )
        assert handler.checkProfile() is True

    def test_non_matching_profile(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices("User 1"),
            path=ROOT,
            config=_make_config(Profiles=["Other User"]),
        )
        assert handler.checkProfile() is False


class TestCheckReadingType:
    def test_valid_pinyin(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="pinyin"),
        )
        assert handler.checkReadingType() is True

    def test_valid_bopomofo(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="bopomofo"),
        )
        assert handler.checkReadingType() is True

    def test_valid_jyutping(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="jyutping"),
        )
        assert handler.checkReadingType() is True

    def test_invalid_type(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="invalid"),
        )
        import chinese_reading_addon_test.cssJSHandler as _mod

        with patch.object(_mod, "show_info"):
            assert handler.checkReadingType() is False


class TestRemoveChineseJs:
    def test_removes_js_block(self, handler):
        text = "before" + handler.chineseParserHeader + "some js content" + handler.chineseParserFooter + "after"
        result = handler.removeChineseJs(text)
        assert handler.chineseParserHeader not in result
        assert "before" in result
        assert "after" in result

    def test_preserves_surrounding_text(self, handler):
        text = "prefix" + handler.chineseParserHeader + "content" + handler.chineseParserFooter + "suffix"
        result = handler.removeChineseJs(text)
        assert result == "prefixsuffix"


class TestRemoveHanziConverterJs:
    def test_removes_converter_block(self, handler):
        text = "before" + handler.hanziConverterHeader + "script content" + handler.hanziConverterFooter + "after"
        result = handler.removeHanziConverterJs(text)
        assert handler.hanziConverterHeader not in result
        assert "before" in result
        assert "after" in result


class TestNewLineReduce:
    def test_reduces_triple_newlines(self, handler):
        assert handler.newLineReduce("a\n\n\nb") == "a\n\nb"

    def test_preserves_double_newlines(self, handler):
        assert handler.newLineReduce("a\n\nb") == "a\n\nb"

    def test_preserves_single_newlines(self, handler):
        assert handler.newLineReduce("a\nb") == "a\nb"


class TestCleanFieldWrappers:
    def test_removes_wrapper_from_front_when_not_in_sides(self, handler):
        template_dict = [["Card 1", "MyField", "back", "hover", "pinyin"]]
        fields = [{"name": "MyField"}]
        front = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        back = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        new_front, _new_back = handler.cleanFieldWrappers(front, back, fields, template_dict)
        assert "{{MyField}}" in new_front
        assert "wrapped-chinese" not in new_front

    def test_removes_wrapper_from_front_and_back_when_no_sides(self, handler):
        template_dict = [["Card 1", "OtherField", "front", "hover", "pinyin"]]
        fields = [{"name": "MyField"}]
        front = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        back = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        new_front, new_back = handler.cleanFieldWrappers(front, back, fields, template_dict)
        assert "wrapped-chinese" not in new_front
        assert "wrapped-chinese" not in new_back
