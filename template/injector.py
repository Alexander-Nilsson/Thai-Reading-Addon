import json
import os
import re
from typing import Any

THAI_PARSER_HEADER = "<!--###THAI READING JS START###\nDo Not Edit If Using Automatic CSS and JS Management-->"
THAI_PARSER_FOOTER = "<!--###THAI READING JS ENDS###-->"

THAI_CSS_HEADER = "/*###THAI READING CSS STARTS###\nDo Not Edit If Using Automatic CSS and JS Management*/"
THAI_CSS_FOOTER = "/*###THAI READING CSS ENDS###*/"
THAI_CSS_PATTERN = (
    r"\/\*###THAI READING CSS STARTS###"
    "\n"
    r"Do Not Edit If Using Automatic CSS and JS Management\*\/"
    r"[^*]*?"
    r"\/\*###THAI READING CSS ENDS###\*\/"
)

THAI_JS_FILE_HEADER = "<!--###THAI READING JS FILE START###-->"
THAI_JS_FILE_FOOTER = "<!--###THAI READING JS FILE ENDS###-->"
THAI_JS_FILE_PATTERN = (
    r"<!--###THAI READING JS FILE START###-->\s*"
    r'<script src="([^"]+)"[^>]*>.*?</script>\s*'
    r"<!--###THAI READING JS FILE ENDS###-->"
)

_COMBINED_JS_TEMPLATE = """\
(function(){
var c=%(config)s;
var s=document.createElement('style');
var css='.unhovered-word .pinyin-ruby{visibility:hidden !important;}'+
'.pinyin-ruby{font-size:'+c.font_size+'%% !important;}';
var ts=c.thai_tones;
if(!ts.every(function(t){return t===ts[0]})){
ts.forEach(function(t,i){
var n='thTone'+(i+1);
css+='.'+n+'{color:'+t+';}'+
'.ankidroid_dark_mode .'+n+',.nightMode .'+n+'{color:'+t+';}';
});
}
s.textContent=css;
document.head.appendChild(s);
var THAI_READING_TYPE=c.reading_type;
%(parser)s
})();
"""


def newline_reduce(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _remove_block(text: str, header: str, footer: str) -> str:
    pattern = re.escape(header) + r".*?" + re.escape(footer)
    return re.sub(pattern, "", text, flags=re.DOTALL)


WRAPPER_REMOVE_RE = re.compile(
    r'<div reading-type="[^>]+?" display-type="[^>]+?" class="wrapped-thai">({{[^}]+?}})</div>'
)

COMPONENTS = frozenset(
    {
        "thai_css",
        "thai_js",
        "wrapper",
        "thai_js_file",
    }
)


class TemplateInjector:
    def __init__(self, js_dir: str):
        self._js_dir = js_dir
        self._js_cache: dict[str, str] = {}

    def _load_js(self, name: str) -> str:
        if name not in self._js_cache:
            path = os.path.join(self._js_dir, name)
            with open(path, encoding="utf-8") as f:
                self._js_cache[name] = f.read()
        return self._js_cache[name]

    def inject(self, component: str, template: str, **kwargs: Any) -> str:
        _validate_component(component)
        match component:
            case "thai_css":
                return self._inject_thai_css(template, **kwargs)
            case "thai_js":
                return self._inject_thai_js(template, **kwargs)
            case "wrapper":
                return self._inject_wrapper(template, **kwargs)
            case "thai_js_file":
                return self._inject_thai_js_file(template, **kwargs)
        raise AssertionError("unreachable")

    def remove(self, component: str, template: str) -> str:
        _validate_component(component)
        match component:
            case "thai_css":
                return self._remove_thai_css(template)
            case "thai_js":
                return self._remove_thai_js(template)
            case "wrapper":
                return self._remove_wrappers(template)
            case "thai_js_file":
                return self._remove_thai_js_file(template)
        raise AssertionError("unreachable")

    @staticmethod
    def overwrite_wrapper(template: str, field: str, display_type: str, reading_type: str = "default") -> str:
        return _overwrite_wrapper_element(template, field, display_type, reading_type)

    @staticmethod
    def get_thai_css(
        thai_tones: tuple[str, ...] | list[str],
        font_size: int,
    ) -> str:
        css = (
            ".unhovered-word .pinyin-ruby{visibility:hidden  !important;}"
            f".pinyin-ruby{{font-size:{font_size}% !important;}}"
        )
        all_same = len(set(thai_tones)) == 1
        if not all_same:
            count = 1
            for tone in thai_tones:
                css += (
                    f".thTone{count!s}{{color:{tone};}}"
                    f".ankidroid_dark_mode .thTone{count!s}, .nightMode .thTone{count!s}{{color:{tone};}}"
                )
                count += 1
        return THAI_CSS_HEADER + "\n" + css + "\n" + THAI_CSS_FOOTER

    def _inject_thai_css(self, style: str, **kwargs: Any) -> str:
        thai_tones = kwargs.get("thai_tones", ())
        font_size = kwargs.get("font_size", 75)
        new_block = self.get_thai_css(thai_tones, font_size)
        if not style:
            return new_block
        match = re.search(THAI_CSS_PATTERN, style)
        if match:
            if match.group() != new_block:
                return style.replace(match.group(), new_block)
            return style
        return style + "\n" + new_block

    def _remove_thai_css(self, style: str) -> str:
        return re.sub(THAI_CSS_PATTERN, "", style)

    def get_thai_js(self, reading_type: str) -> str:
        js = (
            '<script>(function(){const THAI_READING_TYPE ="'
            + reading_type
            + '";'
            + self._load_js("thaiparser.js")
            + "})();</script>"
        )
        return THAI_PARSER_HEADER + js + THAI_PARSER_FOOTER

    def get_bare_thai_js(self, reading_type: str) -> str:
        return '(function(){const THAI_READING_TYPE ="' + reading_type + '";' + self._load_js("thaiparser.js") + "})();"

    def get_combined_js(
        self,
        reading_type: str,
        thai_tones: tuple[str, ...] | list[str],
        font_size: int,
    ) -> str:
        config = json.dumps(
            {
                "reading_type": reading_type,
                "font_size": font_size,
                "thai_tones": list(thai_tones),
            }
        )
        return _COMBINED_JS_TEMPLATE % {
            "config": config,
            "parser": self._load_js("thaiparser.js"),
        }

    def _inject_thai_js(self, text: str, **kwargs: Any) -> str:
        reading_type = kwargs.get("reading_type", "rtgs")
        new_block = self.get_thai_js(reading_type)
        if not text:
            return new_block
        pattern = re.escape(THAI_PARSER_HEADER) + r".*?" + re.escape(THAI_PARSER_FOOTER)
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            if match.group() != new_block:
                return newline_reduce(re.sub(pattern, lambda _: new_block, text, flags=re.DOTALL))
            return text
        return newline_reduce(text + "\n" + new_block)

    def _remove_thai_js(self, text: str) -> str:
        return _remove_block(text, THAI_PARSER_HEADER, THAI_PARSER_FOOTER)

    @staticmethod
    def _inject_wrapper(text: str, **kwargs: Any) -> str:
        field = kwargs.get("field", "")
        display_type = kwargs.get("display_type", "hover")
        reading_type = kwargs.get("reading_type", "default")
        if not field:
            return text
        tmpl_ref = r"(?:{{(?:[^:}]+:)?)" + re.escape(field) + r"}}"
        repl = (
            '<div reading-type="' + reading_type + '" display-type="' + display_type + '" class="wrapped-thai">'
            "\\g<0>"
            "</div>"
        )
        pat = r'(?<!(?:class="wrapped-thai">))' + tmpl_ref
        return re.sub(pat, repl, text)

    @staticmethod
    def _remove_wrappers(text: str) -> str:
        return re.sub(WRAPPER_REMOVE_RE, r"\1", text)

    @staticmethod
    def get_thai_js_file_ref(filename: str) -> str:
        return THAI_JS_FILE_HEADER + '\n<script src="' + filename + '"></script>\n' + THAI_JS_FILE_FOOTER

    def _inject_thai_js_file(self, text: str, **kwargs: Any) -> str:
        filename = kwargs.get("filename", "")
        if not filename:
            return text
        new_block = self.get_thai_js_file_ref(filename)
        if not text:
            return new_block
        match = re.search(THAI_JS_FILE_PATTERN, text, flags=re.DOTALL)
        if match:
            if match.group() != new_block:
                return text.replace(match.group(), new_block)
            return text
        return text + "\n" + new_block

    def _remove_thai_js_file(self, text: str) -> str:
        return re.sub(THAI_JS_FILE_PATTERN, "", text, flags=re.DOTALL)


def _validate_component(component: str) -> None:
    if component not in COMPONENTS:
        msg = f"Unknown template component: {component!r}. Valid: {sorted(COMPONENTS)}"
        raise ValueError(msg)


def _overwrite_wrapper_element(text: str, field: str, display_type: str, reading_type: str = "default") -> str:
    pat = (
        r'<div reading-type="([^>]+?)" display-type="([^>]+?)" class="wrapped-thai">'
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
                + '" class="wrapped-thai">'
                + inner_ref
                + "</div>"
            )
            new = (
                '<div reading-type="'
                + reading_type
                + '" display-type="'
                + display_type
                + '" class="wrapped-thai">'
                + inner_ref
                + "</div>"
            )
            text = text.replace(old, new)
    return text
