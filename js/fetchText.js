function fetchCText() {
  var field = null;

  // 1. Try globally set currentField (set by addCReadings in handler.py)
  if (typeof currentField !== 'undefined' && currentField) {
    field = currentField;
  } else if (typeof window.currentField !== 'undefined' && window.currentField) {
    field = window.currentField;
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
        if (f && (f.offsetParent !== null || f.offsetWidth > 0 || f.offsetHeight > 0)) {
            field = f;
            break;
        }
    }
    if (!field) {
        var fields = document.querySelectorAll("div.field");
        for (var i = 0; i < fields.length; i++) {
          var f = fields[i];
          if (f.offsetParent !== null || f.offsetWidth > 0 || f.offsetHeight > 0) {  // visible
            field = f;
            break;
          }
        }
    }
  }

  if (!field) {
    var debugInfo = {
      currentFieldDefined: typeof currentField !== 'undefined',
      windowCurrentFieldDefined: typeof window.currentField !== 'undefined',
      editablesCount: document.querySelectorAll("anki-editable").length,
      fieldsCount: document.querySelectorAll("div.field").length,
      url: window.location.href
    };
    console.error("Chinese Reading: Could not find current field. DOM info:", debugInfo);
    alert("Chinese Reading: Could not find the current field.\n\nDebug Info: " + JSON.stringify(debugInfo, null, 2) + "\n\nPlease click inside a field and try again.");
    return;
  }

  const text = field.innerHTML;
  const fieldId = get_field_ordinal(field).toString();
  const noteId = (typeof currentNoteId !== 'undefined' && currentNoteId) ? currentNoteId : 
                 (typeof window.currentNoteId !== 'undefined' && window.currentNoteId) ? window.currentNoteId : '0';
  pycmd("textToCReading:||:||:" + text + ':||:||:' + fieldId + ':||:||:' + noteId);
  
  // Clean up
  if (typeof currentField !== 'undefined') currentField = null;
  if (typeof window.currentField !== 'undefined') window.currentField = null;
}
try {
  fetchCText();
} catch (e) {
  alert(e);
}
