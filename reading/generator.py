import re

THAI_RANGE = re.compile("[\u0e00-\u0e7f]")


def strip_brackets(text, return_sounds=False, remove_audio=False):
    if "[" not in text and "]" not in text:
        return (text, []) if return_sounds else text

    audio_pattern = r"(?:\[sound:[^\]]+?\])|(?:\[\d*\])"
    finds = re.findall(audio_pattern, text)
    stripped = re.sub(audio_pattern, "-_-AUDIO-_-", text)
    stripped = re.sub(r"\[[^]]*?\]", "", stripped)
    stripped = stripped.replace("  ", "")
    for match in finds:
        stripped = stripped.replace("-_-AUDIO-_-", match, 1)
    return (stripped, finds) if return_sounds else stripped


class ReadingGenerator:
    def __init__(self, db, config):
        self._db = db
        self._config = config

    def generate(self, text, reading_type=None):
        reading_type = reading_type or self._config.reading_type
        if reading_type not in ("rtgs", "ipa", "phonetics"):
            return text
        return self._segment_and_lookup(text, reading_type)

    def _segment_and_lookup(self, text, rType):
        text = strip_brackets(text)
        finished = False
        newStr = ""
        count = 0
        while not finished:
            if re.search(THAI_RANGE, text[count]):
                word = text[count]
                lookahead = 10
                limit = count + lookahead
                count += 1
                while count < len(text) and count < limit and re.search(THAI_RANGE, text[count]):
                    word += text[count]
                    count += 1
                result = None
                while not result and len(word) > 0:
                    result = self._db.get_reading(word)
                    if not result:
                        count -= 1
                        word = word[:-1]
                if result:
                    if rType == "phonetics":
                        phon = self._db.get_reading_phonetics(word)
                        if phon:
                            reading, _tone_pattern = phon
                        else:
                            reading, _tone_pattern = result
                    else:
                        reading, _tone_pattern = result
                    newStr += word + "[" + reading + "]"
                else:
                    newStr += text[count]
                    count += 1
            else:
                newStr += text[count]
                count += 1
            if count == len(text):
                finished = True
        return newStr
