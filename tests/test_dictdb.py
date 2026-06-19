class TestGetReading:
    def test_returns_reading_for_known_word(self, test_db):
        result = test_db.get_reading("สวัสดี")
        assert result is not None
        reading, tone_pattern = result
        assert reading == "sa-wat-dii"
        assert tone_pattern == "2-2-1"

    def test_returns_reading_ipa(self, test_db):
        result = test_db.get_reading("ภาษาไทย")
        assert result is not None
        reading, _tone_pattern = result
        assert reading == "pha-sa-thai"

    def test_returns_none_for_missing(self, test_db):
        result = test_db.get_reading("XYZNOTAWORD")
        assert result is None


class TestGetReadingBatch:
    def test_returns_multiple_readings(self, test_db):
        result = test_db.get_reading_batch(("สวัสดี", "ภาษาไทย"))
        assert len(result) == 2
        assert "สวัสดี" in result
        assert "ภาษาไทย" in result
        assert result["สวัสดี"][0] == "sa-wat-dii"
        assert result["ภาษาไทย"][0] == "pha-sa-thai"

    def test_missing_words_omitted(self, test_db):
        result = test_db.get_reading_batch(("สวัสดี", "MISSING"))
        assert len(result) == 1
        assert "สวัสดี" in result

    def test_empty_tuple(self, test_db):
        result = test_db.get_reading_batch(())
        assert result == {}


class TestCommitChanges:
    def test_commit_does_not_raise(self, test_db):
        test_db.commit_changes()
