import os

import pytest

from template.injector import (
    THAI_CSS_HEADER,
    THAI_PARSER_HEADER,
    TemplateInjector,
    newline_reduce,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def injector():
    return TemplateInjector(os.path.join(ROOT, "js"))


THAI_TONES = ("#E60000", "#E68A00", "#00802B", "#005CE6", "gray")


# ── CSS ─────────────────────────────────────────────────────────


class TestGetThaiCss:
    def test_contains_tone_classes(self, injector):
        css = injector.get_thai_css(THAI_TONES, 75)
        assert ".thTone1" in css
        assert ".thTone5" in css

    def test_contains_header_and_footer(self, injector):
        css = injector.get_thai_css(THAI_TONES, 75)
        assert "###THAI READING CSS STARTS###" in css
        assert "###THAI READING CSS ENDS###" in css

    def test_custom_font_size(self, injector):
        css = injector.get_thai_css(THAI_TONES, 100)
        assert "font-size:100%" in css

    def test_hover_classes(self, injector):
        css = injector.get_thai_css(THAI_TONES, 75)
        assert ".unhovered-word .pinyin-ruby" in css
        assert ".thTone1" in css

    def test_skips_tone_rules_when_all_same_color(self, injector):
        uniform = ["gray", "gray", "gray", "gray", "gray"]
        css = injector.get_thai_css(uniform, 75)
        assert ".thTone1" not in css
        assert "font-size:75%" in css

    def test_emits_tone_rules_when_colors_differ(self, injector):
        mixed = ["red", "gray", "gray", "gray", "gray"]
        css = injector.get_thai_css(mixed, 75)
        assert ".thTone1{color:red;" in css
        assert ".thTone2{color:gray;" in css


class TestInjectThaiCss:
    def test_adds_to_empty(self, injector):
        result = injector.inject("thai_css", "", thai_tones=THAI_TONES)
        assert THAI_CSS_HEADER in result

    def test_adds_to_existing_style(self, injector):
        result = injector.inject("thai_css", "body { color: black; }", thai_tones=THAI_TONES)
        assert "body { color: black; }" in result
        assert THAI_CSS_HEADER in result

    def test_replaces_different_block(self, injector):
        old_css = injector.get_thai_css(THAI_TONES, 75)
        result = injector.inject("thai_css", old_css, thai_tones=THAI_TONES, font_size=100)
        assert "font-size:100%" in result

    def test_no_change_when_same(self, injector):
        old_css = injector.get_thai_css(THAI_TONES, 75)
        result = injector.inject("thai_css", old_css, thai_tones=THAI_TONES, font_size=75)
        assert result == old_css


class TestRemoveThaiCss:
    def test_removes_block(self, injector):
        css = "before" + injector.get_thai_css(THAI_TONES, 75) + "after"
        result = injector.remove("thai_css", css)
        assert THAI_CSS_HEADER not in result
        assert "before" in result
        assert "after" in result


# ── Thai JS ──────────────────────────────────────────────────


class TestInjectThaiJs:
    def test_adds_to_empty(self, injector):
        result = injector.inject("thai_js", "", reading_type="rtgs")
        assert THAI_PARSER_HEADER in result

    def test_replaces_different(self, injector):
        old = injector.inject("thai_js", "", reading_type="rtgs")
        result = injector.inject("thai_js", old, reading_type="ipa")
        assert 'THAI_READING_TYPE ="ipa"' in result

    def test_no_change_when_same(self, injector):
        old = injector.inject("thai_js", "prefix", reading_type="ipa")
        result = injector.inject("thai_js", old, reading_type="ipa")
        assert result == old


class TestRemoveThaiJs:
    def test_removes_block(self, injector):
        text = "before" + injector.get_thai_js("rtgs") + "after"
        result = injector.remove("thai_js", text)
        assert THAI_PARSER_HEADER not in result
        assert "before" in result
        assert "after" in result


# ── Wrappers ────────────────────────────────────────────────────


class TestInjectWrapper:
    def test_injects_around_field(self, injector):
        text = "some text {{MyField}} more text"
        result = injector.inject("wrapper", text, field="MyField", display_type="hover", reading_type="rtgs")
        assert 'class="wrapped-thai"' in result
        assert 'display-type="hover"' in result
        assert 'reading-type="rtgs"' in result

    def test_no_double_wrap(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{MyField}}</div>'
        result = injector.inject("wrapper", text, field="MyField", display_type="hover", reading_type="rtgs")
        assert result == text

    def test_injects_around_edit_filtered_field(self, injector):
        text = "some text {{edit:Expression}} more text"
        result = injector.inject("wrapper", text, field="Expression", display_type="hover", reading_type="rtgs")
        assert 'class="wrapped-thai"' in result
        assert "{{edit:Expression}}" in result

    def test_injects_around_text_filtered_field(self, injector):
        text = "{{text:Front}} and {{text:Back}}"
        result = injector.inject("wrapper", text, field="Front", display_type="hover", reading_type="rtgs")
        assert "{{text:Front}}" in result
        assert "wrapped-thai" in result

    def test_preserves_filter_when_injecting(self, injector):
        text = "prefix {{edit:Expression}} suffix"
        result = injector.inject("wrapper", text, field="Expression", display_type="hover", reading_type="rtgs")
        assert "{{edit:Expression}}" in result


class TestRemoveWrappers:
    def test_removes_single(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{MyField}}</div>'
        result = injector.remove("wrapper", text)
        assert result == "{{MyField}}"

    def test_removes_multiple(self, injector):
        text = (
            '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{F1}}</div>'
            " and "
            '<div reading-type="ipa" display-type="color" class="wrapped-thai">{{F2}}</div>'
        )
        result = injector.remove("wrapper", text)
        assert result == "{{F1}} and {{F2}}"

    def test_preserves_plain_text(self, injector):
        assert injector.remove("wrapper", "no wrappers") == "no wrappers"

    def test_removes_wrapper_around_filtered_field(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{edit:Expression}}</div>'
        result = injector.remove("wrapper", text)
        assert result == "{{edit:Expression}}"

    def test_removes_wrapper_with_text_filter(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{text:Front}}</div>'
        result = injector.remove("wrapper", text)
        assert result == "{{text:Front}}"


class TestOverwriteWrapper:
    def test_changes_display_type(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{MyField}}</div>'
        result = injector.overwrite_wrapper(text, "MyField", "coloredhover", "rtgs")
        assert 'display-type="coloredhover"' in result

    def test_changes_reading_type(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{MyField}}</div>'
        result = injector.overwrite_wrapper(text, "MyField", "hover", "ipa")
        assert 'reading-type="ipa"' in result

    def test_no_change_when_same(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{MyField}}</div>'
        result = injector.overwrite_wrapper(text, "MyField", "hover", "rtgs")
        assert result == text

    def test_overwrites_wrapper_with_edit_filter(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{edit:Expression}}</div>'
        result = injector.overwrite_wrapper(text, "Expression", "coloredhover", "ipa")
        assert 'display-type="coloredhover"' in result
        assert 'reading-type="ipa"' in result
        assert "{{edit:Expression}}" in result

    def test_overwrites_wrapper_with_text_filter(self, injector):
        text = '<div reading-type="rtgs" display-type="hover" class="wrapped-thai">{{text:Front}}</div>'
        result = injector.overwrite_wrapper(text, "Front", "hover", "ipa")
        assert 'reading-type="ipa"' in result
        assert "{{text:Front}}" in result


# ── Media file references ───────────────────────────────────────


class TestMediaFileCss:
    def test_injects_css_link(self, injector):
        result = injector.inject("thai_js_file", "", filename="_thai_reading_abc.js")
        assert '<script src="_thai_reading_abc.js">' in result
        assert "###THAI READING JS FILE" in result

    def test_replaces_different_filename(self, injector):
        old = injector.inject("thai_js_file", "", filename="_thai_reading_abc.js")
        result = injector.inject("thai_js_file", old, filename="_thai_reading_def.js")
        assert "_thai_reading_def.js" in result
        assert "_thai_reading_abc.js" not in result

    def test_no_change_when_same(self, injector):
        old = injector.inject("thai_js_file", "prefix", filename="_thai_reading_abc.js")
        result = injector.inject("thai_js_file", old, filename="_thai_reading_abc.js")
        assert result == old


class TestRemoveMediaFileJs:
    def test_removes_script_tag(self, injector):
        text = "before" + injector.get_thai_js_file_ref("_thai_reading_abc.js") + "after"
        result = injector.remove("thai_js_file", text)
        assert "###THAI READING JS FILE" not in result
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
