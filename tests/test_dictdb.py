import os

import pytest

from reading.dictdb import DictDB


@pytest.fixture
def real_db():
    d = DictDB(os.path.dirname(os.path.dirname(__file__)))
    yield d
    d.closeConnection()


class TestGetAltFayin:
    def test_returns_pinyin_for_simplified(self, test_db):
        result = test_db.getAltFayin("一")
        assert result is not None
        assert len(result) > 0
        assert result[0][0] == "yī"

    def test_returns_pinyin_for_traditional(self, test_db):
        result = test_db.getAltFayin("在")
        assert result is not None
        assert result[0][0] == "zài"

    def test_returns_empty_for_missing(self, test_db):
        result = test_db.getAltFayin("XYZNOTACHAR")
        assert result is None

    def test_real_db_lookup(self, real_db):
        result = real_db.getAltFayin("一")
        assert result is not None


class TestGetFayin:
    def test_returns_pinyin_from_cidian(self, test_db):
        result = test_db.getFayin("中国")
        assert result is not None
        assert result[0][0] == "zhōng guó"

    def test_returns_empty_for_missing(self, test_db):
        result = test_db.getFayin("NOTAWORD")
        assert result is None


class TestGetJyutping:
    def test_returns_jyutping_for_simplified(self, test_db):
        result = test_db.getJyutping("中国")
        assert result is not None
        assert result[0][0] == "zung1 gwok3"

    def test_returns_jyutping_for_traditional(self, test_db):
        result = test_db.getJyutping("中國")
        assert result is not None
        assert result[0][0] == "zung1 gwok3"

    def test_returns_empty_for_missing(self, test_db):
        result = test_db.getJyutping("NOTAWORD")
        assert result is None

    def test_real_db_lookup(self, real_db):
        result = real_db.getJyutping("你好")
        assert result is not None


class TestGetSimplified:
    def test_single_char_from_unihan(self, test_db):
        result = test_db.get_simplified("國")
        assert result == "国"

    def test_word_from_cidian(self, test_db):
        result = test_db.get_simplified("中國")
        assert result == "中国"

    def test_already_simplified(self, test_db):
        result = test_db.get_simplified("中国")
        assert result == "中国"

    def test_mixed_string(self, test_db):
        result = test_db.get_simplified("中國學生")
        assert result == "中国学生"

    def test_unknown_single_char_returns_none(self, test_db):
        result = test_db.get_simplified("A")
        assert result is None

    def test_multi_char_unknown_passes_through(self, test_db):
        result = test_db.get_simplified("AB")
        assert result == "AB"

    def test_real_db_lookup(self, real_db):
        result = real_db.get_simplified("國")
        assert result == "国"


class TestGetTraditional:
    def test_single_char_from_unihan(self, test_db):
        result = test_db.get_traditional("学")
        assert result == "學"

    def test_word_from_cidian(self, test_db):
        result = test_db.get_traditional("学生")
        assert result == "學生"

    def test_already_traditional(self, test_db):
        result = test_db.get_traditional("中國")
        assert result == "中國"

    def test_real_db_lookup(self, real_db):
        result = real_db.get_traditional("中国")
        assert result == "中國"


class TestGetAllAltFayin:
    def test_returns_all_entries(self, test_db):
        result = test_db.getAllAltFayin()
        assert result is not False
        assert len(result) >= 2

    def test_real_db_returns_data(self, real_db):
        result = real_db.getAllAltFayin()
        assert result is not False


class TestPushAndCommit:
    def test_push_cantonese(self, test_db):
        test_db.pushCantonese("測試", "测试", "cak1 si3", "ce4 shi4")
        test_db.commitChanges()
        result = test_db.getJyutping("测试")
        assert result is not False
        assert result[0][0] == "cak1 si3"

    def test_push_to_alt_dict(self, test_db):
        test_db.pushToAltDict("測", "测", "cè")
        test_db.commitChanges()
        result = test_db.getAltFayin("测")
        assert result is not False
        assert result[0][0] == "cè"


class TestCharLookup:
    def test_get_char_pinyin(self, test_db):
        result = test_db._get_char_pinyin("中")
        assert result == "zhōng"

    def test_get_char_pinyin_missing(self, test_db):
        result = test_db._get_char_pinyin(" braking ")
        assert result is None

    def test_get_word_pinyin(self, test_db):
        result = test_db._get_word_pinyin("中国")
        assert result == "zhōng guó"

    def test_get_word_pinyin_taiwan(self, test_db):
        result = test_db._get_word_pinyin("中国", taiwan=True)
        assert result == "zhōng guó"

    def test_get_char_traditional(self, test_db):
        result = test_db._get_char_traditional("学")
        assert result == "學"

    def test_get_char_simplified(self, test_db):
        result = test_db._get_char_simplified("國")
        assert result == "国"
