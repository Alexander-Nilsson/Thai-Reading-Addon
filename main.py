#
import json
import os
import sys
from os.path import dirname, join

import aqt.editor
import aqt.utils
from anki.hooks import addHook
from aqt import gui_hooks, mw
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

from .reading import dictdb

sys.path.append(join(dirname(__file__), "lib"))
import requests

from ._infra.anki_services import LiveAnkiServices
from ._infra.utils import show_info
from .config.config import AddonConfig
from .config.mutation import (
    ConfigDelta,
    LiveConfigMutation,
    LiveModelCatalog,
)
from .config.settings import SettingsGui
from .reading.handler import ChineseHandler
from .template.handler import CSSJSHandler

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

defaults = mw.addonManager.addonConfigDefaults(addonPath)


def rebuild_catalog():
    mw.ChineseReadingCatalog = LiveModelCatalog(mw)


mw.ChineseReadingCatalog = LiveModelCatalog(mw)
mw.ChineseReadingMutation = LiveConfigMutation(
    anki_services,
    __name__,
    config,
    defaults,
    mw.ChineseReadingCatalog,
)
gui_hooks.profile_did_open.append(rebuild_catalog)
gui_hooks.profile_did_open.append(autoCssJs.injectWrapperElements)
gui_hooks.profile_did_open.append(autoCssJs.updateWrapperDict)

try:
    requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass

currentNote = False
currentField = False
currentKey = False
wrapperDict = False


def openChineseSettings():
    if not mw.chineseReadingSettings:
        mw.chineseReadingSettings = SettingsGui(
            mw,
            addonPath,
            mw.ChineseReadingCatalog,
            autoCssJs,
            openChineseSettings,
            config,
        )
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


def setupShortcuts(cuts, editor):
    if not checkProfile():
        return
    cuts.append(("F10", lambda: mw.ChineseReading.cleanField(editor)))
    cuts.append(("F9", lambda: mw.ChineseReading.addCReadings(editor)))


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
        return
    txt = self.form.editor.toPlainText()
    try:
        new_conf = json.loads(txt)
    except Exception as e:
        showInfo("Invalid configuration: " + repr(e))
        return

    if not isinstance(new_conf, dict):
        showInfo("Invalid configuration: top level object must be a map")
        return

    if new_conf != self.conf:
        delta = ConfigDelta.from_dict(new_conf)
        try:
            config = mw.ChineseReadingMutation.save_config(delta)
        except Exception as e:
            showInfo("Invalid configuration: " + str(e))
            return
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

gui_hooks.browser_menus_did_init.append(setupMenu)
addHook("setupEditorButtons", setupButtons)
gui_hooks.editor_did_init_shortcuts.append(setupShortcuts)


def getFieldName(fieldId, note):
    fields = mw.col.models.field_names(note.model())
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
