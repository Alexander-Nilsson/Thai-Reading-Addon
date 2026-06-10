import os
import sqlite3
import tempfile

import pytest

from reading.dictdb import DictDB

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "chinese_dict.sqlite")


def _create_test_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE cidian (traditional, simplified, pinyin, pinyin_taiwan, "
        "classifiers, alternates, english, german, french, spanish)"
    )
    c.execute("CREATE TABLE cantonese (traditional TEXT, simplified TEXT, jyutping TEXT, pinyin TEXT)")
    c.execute("CREATE TABLE altDict (traditional TEXT, simplified TEXT, pinyin TEXT)")
    c.execute("CREATE TABLE hanzi (cp, kMandarin, kCantonese, kSimplifiedVariant, kTraditionalVariant)")
    c.execute("CREATE INDEX isimplified ON cidian (simplified)")
    c.execute("CREATE UNIQUE INDEX itraditional ON cidian (traditional, pinyin)")
    conn.commit()
    conn.close()


def _populate_test_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.executemany(
        "INSERT INTO cidian (traditional, simplified, pinyin, pinyin_taiwan) VALUES (?, ?, ?, ?)",
        [
            ("中國", "中国", "zhōng guó", "zhōng guó"),
            ("你好", "你好", "nǐ hǎo", "nǐ hǎo"),
            ("學生", "学生", "xué shēng", None),
        ],
    )
    c.executemany(
        "INSERT INTO cantonese (traditional, simplified, jyutping, pinyin) VALUES (?, ?, ?, ?)",
        [
            ("中國", "中国", "zung1 gwok3", "zhong1 guo2"),
            ("你好", "你好", "lei5 hou2", "ni3 hao3"),
        ],
    )
    c.executemany(
        "INSERT INTO altDict (traditional, simplified, pinyin) VALUES (?, ?, ?)",
        [
            ("一", "一", "yī"),
            ("在", "在", "zài"),
        ],
    )
    c.executemany(
        "INSERT INTO hanzi (cp, kMandarin, kCantonese, kSimplifiedVariant, kTraditionalVariant) VALUES (?, ?, ?, ?, ?)",
        [
            ("中", "zhōng", "zung1", None, None),
            ("國", "guó", "gwok3", "国", None),
            ("学", "xué", "hok6", None, "學"),
        ],
    )
    conn.commit()
    conn.close()


@pytest.fixture
def real_db():
    d = DictDB(os.path.dirname(os.path.dirname(__file__)))
    yield d
    d.closeConnection()


@pytest.fixture
def test_db_path():
    with tempfile.TemporaryDirectory() as td:
        db_dir = os.path.join(td, "db")
        os.makedirs(db_dir)
        db_file = os.path.join(db_dir, "chinese_dict.sqlite")
        _create_test_db(db_file)
        _populate_test_db(db_file)
        yield td


@pytest.fixture
def test_db(test_db_path):
    d = DictDB(test_db_path)
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
