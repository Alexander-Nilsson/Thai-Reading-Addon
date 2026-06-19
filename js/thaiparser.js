(function() {
  var READING_TYPE = typeof THAI_READING_TYPE !== 'undefined' ? THAI_READING_TYPE : 'rtgs';

  function isMobile() {
    return /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(navigator.userAgent);
  }

  function getDisplayType(el) {
    return el.getAttribute('display-type') || 'thai';
  }

  function wrapSyllable(syllable, toneNum) {
    if (toneNum >= 1 && toneNum <= 5) {
      return '<span class="thTone' + toneNum + '">' + syllable + '</span>';
    }
    return syllable;
  }

  function parseReadingWithTones(reading) {
    var parts = reading.split(' ');
    var result = [];
    for (var i = 0; i < parts.length; i++) {
      var syl = parts[i];
      var tone = 0;
      var match = syl.match(/(\d)$/);
      if (match) {
        tone = parseInt(match[1], 10);
        syl = syl.slice(0, -1);
      }
      result.push(wrapSyllable(syl, tone));
    }
    return result.join(' ');
  }

  function parseFieldContent(html) {
    var parts = [];
    var buffer = '';
    var i = 0;
    while (i < html.length) {
      if (html[i] === '[') {
        if (buffer) {
          parts.push({type: 'text', content: buffer});
          buffer = '';
        }
        var close = html.indexOf(']', i);
        if (close !== -1) {
          parts.push({type: 'reading', content: html.substring(i + 1, close)});
          i = close + 1;
        } else {
          buffer += '[';
          i++;
        }
      } else {
        buffer += html[i];
        i++;
      }
    }
    if (buffer) {
      parts.push({type: 'text', content: buffer});
    }
    return parts;
  }

  function buildThaiDisplay(parts, displayType) {
    var result = '';
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].type === 'text') {
        result += parts[i].content;
      } else {
        var reading = parts[i].content;
        switch (displayType) {
          case 'thai':
            result += '<ruby><rb>' + reading + '</rb></ruby>';
            break;
          case 'coloredthai':
            result += '<ruby><rb>' + parseReadingWithTones(reading) + '</rb></ruby>';
            break;
          case 'reading':
            result += '<ruby><rb>' + reading + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'coloredreading':
            result += '<ruby><rb>' + parseReadingWithTones(reading) + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'thaithai':
            result += '<ruby><rb>' + reading + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'coloredthaithai':
            result += '<ruby><rb>' + parseReadingWithTones(reading) + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'hover':
            result += '<ruby class="unhovered-word"><rb>' + reading + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'coloredhover':
            result += '<ruby class="unhovered-word"><rb>' + parseReadingWithTones(reading) + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          default:
            result += reading;
        }
      }
    }
    return result;
  }

  function processWrappers() {
    var wrappers = document.querySelectorAll('.wrapped-thai');
    for (var i = 0; i < wrappers.length; i++) {
      var wrapper = wrappers[i];
      var displayType = getDisplayType(wrapper);
      var html = wrapper.innerHTML;
      var parts = parseFieldContent(html);
      wrapper.innerHTML = buildThaiDisplay(parts, displayType);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processWrappers);
  } else {
    processWrappers();
  }
})();
