function cleanUpSpaces(text){
    return text.replace(/ /g, '');
}

function removeBrackets() {
  const sel = window.getSelection();
  const field = get_field(sel);
  let text = field.innerHTML;
  if (text === "") return;
  if(!/\[[^\[]*?\]/.test(text))return;
  let pattern2 = /(\[sound:[^\]]+?\])|(?:\[\d*\])/g;
  if(!/\[[^\[]*?\]/.test(text))return ;
  replacements = false;
  pattern = /<[^<]*?>/g;
  let matches = false;
  if (pattern.test(text)){
    matches = text.match(pattern)
    for (let i = 0; i < matches.length; i++){
        text = text.replace(matches[i], '---NEWLINE___')
    }
  }
  
  let matches2 = false;
  if (pattern2.test(text)){
    matches2 = text.match(pattern2)
    for (let i = 0; i < matches2.length; i++){
        text = text.replace(matches2[i], '---SOUNDREF___')
    }
  }
  text = cleanUpSpaces(text);
  if(matches){
    for (let i = 0; i < matches.length; i++){
      text = text.replace( '---NEWLINE___', matches[i])
    }
  }

  text = text.replace(/\[[^\[]*?\]/g, "");
  if(matches2){
    for (let i = 0; i < matches2.length; i++){
      text = text.replace( '---SOUNDREF___', matches2[i])
    }
  }
  const html = text;
  selectAllFieldNodes(field, sel);
  setFormat("inserthtml", html);
}
try {
  removeBrackets();
} catch (e) {
  alert(e);
}
