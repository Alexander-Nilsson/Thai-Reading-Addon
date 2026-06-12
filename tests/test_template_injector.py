import os

import pytest

from template.injector import (
    CHINESE_CSS_HEADER,
    CHINESE_PARSER_HEADER,
    HANZI_CONVERTER_HEADER,
    PINBOPO_CONVERTER_HEADER,
    TemplateInjector,
    newline_reduce,
)
from template.js_registry import JsRegistry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def injector():
    return TemplateInjector(JsRegistry(os.path.join(ROOT, "js")))


MANDARIN_TONES = ("#E60000", "#E68A00", "#00802B", "#005CE6", "gray")
CANTONESE_TONES = ("#E60000", "#E68A00", "#00802B", "#005CE6", "#AC00E6", "gray")


# ── CSS ─────────────────────────────────────────────────────────


class TestGetChineseCss:
    def test_contains_tone_classes(self, injector):
        css = injector.get_chinese_css(MANDARIN_TONES, CANTONESE_TONES, 75)
        assert ".tone1" in css
        assert ".tone5" in css
        assert ".canTone1" in css
        assert ".canTone6" in css

    def test_contains_header_and_footer(self, injector):
        css = injector.get_chinese_css(MANDARIN_TONES, CANTONESE_TONES, 75)
        assert "###CHINESE READING CSS STARTS###" in css
        assert "###CHINESE READING CSS ENDS###" in css

    def test_custom_font_size(self, injector):
        css = injector.get_chinese_css(MANDARIN_TONES, CANTONESE_TONES, 100)
        assert "font-size:100%" in css

    def test_hover_classes(self, injector):
        css = injector.get_chinese_css(MANDARIN_TONES, CANTONESE_TONES, 75)
        assert ".unhovered-word .pinyin-ruby" in css
        assert ".hanzi-ruby" not in css

    def test_skips_tone_rules_when_all_same_color(self, injector):
        uniform = ["gray", "gray", "gray", "gray", "gray"]
        css = injector.get_chinese_css(uniform, uniform[:5], 75)
        assert ".tone1" not in css
        assert ".canTone1" not in css
        assert "font-size:75%" in css

    def test_emits_tone_rules_when_colors_differ(self, injector):
        mixed_m = ["red", "gray", "gray", "gray", "gray"]
        mixed_c = ["red", "gray", "gray", "gray", "gray", "gray"]
        css = injector.get_chinese_css(mixed_m, mixed_c, 75)
        assert ".tone1{color:red;" in css
        assert ".tone2{color:gray;" in css
        assert ".canTone1{color:red;" in css


class TestInjectChineseCss:
    def test_adds_to_empty(self, injector):
        result = injector.inject("chinese_css", "", mandarin_tones=MANDARIN_TONES, cantonese_tones=CANTONESE_TONES)
        assert CHINESE_CSS_HEADER in result

    def test_adds_to_existing_style(self, injector):
        result = injector.inject(
            "chinese_css", "body { color: black; }", mandarin_tones=MANDARIN_TONES, cantonese_tones=CANTONESE_TONES
        )
        assert "body { color: black; }" in result
        assert CHINESE_CSS_HEADER in result

    def test_replaces_different_block(self, injector):
        old_css = injector.get_chinese_css(MANDARIN_TONES, CANTONESE_TONES, 75)
        result = injector.inject(
            "chinese_css", old_css, mandarin_tones=MANDARIN_TONES, cantonese_tones=CANTONESE_TONES, font_size=100
        )
        assert "font-size:100%" in result

    def test_no_change_when_same(self, injector):
        old_css = injector.get_chinese_css(MANDARIN_TONES, CANTONESE_TONES, 75)
        result = injector.inject(
            "chinese_css", old_css, mandarin_tones=MANDARIN_TONES, cantonese_tones=CANTONESE_TONES, font_size=75
        )
        assert result == old_css


class TestRemoveChineseCss:
    def test_removes_block(self, injector):
        css = "before" + injector.get_chinese_css(MANDARIN_TONES, CANTONESE_TONES, 75) + "after"
        result = injector.remove("chinese_css", css)
        assert CHINESE_CSS_HEADER not in result
        assert "before" in result
        assert "after" in result


# ── Chinese JS ──────────────────────────────────────────────────


class TestInjectChineseJs:
    def test_adds_to_empty(self, injector):
        result = injector.inject("chinese_js", "", reading_type="pinyin")
        assert CHINESE_PARSER_HEADER in result

    def test_replaces_different(self, injector):
        old = injector.inject("chinese_js", "", reading_type="pinyin")
        result = injector.inject("chinese_js", old, reading_type="bopomofo")
        assert 'CHINESE_READING_TYPE ="bopomofo"' in result

    def test_no_change_when_same(self, injector):
        old = injector.inject("chinese_js", "prefix", reading_type="jyutping")
        result = injector.inject("chinese_js", old, reading_type="jyutping")
        assert result == old


class TestRemoveChineseJs:
    def test_removes_block(self, injector):
        text = "before" + injector.get_chinese_js("pinyin") + "after"
        result = injector.remove("chinese_js", text)
        assert CHINESE_PARSER_HEADER not in result
        assert "before" in result
        assert "after" in result


# ── Wrappers ────────────────────────────────────────────────────


class TestInjectWrapper:
    def test_injects_around_field(self, injector):
        text = "some text {{MyField}} more text"
        result = injector.inject("wrapper", text, field="MyField", display_type="hover", reading_type="pinyin")
        assert 'class="wrapped-chinese"' in result
        assert 'display-type="hover"' in result
        assert 'reading-type="pinyin"' in result

    def test_no_double_wrap(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = injector.inject("wrapper", text, field="MyField", display_type="hover", reading_type="pinyin")
        assert result == text

    def test_injects_around_edit_filtered_field(self, injector):
        text = "some text {{edit:Expression}} more text"
        result = injector.inject("wrapper", text, field="Expression", display_type="hover", reading_type="pinyin")
        assert 'class="wrapped-chinese"' in result
        assert "{{edit:Expression}}" in result

    def test_injects_around_text_filtered_field(self, injector):
        text = "{{text:Front}} and {{text:Back}}"
        result = injector.inject("wrapper", text, field="Front", display_type="hover", reading_type="pinyin")
        assert "{{text:Front}}" in result
        assert "wrapped-chinese" in result

    def test_preserves_filter_when_injecting(self, injector):
        text = "prefix {{edit:Expression}} suffix"
        result = injector.inject("wrapper", text, field="Expression", display_type="hover", reading_type="pinyin")
        assert "{{edit:Expression}}" in result


class TestRemoveWrappers:
    def test_removes_single(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = injector.remove("wrapper", text)
        assert result == "{{MyField}}"

    def test_removes_multiple(self, injector):
        text = (
            '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{F1}}</div>'
            " and "
            '<div reading-type="jyutping" display-type="color" class="wrapped-chinese">{{F2}}</div>'
        )
        result = injector.remove("wrapper", text)
        assert result == "{{F1}} and {{F2}}"

    def test_preserves_plain_text(self, injector):
        assert injector.remove("wrapper", "no wrappers") == "no wrappers"

    def test_removes_wrapper_around_filtered_field(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{edit:Expression}}</div>'
        result = injector.remove("wrapper", text)
        assert result == "{{edit:Expression}}"

    def test_removes_wrapper_with_text_filter(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{text:Front}}</div>'
        result = injector.remove("wrapper", text)
        assert result == "{{text:Front}}"


class TestOverwriteWrapper:
    def test_changes_display_type(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = injector.overwrite_wrapper(text, "MyField", "coloredhover", "pinyin")
        assert 'display-type="coloredhover"' in result

    def test_changes_reading_type(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = injector.overwrite_wrapper(text, "MyField", "hover", "bopomofo")
        assert 'reading-type="bopomofo"' in result

    def test_no_change_when_same(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        result = injector.overwrite_wrapper(text, "MyField", "hover", "pinyin")
        assert result == text

    def test_overwrites_wrapper_with_edit_filter(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{edit:Expression}}</div>'
        result = injector.overwrite_wrapper(text, "Expression", "coloredhover", "bopomofo")
        assert 'display-type="coloredhover"' in result
        assert 'reading-type="bopomofo"' in result
        assert "{{edit:Expression}}" in result

    def test_overwrites_wrapper_with_text_filter(self, injector):
        text = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{text:Front}}</div>'
        result = injector.overwrite_wrapper(text, "Front", "hover", "jyutping")
        assert 'reading-type="jyutping"' in result
        assert "{{text:Front}}" in result


# ── Hanzi converter ─────────────────────────────────────────────


class TestInjectHanziConverter:
    def test_injects_js(self, injector):
        text = "some template"
        result = injector.inject("hanzi_converter", text, conversion_type="Simplified")
        assert HANZI_CONVERTER_HEADER in result
        assert "CHINESE_CONVERSION_TYPE" in result

    def test_none_removes_existing(self, injector):
        with_js = injector.inject("hanzi_converter", "text", conversion_type="Simplified")
        result = injector.inject("hanzi_converter", with_js, conversion_type="None")
        assert HANZI_CONVERTER_HEADER not in result


class TestRemoveHanziConverter:
    def test_removes_block(self, injector):
        text = "before" + injector.get_hanzi_converter_js("Simplified") + "after"
        result = injector.remove("hanzi_converter", text)
        assert HANZI_CONVERTER_HEADER not in result
        assert "before" in result
        assert "after" in result


# ── Pinyin/Bopomofo converter ───────────────────────────────────


class TestInjectPinbopoConverter:
    def test_injects_pinyin_converter(self, injector):
        text = "template"
        result = injector.inject("pinyin_bopomo_converter", text, reading_conversion="Pinyin")
        assert PINBOPO_CONVERTER_HEADER in result

    def test_injects_bopomofo_converter(self, injector):
        text = "template"
        result = injector.inject("pinyin_bopomo_converter", text, reading_conversion="Bopomofo")
        assert PINBOPO_CONVERTER_HEADER in result

    def test_none_removes_existing(self, injector):
        with_js = injector.inject("pinyin_bopomo_converter", "text", reading_conversion="Pinyin")
        result = injector.inject("pinyin_bopomo_converter", with_js, reading_conversion="None")
        assert PINBOPO_CONVERTER_HEADER not in result

    def test_inserts_before_chinese_js_header(self, injector):
        base = injector.inject("chinese_js", "{{{MyField}}}", reading_type="pinyin")
        result = injector.inject("pinyin_bopomo_converter", base, reading_conversion="Pinyin")
        # Pinbopo header should come before Chinese parser header
        assert result.index(PINBOPO_CONVERTER_HEADER) < result.index(CHINESE_PARSER_HEADER)


class TestRemovePinbopoConverter:
    def test_removes_block(self, injector):
        text = "before" + injector.get_pinbopo_converter_js("Pinyin") + "after"
        result = injector.remove("pinyin_bopomo_converter", text)
        assert PINBOPO_CONVERTER_HEADER not in result
        assert "before" in result
        assert "after" in result


# ── Media file references ───────────────────────────────────────


class TestMediaFileCss:
    def test_injects_css_link(self, injector):
        result = injector.inject("chinese_css_file", "", filename="_chinese_reading_abc.css")
        assert '<link rel="stylesheet" href="_chinese_reading_abc.css">' in result
        assert "###CHINESE READING CSS FILE" in result

    def test_replaces_different_filename(self, injector):
        old = injector.inject("chinese_css_file", "", filename="_chinese_reading_abc.css")
        result = injector.inject("chinese_css_file", old, filename="_chinese_reading_def.css")
        assert "_chinese_reading_def.css" in result
        assert "_chinese_reading_abc.css" not in result

    def test_no_change_when_same(self, injector):
        old = injector.inject("chinese_css_file", "prefix", filename="_chinese_reading_abc.css")
        result = injector.inject("chinese_css_file", old, filename="_chinese_reading_abc.css")
        assert result == old


class TestRemoveMediaFileCss:
    def test_removes_css_link(self, injector):
        text = "before" + injector.get_chinese_css_file_ref("_chinese_reading_abc.css") + "after"
        result = injector.remove("chinese_css_file", text)
        assert "###CHINESE READING CSS FILE" not in result
        assert "before" in result
        assert "after" in result


class TestMediaFileJs:
    def test_injects_script_tag(self, injector):
        result = injector.inject("chinese_js_file", "", filename="_chinese_reading_abc.js")
        assert '<script src="_chinese_reading_abc.js">' in result
        assert "###CHINESE READING JS FILE" in result

    def test_replaces_different_js_file(self, injector):
        old = injector.inject("chinese_js_file", "", filename="_chinese_reading_abc.js")
        result = injector.inject("chinese_js_file", old, filename="_chinese_reading_def.js")
        assert "_chinese_reading_def.js" in result
        assert "_chinese_reading_abc.js" not in result


class TestRemoveMediaFileJs:
    def test_removes_script_tag(self, injector):
        text = "before" + injector.get_chinese_js_file_ref("_chinese_reading_abc.js") + "after"
        result = injector.remove("chinese_js_file", text)
        assert "###CHINESE READING JS FILE" not in result
        assert "before" in result
        assert "after" in result


# ── Error handling ──────────────────────────────────────────────


class TestInvalidComponent:
    def test_inject_raises(self, injector):
        with pytest.raises(ValueError, match="Unknown template component"):
            injector.inject("bogus", "text")

    def test_remove_raises(self, injector):
        with pytest.raises(ValueError, match="Unknown template component"):
            injector.remove("bogus", "text")


# ── newline_reduce ──────────────────────────────────────────────


class TestNewlineReduce:
    def test_reduces_triple(self):
        assert newline_reduce("a\n\n\nb") == "a\n\nb"

    def test_preserves_double(self):
        assert newline_reduce("a\n\nb") == "a\n\nb"

    def test_preserves_single(self):
        assert newline_reduce("a\nb") == "a\nb"
