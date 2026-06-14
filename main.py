#
import json
import logging
import os
import sys
from os.path import dirname, join

import aqt.editor
import aqt.utils
from anki.hooks import addHook
from aqt import gui_hooks
from aqt.utils import saveGeom, saveSplitter, showInfo
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .reading import dictdb  # ty: ignore[unresolved-import]

sys.path.append(join(dirname(__file__), "lib"))
import requests

from ._infra.anki_services import LiveAnkiServices  # ty: ignore[unresolved-import]
from ._infra.utils import show_info  # ty: ignore[unresolved-import]
from .config.config import AddonConfig  # ty: ignore[unresolved-import]
from .config.mutation import (  # ty: ignore[unresolved-import]
    ConfigDelta,
    LiveConfigMutation,
    LiveModelCatalog,
)
from .config.settings import SettingsGui  # ty: ignore[unresolved-import]
from .reading.handler import ChineseHandler  # ty: ignore[unresolved-import]
from .template.handler import CSSJSHandler  # ty: ignore[unresolved-import]

addonPath = dirname(__file__)
ADDON_MODULE = __name__.partition(".")[0]

_log = logging.getLogger("chinese_reading")
_log.setLevel(logging.DEBUG)
_handler = logging.FileHandler(join(addonPath, "debug.log"), mode="w")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_log.addHandler(_handler)
_log.info("Addon loaded")

try:
    requests.packages.urllib3.disable_warnings()  # ty:ignore[unresolved-attribute]
except AttributeError:
    pass

currentNote = False
currentField = False
currentKey = False
wrapperDict = False

db = dictdb.DictDB(addonPath)

config: AddonConfig
anki_services: LiveAnkiServices
autoCssJs: CSSJSHandler
defaults: dict[str, object] | None = None


def _init_profile():
    from aqt import mw
    from aqt.utils import showInfo

    global config, anki_services, autoCssJs, defaults

    try:
        anki_services = LiveAnkiServices(mw)
        config = AddonConfig.from_anki(mw, ADDON_MODULE)
        _log.info("_init_profile: config profiles=%s", config.profiles)
    except Exception as e:
        _log.error("_init_profile: failed at step 1 (config): %s", e, exc_info=True)
        showInfo("Chinese Reading init error (step 1): " + str(e))
        return

    try:
        mw.chineseReadingSettings = False  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        autoCssJs = CSSJSHandler(mw, anki_services, addonPath, config)
        mw.ChineseReading = ChineseHandler(mw, anki_services, addonPath, db, autoCssJs, config)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        mw.ChineseReadingConfig = config  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        mw.updateChineseReadingConfig = updateChineseReadingConfig  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    except Exception as e:
        _log.error("_init_profile: failed at step 2 (handlers): %s", e, exc_info=True)
        showInfo("Chinese Reading init error (step 2): " + str(e))
        return

    try:
        defaults = mw.addonManager.addonConfigDefaults(addonPath)
    except Exception as e:
        _log.error("_init_profile: failed at step 3 (defaults): %s", e, exc_info=True)
        showInfo("Chinese Reading init error (step 3): " + str(e))
        return

    try:
        mw.ChineseReadingCatalog = LiveModelCatalog(mw)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        mw.ChineseReadingMutation = LiveConfigMutation(  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
            anki_services,
            ADDON_MODULE,
            config,
            defaults,
            mw.ChineseReadingCatalog,  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        )
    except Exception as e:
        _log.error("_init_profile: failed at step 4 (catalog): %s", e, exc_info=True)
        showInfo("Chinese Reading init error (step 4): " + str(e))
        return

    try:
        autoCssJs.injectWrapperElements()
        autoCssJs.updateWrapperDict()
        setupGuiMenu()
    except Exception as e:
        _log.error("_init_profile: failed at step 5 (inject+menu): %s", e, exc_info=True)
        showInfo("Chinese Reading init error (step 5): " + str(e))
        return


def _rebuild_catalog():
    from aqt import mw

    assert defaults is not None
    mw.ChineseReadingCatalog = LiveModelCatalog(mw)  # type: ignore[attr-defined]
    mw.ChineseReadingMutation = LiveConfigMutation(  # type: ignore[attr-defined]
        anki_services,
        ADDON_MODULE,
        config,
        defaults,
        mw.ChineseReadingCatalog,  # type: ignore[attr-defined]
    )


def updateChineseReadingConfig():
    global config
    from aqt import mw

    config = AddonConfig.from_anki(mw, ADDON_MODULE)
    mw.ChineseReadingConfig = config  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]


gui_hooks.profile_did_open.append(_init_profile)


def openChineseSettings():
    from aqt import mw

    if not mw.chineseReadingSettings:  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        mw.chineseReadingSettings = SettingsGui(  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
            mw,
            addonPath,
            mw.ChineseReadingCatalog,  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
            autoCssJs,
            openChineseSettings,
            config,
        )
    else:
        mw.chineseReadingSettings.config = config  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    mw.chineseReadingSettings.show()  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    if mw.chineseReadingSettings.windowState() == Qt.WindowState.WindowMinimized:  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        mw.chineseReadingSettings.setWindowState(Qt.WindowState.WindowNoState)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    mw.chineseReadingSettings.setFocus()  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    mw.chineseReadingSettings.activateWindow()  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]


def setupGuiMenu():
    from aqt import mw

    if getattr(mw, "_chinese_reading_menu_added", False):
        return
    mw._chinese_reading_menu_added = True  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]

    mw.ChineseReadingMenuSettings = []  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    mw.ChineseReadingMenuActions = []  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]

    setting = QAction("Chinese Reading Settings", mw)
    setting.triggered.connect(openChineseSettings)
    mw.ChineseReadingMenuSettings.append(setting)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]

    mw.form.menuTools.addSeparator()
    for act in mw.ChineseReadingMenuSettings:  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        mw.form.menuTools.addAction(act)
    for act in mw.ChineseReadingMenuActions:  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        mw.form.menuTools.addAction(act)


def checkProfile():
    from aqt import mw

    result = mw.pm.name in config.profiles or ("all" in config.profiles or "All" in config.profiles)
    _log.debug("checkProfile: profile=%s, in_config=%s, result=%s", mw.pm.name, config.profiles, result)
    return result


def setupButtons(righttopbtns, editor):
    from aqt import mw

    _log.debug("setupButtons called, checkProfile=%s", checkProfile())
    if not checkProfile():
        return righttopbtns
    editor._links["removeFormatting"] = lambda editor: mw.ChineseReading.cleanField(editor)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    if config.traditional_icons:
        duPath = os.path.join(addonPath, "icons", "tradDu.svg")
        shanPath = os.path.join(addonPath, "icons", "tradShan.svg")
    else:
        duPath = os.path.join(addonPath, "icons", "simpDu.svg")
        shanPath = os.path.join(addonPath, "icons", "simpShan.svg")

    righttopbtns.insert(0, editor._addButton(icon=shanPath, cmd="removeFormatting", tip="Hotkey: F10", id="删"))
    editor._links["addCReadings"] = lambda editor: mw.ChineseReading.addCReadings(editor)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    righttopbtns.insert(0, editor._addButton(icon=duPath, cmd="addCReadings", tip="Hotkey: F9", id="读"))
    _log.debug("setupButtons completed, editor._links keys: %s", list(editor._links.keys()))
    return righttopbtns


def setupShortcuts(cuts, editor):
    from aqt import mw

    _log.debug("setupShortcuts called, checkProfile=%s", checkProfile())
    if not checkProfile():
        return
    cuts.append(("F10", lambda: mw.ChineseReading.cleanField(editor)))  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    cuts.append(("F9", lambda: mw.ChineseReading.addCReadings(editor)))  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
    _log.debug("setupShortcuts completed, shortcuts count: %d", len(cuts))


def onRegenerate(browser):
    import anki.find
    from aqt import mw

    notes = browser.selectedNotes()
    if notes:
        fields = anki.find.fieldNamesForNotes(mw.col, notes)
        generateWidget = QDialog(None, Qt.WindowType.Window)
        generateWidget.setWindowTitle("Generate Chinese Readings")
        generateWidget.setWindowIcon(QIcon(join(addonPath, "icons", "chinese-reading.svg")))
        generateWidget.setMinimumWidth(480)
        generateWidget.resize(520, 220)

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        fm = QFormLayout()
        fm.setSpacing(6)
        fm.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        og = QLabel("Origin:")
        cb = QComboBox()
        cb.addItems(fields)
        fm.addRow(og, cb)

        dest = QLabel("Destination:")
        destCB = QComboBox()
        destCB.addItems(fields)
        fm.addRow(dest, destCB)

        om = QLabel("Output Mode:")
        omCB = QComboBox()
        omCB.addItems(["Add", "Overwrite", "If Empty"])
        fm.addRow(om, omCB)

        rt = QLabel("Reading Type:")
        rtCB = QComboBox()
        rtCB.addItems(["Pinyin", "Bopomofo", "Jyutping"])
        fm.addRow(rt, rtCB)

        layout.addLayout(fm)
        layout.addStretch()

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(8)
        btnLayout.addStretch()
        b4 = QPushButton("Add Readings")
        b4.clicked.connect(
            lambda: mw.ChineseReading.massGenerate(  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
                cb.currentText(),
                destCB.currentText(),
                omCB.currentText(),
                rtCB.currentText().lower(),
                notes,
                generateWidget,
            )
        )
        b4.setDefault(True)
        btnLayout.addWidget(b4)
        b5 = QPushButton("Remove Readings")
        b5.clicked.connect(lambda: mw.ChineseReading.massRemove(cb.currentText(), notes, generateWidget))  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        btnLayout.addWidget(b5)
        layout.addLayout(btnLayout)

        generateWidget.setLayout(layout)
        generateWidget.exec()
    else:
        show_info("Please select some cards before attempting to mass generate.")


def setupMenu(browser):
    _log.debug("setupMenu called, checkProfile=%s", checkProfile())
    if not checkProfile():
        return
    try:
        submenu = browser.form.menuEdit.addMenu("Chinese Reading")
        a = QAction("Generate Chinese Readings", browser)
        a.triggered.connect(lambda: onRegenerate(browser))
        submenu.addAction(a)
        _log.debug("setupMenu: submenu added successfully")
    except Exception as e:
        _log.error("setupMenu: failed: %s", e, exc_info=True)


current_path = os.path.abspath(".")
parent_path = os.path.dirname(current_path)
sys.path.append(parent_path)


def supportAccept(self):
    from aqt import mw

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
            config = mw.ChineseReadingMutation.save_config(delta)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        except Exception as e:
            showInfo("Invalid configuration: " + str(e))
            return
        mw.ChineseReadingConfig = config  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        autoCssJs.refreshConfig(config)
        mw.ChineseReading.refreshConfig(config)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        act = self.mgr.configUpdatedAction(self.addon)
        if act:
            act(new_conf)
        if not autoCssJs.injectWrapperElements():
            return

    saveGeom(self, "addonconf")
    saveSplitter(self.form.splitter, "addonconf")
    self.hide()


ogAccept = aqt.addons.ConfigEditor.accept
aqt.addons.ConfigEditor.accept = supportAccept  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

addHook("browser.setupMenus", setupMenu)
addHook("setupEditorButtons", setupButtons)
gui_hooks.editor_did_init_shortcuts.append(setupShortcuts)


def getFieldName(fieldId, note):
    from aqt import mw

    fields = mw.col.models.field_names(note.model())
    field = fields[int(fieldId)]
    return field


def bridgeReroute(self, cmd):
    from aqt import mw

    global currentKey
    _log.debug(
        "bridgeReroute called with cmd=%s, note.id=%s",
        cmd[:200] if len(cmd) > 200 else cmd,
        self.note.id if hasattr(self, "note") and self.note else "N/A",
    )

    if cmd.startswith("focus:") or cmd.startswith("blur:"):
        parts = cmd.split(":")
        if len(parts) >= 2:
            try:
                mw._lastFocusedFieldOrdinal = int(parts[1])  # type: ignore[attr-defined]
                _log.debug("Tracking focused field ordinal: %d", mw._lastFocusedFieldOrdinal)  # type: ignore[attr-defined]
            except ValueError:
                pass

    if checkProfile():
        if cmd.startswith("textToCReading"):
            splitList = cmd.split(":||:||:")
            _log.debug(
                "textToCReading split: parts_count=%d, note_id=%s",
                len(splitList),
                splitList[3] if len(splitList) > 3 else "N/A",
            )
            try:
                note_id_from_js = int(splitList[3])
                _log.debug("textToCReading note_id_from_js=%d, self.note.id=%d", note_id_from_js, self.note.id)
                if self.note.id == note_id_from_js:
                    field = getFieldName(splitList[2], self.note)
                    _log.debug(
                        "Calling finalizeReadings with text length=%d, field=%s",
                        len(splitList[1]) if splitList[1] else 0,
                        field,
                    )
                    mw.ChineseReading.finalizeReadings(splitList[1], field, self.note, self)  # type: ignore[attr-defined]
                else:
                    _log.debug("Note ID mismatch, skipping")
            except (ValueError, IndexError) as e:
                _log.error("Error parsing textToCReading command: %s", e)
            return
    if not cmd.startswith("textToCReading"):
        ogReroute(self, cmd)


ogReroute = aqt.editor.Editor.onBridgeCmd
aqt.editor.Editor.onBridgeCmd = bridgeReroute  # type: ignore[assignment]  # ty:ignore[invalid-assignment]


def _on_editor_focus_field(note, current_field_index: int) -> None:
    from aqt import mw

    mw._lastFocusedFieldOrdinal = current_field_index  # type: ignore[attr-defined]
    _log.debug("editor_did_focus_field: ordinal=%d", current_field_index)


gui_hooks.editor_did_focus_field.append(_on_editor_focus_field)
gui_hooks.profile_did_open.append(_rebuild_catalog)
