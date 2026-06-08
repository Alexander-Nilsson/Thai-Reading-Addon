#

from os.path import dirname, join

import aqt
from aqt.qt import *
from PyQt6.QtWidgets import QMessageBox

addon_path = dirname(__file__)


def miInfo(text, parent=False, level="msg", day=True):
    if level == "wrn":
        title = "Migaku Chinese Warning"
    elif level == "not":
        title = "Migaku Chinese Notice"
    elif level == "err":
        title = "Migaku Chinese Error"
    else:
        title = "Migaku Chinese"
    if parent is False:
        parent = aqt.mw.app.activeWindow() or aqt.mw
    icon = QIcon(join(addon_path, "icons", "migaku.png"))
    mb = QMessageBox(parent)
    if not day:
        mb.setStyleSheet(" QMessageBox {background-color: #272828;}")
    mb.setText(text)
    mb.setWindowIcon(icon)
    mb.setWindowTitle(title)
    b = mb.addButton(QMessageBox.Ok)
    b.setFixedSize(100, 30)
    b.setDefault(True)

    return mb.exec_()


def miAsk(text, parent=None, title="Migaku"):
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    # Change from QMessageBox.Yes to StandardButton
    b = msg.addButton(QMessageBox.StandardButton.Yes)
    c = msg.addButton(QMessageBox.StandardButton.No)
    msg.setDefaultButton(c)
    msg.exec()
    return msg.clickedButton() == b
