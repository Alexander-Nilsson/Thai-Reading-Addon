#

from os.path import dirname, join

import aqt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox

addon_path = dirname(__file__)


def show_info(text, parent=False, level="msg", day=True):
    if level == "wrn":
        title = "Chinese Reading Warning"
    elif level == "not":
        title = "Chinese Reading Notice"
    elif level == "err":
        title = "Chinese Reading Error"
    else:
        title = "Chinese Reading"
    if parent is False:
        parent = aqt.mw.app.activeWindow() or aqt.mw
    icon = QIcon(join(addon_path, "icons", "chinese-reading.svg"))
    mb = QMessageBox(parent)
    if not day:
        mb.setStyleSheet(" QMessageBox {background-color: #272828;}")
    mb.setText(text)
    mb.setWindowIcon(icon)
    mb.setWindowTitle(title)
    mb.setStandardButtons(QMessageBox.StandardButton.Ok)
    return mb.exec()


def show_ask(text, parent=None, title="Chinese Reading"):
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    # Change from QMessageBox.Yes to StandardButton
    b = msg.addButton(QMessageBox.StandardButton.Yes)
    c = msg.addButton(QMessageBox.StandardButton.No)
    msg.setDefaultButton(c)
    msg.exec()
    return msg.clickedButton() == b
