import platform
from os.path import join
from typing import Any

from anki.utils import is_win
from aqt.theme import theme_manager
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .._infra import show_ask, show_info
from .config import parse_active_field
from .mutation import ConfigDelta

versionNumber = "ver. 0.1.0"


class ClickableSVG(QSvgWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        QSvgWidget.__init__(self, parent)

    def mousePressEvent(self, a0):
        self.clicked.emit()


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, a0):
        self.clicked.emit()


class SettingsGui(QWidget):
    def __init__(self, mw, path, catalog, cssJsHandler, reboot, config):
        super().__init__()
        self.cssJsHandler = cssJsHandler
        self.reboot = reboot
        self.mutation = mw.ThaiReadingMutation
        self.catalog = catalog
        self.readingTypes = {
            "RTGS": "RTGS: The reading will be generated in Royal Thai General System of Transcription.",
            "IPA": "IPA: The reading will be generated in the International Phonetic Alphabet.",
            "Paiboon": "Paiboon: The reading will be generated in Paiboon phonetic notation "
            "(tone diacritics, doubled long vowels).",
        }
        self.sides = {
            "Front": "Front: Applies the display type to the front of the card.",
            "Back": "Back: Applies the display type to the back of the card.",
            "Both": "Both: Applies the display type to the front and back of the card.",
        }
        self.displayTypes = {
            "Thai": ["thai", "Thai: Displays text without tone coloring or reading information."],
            "Colored Thai": [
                "coloredthai",
                "Colored Thai: Displays text with tone coloring but no reading information.",
            ],
            "Hover": [
                "hover",
                (
                    "Hover: Displays text without tone coloring or reading information,\n"
                    "but displays an individual word's reading information when it is hovered."
                ),
            ],
            "Colored Hover": [
                "coloredhover",
                (
                    "Colored Hover: Displays text without tone coloring or reading information,\n"
                    "but displays an individual word's tone coloring and reading information when it is hovered."
                ),
            ],
            "Thai Reading": [
                "thaithai",
                "Thai Reading: Displays text without tone coloring but with reading information.",
            ],
            "Colored Thai Reading": [
                "coloredthaithai",
                "Colored Thai Reading: Displays text with tone coloring and reading information.",
            ],
            "Reading": [
                "reading",
                (
                    "Reading: Displays text in your chosen reading type without tone coloring.\n"
                    "Note that if a word's reading is not available it will be displayed in Thai."
                ),
            ],
            "Colored Reading": [
                "coloredreading",
                (
                    "Colored Reading: Displays text in your chosen reading type with tone coloring.\n"
                    "Note that if a word's reading is not available it will be displayed in Thai."
                ),
            ],
        }
        self.displayTranslation = {
            "thai": "Thai",
            "coloredthai": "Colored Thai",
            "hover": "Hover",
            "coloredhover": "Colored Hover",
            "thaithai": "Thai Reading",
            "coloredthaithai": "Colored Thai Reading",
            "reading": "Reading",
            "coloredreading": "Colored Reading",
        }
        self.rtTranslation = {"rtgs": "RTGS", "ipa": "IPA", "phonetics": "Paiboon"}
        self.mw = mw
        self.sortedProfiles: list = []
        self.sortedNoteTypes: list = []
        self.selectedRow = False
        self.initializing = False
        self.changingProfile = False
        self.buttonStatus = 0
        self.config = config
        self.tabs = QTabWidget()
        self.allFields = self.getAllFields()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.addonPath = path
        self.setWindowIcon(QIcon(join(self.addonPath, "icons", "thai-reading.svg")))
        self.selectedProfiles = []
        self.resetButton = QPushButton("Restore Defaults")
        self.cancelButton = QPushButton("Cancel")
        self.applyButton = QPushButton("Apply")
        self.mainLayout = QVBoxLayout()
        self.innerWidget = QWidget()
        self.setupMainLayout()
        self.tabs.addTab(self.getOptionsTab(), "Options")
        self.tabs.addTab(self.getAFTab(), "Active Fields")
        self.initTooltips()
        self.loadProfileCB()
        self.loadFontSize()
        self.loadProfilesList()
        self.loadDefaultReadingCB()
        self.loadRTGSToneStyle()
        self.loadColors()
        self.loadUseFileRefs()
        self.initActiveFieldsCB()
        self.loadAutoCSSJS()
        self.loadActiveFields()
        self.hotkeyEsc = QShortcut(QKeySequence("Esc"), self)
        self.hotkeyEsc.activated.connect(self.hide)
        self.handleAutoCSSJS()
        self.initHandlers()
        self.setLayout(self.ml)
        self.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        scaling_factor = max(0.7, min(1.5, width / 1000.0))
        new_font_size = int(10 * scaling_factor)
        self.setStyleSheet(f"font-size: {new_font_size}pt;")

    def resetDefaults(self):
        if show_ask("Are you sure you would like to restore the default settings? This cannot be undone."):
            defaults = self.mw.addonManager.addonConfigDefaults(self.addonPath)
            delta = ConfigDelta.from_dict(defaults)
            self.mutation.save_config(delta)
            self.close()
            self.mw.thaiReadingSettings = None
            self.reboot()

    def loadFontSize(self):
        self.fontSize.setValue(self.config.font_size)

    def loadAutoCSSJS(self):
        self.autoCSSJS.setChecked(self.config.auto_css_js_generation)

    def loadUseFileRefs(self):
        self.useFileRefs.setChecked(True)
        self.useFileRefs.setEnabled(False)

    def loadDefaultReadingCB(self):
        for key, value in self.readingTypes.items():
            self.defaultReading.addItem(key)
            self.defaultReading.setItemData(self.defaultReading.count() - 1, value, Qt.ItemDataRole.ToolTipRole)
        r = self.config.reading_type
        self.defaultReading.setCurrentText(self.rtTranslation.get(r, "RTGS"))

    def loadRTGSToneStyle(self):
        style = self.config.rtgs_tone_style
        if style == "marks":
            self.rtgsToneStyle.setCurrentIndex(0)
        else:
            self.rtgsToneStyle.setCurrentIndex(1)

    def getAllFields(self):
        fieldList = []
        for prof in self.catalog.profile_names():
            for model in self.catalog.model_names(prof):
                for f in self.catalog.field_names(prof, model):
                    if f not in fieldList:
                        fieldList.append(f)
        return self.ciSort(fieldList)

    def ciSort(self, lst):
        return sorted(lst, key=lambda s: s.lower())

    def loadColors(self):
        thColors = self.config.thai_tones
        for idx, c in enumerate(thColors):
            name = "t" + str(idx + 1) + "color"
            widget = getattr(self, name)
            widget.setText(c)
            widget.setStyleSheet(f"color: {c}; background-color: palette(window);")

    def getOptionsTab(self):
        self.profileCB = QComboBox()
        self.profileCB.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.addRemProfile = QPushButton("Add")
        self.currentProfiles = QLabel("None")
        self.defaultReading = QComboBox()
        self.defaultReading.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        self.t1color = QLineEdit()
        self.t2color = QLineEdit()
        self.t3color = QLineEdit()
        self.t4color = QLineEdit()
        self.t5color = QLineEdit()
        for c in (self.t1color, self.t2color, self.t3color, self.t4color, self.t5color):
            c.setFixedWidth(80)

        self.t1pb = QPushButton("Select Color")
        self.t2pb = QPushButton("Select Color")
        self.t3pb = QPushButton("Select Color")
        self.t4pb = QPushButton("Select Color")
        self.t5pb = QPushButton("Select Color")
        for b in (self.t1pb, self.t2pb, self.t3pb, self.t4pb, self.t5pb):
            b.setFixedWidth(75)

        self.useFileRefs = QCheckBox()

        self.fontSize = QSpinBox()
        self.fontSize.setMinimum(1)
        self.fontSize.setMaximum(200)

        self.rtgsToneStyle = QComboBox()
        self.rtgsToneStyle.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.rtgsToneStyle.addItem("Marks (sà wàt di)")
        self.rtgsToneStyle.addItem("Numbers (sa2 wat2 di1)")

        optionsTab = QWidget(self)
        optionsTab.setLayout(self.getOptionsLayout())
        scroll = QScrollArea()
        scroll.setWidget(optionsTab)
        scroll.setWidgetResizable(True)
        return scroll

    def getOptionsLayout(self):
        _M = 2
        ol = QVBoxLayout()
        ol.setContentsMargins(_M, _M, _M, _M)
        ol.setSpacing(0)

        # --- Profiles ---
        pgb = QGroupBox("Profiles")
        pg = QGridLayout()
        pg.setContentsMargins(_M * 3, _M * 3, _M * 3, _M * 3)
        pg.setSpacing(_M * 3)
        pg.addWidget(self.profileCB, 0, 0)
        pg.addWidget(self.addRemProfile, 0, 1)
        pg.addWidget(QLabel("Current:"), 0, 2)
        pg.addWidget(self.currentProfiles, 0, 3)
        pg.setColumnStretch(3, 1)
        pgb.setLayout(pg)
        ol.addWidget(pgb)

        # --- Generation ---
        ggb = QGroupBox("Generation")
        gg = QGridLayout()
        gg.setContentsMargins(_M * 3, _M * 3, _M * 3, _M * 3)
        gg.setSpacing(_M * 3)
        gg.addWidget(QLabel("Default Reading Type:"), 0, 0)
        gg.addWidget(self.defaultReading, 0, 1, 1, 2)
        gg.addWidget(QLabel("Use File References:"), 1, 0)
        gg.addWidget(self.useFileRefs, 1, 1)
        gg.setColumnStretch(2, 1)
        ggb.setLayout(gg)
        ol.addWidget(ggb)

        # --- Colors / Thai Tones ---
        cgb = QGroupBox("Colors")
        cg = QVBoxLayout()
        cg.setContentsMargins(_M * 3, _M * 3, _M * 3, _M * 3)
        cg.setSpacing(_M * 3)

        tgb = QGroupBox("Thai Tones")
        tg = QGridLayout()
        tg.setSpacing(_M * 3)
        tone_data = [
            ("Mid:", self.t1color, self.t1pb),
            ("Low:", self.t2color, self.t2pb),
            ("Falling:", self.t3color, self.t3pb),
            ("High:", self.t4color, self.t4pb),
            ("Rising:", self.t5color, self.t5pb),
        ]
        for idx, (label, color, btn) in enumerate(tone_data):
            r = idx // 3
            c = (idx % 3) * 3
            tg.addWidget(QLabel(label), r, c)
            tg.addWidget(color, r, c + 1)
            tg.addWidget(btn, r, c + 2)
        tgb.setLayout(tg)
        cg.addWidget(tgb)
        cgb.setLayout(cg)
        ol.addWidget(cgb)

        # --- Behavior ---
        bgb = QGroupBox("Behavior")
        bg = QGridLayout()
        bg.setContentsMargins(_M * 3, _M * 3, _M * 3, _M * 3)
        bg.setSpacing(_M * 3)
        bg.addWidget(QLabel("Reading Font Size:"), 0, 0)
        bg.addWidget(self.fontSize, 0, 1)
        bg.addWidget(QLabel("%"), 0, 2)
        bg.addWidget(QLabel("RTGS Tone Style:"), 1, 0)
        bg.addWidget(self.rtgsToneStyle, 1, 1, 1, 2)
        bg.setColumnStretch(3, 1)
        bgb.setLayout(bg)
        ol.addWidget(bgb)

        return ol

    def getAFTable(self):
        afTable = QTableWidget(self)
        if is_win and platform.release() == "10" and not theme_manager.night_mode:
            afTable.setStyleSheet(
                "QHeaderView::section{"
                "border-top:0px solid #D8D8D8;"
                "border-left:0px solid #D8D8D8;"
                "border-right:1px solid #D8D8D8;"
                "border-bottom: 1px solid #D8D8D8;"
                "background-color:white;"
                "padding:4px;"
                "}"
                "QTableCornerButton::section{"
                "border-top:0px solid #D8D8D8;"
                "border-left:0px solid #D8D8D8;"
                "border-right:1px solid #D8D8D8;"
                "border-bottom: 1px solid #D8D8D8;"
                "background-color:white;"
                "}"
            )
        afTable.setSortingEnabled(True)
        afTable.setColumnCount(8)
        afTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        afTable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tableHeader = afTable.horizontalHeader()
        afTable.setHorizontalHeaderLabels(
            ["Profile", "Note Type", "Card Type", "Field", "Side", "Display Type", "Reading Type", ""]
        )
        assert tableHeader is not None
        tableHeader.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tableHeader.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tableHeader.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tableHeader.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        tableHeader.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        tableHeader.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        tableHeader.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        tableHeader.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        afTable.setColumnWidth(7, 40)
        afTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return afTable

    def sizeAFLayout(self):
        self.profileAF.setMinimumWidth(120)
        self.noteTypeAF.setMinimumWidth(120)
        self.cardTypeAF.setMinimumWidth(120)
        self.fieldAF.setMinimumWidth(120)
        self.sideAF.setMinimumWidth(120)
        self.displayAF.setMinimumWidth(120)
        self.readingAF.setMinimumWidth(120)

    def getAFLayout(self):
        self.sizeAFLayout()
        afl = QVBoxLayout()

        afh1 = QHBoxLayout()
        afh1.addWidget(QLabel("Auto CSS & JS Generation:"))
        afh1.addWidget(self.autoCSSJS)
        afl.addLayout(afh1)

        afh2 = QHBoxLayout()
        afh2.addWidget(self.profileAF)
        afh2.addWidget(self.noteTypeAF)
        afh2.addWidget(self.cardTypeAF)
        afh2.addWidget(self.fieldAF)
        afh2.addWidget(self.sideAF)
        afh2.addWidget(self.displayAF)
        afh2.addWidget(self.readingAF)
        afl.addLayout(afh2)

        afh3 = QHBoxLayout()
        afh3.addWidget(self.addEditAF)
        afl.addLayout(afh3)

        afl.addWidget(self.afTable)

        return afl

    def getAFTab(self):
        self.autoCSSJS = QCheckBox()
        self.profileAF = QComboBox()
        self.noteTypeAF = QComboBox()
        self.cardTypeAF = QComboBox()
        self.fieldAF = QComboBox()
        self.sideAF = QComboBox()
        self.displayAF = QComboBox()
        self.readingAF = QComboBox()
        self.addEditAF = QPushButton("Add")
        self.afTable = self.getAFTable()

        afTab = QWidget(self)
        afTab.setLayout(self.getAFLayout())
        scroll = QScrollArea()
        scroll.setWidget(afTab)
        scroll.setWidgetResizable(True)
        return scroll

    def initTooltips(self):
        self.profileCB.setToolTip(
            "These are the profiles that the add-on will be active on.\n"
            'When set to "All", the add-on will be active on all profiles.'
        )
        self.addRemProfile.setToolTip("Add/Remove a profile.")
        self.defaultReading.setToolTip(
            "Default reading system (RTGS / IPA / Paiboon) used for fields not covered by an Active Field entry."
        )

        self.t1pb.setToolTip("Select the color for mid tone characters.")
        self.t2pb.setToolTip("Select the color for low tone characters.")
        self.t3pb.setToolTip("Select the color for falling tone characters.")
        self.t4pb.setToolTip("Select the color for high tone characters.")
        self.t5pb.setToolTip("Select the color for rising tone characters.")

        self.fontSize.setToolTip(
            "The percentage font size of readings in relation to the characters.\nThe range is from 1% to 200%."
        )

        self.autoCSSJS.setToolTip(
            "Enable or disable automatic CSS and JavaScript handling.\n"
            "Disabling this option is not recommended if you are not familiar with these technologies."
        )
        self.useFileRefs.setToolTip(
            "When enabled, CSS and JS will be written to collection.media/ as standalone files."
        )
        self.rtgsToneStyle.setToolTip(
            "RTGS only: choose how tone is indicated.\n"
            "Marks: sà wàt di (tone marks on vowels, conventional style)\n"
            "Numbers: sa2 wat2 di1 (digit suffix per syllable)\n"
            "IPA and Paiboon always use their native tone notation."
        )
        self.profileAF.setToolTip("Profile: Select the profile.")
        self.noteTypeAF.setToolTip("Note Type: Select the note type.")
        self.cardTypeAF.setToolTip("Card Type: Select the card type.")
        self.fieldAF.setToolTip("Field: Select the field.")
        self.sideAF.setToolTip("Side: Select the side of the card where the display type setting will apply.")
        self.displayAF.setToolTip(
            "Display Type: Select the display type,\nhover over a display type for functionality details."
        )
        self.readingAF.setToolTip(
            "Reading Type: Select the reading system (RTGS / IPA / Paiboon) "
            "used when generating readings for this card type."
        )

    def initHandlers(self):
        self.t1pb.clicked.connect(lambda: self.openDialogColor(self.t1color))
        self.t2pb.clicked.connect(lambda: self.openDialogColor(self.t2color))
        self.t3pb.clicked.connect(lambda: self.openDialogColor(self.t3color))
        self.t4pb.clicked.connect(lambda: self.openDialogColor(self.t4color))
        self.t5pb.clicked.connect(lambda: self.openDialogColor(self.t5color))
        self.addRemProfile.clicked.connect(
            lambda: self.addRemoveFromList(
                self.profileCB.currentText(), self.addRemProfile, self.currentProfiles, self.selectedProfiles, True
            )
        )
        self.profileCB.currentIndexChanged.connect(
            lambda: self.profAltSimpTradChange(self.profileCB.currentText(), self.addRemProfile, self.selectedProfiles)
        )

        self.profileAF.currentIndexChanged.connect(self.profileChange)
        self.noteTypeAF.currentIndexChanged.connect(self.noteTypeChange)
        self.cardTypeAF.currentIndexChanged.connect(self.selectionChange)
        self.fieldAF.currentIndexChanged.connect(self.selectionChange)
        self.sideAF.currentIndexChanged.connect(self.selectionChange)
        self.displayAF.currentIndexChanged.connect(self.selectionChange)
        self.readingAF.currentIndexChanged.connect(self.selectionChange)

        self.afTable.cellClicked.connect(self.loadSelectedRow)

        self.addEditAF.clicked.connect(self.performAddEdit)
        self.applyButton.clicked.connect(self.saveConfig)
        self.resetButton.clicked.connect(self.resetDefaults)
        self.cancelButton.clicked.connect(self.close)
        self.autoCSSJS.toggled.connect(self.handleAutoCSSJS)

    def handleAutoCSSJS(self):
        if self.autoCSSJS.isChecked():
            self.profileAF.setEnabled(True)
            self.noteTypeAF.setEnabled(True)
            self.cardTypeAF.setEnabled(True)
            self.fieldAF.setEnabled(True)
            self.sideAF.setEnabled(True)
            self.displayAF.setEnabled(True)
            self.addEditAF.setEnabled(True)
            self.readingAF.setEnabled(True)
            self.afTable.setEnabled(True)
        else:
            self.profileAF.setEnabled(False)
            self.noteTypeAF.setEnabled(False)
            self.cardTypeAF.setEnabled(False)
            self.fieldAF.setEnabled(False)
            self.sideAF.setEnabled(False)
            self.displayAF.setEnabled(False)
            self.addEditAF.setEnabled(False)
            self.readingAF.setEnabled(False)
            self.afTable.setEnabled(False)

    def profileChange(self):
        if self.initializing:
            return
        self.changingProfile = True
        self.noteTypeAF.clear()
        self.cardTypeAF.clear()
        self.fieldAF.clear()
        if self.profileAF.currentIndex() == 0:
            self.loadAllNotes()
        else:
            prof = self.profileAF.currentText()
            for noteType in self.ciSort(list(self.catalog.model_names(prof))):
                self.noteTypeAF.addItem(noteType)
                self.noteTypeAF.setItemData(
                    self.noteTypeAF.count() - 1, noteType + " (Prof:" + prof + ")", Qt.ItemDataRole.ToolTipRole
                )
                self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, prof + ":pN:" + noteType)
        self.loadCardTypesFields()
        self.changingProfile = False
        self.selectionChange()

    def noteTypeChange(self):
        if self.initializing:
            return
        if not self.changingProfile:
            self.cardTypeAF.clear()
            self.fieldAF.clear()
            self.loadCardTypesFields()
        self.selectionChange()

    def resetWindow(self):
        self.initializing = True
        self.buttonStatus = 0
        self.addEditAF.setText("Add")
        self.selectedRow: Any = False
        self.clearAllAF()
        self.initActiveFieldsCB()
        self.initializing = False

    def selectionChange(self):
        if self.buttonStatus == 1:
            self.buttonStatus = 2
            self.addEditAF.setText("Save Changes")

    def performAddEdit(self):
        if self.buttonStatus == 1:
            self.resetWindow()
        else:
            profile = self.profileAF.currentText()
            nt = self.noteTypeAF.itemData(self.noteTypeAF.currentIndex()).split(":pN:")[1]
            ct = self.cardTypeAF.currentText()
            field = self.fieldAF.currentText()
            side = self.sideAF.currentText()
            dt = self.displayAF.currentText()
            rt = self.readingAF.currentText()
            if profile != "" and nt != "" and ct != "" and field != "" and side != "" and dt != "" and rt != "":
                if self.buttonStatus == 0:
                    self.addToList(profile, nt, ct, field, side, dt, rt)
                elif self.buttonStatus == 2:
                    self.editEntry(profile, nt, ct, field, side, dt, rt)

    def dupeRow(self, afList, profile, nt, ct, field, side, dt, selRow=False):
        for i in range(afList.rowCount()):
            if selRow is not False:
                if i == selRow[0].row():
                    continue
            if (
                (afList.item(i, 0).text() == profile or afList.item(i, 0).text() == "All" or profile == "All")
                and afList.item(i, 1).text() == nt
                and (afList.item(i, 2).text() == ct or afList.item(i, 2).text() == "All" or ct == "All")
                and afList.item(i, 3).text() == field
                and (afList.item(i, 4).text() == side or afList.item(i, 4).text() == "Both" or side == "Both")
            ):
                return i + 1
        return False

    def addToList(self, profile, nt, ct, field, side, dt, rt):
        afList = self.afTable
        found = self.dupeRow(afList, profile, nt, ct, field, side, dt)
        if found:
            show_info(
                "This row cannot be added because row #"
                + str(found)
                + " in the Active Fields List already targets "
                + "this given field and side combination. Please review that entry and try again.",
                level="err",
            )
        else:
            afList.setSortingEnabled(False)
            rc = afList.rowCount()
            afList.setRowCount(rc + 1)
            afList.setItem(rc, 0, QTableWidgetItem(profile))
            afList.setItem(rc, 1, QTableWidgetItem(nt))
            afList.setItem(rc, 2, QTableWidgetItem(ct))
            afList.setItem(rc, 3, QTableWidgetItem(field))
            afList.setItem(rc, 4, QTableWidgetItem(side))
            afList.setItem(rc, 5, QTableWidgetItem(dt))
            afList.setItem(rc, 6, QTableWidgetItem(rt))
            deleteButton = QPushButton("X")
            deleteButton.setFixedWidth(40)
            deleteButton.clicked.connect(self.removeRow)
            afList.setCellWidget(rc, 7, deleteButton)
            afList.setSortingEnabled(True)

    def initEditMode(self):
        self.buttonStatus = 1
        self.addEditAF.setText("Cancel")

    def editEntry(self, profile, nt, ct, field, side, dt, rt):
        afList = self.afTable
        rc = self.selectedRow
        found = self.dupeRow(afList, profile, nt, ct, field, side, dt, rc)
        if found:
            show_info(
                "This row cannot be edited in this manner because row #"
                + str(found)
                + " in the Active Fields List already targets "
                + "this given field and side combination. Please review that entry and try again.",
                level="err",
            )
        else:
            afList.setSortingEnabled(False)
            rc[0].setText(profile)
            rc[1].setText(nt)
            rc[2].setText(ct)
            rc[3].setText(field)
            rc[4].setText(side)
            rc[5].setText(dt)
            rc[6].setText(rt)
            afList.setSortingEnabled(True)
        self.resetWindow()

    def removeRow(self):
        if show_ask("Are you sure you would like to remove this entry from the active field list?"):
            self.afTable.removeRow(self.afTable.selectionModel().currentIndex().row())
            self.resetWindow()

    def loadSelectedRow(self, row, col):
        afList = self.afTable
        prof = afList.item(row, 0).text()
        nt = afList.item(row, 1).text()
        ct = afList.item(row, 2).text()
        field = afList.item(row, 3).text()
        side = afList.item(row, 4).text()
        dt = afList.item(row, 5).text()
        rt = afList.item(row, 6).text()
        if prof.lower() == "all":
            loaded = self.unspecifiedProfileLoad(nt, ct, field, side, dt, rt)
        else:
            loaded = self.specifiedProfileLoad(prof, nt, ct, field, side, dt, rt)
        if loaded:
            self.initEditMode()
            self.selectedRow = [
                afList.item(row, 0),
                afList.item(row, 1),
                afList.item(row, 2),
                afList.item(row, 3),
                afList.item(row, 4),
                afList.item(row, 5),
                afList.item(row, 6),
            ]

    def unspecifiedProfileLoad(self, nt, ct, field, side, dt, rt):
        self.profileAF.setCurrentIndex(0)
        if self.findFirstNoteCardFieldMatch(nt, ct, field):
            index = self.sideAF.findText(side, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.sideAF.setCurrentIndex(index)
            index = self.displayAF.findText(dt, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.displayAF.setCurrentIndex(index)
            index = self.readingAF.findText(rt, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.readingAF.setCurrentIndex(index)
            return True
        else:
            return False

    def findFirstNoteCardFieldMatch(self, nt, ct, field):
        for i in range(self.noteTypeAF.count()):
            if self.noteTypeAF.itemText(i).startswith(nt):
                self.noteTypeAF.setCurrentIndex(i)
                if ct.lower() == "all":
                    ci = 0
                else:
                    ci = self.cardTypeAF.findText(ct, Qt.MatchFlag.MatchFixedString)
                if ci >= 0:
                    fi = self.fieldAF.findText(field, Qt.MatchFlag.MatchFixedString)
                    if fi >= 0:
                        self.noteTypeAF.setCurrentIndex(i)
                        self.cardTypeAF.setCurrentIndex(ci)
                        self.fieldAF.setCurrentIndex(fi)
                        return True
        return False

    def specifiedProfileLoad(self, prof, nt, ct, field, side, dt, rt):
        index = self.profileAF.findText(prof, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.profileAF.setCurrentIndex(index)
        index = self.noteTypeAF.findText(nt, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.noteTypeAF.setCurrentIndex(index)
        index = self.cardTypeAF.findText(ct, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.cardTypeAF.setCurrentIndex(index)
        index = self.fieldAF.findText(field, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.fieldAF.setCurrentIndex(index)
        index = self.sideAF.findText(side, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.sideAF.setCurrentIndex(index)
        index = self.displayAF.findText(dt, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.displayAF.setCurrentIndex(index)
        index = self.readingAF.findText(rt, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.readingAF.setCurrentIndex(index)
        return True

    def loadProfileCB(self):
        pcb = self.profileCB
        pcb.addItem("All")
        pcb.addItem("──────")
        m = pcb.model()
        assert m is not None
        m.item(pcb.count() - 1).setEnabled(False)
        m.item(pcb.count() - 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        for prof in self.catalog.profile_names():
            pcb.addItem(prof)
            pcb.setItemData(pcb.count() - 1, prof, Qt.ItemDataRole.ToolTipRole)

    def loadProfilesList(self):
        pl = self.currentProfiles
        profs = self.config.profiles
        if len(profs) == 0:
            pl.setText("<i>None currently selected.</i>")
        else:
            profl = []
            currentSelection = self.profileCB.currentText()
            for prof in profs:
                if prof.lower() == "all":
                    profl.append("All")
                    self.selectedProfiles = ["All"]
                    if currentSelection == "All":
                        self.addRemProfile.setText("Remove")
                        self.selectedProfiles = profl
                        pl.setText("<i>All</i>")
                        return
                profl.append(prof)
                if currentSelection == prof:
                    self.addRemProfile.setText("Remove")
            self.selectedProfiles = profl
            pl.setText("<i>" + ", ".join(profl) + "</i>")

    def setupMainLayout(self):
        self.ml = QVBoxLayout()
        self.ml.setContentsMargins(0, 0, 0, 0)
        self.ml.addWidget(self.tabs)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.resetButton)
        buttons.addWidget(self.cancelButton)
        buttons.addWidget(self.applyButton)
        self.ml.addLayout(buttons)

    def initActiveFieldsCB(self):
        self.profileAF.clear()
        self.noteTypeAF.clear()
        self.cardTypeAF.clear()
        self.fieldAF.clear()
        self.sideAF.clear()
        self.displayAF.clear()
        self.readingAF.clear()

        self.profileAF.addItem("All")
        self.profileAF.setItemData(0, "All profiles", Qt.ItemDataRole.ToolTipRole)
        self.displayAF.addItems(list(self.displayTypes.keys()))
        self.sideAF.addItems(list(self.sides.keys()))
        self.readingAF.addItems(list(self.readingTypes.keys()))
        self.readingAF.setCurrentText("RTGS")
        self.loadAllNotes()

    def loadAllNotes(self):
        for prof in self.ciSort(list(self.catalog.profile_names())):
            for noteType in self.ciSort(list(self.catalog.model_names(prof))):
                if self.noteTypeAF.findText(noteType) == -1:
                    self.noteTypeAF.addItem(noteType)
                    self.noteTypeAF.setItemData(
                        self.noteTypeAF.count() - 1,
                        noteType + " (Prof:" + prof + ")",
                        Qt.ItemDataRole.ToolTipRole,
                    )
                    self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, prof + ":pN:" + noteType)

    def loadCardTypesFields(self):
        selected = self.noteTypeAF.currentData()
        if selected is not None:
            parts = selected.split(":pN:")
            prof = parts[0]
            nt = parts[1]
            self.cardTypeAF.clear()
            self.cardTypeAF.addItem("All")
            for ct in self.catalog.card_type_names(prof, nt):
                self.cardTypeAF.addItem(ct)
            self.fieldAF.clear()
            for f in self.catalog.field_names(prof, nt):
                self.fieldAF.addItem(f)

    def clearAllAF(self):
        self.initActiveFieldsCB()

    def loadActiveFields(self):
        self.afTable.setRowCount(0)
        for entry in self.config.active_fields:
            try:
                parsed = parse_active_field(entry)
            except ValueError:
                continue
            profile = parsed.profile
            nt = parsed.note_type
            ct = parsed.card_type
            field = parsed.field
            side = parsed.side
            dt = self.displayTranslation.get(parsed.display_type, parsed.display_type)
            rt = (
                parsed.reading_type
                if parsed.reading_type != "default"
                else self.rtTranslation.get(self.config.reading_type, self.config.reading_type)
            )
            if profile == "all":
                profile = "All"
            self.addToList(profile, nt, ct, field, side.capitalize(), dt, rt)

    def saveConfig(self):
        profiles = self.selectedProfiles if self.selectedProfiles else ["all"]
        afList = []
        for row in range(self.afTable.rowCount()):
            profile = self.afTable.item(row, 0).text()
            if profile == "All":
                profile = "all"
            nt = self.afTable.item(row, 1).text()
            ct = self.afTable.item(row, 2).text()
            field = self.afTable.item(row, 3).text()
            side = self.afTable.item(row, 4).text().lower()
            dt = self.displayTypes[self.afTable.item(row, 5).text()][0]
            rt_text = self.afTable.item(row, 6).text()
            rt = (
                "default"
                if rt_text == "Default"
                else next((k for k, v in self.rtTranslation.items() if v == rt_text), "default")
            )
            afList.append(f"{dt};{profile};{nt};{ct};{field};{side};{rt}")

        _rt_rev = {"RTGS": "rtgs", "IPA": "ipa", "Paiboon": "phonetics"}
        delta = ConfigDelta(
            profiles=profiles,
            reading_type=_rt_rev.get(self.defaultReading.currentText(), "rtgs"),
            font_size=self.fontSize.value(),
            use_file_references=self.useFileRefs.isChecked(),
            thai_tones=(
                self.t1color.text(),
                self.t2color.text(),
                self.t3color.text(),
                self.t4color.text(),
                self.t5color.text(),
            ),
            active_fields=tuple(afList) if afList else tuple(),
            auto_css_js_generation=self.autoCSSJS.isChecked(),
            rtgs_tone_style="marks" if self.rtgsToneStyle.currentIndex() == 0 else "numbers",
        )

        try:
            config = self.mutation.save_config(delta)
        except Exception as e:
            show_info("Invalid configuration: " + str(e), level="err")
            return

        self.config = config
        self.cssJsHandler.refreshConfig(config)
        self.mw.ThaiReading.refreshConfig(config)
        self.reboot()

    def openDialogColor(self, lineEdit):
        color = QColorDialog.getColor()
        if color.isValid():
            lineEdit.setText(color.name())
            lineEdit.setStyleSheet(f"color: {color.name()}; background-color: palette(window);")

    def profAltSimpTradChange(self, value, button, vList):
        if value in vList:
            button.setText("Remove")
        else:
            button.setText("Add")

    def addRemoveFromList(self, value, button, lWidget, vList, profiles=False):
        if button.text() == "Remove":
            if value in vList:
                vList.remove(value)
                lWidget.setText("<i>" + ", ".join(vList) + "</i>")
                button.setText("Add")
                if len(vList) == 0 or (len(vList) == 1 and vList[0].lower() == "none"):
                    lWidget.setText("<i>None currently selected.</i>")
        else:
            if profiles and value == "All":
                vList.clear()
                vList.append("All")
                lWidget.setText("<i>All</i>")
                button.setText("Remove")
            else:
                if profiles:
                    if "All" in vList:
                        vList.remove("All")
                if len(vList) == 1 and (vList[0].lower() == "none" or vList[0] == ""):
                    vList.remove(vList[0])
                vList.append(value)
                lWidget.setText("<i>" + ", ".join(vList) + "</i>")
                button.setText("Remove")
