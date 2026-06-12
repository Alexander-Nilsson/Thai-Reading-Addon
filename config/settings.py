#
#
import platform
from operator import itemgetter
from os.path import dirname, join
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
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .._infra.utils import show_ask, show_info  # ty: ignore[unresolved-import]
from .config import ActiveField, parse_active_field, serialize_active_field
from .mutation import ConfigDelta

versionNumber = "ver. 1.2.3"


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

    def mousePressEvent(self, a0):  # ty:ignore[invalid-method-override]
        self.clicked.emit()


class SettingsGui(QWidget):
    def __init__(self, mw, path, catalog, cssJSHandler, reboot, config):
        super().__init__()
        self.cssJSHandler = cssJSHandler
        self.reboot = reboot
        self.mutation = mw.ChineseReadingMutation
        self.catalog = catalog
        self.readingTypes = {
            "Pinyin": "Pinyin: The reading will be generated in pinyin.",
            "Bopomofo": "Bopomofo: The reading will be generated in bopomofo/zhuyin.",
            "Jyutping": "Jyutping: The reading will be generated in jyutping.",
        }
        self.sides = {
            "Front": "Front: Applies the display type to the front of the card.",
            "Back": "Back: Applies the display type to the back of the card.",
            "Both": "Both: Applies the display type to the front and back of the card.",
        }
        self.displayTypes = {
            "Hanzi": ["hanzi", "Hanzi: Displays text without tone coloring or reading information."],
            "Colored Hanzi": [
                "coloredhanzi",
                "Colored Hanzi: Displays text with tone coloring but no reading information.",
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
            "Hanzi Reading": [
                "hanzireading",
                "Hanzi Reading: Displays text without tone coloring but with reading information.",
            ],
            "Colored Hanzi Reading": [
                "coloredhanzireading",
                "Colored Hanzi Reading: Displays text with tone coloring and reading information.",
            ],
            "Reading": [
                "reading",
                (
                    "Reading: Displays text in your chosen reading type without tone coloring.\n"
                    "Note that if a word's reading is not available it will be displayed in hanzi."
                ),
            ],
            "Colored Reading": [
                "coloredreading",
                (
                    "Colored Reading: Displays text in your chosen reading type with tone coloring.\n"
                    "Note that if a word's reading is not available it will be displayed in hanzi."
                ),
            ],
        }
        self.displayTranslation = {
            "hanzi": "Hanzi",
            "coloredhanzi": "Colored Hanzi",
            "hover": "Hover",
            "coloredhover": "Colored Hover",
            "hanzireading": "Hanzi Reading",
            "coloredhanzireading": "Colored Hanzi Reading",
            "reading": "Reading",
            "coloredreading": "Colored Reading",
        }
        self.rtTranslation = {"pinyin": "Pinyin", "bopomofo": "Bopomofo", "jyutping": "Jyutping"}
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
        # self.setMinimumSize(800, 550);
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        # self.setWindowTitle("Chinese Reading Settings (%s)"%versionNumber)
        self.addonPath = path
        self.setWindowIcon(QIcon(join(self.addonPath, "icons", "chinese-reading.svg")))
        self.selectedProfiles = []
        self.selectedAltFields = []
        self.selectedSimpFields = []
        self.selectedTradFields = []
        self.selectedGraphFields = []
        self.resetButton = QPushButton("Restore Defaults")
        self.cancelButton = QPushButton("Cancel")
        self.applyButton = QPushButton("Apply")
        self.mainLayout = QVBoxLayout()
        self.innerWidget = QWidget()
        self.setupMainLayout()
        self.tabs.addTab(self.getOptionsTab(), "Options")
        self.tabs.addTab(self.getAFTab(), "Active Fields")
        # self.tabs.addTab(self.getAboutTab(), "About")
        self.initTooltips()
        self.loadProfileCB()
        self.loadFontSize()
        self.loadProfilesList()
        self.loadDefaultReadingCB()
        self.loadBopoNumbers()
        self.loadAltSimpTradFieldsCB()
        self.loadFieldsList(1)
        self.loadFieldsList(2)
        self.loadFieldsList(3)
        self.loadHanziReadingConversion()
        self.loadColors()
        self.loadTradIcons()
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
        # Scale font size based on window width
        # Base width is 1000px, base font size is 10pt
        width = self.width()
        scaling_factor = max(0.7, min(1.5, width / 1000.0))
        new_font_size = int(10 * scaling_factor)
        self.setStyleSheet(f"font-size: {new_font_size}pt;")

    def resetDefaults(self):
        if show_ask("Are you sure you would like to restore the default settings? This cannot be undone."):
            defaults = self.mw.addonManager.addonConfigDefaults(dirname(__file__))
            delta = ConfigDelta.from_dict(defaults)
            self.mutation.save_config(delta)
            self.close()
            self.mw.chineseReadingSettings = None
            self.reboot()

    def loadFontSize(self):
        self.fontSize.setValue(self.config.font_size)

    def loadAutoCSSJS(self):
        self.autoCSSJS.setChecked(self.config.auto_css_js_generation)

    def loadTradIcons(self):
        self.tradIcons.setChecked(self.config.traditional_icons)

    def loadUseFileRefs(self):
        self.useFileRefs.setChecked(self.config.use_file_references)

    def loadBopoNumbers(self):
        self.bopo2Number.setChecked(self.config.bopomofo_tones_to_number)

    def loadDefaultReadingCB(self):
        for key, value in self.readingTypes.items():
            self.defaultReading.addItem(key)
            self.defaultReading.setItemData(self.defaultReading.count() - 1, value, Qt.ItemDataRole.ToolTipRole)
        r = self.config.reading_type
        self.defaultReading.setCurrentText(self.rtTranslation[r])

    def loadHanziReadingConversion(self):
        hanziConTypes = {
            "None": "None: No conversion.",
            "Simplified": "Simplified: Traditional characters are converted to simplified characters.",
            "Traditional": "Traditional: Simplified characters are converted to traditional characters.",
        }
        readingConTypes = {
            "None": "None: No conversion.",
            "Pinyin": "Pinyin: Bopomofo/zhuyin is converted to pinyin.",
            "Bopomofo": "Bopomofo: Pinyin is converted to bopomofo/zhuyin.",
        }
        for key, value in hanziConTypes.items():
            self.hanziConversion.addItem(key)
            self.hanziConversion.setItemData(self.hanziConversion.count() - 1, value, Qt.ItemDataRole.ToolTipRole)
        for key, value in readingConTypes.items():
            self.readingConversion.addItem(key)
            self.readingConversion.setItemData(self.readingConversion.count() - 1, value, Qt.ItemDataRole.ToolTipRole)
        hc = self.config.hanzi_conversion
        rc = self.config.reading_conversion
        self.hanziConversion.setCurrentText(hc)
        self.readingConversion.setCurrentText(rc)

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
        mColors = self.config.mandarin_tones
        cColors = self.config.cantonese_tones
        for idx, c in enumerate(mColors):
            name = "m" + str(idx + 1) + "color"
            widget = getattr(self, name)
            widget.setText(c)
            widget.setStyleSheet("color:" + c + ";")

        for idx, c in enumerate(cColors):
            name = "c" + str(idx + 1) + "color"
            widget = getattr(self, name)
            widget.setText(c)
            widget.setStyleSheet("color:" + c + ";")

    def getOptionsTab(self):
        self.profileCB = QComboBox()
        self.addRemProfile = QPushButton("Add")
        self.currentProfiles = QLabel("None")
        self.defaultReading = QComboBox()
        self.bopo2Number = QCheckBox()
        self.altCB = QComboBox()
        self.simpCB = QComboBox()
        self.tradCB = QComboBox()
        self.addRemAlt = QPushButton("Add")
        self.addRemSimp = QPushButton("Add")
        self.addRemTrad = QPushButton("Add")
        self.altLayout = QWidget()
        self.simpLayout = QWidget()
        self.tradLayout = QWidget()
        self.altOW = QRadioButton(self.altLayout)
        self.altIfE = QRadioButton(self.altLayout)
        self.altWithSep = QRadioButton(self.altLayout)
        self.altSep = QLineEdit()
        self.simpOW = QRadioButton(self.simpLayout)
        self.simpIfE = QRadioButton(self.simpLayout)
        self.simpWithSep = QRadioButton(self.simpLayout)
        self.simpSep = QLineEdit()
        self.tradOW = QRadioButton(self.tradLayout)
        self.tradIfE = QRadioButton(self.tradLayout)
        self.tradWithSep = QRadioButton(self.tradLayout)
        self.tradSep = QLineEdit()
        self.currentAlt = QLabel("None")
        self.currentSimp = QLabel("None")
        self.currentTrad = QLabel("None")

        self.m1color = QLineEdit()
        self.m2color = QLineEdit()
        self.m3color = QLineEdit()
        self.m4color = QLineEdit()
        self.m5color = QLineEdit()

        self.c1color = QLineEdit()
        self.c2color = QLineEdit()
        self.c3color = QLineEdit()
        self.c4color = QLineEdit()
        self.c5color = QLineEdit()
        self.c6color = QLineEdit()

        self.m1pb = QPushButton("Select Color")
        self.m2pb = QPushButton("Select Color")
        self.m3pb = QPushButton("Select Color")
        self.m4pb = QPushButton("Select Color")
        self.m5pb = QPushButton("Select Color")

        self.c1pb = QPushButton("Select Color")
        self.c2pb = QPushButton("Select Color")
        self.c3pb = QPushButton("Select Color")
        self.c4pb = QPushButton("Select Color")
        self.c5pb = QPushButton("Select Color")
        self.c6pb = QPushButton("Select Color")

        self.hanziConversion = QComboBox()
        self.readingConversion = QComboBox()
        self.tradIcons = QCheckBox()
        self.useFileRefs = QCheckBox()

        self.fontSize = QSpinBox()
        self.fontSize.setMinimum(1)
        self.fontSize.setMaximum(200)

        optionsTab = QWidget(self)
        optionsTab.setLayout(self.getOptionsLayout())
        return optionsTab

    def sizeOptionsWidgets(self):
        self.profileCB.setMinimumWidth(120)
        self.addRemProfile.setMinimumWidth(80)
        self.defaultReading.setMinimumWidth(100)
        self.fontSize.setMinimumWidth(80)

    def getOptionsLayout(self):
        self.sizeOptionsWidgets()
        ol = QVBoxLayout()  # options layout
        ol.setContentsMargins(10, 10, 10, 10)
        ol.setSpacing(10)

        pgb = QGroupBox()  # profile group box
        pgbv = QVBoxLayout()
        pgbv.setContentsMargins(10, 10, 10, 10)
        pgbv.setSpacing(10)
        pgbt = QLabel("<b>Profiles</b>")
        pgbh = QHBoxLayout()
        pgbh.setSpacing(10)
        pgbh.addWidget(self.profileCB)
        pgbh.addWidget(self.addRemProfile)
        pgbh.addStretch()
        pgbh2 = QHBoxLayout()
        pgbh2.setSpacing(10)
        l1 = QLabel("Current Profiles:")
        l1.setMinimumWidth(100)
        pgbh2.addWidget(l1)
        pgbh2.addWidget(self.currentProfiles)
        pgbh2.addStretch()
        pgbv.addWidget(pgbt)
        pgbv.addLayout(pgbh)
        pgbv.addLayout(pgbh2)
        pgb.setLayout(pgbv)
        ol.addWidget(pgb)

        ggb = QGroupBox()  # generation group box
        ggb2 = QGroupBox("Field Settings")
        ggbv = QVBoxLayout()
        ggbv2 = QVBoxLayout()
        ggbt = QLabel("<b>Generation</b>")
        ggbh = QHBoxLayout()
        ggbh.addWidget(QLabel("Default Reading Type:"))
        ggbh.addWidget(self.defaultReading)
        ggbh.addWidget(QLabel("Bopomofo Tones To Numbers:"))
        ggbh.addWidget(self.bopo2Number)
        ggbh.addStretch()

        ggbh2 = QVBoxLayout()
        l2 = QLabel("Alternate Field:")
        l2.setMinimumWidth(100)
        h2 = QHBoxLayout()
        h2.addWidget(self.altCB)
        h2.addWidget(self.addRemAlt)
        h2.addWidget(self.altOW)
        h2.addWidget(QLabel("Overwrite"))
        h2.addWidget(self.altIfE)
        h2.addWidget(QLabel("If Empty"))
        h2.addWidget(self.altWithSep)
        h2.addWidget(QLabel("Add with Separator"))
        h2.addWidget(self.altSep)
        h2.addStretch()
        ggbh2.addWidget(l2)
        ggbh2.addLayout(h2)
        ggbh2.setContentsMargins(0, 0, 0, 0)
        self.altLayout.setLayout(ggbh2)

        ggbh4 = QVBoxLayout()
        l3 = QLabel("Simplified Field:")
        l3.setMinimumWidth(100)
        h4 = QHBoxLayout()
        h4.addWidget(self.simpCB)
        h4.addWidget(self.addRemSimp)
        h4.addWidget(self.simpOW)
        h4.addWidget(QLabel("Overwrite"))
        h4.addWidget(self.simpIfE)
        h4.addWidget(QLabel("If Empty"))
        h4.addWidget(self.simpWithSep)
        h4.addWidget(QLabel("Add with Separator"))
        h4.addWidget(self.simpSep)
        h4.addStretch()
        ggbh4.addWidget(l3)
        ggbh4.addLayout(h4)
        ggbh4.setContentsMargins(0, 0, 0, 0)
        self.simpLayout.setLayout(ggbh4)

        ggbh6 = QVBoxLayout()
        l4 = QLabel("Traditional Field:")
        l4.setMinimumWidth(100)
        h6 = QHBoxLayout()
        h6.addWidget(self.tradCB)
        h6.addWidget(self.addRemTrad)
        h6.addWidget(self.tradOW)
        h6.addWidget(QLabel("Overwrite"))
        h6.addWidget(self.tradIfE)
        h6.addWidget(QLabel("If Empty"))
        h6.addWidget(self.tradWithSep)
        h6.addWidget(QLabel("Add with Separator"))
        h6.addWidget(self.tradSep)
        h6.addStretch()
        ggbh6.addWidget(l4)
        ggbh6.addLayout(h6)
        ggbh6.setContentsMargins(0, 0, 0, 0)
        self.tradLayout.setLayout(ggbh6)

        ggbh3 = QHBoxLayout()
        ggbh3.addWidget(QLabel("Current Alternate Fields:"))
        ggbh3.addWidget(self.currentAlt)
        ggbh3.addStretch()

        ggbh5 = QHBoxLayout()
        ggbh5.addWidget(QLabel("Current Simplified Fields:"))
        ggbh5.addWidget(self.currentSimp)
        ggbh5.addStretch()

        ggbh7 = QHBoxLayout()
        ggbh7.addWidget(QLabel("Current Traditional Fields:"))
        ggbh7.addWidget(self.currentTrad)
        ggbh7.addStretch()

        ggbv2.addWidget(self.altLayout)
        ggbv2.addLayout(ggbh3)
        ggbv2.addWidget(self.simpLayout)
        ggbv2.addLayout(ggbh5)
        ggbv2.addWidget(self.tradLayout)
        ggbv2.addLayout(ggbh7)
        ggbv2.setSpacing(5)
        ggb2.setLayout(ggbv2)

        ggbv.addWidget(ggbt)
        ggbv.addLayout(ggbh)
        ggbv.addWidget(ggb2)
        ggb.setLayout(ggbv)
        ol.addWidget(ggb)

        cgb = QGroupBox()  # colors group box
        cgbv = QVBoxLayout()
        cgbv.addWidget(QLabel("<b>Colors</b>"))
        mcgb = QGroupBox("Mandarin Tones")
        mcv = QVBoxLayout()
        mch1 = QHBoxLayout()
        mch2 = QHBoxLayout()
        ml1 = QLabel("1st:")
        ml2 = QLabel("2nd:")
        ml3 = QLabel("3rd:")
        ml4 = QLabel("4th:")
        ml5 = QLabel("Neutral:")
        ml1.setMinimumWidth(25)
        ml2.setMinimumWidth(45)
        ml3.setMinimumWidth(25)
        ml4.setMinimumWidth(25)
        ml5.setMinimumWidth(45)
        mch1.addWidget(ml1)
        mch1.addWidget(self.m1color)
        mch1.addWidget(self.m1pb)

        mch1.addWidget(ml2)
        mch1.addWidget(self.m2color)
        mch1.addWidget(self.m2pb)

        mch1.addWidget(ml3)
        mch1.addWidget(self.m3color)
        mch1.addWidget(self.m3pb)

        mch2.addWidget(ml4)
        mch2.addWidget(self.m4color)
        mch2.addWidget(self.m4pb)

        mch2.addWidget(ml5)
        mch2.addWidget(self.m5color)
        mch2.addWidget(self.m5pb)

        mch1.addStretch()
        mch2.addStretch()
        mcv.addLayout(mch1)
        mcv.addLayout(mch2)
        mcgb.setLayout(mcv)

        ccgb = QGroupBox("Cantonese Tones")  # canto
        ccv = QVBoxLayout()
        cch1 = QHBoxLayout()
        cch2 = QHBoxLayout()
        cl1 = QLabel("1st:")
        cl2 = QLabel("2nd:")
        cl3 = QLabel("3rd:")
        cl4 = QLabel("4th:")
        cl5 = QLabel("5th:")
        cl6 = QLabel("6th:")
        cl1.setMinimumWidth(25)
        cl2.setMinimumWidth(45)
        cl3.setMinimumWidth(25)
        cl4.setMinimumWidth(25)
        cl5.setMinimumWidth(45)
        cl6.setMinimumWidth(25)
        cch1.addWidget(cl1)
        cch1.addWidget(self.c1color)
        cch1.addWidget(self.c1pb)

        cch1.addWidget(cl2)
        cch1.addWidget(self.c2color)
        cch1.addWidget(self.c2pb)

        cch1.addWidget(cl3)
        cch1.addWidget(self.c3color)
        cch1.addWidget(self.c3pb)

        cch2.addWidget(cl4)
        cch2.addWidget(self.c4color)
        cch2.addWidget(self.c4pb)

        cch2.addWidget(cl5)
        cch2.addWidget(self.c5color)
        cch2.addWidget(self.c5pb)

        cch2.addWidget(cl6)
        cch2.addWidget(self.c6color)
        cch2.addWidget(self.c6pb)

        cch1.addStretch()
        cch2.addStretch()
        ccv.addLayout(cch1)
        ccv.addLayout(cch2)
        ccgb.setLayout(ccv)

        cgbv.addWidget(mcgb)
        cgbv.addWidget(ccgb)
        cgb.setLayout(cgbv)
        ol.addWidget(cgb)

        bgb = QGroupBox()  # profile group box
        bgbv = QVBoxLayout()
        bgbt = QLabel("<b>Behavior</b>")
        bgbh = QHBoxLayout()
        bgbh.addWidget(QLabel("Hanzi/Reading Conversion:"))
        bgbh.addWidget(self.hanziConversion)
        bgbh.addWidget(self.readingConversion)
        bgbh.addStretch()
        bgbh.addWidget(QLabel("Reading Font Size:"))
        bgbh.addWidget(self.fontSize)
        bgbh.addWidget(QLabel("%"))
        bgbh.addStretch()
        bgbh2 = QHBoxLayout()
        bgbh2.addWidget(QLabel("Traditional Icons:"))
        bgbh2.addWidget(self.tradIcons)
        bgbh2.addStretch()
        bgbh2.addWidget(QLabel("File Refs for CSS/JS:"))
        bgbh2.addWidget(self.useFileRefs)
        bgbv.addWidget(bgbt)
        bgbv.addLayout(bgbh)
        bgbv.addLayout(bgbh2)
        bgb.setLayout(bgbv)
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

    def enableSep(self, sep):
        sep.setEnabled(True)

    def disableSep(self, sep):
        sep.setEnabled(False)

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
        afl = QVBoxLayout()  # active fields layout

        afh1 = QHBoxLayout()
        afh1.addWidget(QLabel("Auto CSS & JS Generation:"))
        afh1.addWidget(self.autoCSSJS)
        afh1.addStretch()
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
        afh3.addStretch()
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
        return afTab

    def initTooltips(self):
        self.profileCB.setToolTip(
            "These are the profiles that the add-on will be active on.\n"
            'When set to "All", the add-on will be active on all profiles.'
        )
        self.addRemProfile.setToolTip("Add/Remove a profile.")
        self.defaultReading.setToolTip(
            "This is the default reading generation that will be used when "
            "generating in a field that has not been designated as an Active Field."
        )
        self.bopo2Number.setToolTip(
            "When enabled bopomofo readings will be generated with numbers "
            "instead of tone marks. This makes editing incorrect tones easier because "
            "numbers are easier to type then tone marks. When viewed during reviews, or previews "
            "tone marks will replace the numbers."
        )
        self.altCB.setToolTip(
            "The fields where the alternate characters will be generated. "
            "If the target field where readings are generated has only simplified characters "
            "then traditional characters will be placed in this field and vice versa. "
            "If the target contains a mix of both simplified and traditional characters then "
            "a consistent alternate containing only simplified and traditional characters. "
            "A variant will only be generated if it is different than the original text."
        )
        self.simpCB.setToolTip(
            "The fields where simplified characters version of the text "
            "will be generated when reading generation occurs. The variant will be added "
            "even it it is the same as the original text."
        )
        self.tradCB.setToolTip(
            "The fields where traditional characters version of the text "
            "will be generated when reading generation occurs. The variant will be added "
            "even it it is the same as the original text."
        )
        self.altOW.setToolTip(
            "The alternate variant will be generated into the selected field(s), overwriting their current contents."
        )
        self.altIfE.setToolTip(
            "The alternate variant will be generated into the selected field(s) only if they are empty."
        )
        self.altWithSep.setToolTip(
            "The alternate variant will be added on to the selected field(s) "
            'following the separator. The default separator is an html line break "<br>".'
        )
        self.altSep.setToolTip("The separator to be used when adding the alternate variant.")
        self.simpOW.setToolTip(
            "The simplified variant will be generated into the selected field(s), overwriting their current contents."
        )
        self.simpIfE.setToolTip(
            "The simplified variant will be generated into the selected field(s) only if they are empty."
        )
        self.simpWithSep.setToolTip(
            "The simplified variant will be added on to the selected field(s) "
            'following the separator. The default separator is an html line break "<br>".'
        )
        self.simpSep.setToolTip("The separator to be used when adding the simplified variant.")
        self.tradOW.setToolTip(
            "The traditional variant will be generated into the selected field(s), overwriting their current contents."
        )
        self.tradIfE.setToolTip(
            "The traditional variant will be generated into the selected field(s) only if they are empty."
        )
        self.tradWithSep.setToolTip(
            "The traditional variant will be added on to the selected field(s) following "
            'the separator. The default separator is an html line break "<br>".'
        )
        self.tradSep.setToolTip("The separator to be used when adding the traditional variant.")

        self.m1pb.setToolTip("Select the color for characters in the first tone.")
        self.m2pb.setToolTip("Select the color for characters in the second tone.")
        self.m3pb.setToolTip("Select the color for characters in the third tone.")
        self.m4pb.setToolTip("Select the color for characters in the fourth tone.")
        self.m5pb.setToolTip("Select the color for characters in the fifth tone.")

        self.c1pb.setToolTip("Select the color for characters in the first tone.")
        self.c2pb.setToolTip("Select the color for characters in the second tone.")
        self.c3pb.setToolTip("Select the color for characters in the third tone.")
        self.c4pb.setToolTip("Select the color for characters in the fourth tone.")
        self.c5pb.setToolTip("Select the color for characters in the fifth tone.")
        self.c6pb.setToolTip("Select the color for characters in the sixth tone.")

        self.hanziConversion.setToolTip("Will convert characters in all notes with Active Fields to the selected type.")
        self.readingConversion.setToolTip(
            "Will convert readings in all Active Fields from pinyin to bopomofo and vice versa."
        )
        self.tradIcons.setToolTip(
            "Display the conversion icons in traditional characters instead of simplified characters."
        )

        self.fontSize.setToolTip(
            "The percentage font size of readings in relation to the characters.\nThe range is from 1% to 200%."
        )

        self.autoCSSJS.setToolTip(
            "Enable or disable automatic CSS and JavaScript handling.\n"
            "Disabling this option is not recommended if you are not familiar with these technologies."
        )
        self.profileAF.setToolTip("Profile: Select the profile.")
        self.noteTypeAF.setToolTip("Note Type: Select the note type.")
        self.cardTypeAF.setToolTip("Card Type: Select the card type.")
        self.fieldAF.setToolTip("Field: Select the field.")
        self.sideAF.setToolTip("Side: Select the side of the card where the display type setting will apply.")
        self.displayAF.setToolTip(
            "Display Type: Select the display type,\nhover over a display type for fuctionality details."
        )
        self.readingAF.setToolTip(
            "Reading Type: Select the reading type, "
            "determines which reading system will be used when generating readings "
            "for this card type."
        )

    def initHandlers(self):
        self.m1pb.clicked.connect(lambda: self.openDialogColor(self.m1color))
        self.m2pb.clicked.connect(lambda: self.openDialogColor(self.m2color))
        self.m3pb.clicked.connect(lambda: self.openDialogColor(self.m3color))
        self.m4pb.clicked.connect(lambda: self.openDialogColor(self.m4color))
        self.m5pb.clicked.connect(lambda: self.openDialogColor(self.m5color))
        self.c1pb.clicked.connect(lambda: self.openDialogColor(self.c1color))
        self.c2pb.clicked.connect(lambda: self.openDialogColor(self.c2color))
        self.c3pb.clicked.connect(lambda: self.openDialogColor(self.c3color))
        self.c4pb.clicked.connect(lambda: self.openDialogColor(self.c4color))
        self.c5pb.clicked.connect(lambda: self.openDialogColor(self.c5color))
        self.c6pb.clicked.connect(lambda: self.openDialogColor(self.c6color))
        self.addRemProfile.clicked.connect(
            lambda: self.addRemoveFromList(
                self.profileCB.currentText(), self.addRemProfile, self.currentProfiles, self.selectedProfiles, True
            )
        )
        self.profileCB.currentIndexChanged.connect(
            lambda: self.profAltSimpTradChange(self.profileCB.currentText(), self.addRemProfile, self.selectedProfiles)
        )
        self.addRemAlt.clicked.connect(
            lambda: self.addRemoveFromList(
                self.altCB.currentText(), self.addRemAlt, self.currentAlt, self.selectedAltFields, True
            )
        )
        self.altCB.currentIndexChanged.connect(
            lambda: self.profAltSimpTradChange(self.altCB.currentText(), self.addRemAlt, self.selectedAltFields)
        )
        self.addRemSimp.clicked.connect(
            lambda: self.addRemoveFromList(
                self.simpCB.currentText(), self.addRemSimp, self.currentSimp, self.selectedSimpFields, True
            )
        )
        self.simpCB.currentIndexChanged.connect(
            lambda: self.profAltSimpTradChange(self.simpCB.currentText(), self.addRemSimp, self.selectedSimpFields)
        )
        self.addRemTrad.clicked.connect(
            lambda: self.addRemoveFromList(
                self.tradCB.currentText(), self.addRemTrad, self.currentTrad, self.selectedTradFields, True
            )
        )
        self.tradCB.currentIndexChanged.connect(
            lambda: self.profAltSimpTradChange(self.tradCB.currentText(), self.addRemTrad, self.selectedTradFields)
        )
        self.altWithSep.clicked.connect(lambda: self.enableSep(self.altSep))
        self.altOW.clicked.connect(lambda: self.disableSep(self.altSep))
        self.altIfE.clicked.connect(lambda: self.disableSep(self.altSep))
        self.simpWithSep.clicked.connect(lambda: self.enableSep(self.simpSep))
        self.simpOW.clicked.connect(lambda: self.disableSep(self.simpSep))
        self.simpIfE.clicked.connect(lambda: self.disableSep(self.simpSep))
        self.tradWithSep.clicked.connect(lambda: self.enableSep(self.tradSep))
        self.tradOW.clicked.connect(lambda: self.disableSep(self.tradSep))
        self.tradIfE.clicked.connect(lambda: self.disableSep(self.tradSep))

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
                    ci = 0  # "All" is always the first item
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

    def loadAltSimpTradFieldsCB(self):
        self.altCB.addItem("Clipboard")
        self.altCB.addItem("──────────────────")
        m = self.altCB.model()
        assert m is not None
        m.item(self.altCB.count() - 1).setEnabled(False)  # ty:ignore[unresolved-attribute]
        m.item(self.altCB.count() - 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # ty:ignore[unresolved-attribute]
        self.altCB.addItems(self.allFields)
        self.simpCB.addItem("Clipboard")
        self.simpCB.addItem("──────────────────")
        m2 = self.simpCB.model()
        assert m2 is not None
        m2.item(self.simpCB.count() - 1).setEnabled(False)  # ty:ignore[unresolved-attribute]
        m2.item(self.simpCB.count() - 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # ty:ignore[unresolved-attribute]
        self.simpCB.addItems(self.allFields)
        self.tradCB.addItem("Clipboard")
        self.tradCB.addItem("──────────────────")
        m3 = self.tradCB.model()
        assert m3 is not None
        m3.item(self.tradCB.count() - 1).setEnabled(False)  # ty:ignore[unresolved-attribute]
        m3.item(self.tradCB.count() - 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # ty:ignore[unresolved-attribute]
        self.tradCB.addItems(self.allFields)

    def loadFieldsList(self, which):
        if which == 1:
            fl = self.currentAlt
            currentSelection = self.altCB.currentText()
            fs = self.config.simp_trad_field
        elif which == 2:
            fl = self.currentSimp
            currentSelection = self.simpCB.currentText()
            fs = self.config.simplified_field
        else:
            fl = self.currentTrad
            currentSelection = self.tradCB.currentText()
            fs = self.config.traditional_field

        fieldList = fs.split(";")
        separator = False
        if len(fieldList) > 2:
            fields, addMode, separator = fieldList
        else:
            fields, addMode = fieldList
        fields = fields.split(",")
        for idx, field in enumerate(fields):
            if field == "clipboard":
                fields[idx] = "Clipboard"
        if len(fields) == 1 and (fields[0].lower() == "none" or fields[0].lower() == ""):
            fl.setText("<i>None currently selected.</i>")
        else:
            fl.setText("<i>" + ", ".join(fields) + "</i>")
        if which == 1:
            self.selectedAltFields = fields
            if currentSelection in self.selectedAltFields:
                self.addRemAlt.setText("Remove")
        elif which == 2:
            self.selectedSimpFields = fields
            if currentSelection in self.selectedSimpFields:
                self.addRemSimp.setText("Remove")
        else:
            self.selectedTradFields = fields
            if currentSelection in self.selectedTradFields:
                self.addRemTrad.setText("Remove")
        self.loadAddModes(addMode.lower(), separator, which)

    def loadAddModes(self, addMode, separator, which):
        if which == 1:
            add = self.altWithSep
            overwrite = self.altOW
            ifEmpty = self.altIfE
            sepB = self.altSep
        elif which == 2:
            add = self.simpWithSep
            overwrite = self.simpOW
            ifEmpty = self.simpIfE
            sepB = self.simpSep
        else:
            add = self.tradWithSep
            overwrite = self.tradOW
            ifEmpty = self.tradIfE
            sepB = self.tradSep
        if addMode == "overwrite":
            overwrite.setChecked(True)
        elif addMode == "add":
            add.setChecked(True)
        elif addMode == "no":
            ifEmpty.setChecked(True)
        if separator:
            sepB.setText(separator)
        else:
            sepB.setText("<br>")
        if not add.isChecked():
            sepB.setEnabled(False)

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

    def profAltSimpTradChange(self, value, button, vList):
        if value in vList:
            button.setText("Remove")
        else:
            button.setText("Add")

    def loadProfileCB(self):
        pcb = self.profileCB
        pcb.addItem("All")
        pcb.addItem("──────")
        m = pcb.model()
        assert m is not None
        m.item(pcb.count() - 1).setEnabled(False)  # ty:ignore[unresolved-attribute]
        m.item(pcb.count() - 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # ty:ignore[unresolved-attribute]
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

    def saveAltSimpTradConfig(self):
        if len(self.selectedAltFields) < 1:
            altConfig = ["none"]
        else:
            altConfig = [",".join(self.selectedAltFields)]
        if len(self.selectedSimpFields) < 1:
            simpConfig = ["none"]
        else:
            simpConfig = [",".join(self.selectedSimpFields)]
        if len(self.selectedTradFields) < 1:
            tradConfig = ["none"]
        else:
            tradConfig = [",".join(self.selectedTradFields)]
        if self.altWithSep.isChecked():
            altConfig.append("add")
            altConfig.append(self.altSep.text())
        elif self.altOW.isChecked():
            altConfig.append("overwrite")
        elif self.altIfE.isChecked():
            altConfig.append("no")
        if self.simpWithSep.isChecked():
            simpConfig.append("add")
            simpConfig.append(self.simpSep.text())
        elif self.simpOW.isChecked():
            simpConfig.append("overwrite")
        elif self.simpIfE.isChecked():
            simpConfig.append("no")

        if self.tradWithSep.isChecked():
            tradConfig.append("add")
            tradConfig.append(self.tradSep.text())
        elif self.tradOW.isChecked():
            tradConfig.append("overwrite")
        elif self.tradIfE.isChecked():
            tradConfig.append("no")
        return ";".join(altConfig), ";".join(simpConfig), ";".join(tradConfig)

    def getColors(self, letter, maxr):
        colors = []
        for idx in range(1, maxr):
            name = letter + str(idx) + "color"
            widget = getattr(self, name)
            colors.append(widget.text())
        return colors

    def saveActiveFields(self):
        afList = self.afTable
        afs = []
        for i in range(afList.rowCount()):
            prof = afList.item(i, 0).text()
            if prof == "All":
                prof = "all"
            nt = afList.item(i, 1).text()
            ct = afList.item(i, 2).text()
            field = afList.item(i, 3).text()
            side = afList.item(i, 4).text().lower()
            target = afList.item(i, 5).text()
            dt = target
            for key, value in self.displayTranslation.items():
                if value == target:
                    dt = key
                    break
            rt = afList.item(i, 6).text().lower()
            af = ActiveField(
                display_type=dt,
                profile=prof,
                note_type=nt,
                card_type=ct,
                field=field,
                side=side,
                reading_type=rt,
            )
            afs.append(serialize_active_field(af))
        return afs

    def saveConfig(self):
        drt = self.defaultReading.currentText().lower()
        b2n = self.bopo2Number.isChecked()
        tradIcons = self.tradIcons.isChecked()
        alt, simp, trad = self.saveAltSimpTradConfig()
        mColors = tuple(self.getColors("m", 6))
        cColors = tuple(self.getColors("c", 7))
        autoCSSJS = self.autoCSSJS.isChecked()
        hc = self.hanziConversion.currentText()
        rc = self.readingConversion.currentText()
        fontSize = self.fontSize.value()
        useFileRefs = self.useFileRefs.isChecked()
        afs = tuple(self.saveActiveFields())

        delta = ConfigDelta(
            profiles=self.selectedProfiles,
            reading_type=drt,
            bopomofo_tones_to_number=b2n,
            hanzi_conversion=hc,
            reading_conversion=rc,
            auto_css_js_generation=autoCSSJS,
            simplified_field=simp,
            traditional_field=trad,
            simp_trad_field=alt,
            traditional_icons=tradIcons,
            font_size=fontSize,
            use_file_references=useFileRefs,
            cantonese_tones=cColors,
            mandarin_tones=mColors,
            active_fields=afs,
        )
        config = self.mutation.save_config(delta)
        self.cssJSHandler.refreshConfig(config)
        self.cssJSHandler.injectWrapperElements()
        self.mw.ChineseReading.refreshConfig(config)
        self.hide()

    def openDialogColor(self, lineEd):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            lineEd.setText(color.name())
            lineEd.setStyleSheet("color:" + color.name() + ";")

    def create_label(self, text, width):
        label = QLabel(text)
        label.setFixedHeight(30)
        label.setFixedWidth(width)
        return label

    def setupMainLayout(self):
        self.ml = QVBoxLayout()
        self.ml.setContentsMargins(10, 10, 10, 10)
        self.ml.setSpacing(10)
        self.ml.addWidget(self.tabs)
        bl = QHBoxLayout()
        bl.setSpacing(10)
        bl.addWidget(self.resetButton)
        bl.addStretch()
        bl.addWidget(self.cancelButton)
        bl.addWidget(self.applyButton)
        self.ml.addLayout(bl)
        self.innerWidget.setLayout(self.ml)

    def getSVGWidget(self, name):
        widget = ClickableSVG(join(self.addonPath, "icons", name))
        widget.setFixedSize(27, 27)
        return widget

    def clearAllAF(self):
        self.profileAF.clear()
        self.noteTypeAF.clear()
        self.cardTypeAF.clear()
        self.fieldAF.clear()
        self.sideAF.clear()
        self.displayAF.clear()
        self.readingAF.clear()

    def initActiveFieldsCB(self):
        aP = self.profileAF
        aP.addItem("All")
        aP.addItem("──────────────────")
        m = aP.model()
        assert m is not None
        m.item(aP.count() - 1).setEnabled(False)  # ty:ignore[unresolved-attribute]
        m.item(aP.count() - 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # ty:ignore[unresolved-attribute]
        self.loadAllProfiles()
        self.loadCardTypesFields()
        for key, value in self.sides.items():
            self.sideAF.addItem(key)
            self.sideAF.setItemData(self.sideAF.count() - 1, value, Qt.ItemDataRole.ToolTipRole)
        for key, value in self.displayTypes.items():
            self.displayAF.addItem(key)
            self.displayAF.setItemData(self.displayAF.count() - 1, value[1], Qt.ItemDataRole.ToolTipRole)
            self.displayAF.setItemData(self.displayAF.count() - 1, value[0])
        for key, value in self.readingTypes.items():
            self.readingAF.addItem(key)
            self.readingAF.setItemData(self.readingAF.count() - 1, value, Qt.ItemDataRole.ToolTipRole)

    def loadAllProfiles(self):
        if not self.sortedProfiles and not self.sortedNoteTypes:
            profL = []
            noteL = []
            for prof in self.catalog.profile_names():
                profL.append(prof)
                for noteType in self.catalog.model_names(prof):
                    noteL.append([noteType + " (Prof:" + prof + ")", prof + ":pN:" + noteType])
            self.sortedProfiles = self.ciSort(profL)
            self.sortedNoteTypes = sorted(noteL, key=itemgetter(0))
        aP = self.profileAF
        for prof in self.sortedProfiles:
            aP.addItem(prof)
            aP.setItemData(aP.count() - 1, prof, Qt.ItemDataRole.ToolTipRole)
        self.loadAllNotes()

    def loadAllNotes(self):
        for noteType in self.sortedNoteTypes:
            self.noteTypeAF.addItem(noteType[0])
            self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, noteType[0], Qt.ItemDataRole.ToolTipRole)
            self.noteTypeAF.setItemData(self.noteTypeAF.count() - 1, noteType[1])

    def loadCardTypesFields(self):
        curProf, curNote = self.noteTypeAF.itemData(self.noteTypeAF.currentIndex()).split(":pN:")
        self.cardTypeAF.addItem("All")
        self.cardTypeAF.setItemData(self.cardTypeAF.count() - 1, "All", Qt.ItemDataRole.ToolTipRole)
        for cardType in self.catalog.card_type_names(curProf, curNote):
            self.cardTypeAF.addItem(cardType)
            self.cardTypeAF.setItemData(self.cardTypeAF.count() - 1, cardType, Qt.ItemDataRole.ToolTipRole)
        for field in self.catalog.field_names(curProf, curNote):
            self.fieldAF.addItem(field)
            self.fieldAF.setItemData(self.fieldAF.count() - 1, field, Qt.ItemDataRole.ToolTipRole)
        return

    def loadActiveFields(self):
        afs = self.config.active_fields
        for af_str in afs:
            parsed = parse_active_field(af_str)
            if isinstance(parsed, str):
                continue
            dt = parsed.display_type
            rt = parsed.reading_type
            if dt in self.displayTranslation:
                prof = parsed.profile
                if prof == "all":
                    prof = "All"
                rt_display = self.rtTranslation.get(rt, rt.title())
                ct = parsed.card_type
                if ct.lower() == "all":
                    ct = "All"
                self.addToList(
                    prof,
                    parsed.note_type,
                    ct,
                    parsed.field,
                    parsed.side[0].upper() + parsed.side[1:].lower(),
                    self.displayTranslation[dt],
                    rt_display,
                )
