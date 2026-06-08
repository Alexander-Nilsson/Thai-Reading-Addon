from characterManipulator import CharacterManipulator


def make_cm():
    return CharacterManipulator(None)


def test_separate_pinyin_two_syllables():
    cm = make_cm()
    result = cm.separatePinyin("zhōngwén")
    assert result == "zhōng wén"


def test_separate_pinyin_with_apostrophe():
    cm = make_cm()
    result = cm.separatePinyin("xī'ān")
    assert result == "xī ān"


def test_separate_pinyin_single_syllable():
    cm = make_cm()
    result = cm.separatePinyin("wǒ")
    assert result == "wǒ"


def test_separate_pinyin_with_tones():
    cm = make_cm()
    result = cm.separatePinyin("hǎo de")
    assert result == "hǎo de"


def test_separate_pinyin_standalone():
    cm = make_cm()
    result = cm.separatePinyin("Ào mén")
    assert result == "Ào mén"


def test_no_pinyin_input():
    cm = make_cm()
    result = cm.separatePinyin("abc")
    assert result == "abc"


def test_separate_pinyin_no_space_pairs():
    cm = make_cm()
    result = cm.separatePinyin("xuéxí hànyǔ")
    assert result == "xué xí hàn yǔ"
