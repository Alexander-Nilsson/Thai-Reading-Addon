#
import sys
from os.path import dirname, join

import aqt.editor
import aqt.utils

sys.path.append(join(dirname(__file__), "..", "lib"))
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from .._infra.utils import show_ask
from ..template.js_registry import JsRegistry
from .generator import ReadingGenerator
from .text_utils import strip_brackets


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
        if not text:
            return False
        else:
            return text

    def cleanField(self, editor):
        if self.editorText(editor):
            editor.web.eval(self.commonJS + self.bracketsFromSelJS)
        else:
            editor.web.eval(self.commonJS + self.removeBracketsJS)

    def addCReadings(self, editor):
        editor.web.eval(self.commonJS + self.fetchTextJS)

    def finalizeReadings(self, text, field, note, editor=False, rType=False):
        if text == "":
            return
        if not rType:
            altType = self.cssJSHandler.get_alt_reading_type(note.model()["name"], field)
            if altType:
                rType = altType
            else:
                rType = self.config.reading_type
            if rType not in ["pinyin", "bopomofo", "jyutping"]:
                return
        newStr = self.reading_generator.generate(text, rType)
        if editor:
            editor.web.eval(self.commonJS + self.insertHTMLJS % newStr.replace('"', '\\"').replace("\n", ""))
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
                        separator = "<br>"
                        if len(varAr) == 3:
                            separator = varAr[2]
                        if note[selField] == "" or editor:
                            self.addToNote(
                                editor,
                                note,
                                selField,
                                ordinal,
                                note[selField] + separator.replace("<br>", "", 1) + text,
                            )
                        else:
                            self.addToNote(editor, note, selField, ordinal, note[selField] + separator + text)
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
            if not sSame and not tSame:
                return fText + separator + simplified + sep2 + traditional
            elif not sSame and tSame:
                return fText + separator + simplified
            elif not tSame and sSame:
                return fText + sep2 + traditional

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
        if ordinal is not False and editor is not False:
            editor.web.eval(self.commonJS + self.insertToFieldJS % (text.replace('"', '\\"'), str(ordinal)))
        else:
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
