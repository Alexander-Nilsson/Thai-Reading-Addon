function fetchCText() {
  var field = null;

  // 1. Try currentField first (set by addCReadings in handler.py)
  if (typeof currentField !== 'undefined' && currentField) {
    field = currentField;
  }

  // 2. Try window selection
  if (!field) {
    const sel = window.getSelection();
    field = get_field(sel);
  }

  // 3. Last resort fallback (find first visible field)
  if (!field) {
    var editables = document.querySelectorAll("anki-editable");
    for (var i = 0; i < editables.length; i++) {
        var f = editables[i].shadowRoot ? editables[i].shadowRoot.querySelector("div.field") : editables[i].querySelector("div.field");
        if (f && f.offsetParent !== null) {
            field = f;
            break;
        }
    }
    if (!field) {
        var fields = document.querySelectorAll("div.field");
        for (var i = 0; i < fields.length; i++) {
          var f = fields[i];
          if (f.offsetParent !== null) {  // visible
            field = f;
            break;
          }
        }
    }
  }

  if (!field) {
    alert("Chinese Reading: Could not find the current field. Please click inside a field and try again.");
    return;
  }

  const text = field.innerHTML;
  const fieldId = get_field_ordinal(field).toString();
  const noteId = typeof currentNoteId !== 'undefined' ? currentNoteId : '0';
  pycmd("textToCReading:||:||:" + text + ':||:||:' + fieldId + ':||:||:' + noteId);
}
try {
  fetchCText();
} catch (e) {
  alert(e);
}
