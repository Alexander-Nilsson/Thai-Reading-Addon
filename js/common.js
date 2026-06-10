function unnest_span(span) {
  span.normalize();
  var result = [];
  for (var i = 0; i < span.childNodes.length; i++) {
    var node = span.childNodes[i];
    if (node.nodeName === "SPAN") {
      if (node.childNodes.length === 1) {
        result.push(node);
      } else if (node.childNodes.length > 1) {
        result.push.apply(result, unnest_span(node));
      }
    } else {
      var new_span = span.cloneNode(false);
      new_span.innerHTML = "";
      new_span.appendChild(node.cloneNode(true));
      result.push(new_span);
    }
  }
  return result;
}

function selectAllFieldNodes(field, sel){
  if (!field) return;
  field.focus();
  setFormat("inserthtml", '');
  const newRange = new Range();
  sel.removeAllRanges();
  newRange.selectNodeContents(field);
  sel.addRange(newRange)
}

function selectText(node, sel) {
    sel.selectAllChildren(node)

}

function clean_field(field) {
  var new_field = document.createDocumentFragment();
  for (var i = 0; i < field.childNodes.length; i++) {
    var node = field.childNodes[i];
    if (node.nodeName === "SPAN") {
      var new_nodes = unnest_span(node);
      for (var j = 0; j < new_nodes.length; j++) {
        new_field.appendChild(new_nodes[j]);
      }
    } else {
      new_field.appendChild(node.cloneNode(true));
    }
  }
  field.innerHTML = "";
  field.appendChild(new_field);
}

function is_field(node) {
  return node && node.nodeName === "DIV" && node.classList && node.classList.contains("field");
}

function get_field(sel) {
  if (!sel) return null;
  var node = sel.baseNode || sel.anchorNode;
  while (node) {
    if (is_field(node)) return node;
    // Cross shadow boundary
    if (node.parentNode) {
      node = node.parentNode;
    } else if (node.host) {
      node = node.host;
    } else if (node.getRootNode && node.getRootNode().host) {
      node = node.getRootNode().host;
    } else {
      break;
    }
  }
  // Fallback to active element
  node = document.activeElement;
  while (node) {
    if (is_field(node)) return node;
    if (node.nodeName === "ANKI-EDITABLE" && node.shadowRoot) {
      var f = node.shadowRoot.querySelector("div.field");
      if (f) return f;
    }
    node = node.parentNode || node.host || (node.getRootNode && node.getRootNode().host);
  }
  return null;
}

function get_field_by_ordinal(ordinal) {
  var doc = document;
  // If we are in a legacy/isolated context, try to look at the parent
  if (doc.querySelectorAll('anki-editable').length === 0 && window.parent && window.parent.document) {
      doc = window.parent.document;
  }

  // Try ID first (old Anki)
  var field = doc.getElementById('f' + ordinal);
  if (field) return field;

  // Try anki-editable (modern Anki)
  var editables = doc.querySelectorAll('anki-editable');
  if (editables[ordinal]) {
    if (editables[ordinal].shadowRoot) {
      return editables[ordinal].shadowRoot.querySelector("div.field");
    }
    return editables[ordinal].querySelector("div.field");
  }

  // Try counting div.field
  var fields = doc.querySelectorAll('div.field');
  if (fields[ordinal]) return fields[ordinal];

  return null;
}

function get_field_ordinal(field) {
    if (!field) return 0;
    if (field.id && field.id.startsWith('f')) {
        return parseInt(field.id.substring(1));
    }
    // Try to find via anki-editable
    var editables = document.querySelectorAll('anki-editable');
    for (var i = 0; i < editables.length; i++) {
        var f = editables[i].shadowRoot ? editables[i].shadowRoot.querySelector("div.field") : editables[i].querySelector("div.field");
        if (f === field) return i;
    }
    // Try to find via div.field
    var fields = document.querySelectorAll('div.field');
    for (var i = 0; i < fields.length; i++) {
        if (fields[i] === field) return i;
    }
    return 0;
}

