#
import json
import os
import sys
from os.path import dirname, join

import aqt.editor
import aqt.utils
from anki.hooks import addHook, wrap
from aqt import mw
from aqt.qt import _
from aqt.utils import saveGeom, saveSplitter, showInfo
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from . import dictdb

sys.path.append(join(dirname(__file__), "lib"))
import requests
from anki import Collection
from aqt.main import AnkiQt

from .addon_config import AddonConfig
from .anki_services import LiveAnkiServices
from .chineseHandler import ChineseHandler
from .cssJSHandler import CSSJSHandler
from .settings import SettingsGui
from .utils import show_info

anki_services = LiveAnkiServices(mw)
config = AddonConfig.from_anki(mw)


def updateChineseReadingConfig():
    global config
    config = AddonConfig.from_anki(mw)
    mw.ChineseReadingConfig = config


addonPath = dirname(__file__)
mw.chineseReadingSettings = False
db = dictdb.DictDB(addonPath)
autoCssJs = CSSJSHandler(mw, anki_services, addonPath, config)
mw.ChineseReading = ChineseHandler(mw, anki_services, addonPath, db, autoCssJs, config)
mw.ChineseReadingConfig = config
mw.updateChineseReadingConfig = updateChineseReadingConfig
# addHook("profileLoaded", autoCssJs.loadWrapperDict)
addHook("profileLoaded", autoCssJs.injectWrapperElements)
addHook("profileLoaded", autoCssJs.updateWrapperDict)

try:
    requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass

currentNote = False
currentField = False
currentKey = False
wrapperDict = False
colArray = False


def loadCollectionArray(self=None, b=None):
    global colArray
    colArray = {}
    loadAllProfileInformation()


def loadAllProfileInformation():
    global colArray
    for prof in mw.pm.profiles():
        cpath = join(mw.pm.base, prof, "collection.anki2")
        try:
            tempCol = Collection(cpath)
            noteTypes = tempCol.models.all()
            tempCol.close()
            tempCol = None
            noteTypeDict = {}
            for note in noteTypes:
                noteTypeDict[note["name"]] = {"cardTypes": [], "fields": []}
                for ct in note["tmpls"]:
                    noteTypeDict[note["name"]]["cardTypes"].append(ct["name"])
                for f in note["flds"]:
                    noteTypeDict[note["name"]]["fields"].append(f["name"])
            colArray[prof] = noteTypeDict
        except Exception:
            show_info(
                "<b>Warning:</b><br>One of your profiles could not be loaded. "
                "This usually happens if you've just created a new profile and are opening it for the first time. "
                "The issue should be fixed after restarting Anki. "
                "If it persists, then your profile is corrupted in some way.\n\n"
                "You can fix this corruption by exporting your collection, importing it into a new profile, "
                "and then deleting your previous profile. <b>",
                level="wrn",
            )


AnkiQt.loadProfile = wrap(AnkiQt.loadProfile, loadCollectionArray, "before")


def openChineseSettings():
    if not mw.chineseReadingSettings:
        mw.chineseReadingSettings = SettingsGui(mw, addonPath, colArray, autoCssJs, openChineseSettings, config)
    mw.chineseReadingSettings.show()
    if mw.chineseReadingSettings.windowState() == Qt.WindowState.WindowMinimized:
        # Window is minimised. Restore it.
        mw.chineseReadingSettings.setWindowState(Qt.WindowState.WindowNoState)
    mw.chineseReadingSettings.setFocus()
    mw.chineseReadingSettings.activateWindow()


def setupGuiMenu():

    if not hasattr(mw, "ChineseReadingMenuSettings"):
        mw.ChineseReadingMenuSettings = []
    if not hasattr(mw, "ChineseReadingMenuActions"):
        mw.ChineseReadingMenuActions = []

    # Add to Tools menu
    setting = QAction("Chinese Reading Settings", mw)
    setting.triggered.connect(openChineseSettings)
    mw.ChineseReadingMenuSettings.append(setting)

    mw.form.menuTools.addSeparator()
    for act in mw.ChineseReadingMenuSettings:
        mw.form.menuTools.addAction(act)
    for act in mw.ChineseReadingMenuActions:
        mw.form.menuTools.addAction(act)


setupGuiMenu()


def setupButtons(righttopbtns, editor):
    if not checkProfile():
        return righttopbtns
    editor._links["removeFormatting"] = lambda editor: mw.ChineseReading.cleanField(editor)
    if config.traditional_icons:
        duPath = os.path.join(addonPath, "icons", "tradDu.svg")
        shanPath = os.path.join(addonPath, "icons", "tradShan.svg")
    else:
        duPath = os.path.join(addonPath, "icons", "simpDu.svg")
        shanPath = os.path.join(addonPath, "icons", "simpShan.svg")

    righttopbtns.insert(0, editor._addButton(icon=shanPath, cmd="removeFormatting", tip="Hotkey: F10", id="删"))
    editor._links["addCReadings"] = lambda editor: mw.ChineseReading.addCReadings(editor)
    righttopbtns.insert(0, editor._addButton(icon=duPath, cmd="addCReadings", tip="Hotkey: F9", id="读"))
    return righttopbtns


def shortcutCheck(x, key):
    if x == key:
        return False
    else:
        return True


def setupShortcuts(shortcuts, editor):
    if not checkProfile():
        return shortcuts
    # config = getConfig()
    pitchData = []
    pitchData.append(
        {"hotkey": "F10", "name": "extra", "function": lambda editor=editor: mw.ChineseReading.cleanField(editor)}
    )
    pitchData.append(
        {"hotkey": "F9", "name": "extra", "function": lambda editor=editor: mw.ChineseReading.addCReadings(editor)}
    )
    newKeys = shortcuts
    for pitch in pitchData:
        newKeys = list(filter(lambda x: shortcutCheck(x[0], pitch["hotkey"]), newKeys))
        newKeys += [(pitch["hotkey"], pitch["function"])]
    shortcuts.clear()
    shortcuts += newKeys
    return


def onRegenerate(browser):
    import anki.find

    notes = browser.selectedNotes()
    if notes:
        fields = anki.find.fieldNamesForNotes(mw.col, notes)
        generateWidget = QDialog(None, Qt.Window)
        layout = QHBoxLayout()
        og = QLabel("Origin:")
        cb = QComboBox()
        cb.addItems(fields)
        dest = QLabel("Destination:")
        destCB = QComboBox()
        destCB.addItems(fields)
        om = QLabel("Output Mode:")
        omCB = QComboBox()
        omCB.addItems(["Add", "Overwrite", "If Empty"])
        rt = QLabel("Reading Type:")
        rtCB = QComboBox()
        rtCB.addItems(["Pinyin", "Bopomofo", "Jyutping"])
        b4 = QPushButton("Add Readings")
        b4.clicked.connect(
            lambda: mw.ChineseReading.massGenerate(
                cb.currentText(),
                destCB.currentText(),
                omCB.currentText(),
                rtCB.currentText().lower(),
                notes,
                generateWidget,
            )
        )  ##add in the vars
        b5 = QPushButton("Remove Readings")
        b5.clicked.connect(lambda: mw.ChineseReading.massRemove(cb.currentText(), notes, generateWidget))
        layout.addWidget(og)
        layout.addWidget(cb)
        layout.addWidget(dest)
        layout.addWidget(destCB)
        layout.addWidget(om)
        layout.addWidget(omCB)
        layout.addWidget(rt)
        layout.addWidget(rtCB)
        layout.addWidget(b4)
        layout.addWidget(b5)
        generateWidget.setWindowTitle("Generate Chinese Readings")
        generateWidget.setWindowIcon(QIcon(join(addonPath, "icons", "chinese-reading.svg")))
        generateWidget.setLayout(layout)
        generateWidget.exec_()
    else:
        show_info("Please select some cards before attempting to mass generate.")


def setupMenu(browser):
    if not checkProfile():
        return
    a = QAction("Generate Chinese Readings", browser)
    a.triggered.connect(lambda: onRegenerate(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


current_path = os.path.abspath(".")
parent_path = os.path.dirname(current_path)
sys.path.append(parent_path)


def checkProfile():
    if mw.pm.name in config.profiles or ("all" in config.profiles or "All" in config.profiles):
        return True
    return False


def supportAccept(self):
    global config
    if self.addon != os.path.basename(addonPath):
        ogAccept(self)
    txt = self.form.editor.toPlainText()
    try:
        new_conf = json.loads(txt)
    except Exception as e:
        showInfo(_("Invalid configuration: ") + repr(e))
        return

    if not isinstance(new_conf, dict):
        showInfo(_("Invalid configuration: top level object must be a map"))
        return

    if new_conf != self.conf:
        self.mgr.writeConfig(self.addon, new_conf)
        config = AddonConfig(_raw=new_conf)
        mw.ChineseReadingConfig = config
        autoCssJs.refreshConfig(config)
        mw.ChineseReading.refreshConfig(config)
        act = self.mgr.configUpdatedAction(self.addon)
        if act:
            act(new_conf)
        if not autoCssJs.injectWrapperElements():
            return

    saveGeom(self, "addonconf")
    saveSplitter(self.form.splitter, "addonconf")
    self.hide()


ogAccept = aqt.addons.ConfigEditor.accept
aqt.addons.ConfigEditor.accept = supportAccept

addHook("browser.setupMenus", setupMenu)
addHook("setupEditorButtons", setupButtons)
addHook("setupEditorShortcuts", setupShortcuts)


def getFieldName(fieldId, note):
    fields = mw.col.models.fieldNames(note.model())
    field = fields[int(fieldId)]
    return field


def bridgeReroute(self, cmd):
    global currentKey
    if checkProfile():
        if cmd.startswith("textToCReading"):
            splitList = cmd.split(":||:||:")
            if self.note.id == int(splitList[3]):
                field = getFieldName(splitList[2], self.note)
                mw.ChineseReading.finalizeReadings(splitList[1], field, self.note, self)
            return
    if not cmd.startswith("textToCReading"):
        ogReroute(self, cmd)


ogReroute = aqt.editor.Editor.onBridgeCmd
aqt.editor.Editor.onBridgeCmd = bridgeReroute
