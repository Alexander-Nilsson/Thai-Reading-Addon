import re


def html_remove(text):
    pattern = r"(?:<[^<]+?>)"
    finds = re.findall(pattern, text)
    text = re.sub(r"<[^<]+?>", "--=HTML=--", text)
    return finds, text


def replace_html(text, matches):
    if matches:
        for match in matches:
            text = text.replace("--=HTML=--", match, 1)
    return text


def clean_spaces(text):
    return text.replace("  ", "")


def _pinyin_re_sub():
    inits = "zh|sh|ch|[bpmfdtnlgkhjqxrzscwy]"
    finals = (
        "i[ōóǒòo]ng|[ūúǔùu]ng|[āáǎàa]ng|[ēéěèe]ng|"
        "i[āɑ̄áɑ́ɑ́ǎɑ̌àɑ̀aāáǎàa]ng|"  # noqa: RUF001
        "[īíǐìi]ng|"
        "i[āáǎàa]n|u[āáǎàa]n|[ōóǒòo]ng|[ēéěèe]r|"
        "i[āáǎàa]|i[ēéěèe]|i[āáǎàa]o|i[ūúǔùu]|"
        "[īíǐìi]n|u[āáǎàa]|u[ōóǒòo]|u[āáǎàa]i|u[īíǐìi]|"
        "[ūúǔùu]n|u[ēéěèe]|ü[ēéěèe]|v[ēéěèe]|i[ōóǒòo]|"
        "[āáǎàa]i|[ēéěèe]i|[āáǎàa]o|[ōóǒòo]u|"
        "[āáǎàa]n|[ēéěèe]n|[āáǎàa]|[ēéěèe]|"
        "[ōóǒòo]|[īíǐìi]|[ūúǔùu]|[ǖǘǚǜüv]"
    )
    standalones = (
        "'[āáǎàa]ng|'[ēéěèe]ng|'[ēéěèe]r|'[āáǎàa]i|"
        "'[ēéěèe]i|'[āáǎàa]o|'[ōóǒòo]u|'[āáǎàa]n|"
        "'[ēéěèe]n|'[āáǎàa]|'[ēéěèe]|'[ōóǒòo]"
    )
    return "((" + inits + ")(" + finals + ")[1-5]?|(" + standalones + ")[1-5]?)"


_PINYIN_RE = re.compile(
    "(?P<one>" + _pinyin_re_sub() + ")(?P<two>" + _pinyin_re_sub() + ")",
    flags=re.I,
)


def separate_pinyin(text):
    def _clean(t):
        if "'" == t[0]:
            return t[1:]
        return t

    def _separate_pinyin_sub(p):
        return _clean(p.group("one")) + " " + _clean(p.group("two"))

    return _PINYIN_RE.sub(_separate_pinyin_sub, text)
