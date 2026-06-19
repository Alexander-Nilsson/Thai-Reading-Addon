import os.path
import sqlite3
from functools import cache


class DictDB:
    def __init__(self, addon_path=None):
        if addon_path is None:
            addon_path = os.path.dirname(__file__)
        db_file = os.path.join(addon_path, "db", "thai_dict.sqlite")

        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()

    def commit_changes(self):
        self.conn.commit()

    def close_connection(self):
        self.c.close()
        self.conn.close()

    @cache
    def get_reading(self, w):
        self.c.execute(
            "select distinct reading, tone_pattern from words where word=? limit 1;",
            (w,),
        )
        return self.c.fetchone() or None

    @cache
    def get_reading_batch(self, words):
        if not words:
            return {}
        placeholders = ",".join("?" for _ in words)
        self.c.execute(
            f"select word, reading, tone_pattern from words where word in ({placeholders});",
            words,
        )
        return {row[0]: (row[1], row[2]) for row in self.c.fetchall()}
