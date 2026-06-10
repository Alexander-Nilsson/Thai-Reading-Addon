#
import logging
import sys
from os.path import dirname, join

import aqt.editor
import aqt.utils

sys.path.append(join(dirname(__file__), "..", "lib"))
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from .._infra.utils import show_ask  # ty: ignore[unresolved-import]
from ..template.js_registry import JsRegistry  # ty: ignore[unresolved-import]
from .generator import ReadingGenerator
from .text_utils import strip_brackets

_log = logging.getLogger("chinese_reading")


class ChineseHandler:
    def __init__(self, mw, anki_services, path, db, cssJSHandler, config):
        self.mw = mw
        self.anki = anki_services
        self.cssJSHandler = cssJSHandler
        self.path = path
        self.db = db
        self.config = config
        self.reading_generator = ReadingGenerator(db, config)
        self.js = JsRegistry(join(path, "js"))
        self.commonJS = self.js.load("common.js")
        self.insertHTMLJS = self.js.load("insertHTML.js")
        self.insertToFieldJS = self.js.load("insertHTMLToField.js")
        self.fetchTextJS = self.js.load("fetchText.js")
        self.bracketsFromSelJS = self.js.load("bracketsFromSel.js")
        self.removeBracketsJS = self.js.load("removeBrackets.js")

    def refreshConfig(self, config=None):
        if config is not None:
            self.config = config

    def getProgressWidget(self):
        progressWidget = QWidget(None)
        QVBoxLayout()
        progressWidget.setFixedSize(400, 70)
        progressWidget.setWindowModality(Qt.WindowModality.ApplicationModal)
        progressWidget.setWindowIcon(QIcon(join(self.path, "icons", "chinese-reading.svg")))
        bar = QProgressBar(progressWidget)
        bar.setFixedSize(390, 50)
        bar.move(10, 10)
        per = QLabel(bar)
        per.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progressWidget.show()
        return progressWidget, bar

    def massGenerate(self, og, dest, om, rt, notes, generateWidget):
        _log.debug("massGenerate called: og=%s, dest=%s, om=%s, rt=%s, notes_count=%d", og, dest, om, rt, len(notes))
        self.anki.checkpoint("Chinese Reading Generation")
        if not show_ask(
            'Are you sure you want to generate from the "' + og + '" field into  the "' + dest + '" field?.'
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
            if og in fields and dest in fields:
                text = note[og]
                _log.debug("massGenerate: processing note %d, text length=%d", nid, len(text) if text else 0)
                newText = self.finalizeReadings(text, og, note, rType=rt)
                note[dest] = self.applyOM(om, note[dest], newText)
                self.addVariants(self.removeBrackets(text), note)
                self.addSimpTrad(self.removeBrackets(text), note)
                self.anki.col.update_note(note)
            val += 1
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

    def editorText(self, editor):
        text = editor.web.selectedText()
        _log.debug("editorText: got text=%s", repr(text[:50]) if text and len(text) > 50 else repr(text))
        if not text:
            return False
        else:
            return text

    def cleanField(self, editor):
        if self.editorText(editor):
            editor.web.eval(self.commonJS + self.bracketsFromSelJS)
            return

        note = editor.note
        configured_field_name = None

        if note is not None:
            note_type_name = note.model()["name"]
            wrapper = self.cssJSHandler.wrapperDict.get(note_type_name)
            if wrapper:
                configured_field_name = wrapper[0][1]

        if configured_field_name and note and configured_field_name in note:
            text = note[configured_field_name]
            cleaned_text = self.removeBrackets(text)
            if text != cleaned_text:
                _log.debug("cleanField: bypassing JS, removing brackets directly for field %s", configured_field_name)
                note[configured_field_name] = cleaned_text
                self.anki.col.update_note(note)
                # Find ordinal to update the UI
                ordinal = self.getFieldOrdinal(note, configured_field_name)
                if ordinal is not False:
                    editor.web.eval(self.commonJS + self.insertToFieldJS % (cleaned_text.replace('"', '\\"'), str(ordinal)))
                
                # Always trigger a reload as a fallback to ensure the UI matches the DB
                editor.loadNoteKeepingFocus()
            return

        editor.web.eval(self.commonJS + self.removeBracketsJS)

    def addCReadings(self, editor):
        _log.debug("addCReadings called, editor=%s", editor)
        text = self.editorText(editor)
        if text:
            _log.debug("addCReadings: text selected, calling fetchTextJS")
            editor.web.eval(self.commonJS + self.fetchTextJS)
            return

        _log.debug("addCReadings: no text selected, resolving field")
        ordinal = None
        note = editor.note
        note_id = note.id if note else 0
        configured_field_name = None

        # Try note-type config first
        if note is not None:
            note_type_name = note.model()["name"]
            wrapper = self.cssJSHandler.wrapperDict.get(note_type_name)
            if wrapper:
                configured_field_name = wrapper[0][1]
                ordinal = self.getFieldOrdinal(note, configured_field_name)
                _log.debug(
                    "addCReadings: note type config found: field=%s ordinal=%s",
                    configured_field_name,
                    ordinal,
                )

        # If we have a configured field, we can bypass the DOM and use the note data directly
        if configured_field_name and note and configured_field_name in note:
            text = note[configured_field_name]
            # IDEMPOTENCY: Remove existing readings before adding new ones
            cleaned_text = self.removeBrackets(text)
            _log.debug("addCReadings: bypassing JS, finalizing directly for field %s", configured_field_name)
            self.finalizeReadings(cleaned_text, configured_field_name, note, editor)
            # Ensure the note is saved and UI is updated
            self.anki.col.update_note(note)
            editor.loadNoteKeepingFocus()
            return

        # Fallback for unconfigured fields: try to find focused field via JS
        if ordinal is None and self.mw and getattr(self.mw, "_lastFocusedFieldOrdinal", None) is not None:
            ordinal = self.mw._lastFocusedFieldOrdinal
            _log.debug("addCReadings: using tracked ordinal=%d", ordinal)

        if ordinal is not None:
            js_set_field = f"var currentField = get_field_by_ordinal({ordinal}); var currentNoteId = '{note_id}';"
        else:
            js_set_field = "console.log('Chinese Reading: No field could be resolved');"

        editor.web.eval(self.commonJS + js_set_field + self.fetchTextJS)

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

        # IDEMPOTENCY: Ensure we don't add readings to already bracketed text
        text = self.removeBrackets(text)

        note_type_name = note.model()["name"]
        if not rType:
            altType = self.cssJSHandler.get_alt_reading_type(note_type_name, field)
            _log.debug("finalizeReadings: note_type=%s, field=%s, altType=%s", note_type_name, field, altType)
            if altType:
                rType = altType
            else:
                rType = self.config.reading_type
                _log.debug("finalizeReadings: using config.reading_type=%s", rType)
            if rType not in ["pinyin", "bopomofo", "jyutping"]:
                _log.debug("finalizeReadings: invalid rType=%s, returning", rType)
                return
        _log.debug("finalizeReadings: generating with rType=%s", rType)
        newStr = self.reading_generator.generate(text, rType)
        _log.debug("finalizeReadings: generated string length=%d", len(newStr) if newStr else 0)
        if editor:
            if not newStr:
                _log.warning("finalizeReadings: newStr is empty, nothing to insert")
                return
            
            # IDEMPOTENCY: Use addToNote which now checks for duplicates
            self.addToNote(editor, note, field, self.getFieldOrdinal(note, field), newStr)
            
            self.addVariants(text, note, editor)
            self.addSimpTrad(text, note, editor)
        else:
            return newStr

    def fetchParsed(self, text, field, note, rType=False):
        if text == "":
            return ""
        if not rType:
            altType = self.cssJSHandler.get_alt_reading_type(note.model()["name"], field)
            if altType:
                rType = altType
            else:
                rType = self.config.reading_type
        if rType not in ["pinyin", "bopomofo", "jyutping"]:
            return text
        newStr = self.reading_generator.generate(text, rType)
        self.addVariants(text, note)
        self.addSimpTrad(text, note)
        return newStr

    def addVariants(self, text, note, editor=False):
        fields = self.anki.field_names(note.model())
        for variant_key in ["simplified_field", "traditional_field"]:
            varAr = getattr(self.config, variant_key).split(";")
            selFields = varAr[0].split(",")
            for selField in selFields:
                if selField.lower() == "none":
                    continue
                if selField in fields:
                    ordinal = False
                    if editor:
                        ordinal = self.getFieldOrdinal(note, selField)
                    if variant_key == "simplified_field":
                        text = self.db.get_simplified(self.removeBrackets(text))
                    elif variant_key == "traditional_field":
                        text = self.db.get_traditional(self.removeBrackets(text))
                    if not text:
                        return
                    if varAr[1] == "overwrite":
                        self.addToNote(editor, note, selField, ordinal, text)
                    elif varAr[1] == "add":
                        if text in note[selField]:
                            _log.debug("addVariants: variant already in field %s, skipping", selField)
                            continue

                        separator = "<br>"
                        if len(varAr) == 3:
                            separator = varAr[2]
                        
                        current_val = note[selField]
                        new_val = current_val + (separator if current_val else "") + text
                        self.addToNote(editor, note, selField, ordinal, new_val)
                    elif varAr[1] == "no":
                        if note[selField] == "":
                            self.addToNote(editor, note, selField, ordinal, text)

    def getSimpTradString(self, fText, varAr, text, simplified, traditional):
        sSame = False
        tSame = False
        separator = "<br>"
        if len(varAr) == 3:
            separator = varAr[2]
        if text == simplified:
            sSame = True
        if text == traditional:
            tSame = True
        if tSame and sSame:
            return ""
        if varAr[1] == "overwrite" or varAr[1] == "no":
            if varAr[1] == "no" and fText != "":
                return fText
            if not sSame and not tSame:
                return simplified + separator + traditional
            elif not sSame and tSame:
                return simplified
            elif not tSame and sSame:
                return traditional
        elif varAr[1] == "add":
            sep2 = separator
            if fText == "":
                sep2 = sep2.replace("<br>", "", 1)
                separator = separator.replace("<br>", "", 1)
            if len(varAr) == 4:
                separator = varAr[3]
            
            s_to_add = simplified if not sSame and simplified not in fText else ""
            t_to_add = traditional if not tSame and traditional not in fText else ""
            
            if not s_to_add and not t_to_add:
                return fText
            
            res = fText
            if s_to_add:
                res += separator + s_to_add
            if t_to_add:
                res += (sep2 if s_to_add else separator) + t_to_add
            return res

    def addSimpTrad(self, text, note, editor=False):
        varAr = self.config.simp_trad_field.split(";")
        fields = self.anki.field_names(note.model())
        altFields = varAr[0].split(",")
        for altField in altFields:
            if altField.lower() == "none":
                return
            if altField in fields:
                ordinal = False
                if editor:
                    ordinal = self.getFieldOrdinal(note, altField)
                simplified = self.db.get_simplified(self.removeBrackets(text))
                traditional = self.db.get_traditional(self.removeBrackets(text))
                self.addToNote(
                    editor,
                    note,
                    altField,
                    ordinal,
                    self.getSimpTradString(note[altField], varAr, text, simplified, traditional),
                )

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

        if ordinal is not False and editor is not False:
            editor.web.eval(self.commonJS + self.insertToFieldJS % (text.replace('"', '\\"'), str(ordinal)))

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
