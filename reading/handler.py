import logging
import os
import re

import aqt.utils
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from .._infra import show_ask
from .generator import ReadingGenerator, strip_brackets

_log = logging.getLogger("thai_reading")


class ThaiHandler:
    def __init__(self, mw, anki_services, path, db, cssJsHandler, config):
        self.mw = mw
        self.anki = anki_services
        self.cssJsHandler = cssJsHandler
        self.path = path
        self.db = db
        self.config = config
        self.reading_generator = ReadingGenerator(db, config)

    def refreshConfig(self, config=None):
        if config is not None:
            self.config = config
            self.reading_generator._config = config

    def getProgressWidget(self):
        progressWidget = QWidget(None)
        QVBoxLayout()
        progressWidget.setFixedSize(400, 70)
        progressWidget.setWindowModality(Qt.WindowModality.ApplicationModal)
        progressWidget.setWindowIcon(QIcon(os.path.join(self.path, "icons", "thai-reading.svg")))
        bar = QProgressBar(progressWidget)
        bar.setFixedSize(390, 50)
        bar.move(10, 10)
        per = QLabel(bar)
        per.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progressWidget.show()
        return progressWidget, bar

    def massGenerate(self, og, dest, om, rt, notes, generateWidget):
        _log.debug("massGenerate called: og=%s, dest=%s, om=%s, rt=%s, notes_count=%d", og, dest, om, rt, len(notes))
        self.anki.checkpoint("Thai Reading Generation")
        if not show_ask(
            "Generate readings for " + str(len(notes)) + ' selected cards from "' + og + '" into "' + dest + '"?'
        ):
            return
        generateWidget.close()
        _progWid, bar = self.getProgressWidget()
        bar.setMinimum(0)
        bar.setMaximum(len(notes))

        progress_interval = max(1, len(notes) // 100) if len(notes) > 1 else 1

        val = 0
        for nid in notes:
            note = self.anki.get_note(nid)
            fields = self.anki.field_names(note.model())
            if og in fields and dest in fields:
                text = note[og]
                cleaned = self.removeBrackets(text)
                newText = self.finalizeReadings(cleaned, og, note, rType=rt)
                note[dest] = self.applyOM(om, note[dest], newText)
                self.anki.col.update_note(note)
            val += 1
            if val % progress_interval == 0 or val == len(notes):
                bar.setValue(val)
                self.anki.process_events()
        self.anki.progress_finish()
        self.anki.reset()

    def applyOM(self, addType, dest, text):
        if text:
            if addType == "If Empty":
                if dest == "":
                    dest = text
            elif addType == "Add":
                if dest == "":
                    dest = text
                else:
                    dest += "<br>" + text
            else:
                dest = text
        return dest

    def massRemove(self, field, notes, generateWidget):
        if not show_ask(
            '####WARNING#####\nAre you sure you want to mass remove readings from the "'
            + field
            + '" field? Please make sure you have selected the correct field '
            'as this will remove all "[" and "]" and text in between from a field.'
        ):
            return
        generateWidget.close()
        _progWid, bar = self.getProgressWidget()
        bar.setMinimum(0)
        bar.setMaximum(len(notes))
        val = 0
        for nid in notes:
            note = self.anki.get_note(nid)
            fields = self.anki.field_names(note.model())
            if field in fields:
                text = note[field]
                text = self.removeBrackets(text)
                note[field] = text
                self.anki.col.update_note(note)
            val += 1
            bar.setValue(val)
            self.anki.process_events()
        self.anki.progress_finish()
        self.anki.reset()

    @staticmethod
    def _has_readings(text: str) -> bool:
        if "[" not in text:
            return False
        audio_pat = re.compile(r"\[sound:[^\]]+\]|\[\d*\]")
        return "[" in audio_pat.sub("", text)

    def toggleReadings(self, editor):
        _log.debug("toggleReadings called")
        note = editor.note
        if not note:
            aqt.utils.showInfo("Thai Reading: No note loaded")
            return

        field_name, _source = self._resolve_field_name(note)
        if field_name is None:
            aqt.utils.showInfo("Thai Reading: Please click inside a field and try again.")
            return

        text = note[field_name]
        if self._has_readings(text):
            cleaned = self.removeBrackets(text)
            if text != cleaned:
                note[field_name] = cleaned
                self.anki.col.update_note(note)
                editor.loadNoteKeepingFocus()
        else:
            cleaned = self.removeBrackets(text)
            self.finalizeReadings(cleaned, field_name, note, editor)
            self.anki.col.update_note(note)
            editor.loadNoteKeepingFocus()

    def _resolve_field_name(self, note):
        note_type_name = note.model()["name"]
        wrapper = self.cssJsHandler.wrapperDict.get(note_type_name)
        if wrapper:
            field_name = wrapper[0][1]
            if field_name and field_name in note:
                return field_name, "config"

        ordinal = getattr(self.mw, "_lastFocusedFieldOrdinal", None) if self.mw else None
        if ordinal is not None:
            field_name = note.keys()[ordinal]
            return field_name, "ordinal"

        return None, None

    def cleanField(self, editor):
        _log.debug("cleanField called, editor=%s", editor)
        note = editor.note
        if not note:
            aqt.utils.showInfo("Thai Reading: No note loaded")
            return

        field_name, _source = self._resolve_field_name(note)
        if field_name is None:
            _log.warning("cleanField: no field could be resolved")
            aqt.utils.showInfo("Thai Reading: Please click inside a field and try again.")
            return

        text = note[field_name]
        cleaned_text = self.removeBrackets(text)
        if text != cleaned_text:
            _log.debug("cleanField: using field %s", field_name)
            note[field_name] = cleaned_text
            self.anki.col.update_note(note)
            editor.loadNoteKeepingFocus()
        else:
            _log.debug("cleanField: no brackets found in field %s", field_name)

    def addCReadings(self, editor):
        _log.debug("addCReadings called, editor=%s", editor)
        note = editor.note
        if not note:
            aqt.utils.showInfo("Thai Reading: No note loaded")
            return

        field_name, _source = self._resolve_field_name(note)
        if field_name is None:
            _log.warning("addCReadings: no field could be resolved")
            aqt.utils.showInfo("Thai Reading: Please click inside a field and try again.")
            return

        text = note[field_name]
        cleaned_text = self.removeBrackets(text)
        _log.debug("addCReadings: using field %s", field_name)
        self.finalizeReadings(cleaned_text, field_name, note, editor)
        self.anki.col.update_note(note)
        editor.loadNoteKeepingFocus()

    def finalizeReadings(self, text, field, note, editor=False, rType=False):
        _log.debug(
            "finalizeReadings called: text=%s, field=%s, editor=%s, rType=%s",
            repr(text[:50]) if text and len(text) > 50 else repr(text),
            field,
            bool(editor),
            rType,
        )
        if text == "":
            _log.debug("finalizeReadings: empty text, returning")
            return

        text = self.removeBrackets(text)

        note_type_name = note.model()["name"]
        if not rType:
            altType = self.cssJsHandler.get_alt_reading_type(note_type_name, field)
            _log.debug("finalizeReadings: note_type=%s, field=%s, altType=%s", note_type_name, field, altType)
            if altType:
                rType = altType
            else:
                rType = self.config.reading_type
                _log.debug("finalizeReadings: using config.reading_type=%s", rType)
            if rType not in ["rtgs", "ipa", "phonetics"]:
                _log.debug("finalizeReadings: invalid rType=%s, returning", rType)
                return
        _log.debug("finalizeReadings: generating with rType=%s", rType)
        newStr = self.reading_generator.generate(text, rType)
        _log.debug("finalizeReadings: generated string length=%d", len(newStr) if newStr else 0)
        if editor:
            if not newStr:
                _log.warning("finalizeReadings: newStr is empty, nothing to insert")
                return

            self.addToNote(editor, note, field, self.getFieldOrdinal(note, field), newStr)
        else:
            return newStr

    def fetchParsed(self, text, field, note, rType=False):
        if text == "":
            return ""
        if not rType:
            altType = self.cssJsHandler.get_alt_reading_type(note.model()["name"], field)
            if altType:
                rType = altType
            else:
                rType = self.config.reading_type
        if rType not in ["rtgs", "ipa", "phonetics"]:
            return text
        newStr = self.reading_generator.generate(text, rType)
        return newStr

    def getFieldOrdinal(self, note, field):
        fields = note.note_type()["flds"]
        for f in fields:
            if field == f["name"]:
                return f["ord"]
        else:
            return False

    def addToNote(self, editor, note, field, ordinal, text):
        if note[field] == text:
            _log.debug("addToNote: text is identical, skipping update for field %s", field)
            return

        _log.debug("addToNote: updating field %s", field)
        note[field] = text

    def reloadEditor(self):
        browser = aqt.DialogManager._dialogs["Browser"][1]
        if browser:
            self.mw.progress.timer(100, browser.editor.loadNoteKeepingFocus, False)
        adder = aqt.DialogManager._dialogs["AddCards"][1]
        if adder:
            self.mw.progress.timer(100, adder.editor.loadNoteKeepingFocus, False)
        editCurrent = aqt.DialogManager._dialogs["EditCurrent"][1]
        if editCurrent:
            self.mw.progress.timer(100, editCurrent.editor.loadNoteKeepingFocus, False)

    def removeBrackets(self, text, returnSounds=False, removeAudio=False):
        return strip_brackets(text, return_sounds=returnSounds, remove_audio=removeAudio)
