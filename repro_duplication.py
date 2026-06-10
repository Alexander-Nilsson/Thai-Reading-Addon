import sys
import os
from unittest.mock import MagicMock

# Add current directory and lib to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "lib"))

# Mock relative imports before they are called
import aqt
aqt.editor = MagicMock()
aqt.utils = MagicMock()
aqt.DialogManager = MagicMock()

import logging
logging.basicConfig(level=logging.DEBUG)

# Mock _infra.utils
sys.modules["_infra"] = MagicMock()
sys.modules["_infra.utils"] = MagicMock()
sys.modules["template"] = MagicMock()
sys.modules["template.js_registry"] = MagicMock()

from reading.handler import ChineseHandler
from reading.generator import ReadingGenerator

# Mock dependencies
mw = MagicMock()
anki_services = MagicMock()
config = MagicMock()
config.reading_type = "pinyin"
config.bopomofo_tones_to_number = True
config.variant_field = "None;overwrite"
config.simplified_field = "None;overwrite"
config.traditional_field = "None;overwrite"
config.simp_trad_field = "None;overwrite"

# Mock DB
db = MagicMock()
# Mock "你好" -> "ni3 hao3"
db.getAltFayin.side_effect = lambda word: [["ni3 hao3"]] if word == "你好" else ( [["ni3"]] if word == "你" else ([["hao3"]] if word == "好" else False))
db.get_simplified.side_effect = lambda x: x
db.get_traditional.side_effect = lambda x: x

# Mock CSSJSHandler
cssJSHandler = MagicMock()
cssJSHandler.wrapperDict = {"Subs2srs": [["Card 1", "Expression", "front", "ruby", "pinyin"]]}

# Initialize Handler
handler = ChineseHandler(mw, anki_services, os.getcwd(), db, cssJSHandler, config)

# Mock Note
note_data = {"Expression": "你好"}
note = MagicMock()
note.__getitem__.side_effect = lambda key: note_data[key]
note.__setitem__.side_effect = lambda key, val: note_data.__setitem__(key, val)
note.__contains__.side_effect = lambda key: key in note_data
note.model.return_value = {"name": "Subs2srs"}
note.note_type.return_value = {"flds": [{"name": "Expression", "ord": 0}]}

# Mock Editor
editor = MagicMock()
editor.note = note
editor.web.selectedText.return_value = ""

print("Initial Expression:", note_data["Expression"])

# First Run
print("\n--- First Run ---")
handler.addCReadings(editor)
print("After first run:", note_data["Expression"])

# Second Run
print("\n--- Second Run ---")
handler.addCReadings(editor)
print("After second run:", note_data["Expression"])

# Third Run
print("\n--- Third Run ---")
handler.addCReadings(editor)
print("After third run:", note_data["Expression"])

if note_data["Expression"].count("[ni3 hao3]") > 1:
    print("\nBUG DETECTED: Duplication found!")
else:
    print("\nNO BUG: Idempotency confirmed.")
