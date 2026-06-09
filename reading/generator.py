import re
from typing import Any

from . import text_utils
from .text_utils import strip_brackets

HANZI_RANGE = re.compile(
    "[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df"
    "\U0002a700-\U0002b73f\U0002b740-\U0002b81f"
    "\U0002b820-\U0002ceaf\U0002ceb0-\U0002ebef"
    "\uf900-\ufaff\U0002f800-\U0002fa1f]"
)

TONE_TO_NUMBER: dict[str, str] = {"ˊ": "2", "ˇ": "3", "ˋ": "4", "˙": "5"}  # noqa: RUF001


def bopoToneToNumber(text: str, enabled: bool = True) -> str:
    if not enabled:
        return text
    last = text[-1:]
    if last in TONE_TO_NUMBER:
        text = text[:-1] + TONE_TO_NUMBER[last]
    else:
        text += "1"
    return text


def _strip_reading_brackets(text: str) -> str:
    return strip_brackets(text)


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
        text = _strip_reading_brackets(text)
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
                        results = text_utils.separate_pinyin(result[0][0]).split(" ")
                        for idx, fayin in enumerate(results):
                            if rType == "bopomofo":
                                from dragonmapper import transcriptions

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
