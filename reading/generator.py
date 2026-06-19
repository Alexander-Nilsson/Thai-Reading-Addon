import re
import sys
from os.path import dirname, join
from typing import Any

sys.path.append(join(dirname(__file__), "..", "lib"))
from dragonmapper import transcriptions

HANZI_RANGE = re.compile(
    "[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df"
    "\U0002a700-\U0002b73f\U0002b740-\U0002b81f"
    "\U0002b820-\U0002ceaf\U0002ceb0-\U0002ebef"
    "\uf900-\ufaff\U0002f800-\U0002fa1f]"
)

TONE_TO_NUMBER: dict[str, str] = {"ˊ": "2", "ˇ": "3", "ˋ": "4", "˙": "5"}  # noqa: RUF001


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


def bopoToneToNumber(text: str, enabled: bool = True) -> str:
    if not enabled:
        return text
    last = text[-1:]
    if last in TONE_TO_NUMBER:
        text = text[:-1] + TONE_TO_NUMBER[last]
    else:
        text += "1"
    return text


def html_remove(text):
    pattern = re.compile(r"(?:<[^<]+?>)")
    finds = pattern.findall(text)
    text = pattern.sub("--=HTML=--", text)
    return finds, text


def replace_html(text, matches):
    if matches:
        for match in matches:
            text = text.replace("--=HTML=--", match, 1)
    return text


def clean_spaces(text):
    return text.replace("  ", "")


def _separate_pinyin_sub(p):
    def _clean(t):
        if "'" == t[0]:
            return t[1:]
        return t

    return _clean(p.group("one")) + " " + _clean(p.group("two"))


def separate_pinyin(text):
    return _PINYIN_RE.sub(_separate_pinyin_sub, text)


def strip_brackets(text, return_sounds=False, remove_audio=False):
    if "[" not in text and "]" not in text:
        return (text, []) if return_sounds else text
    matches, stripped = html_remove(text)
    if remove_audio:
        stripped = clean_spaces(stripped)
        stripped = replace_html(stripped, matches)
        return re.sub(r"\[[^]]*?\]", "", stripped)
    audio_pattern = r"(?:\[sound:[^\]]+?\])|(?:\[\d*\])"
    finds = re.findall(audio_pattern, stripped)
    stripped = re.sub(audio_pattern, "-_-AUDIO-_-", stripped)
    stripped = re.sub(r"\[[^]]*?\]", "", stripped)
    stripped = clean_spaces(stripped)
    stripped = replace_html(stripped, matches)
    for match in finds:
        stripped = stripped.replace("-_-AUDIO-_-", match, 1)
    return (stripped, finds) if return_sounds else stripped


class ReadingGenerator:
    def __init__(self, db: Any, config: Any) -> None:
        self._db = db
        self._config = config

    def generate(self, text: str, reading_type: str | None = None) -> str:
        reading_type = reading_type or self._config.reading_type
        if reading_type not in ("pinyin", "bopomofo", "jyutping"):
            return text
        return self._segment_and_lookup(text, reading_type)

    def _segment_and_lookup(self, text: str, rType: str) -> str:
        text = strip_brackets(text)
        finished = False
        newStr = ""
        count = 0
        while not finished:
            if re.search(HANZI_RANGE, text[count]):
                word = text[count]
                lookahead = 10
                limit = count + lookahead
                count += 1
                while count < len(text) and count < limit and re.search(HANZI_RANGE, text[count]):
                    word += text[count]
                    count += 1
                result = False
                while not result and len(word) > 0:
                    if rType == "jyutping":
                        result = self._db.getJyutping(word)
                    else:
                        result = self._db.getAltFayin(word)
                    if not result:
                        count -= 1
                        word = word[:-1]
                if result:
                    if rType == "jyutping":
                        results = result[0][0].split(" ")
                    else:
                        results = separate_pinyin(result[0][0]).split(" ")
                        for idx, fayin in enumerate(results):
                            if rType == "bopomofo":
                                results[idx] = bopoToneToNumber(
                                    transcriptions.pinyin_to_zhuyin(fayin),
                                    self._config.bopomofo_tones_to_number,
                                )
                    newStr += word + "[" + " ".join(results).lower() + "]"
                else:
                    newStr += text[count]
                    count += 1
            else:
                newStr += text[count]
                count += 1
            if count == len(text):
                finished = True
        return newStr
