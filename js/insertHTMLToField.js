function insertHTMLToField(newHTML, ordinal) {
  const sel = window.getSelection();
  const field = get_field_by_ordinal(ordinal);
  if (!field) return;
  selectAllFieldNodes(field, sel);
  selectText(field, sel);
  setFormat("inserthtml", newHTML.trim());

}
try {

  insertHTMLToField("%s", "%s");
} catch (e) {
  alert(e);
}
