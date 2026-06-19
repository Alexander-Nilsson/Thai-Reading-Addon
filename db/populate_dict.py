#!/usr/bin/env python3
"""Populate thai_dict.sqlite with Thai word pronunciations.

Uses `thaiphon` (RTGS + IPA transcription) with the optional
`thaiphon-data-volubilis` lexicon (~84k words) for the best results.

Usage:
    uv run python db/populate_dict.py
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thaiphon.model.phonological_word import PhonologicalWord
    from thaiphon.renderers.base import Renderer
    from thaiphon.renderers.mapping import MappingRenderer

THAI_RE = re.compile(r"^[\u0e00-\u0e7f]+$")

_PHONETICS_RENDERER: Renderer | None = None


def _get_phonetics_renderer() -> Renderer:
    from thaiphon import renderers as _  # noqa: F401 — trigger renderer registration
    from thaiphon.registry import RENDERERS

    global _PHONETICS_RENDERER
    if _PHONETICS_RENDERER is None:
        _PHONETICS_RENDERER = RENDERERS.get("paiboon")
    return _PHONETICS_RENDERER


_log = logging.getLogger("populate_dict")


def _setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def _open_db(addon_root: str) -> sqlite3.Connection:
    db_path = os.path.join(addon_root, "db", "thai_dict.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA cache_size = -64000")
    return conn


def build_phonetics(word: str, result: PhonologicalWord) -> str:
    """Build Paiboon-inspired phonetic transcription for a word.

    Uses the ``paiboon`` scheme from thaiphon — tones as combining
    diacritics (grave, circumflex, acute, caron), vowel length doubled
    for long vowels, ``ɔ`` distinct from ``o``, syllables separated by
    hyphens.
    """
    from thaiphon.renderers.base import RenderContext

    renderer = _get_phonetics_renderer()
    ctx = RenderContext(format="text", show_tone=True, show_length=True)
    return renderer.render_word(result, ctx)


def _build_pronunciation(
    word: str,
    result: PhonologicalWord,
    renderer: MappingRenderer,
) -> tuple[str, str, str, str]:
    """Build (reading_with_tones, tone_pattern, reading_ipa, reading_phonetics) for a word.

    *reading_with_tones* — space-separated syllables in RTGS, each with a
    trailing tone digit (1-5) — e.g. ``sa2 wat2 di1``.
    *tone_pattern* — space-separated tone digits (e.g. ``2 2 1``).
    *reading_ipa* — IPA phonetic transcription via thaiphon.
    *reading_phonetics* — Paiboon-inspired phonetic transcription.
    """
    from thaiphon import transcribe
    from thaiphon.model import Tone

    TONE_MAP = {Tone.MID: 1, Tone.LOW: 2, Tone.FALLING: 3, Tone.HIGH: 4, Tone.RISING: 5}

    tones: list[str] = []
    syl_parts: list[str] = []
    for syl in result.syllables:
        rtgs_syl = renderer.render_syllable(syl)
        tn = TONE_MAP.get(syl.tone, 0)
        syl_parts.append(f"{rtgs_syl}{tn}")
        tones.append(str(tn))

    reading = " ".join(syl_parts)
    tone_pattern = " ".join(tones)
    reading_ipa = transcribe(word, scheme="ipa")
    reading_phonetics = build_phonetics(word, result)
    return reading, tone_pattern, reading_ipa, reading_phonetics


def populate_from_volubilis(conn: sqlite3.Connection, batch_size: int = 1000):
    """Populate DB from the thaiphon-data-volubilis lexicon."""
    from thaiphon.renderers.rtgs import _factory as rtgs_factory
    from thaiphon_data_volubilis import ENTRIES

    renderer = rtgs_factory()
    cursor = conn.cursor()

    thai_entries = [k for k in ENTRIES if THAI_RE.match(k)]
    _log.info("Found %d Thai-script entries in volubilis lexicon", len(thai_entries))

    inserted = 0
    skipped = 0

    for i in range(0, len(thai_entries), batch_size):
        batch = thai_entries[i : i + batch_size]
        rows: list[tuple[str, str, str, str, str]] = []

        for word in batch:
            pw = ENTRIES[word]
            if not pw.syllables:
                skipped += 1
                continue

            try:
                reading, tone_pattern, ipa, phonetics = _build_pronunciation(word, pw, renderer)
                rows.append((word, reading, tone_pattern, ipa, phonetics))
            except Exception:
                skipped += 1
                continue

        cursor.executemany(
            "INSERT OR IGNORE INTO words "
            "(word, reading, tone_pattern, reading_ipa, reading_phonetics) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        inserted += len(rows)
        conn.commit()

        pct = 100.0 * (i + len(batch)) / len(thai_entries)
        _log.info(
            "Progress: %5d / %d (%5.1f%%) | inserted=%d skipped=%d",
            min(i + batch_size, len(thai_entries)),
            len(thai_entries),
            pct,
            inserted,
            skipped,
        )

    _log.info("Volubilis done: inserted=%d, skipped=%d", inserted, skipped)
    return inserted


def populate_fallback(conn: sqlite3.Connection):
    """Add a small set of common Thai words as fallback.

    These are hand-curated for correctness since the volubilis lexicon
    covers most everyday vocabulary already.
    """
    from thaiphon import analyze
    from thaiphon.renderers.rtgs import _factory as rtgs_factory

    renderer = rtgs_factory()
    cursor = conn.cursor()

    common_words = [
        "สวัสดี",
        "ขอบคุณ",
        "ครับ",
        "ค่ะ",
        "ใช่",
        "ไม่",
        "ไป",
        "มา",
        "กิน",
        "นอน",
        "รัก",
        "ดี",
        "คน",
        "บ้าน",
        "น้ำ",
        "ข้าว",
        "หมา",
        "แมว",
        "นก",
        "ปลา",
        "หนึ่ง",
        "สอง",
        "สาม",
        "สี่",
        "ห้า",
        "ใหญ่",
        "เล็ก",
        "สวย",
        "หล่อ",
        "ใจ",
        "มือ",
        "ตา",
        "หู",
        "จมูก",
        "ปาก",
        "ฟัน",
        "ผม",
        "ภาษา",
        "หนังสือ",
        "โรงเรียน",
        "หมอ",
        "ครู",
        "พ่อ",
        "แม่",
        "พี่",
        "น้อง",
        "เพื่อน",
        "ชื่อ",
        "กินข้าว",
        "เรียน",
        "ทำงาน",
        "สบาย",
        "มีความสุข",
    ]

    inserted = 0
    for word in common_words:
        try:
            result = analyze(word)
            pw = result.best
            reading, tone_pattern, ipa, phonetics = _build_pronunciation(word, pw, renderer)
            cursor.execute(
                "INSERT OR IGNORE INTO words "
                "(word, reading, tone_pattern, reading_ipa, reading_phonetics) "
                "VALUES (?, ?, ?, ?, ?)",
                (word, reading, tone_pattern, ipa, phonetics),
            )
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as exc:
            _log.warning("Failed to process fallback word '%s': %s", word, exc)

    conn.commit()
    _log.info("Fallback done: inserted=%d", inserted)
    return inserted


def add_from_thaiphon_api(conn: sqlite3.Connection, existing_count: int):
    """Generate readings for additional words using thaiphon's analyze API.

    This picks up words that are in the volubilis lexicon but were
    filtered out by the Thai-script check, plus any other analyzable strings.
    """
    from thaiphon import analyze
    from thaiphon.renderers.rtgs import _factory as rtgs_factory

    renderer = rtgs_factory()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM words")
    before = cursor.fetchone()[0]
    if before > existing_count:
        _log.info("Words already exist beyond volubilis count, skipping API pass")
        return 0

    _log.info("Checking for additional words via thaiphon API...")
    api_candidates: set[str] = set()
    try:
        from thaiphon_data_volubilis import ENTRIES as volubilis_entries

        for k in volubilis_entries:
            if not THAI_RE.match(k):
                continue
            api_candidates.add(k)
    except ImportError:
        pass

    _log.info("Processing %d unique candidates...", len(api_candidates))
    inserted = 0
    batch: list[tuple[str, str, str, str, str]] = []

    for word in api_candidates:
        try:
            result = analyze(word)
            pw = result.best
            reading, tone_pattern, ipa, phonetics = _build_pronunciation(word, pw, renderer)
            batch.append((word, reading, tone_pattern, ipa, phonetics))
        except Exception:
            continue

        if len(batch) >= 500:
            cursor.executemany(
                "INSERT OR IGNORE INTO words "
                "(word, reading, tone_pattern, reading_ipa, reading_phonetics) "
                "VALUES (?, ?, ?, ?, ?)",
                batch,
            )
            inserted += cursor.rowcount
            conn.commit()
            batch.clear()

    if batch:
        cursor.executemany(
            "INSERT OR IGNORE INTO words "
            "(word, reading, tone_pattern, reading_ipa, reading_phonetics) "
            "VALUES (?, ?, ?, ?, ?)",
            batch,
        )
        inserted += cursor.rowcount
        conn.commit()

    _log.info("API pass done: inserted=%d", inserted)
    return inserted


def _ensure_phonetics_column(conn: sqlite3.Connection) -> None:
    """Add ``reading_phonetics`` column if it does not exist yet (schema migration)."""
    try:
        conn.execute("ALTER TABLE words ADD COLUMN reading_phonetics TEXT")
        _log.info("Added reading_phonetics column to words table")
    except sqlite3.OperationalError:
        pass


def _backfill_phonetics(conn: sqlite3.Connection) -> int:
    """Fill missing ``reading_phonetics`` values for rows that already exist."""
    from thaiphon import analyze

    cursor = conn.cursor()
    cursor.execute("SELECT word FROM words WHERE reading_phonetics IS NULL OR reading_phonetics = ''")
    missing = [row[0] for row in cursor.fetchall()]
    if not missing:
        return 0

    filled = 0
    for word in missing:
        try:
            result = analyze(word)
            pw = result.best
            phon = build_phonetics(word, pw)
            cursor.execute("UPDATE words SET reading_phonetics = ? WHERE word = ?", (phon, word))
            filled += 1
        except Exception:
            pass
    conn.commit()
    _log.info("Backfilled phonetics for %d / %d missing rows", filled, len(missing))
    return filled


def main():
    _setup_logging()
    addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn = _open_db(addon_root)

    _ensure_phonetics_column(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM words")
    initial = cursor.fetchone()[0]
    _log.info("Initial rows in DB: %d", initial)

    total = initial

    if initial == 0:
        try:
            from thaiphon_data_volubilis import ENTRIES as _  # noqa: F401

            has_volubilis = True
        except ImportError:
            has_volubilis = False

        if has_volubilis:
            _log.info("Using thaiphon-data-volubilis lexicon...")
            total += populate_from_volubilis(conn)
        else:
            _log.warning("thaiphon-data-volubilis not installed. Install with: uv pip install thaiphon-data-volubilis")

        _log.info("Adding fallback common words...")
        total += populate_fallback(conn)

        _log.info("Additional pass from thaiphon API...")
        total += add_from_thaiphon_api(conn, total - initial)
    else:
        _log.info("DB already populated (%d rows), skipping", initial)

    _backfill_phonetics(conn)

    cursor.execute("SELECT COUNT(*) FROM words")
    final = cursor.fetchone()[0]
    conn.close()

    _log.info("=" * 50)
    _log.info("Population complete!")
    _log.info("  Before: %d", initial)
    _log.info("  After:  %d", final)
    _log.info("  Added:  %d", final - initial)


if __name__ == "__main__":
    main()
