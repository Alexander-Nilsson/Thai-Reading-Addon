import re
from typing import Any

from .js_registry import JsRegistry

# ── Marker constants ───────────────────────────────────────────

CHINESE_PARSER_HEADER = "<!--###CHINESE READING JS START###\nDo Not Edit If Using Automatic CSS and JS Management-->"
CHINESE_PARSER_FOOTER = "<!--###CHINESE READING JS ENDS###-->"

CHINESE_CSS_HEADER = "/*###CHINESE READING CSS STARTS###\nDo Not Edit If Using Automatic CSS and JS Management*/"
CHINESE_CSS_FOOTER = "/*###CHINESE READING CSS ENDS###*/"
CHINESE_CSS_PATTERN = (
    r"\/\*###CHINESE READING CSS STARTS###"
    "\n"
    r"Do Not Edit If Using Automatic CSS and JS Management\*\/"
    r"[^*]*?"
    r"\/\*###CHINESE READING CSS ENDS###\*\/"
)

HANZI_CONVERTER_HEADER = (
    "<!--###CHINESE READING CONVERTER JS START###\nDo Not Edit If Using Automatic CSS and JS Management-->"
)
HANZI_CONVERTER_FOOTER = "<!--###CHINESE READING CONVERTER JS ENDS###-->"

PINBOPO_CONVERTER_HEADER = (
    "<!--###CHINESE READING PINYIN BOPOMOFO CONVERTER JS START###\n"
    "Do Not Edit If Using Automatic CSS and JS Management-->"
)
PINBOPO_CONVERTER_FOOTER = "<!--###CHINESE READING PINYIN BOPOMOFO CONVERTER JS ENDS###-->"

# ── Media file markers ─────────────────────────────────────────

CHINESE_CSS_FILE_HEADER = "<!--###CHINESE READING CSS FILE START###-->"
CHINESE_CSS_FILE_FOOTER = "<!--###CHINESE READING CSS FILE ENDS###-->"
CHINESE_CSS_FILE_PATTERN = (
    r"<!--###CHINESE READING CSS FILE START###-->\s*"
    r'<link rel="stylesheet" href="([^"]+)"[^>]*>\s*'
    r"<!--###CHINESE READING CSS FILE ENDS###-->"
)

CHINESE_JS_FILE_HEADER = "<!--###CHINESE READING JS FILE START###-->"
CHINESE_JS_FILE_FOOTER = "<!--###CHINESE READING JS FILE ENDS###-->"
CHINESE_JS_FILE_PATTERN = (
    r"<!--###CHINESE READING JS FILE START###-->\s*"
    r'<script src="([^"]+)"[^>]*>.*?</script>\s*'
    r"<!--###CHINESE READING JS FILE ENDS###-->"
)


# ── Helpers ─────────────────────────────────────────────────────


def newline_reduce(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _remove_block(text: str, header: str, footer: str) -> str:
    pattern = re.escape(header) + r".*?" + re.escape(footer)
    return re.sub(pattern, "", text, flags=re.DOTALL)


# ── TemplateInjector ────────────────────────────────────────────

WRAPPER_REMOVE_RE = re.compile(
    r'<div reading-type="[^>]+?" display-type="[^>]+?" class="wrapped-chinese">({{[^}]+?}})</div>'
)

COMPONENTS = frozenset(
    {
        "chinese_css",
        "chinese_js",
        "wrapper",
        "hanzi_converter",
        "pinyin_bopomo_converter",
        "chinese_css_file",
        "chinese_js_file",
    }
)


class TemplateInjector:
    def __init__(self, js_registry: JsRegistry):
        self._js = js_registry

    # ── Public API ──────────────────────────────────────────

    def inject(self, component: str, template: str, **kwargs: Any) -> str:
        _validate_component(component)
        match component:
            case "chinese_css":
                return self._inject_chinese_css(template, **kwargs)
            case "chinese_js":
                return self._inject_chinese_js(template, **kwargs)
            case "wrapper":
                return self._inject_wrapper(template, **kwargs)
            case "hanzi_converter":
                return self._inject_hanzi_converter(template, **kwargs)
            case "pinyin_bopomo_converter":
                return self._inject_pinbopo_converter(template, **kwargs)
            case "chinese_css_file":
                return self._inject_chinese_css_file(template, **kwargs)
            case "chinese_js_file":
                return self._inject_chinese_js_file(template, **kwargs)
        raise AssertionError("unreachable")

    def remove(self, component: str, template: str) -> str:
        _validate_component(component)
        match component:
            case "chinese_css":
                return self._remove_chinese_css(template)
            case "chinese_js":
                return self._remove_chinese_js(template)
            case "wrapper":
                return self._remove_wrappers(template)
            case "hanzi_converter":
                return self._remove_hanzi_converter(template)
            case "pinyin_bopomo_converter":
                return self._remove_pinbopo_converter(template)
            case "chinese_css_file":
                return self._remove_chinese_css_file(template)
            case "chinese_js_file":
                return self._remove_chinese_js_file(template)
        raise AssertionError("unreachable")

    @staticmethod
    def overwrite_wrapper(template: str, field: str, display_type: str, reading_type: str = "default") -> str:
        return _overwrite_wrapper_element(template, field, display_type, reading_type)

    # ── CSS ────────────────────────────────────────────────

    @staticmethod
    def get_chinese_css(
        mandarin_tones: tuple[str, ...] | list[str],
        cantonese_tones: tuple[str, ...] | list[str],
        font_size: int,
    ) -> str:
        css = (
            ".unhovered-word .pinyin-ruby{visibility:hidden  !important;}"
            f".pinyin-ruby{{font-size:{font_size}% !important;}}"
        )
        all_mandarin_same = len(set(mandarin_tones)) == 1
        all_cantonese_same = len(set(cantonese_tones)) == 1
        if not (all_mandarin_same and all_cantonese_same):
            count = 1
            for tone in mandarin_tones:
                css += (
                    f".tone{count!s}{{color:{tone};}}"
                    f".ankidroid_dark_mode .tone{count!s}, .nightMode .tone{count!s}{{color:{tone};}}"
                )
                count += 1
            count = 1
            for tone in cantonese_tones:
                css += (
                    f".canTone{count!s}{{color:{tone};}}"
                    f".ankidroid_dark_mode .canTone{count!s}, .nightMode .canTone{count!s}{{color:{tone};}}"
                )
                count += 1
        return CHINESE_CSS_HEADER + "\n" + css + "\n" + CHINESE_CSS_FOOTER

    def _inject_chinese_css(self, style: str, **kwargs: Any) -> str:
        mandarin_tones = kwargs.get("mandarin_tones", ())
        cantonese_tones = kwargs.get("cantonese_tones", ())
        font_size = kwargs.get("font_size", 75)
        new_block = self.get_chinese_css(mandarin_tones, cantonese_tones, font_size)
        if not style:
            return new_block
        match = re.search(CHINESE_CSS_PATTERN, style)
        if match:
            if match.group() != new_block:
                return style.replace(match.group(), new_block)
            return style
        return style + "\n" + new_block

    def _remove_chinese_css(self, style: str) -> str:
        return re.sub(CHINESE_CSS_PATTERN, "", style)

    # ── Chinese JS ─────────────────────────────────────────

    def get_chinese_js(self, reading_type: str) -> str:
        js = (
            '<script>(function(){const CHINESE_READING_TYPE ="'
            + reading_type
            + '";'
            + self._js.load("chineseparser.js")
            + "})();</script>"
        )
        return CHINESE_PARSER_HEADER + js + CHINESE_PARSER_FOOTER

    def get_bare_chinese_js(self, reading_type: str) -> str:
        """Returns pure JS (no HTML wrappers) suitable for writing to a .js file."""
        return (
            '(function(){const CHINESE_READING_TYPE ="'
            + reading_type
            + '";'
            + self._js.load("chineseparser.js")
            + "})();"
        )

    def _inject_chinese_js(self, text: str, **kwargs: Any) -> str:
        reading_type = kwargs.get("reading_type", "pinyin")
        new_block = self.get_chinese_js(reading_type)
        if not text:
            return new_block
        pattern = re.escape(CHINESE_PARSER_HEADER) + r".*?" + re.escape(CHINESE_PARSER_FOOTER)
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            if match.group() != new_block:
                return newline_reduce(re.sub(pattern, lambda _: new_block, text, flags=re.DOTALL))
            return text
        return newline_reduce(text + "\n" + new_block)

    def _remove_chinese_js(self, text: str) -> str:
        return _remove_block(text, CHINESE_PARSER_HEADER, CHINESE_PARSER_FOOTER)

    # ── Wrappers ───────────────────────────────────────────

    @staticmethod
    def _inject_wrapper(text: str, **kwargs: Any) -> str:
        field = kwargs.get("field", "")
        display_type = kwargs.get("display_type", "hover")
        reading_type = kwargs.get("reading_type", "default")
        if not field:
            return text
        # Match {{FieldName}} or {{filter:FieldName}} — anywhere a filter prefix may appear
        tmpl_ref = r"(?:{{(?:[^:}]+:)?)" + re.escape(field) + r"}}"
        repl = (
            '<div reading-type="' + reading_type + '" display-type="' + display_type + '" class="wrapped-chinese">'
            "\\g<0>"
            "</div>"
        )
        # Negative lookbehind prevents double-wrapping an already-wrapped field
        pat = r'(?<!(?:class="wrapped-chinese">))' + tmpl_ref
        return re.sub(pat, repl, text)

    @staticmethod
    def _remove_wrappers(text: str) -> str:
        return re.sub(WRAPPER_REMOVE_RE, r"\1", text)

    # ── Hanzi converter JS ─────────────────────────────────

    def get_hanzi_converter_js(self, conversion_type: str) -> str:
        js = (
            '<script>const CHINESE_CONVERSION_TYPE ="'
            + conversion_type.lower()
            + '";'
            + self._js.load("tongwen_core.js")
            + self._js.load("tongwen_table_ps2t.js")
            + self._js.load("tongwen_table_pt2s.js")
            + self._js.load("tongwen_table_s2t.js")
            + self._js.load("tongwen_table_ss2t.js")
            + self._js.load("tongwen_table_st2s.js")
            + self._js.load("tongwen_table_t2s.js")
            + '"simplified"===CHINESE_CONVERSION_TYPE'
            "?TongWen.trans2Simp(document)"
            ':"traditional"===CHINESE_CONVERSION_TYPE&&TongWen.trans2Trad(document);</script>'
        )
        return HANZI_CONVERTER_HEADER + js + HANZI_CONVERTER_FOOTER

    def _inject_hanzi_converter(self, text: str, **kwargs: Any) -> str:
        conversion_type = kwargs.get("conversion_type", "None")
        if conversion_type == "None" or conversion_type not in ("Simplified", "Traditional"):
            return self._remove_hanzi_converter(text)
        text = self._remove_hanzi_converter(text)
        js = self.get_hanzi_converter_js(conversion_type)
        return newline_reduce(text + "\n\n" + js)

    def _remove_hanzi_converter(self, text: str) -> str:
        return _remove_block(text, HANZI_CONVERTER_HEADER, HANZI_CONVERTER_FOOTER)

    # ── Pinyin/Bopomofo converter JS ───────────────────────

    def get_pinbopo_converter_js(self, reading_conversion: str) -> str:
        js_src = (
            self._js.load("bopoToPinyin.js") if reading_conversion == "Pinyin" else self._js.load("pinyinToBopo.js")
        )
        return PINBOPO_CONVERTER_HEADER + "<script>" + js_src + "</script>" + PINBOPO_CONVERTER_FOOTER

    def _inject_pinbopo_converter(self, text: str, **kwargs: Any) -> str:
        reading_conversion = kwargs.get("reading_conversion", "None")
        if reading_conversion == "None" or reading_conversion not in ("Pinyin", "Bopomofo"):
            return self._remove_pinbopo_converter(text)
        text = self._remove_pinbopo_converter(text)
        js = self.get_pinbopo_converter_js(reading_conversion)
        if CHINESE_PARSER_HEADER in text:
            return text.replace(CHINESE_PARSER_HEADER, js + "\n\n" + CHINESE_PARSER_HEADER)
        return newline_reduce(text) + "\n\n" + js

    def _remove_pinbopo_converter(self, text: str) -> str:
        return _remove_block(text, PINBOPO_CONVERTER_HEADER, PINBOPO_CONVERTER_FOOTER)

    # ── Media file references ────────────────────────────────

    @staticmethod
    def get_chinese_css_file_ref(filename: str) -> str:
        return CHINESE_CSS_FILE_HEADER + '\n<link rel="stylesheet" href="' + filename + '">\n' + CHINESE_CSS_FILE_FOOTER

    @staticmethod
    def get_chinese_js_file_ref(filename: str) -> str:
        return CHINESE_JS_FILE_HEADER + '\n<script src="' + filename + '"></script>\n' + CHINESE_JS_FILE_FOOTER

    def _inject_chinese_css_file(self, text: str, **kwargs: Any) -> str:
        filename = kwargs.get("filename", "")
        if not filename:
            return text
        new_block = self.get_chinese_css_file_ref(filename)
        if not text:
            return new_block
        match = re.search(CHINESE_CSS_FILE_PATTERN, text, flags=re.DOTALL)
        if match:
            if match.group() != new_block:
                return text.replace(match.group(), new_block)
            return text
        return text + "\n" + new_block

    def _remove_chinese_css_file(self, text: str) -> str:
        return re.sub(CHINESE_CSS_FILE_PATTERN, "", text, flags=re.DOTALL)

    def _inject_chinese_js_file(self, text: str, **kwargs: Any) -> str:
        filename = kwargs.get("filename", "")
        if not filename:
            return text
        new_block = self.get_chinese_js_file_ref(filename)
        if not text:
            return new_block
        match = re.search(CHINESE_JS_FILE_PATTERN, text, flags=re.DOTALL)
        if match:
            if match.group() != new_block:
                return text.replace(match.group(), new_block)
            return text
        return text + "\n" + new_block

    def _remove_chinese_js_file(self, text: str) -> str:
        return re.sub(CHINESE_JS_FILE_PATTERN, "", text, flags=re.DOTALL)


# ── Module-level helpers ────────────────────────────────────────


def _validate_component(component: str) -> None:
    if component not in COMPONENTS:
        msg = f"Unknown template component: {component!r}. Valid: {sorted(COMPONENTS)}"
        raise ValueError(msg)


def _overwrite_wrapper_element(text: str, field: str, display_type: str, reading_type: str = "default") -> str:
    pat = (
        r'<div reading-type="([^>]+?)" display-type="([^>]+?)" class="wrapped-chinese">'
        r"({{(?:[^:}]+:)?" + re.escape(field) + r"}})"
        r"</div>"
    )
    for old_reading, old_display, inner_ref in re.findall(pat, text):
        if display_type.lower() != old_display.lower() or reading_type.lower() != old_reading.lower():
            old = (
                '<div reading-type="'
                + old_reading
                + '" display-type="'
                + old_display
                + '" class="wrapped-chinese">'
                + inner_ref
                + "</div>"
            )
            new = (
                '<div reading-type="'
                + reading_type
                + '" display-type="'
                + display_type
                + '" class="wrapped-chinese">'
                + inner_ref
                + "</div>"
            )
            text = text.replace(old, new)
    return text
