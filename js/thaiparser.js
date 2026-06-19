(function() {
  var READING_TYPE = typeof THAI_READING_TYPE !== 'undefined' ? THAI_READING_TYPE : 'rtgs';
  var RTGS_TONE_STYLE = typeof THAI_RTGS_TONE_STYLE !== 'undefined' ? THAI_RTGS_TONE_STYLE : 'marks';

  var TONE_VOWELS = {
    2: { a: "\u00e0", e: "\u00e8", i: "\u00ec", o: "\u00f2", u: "\u00f9" },
    3: { a: "\u00e2", e: "\u00ea", i: "\u00ee", o: "\u00f4", u: "\u00fb" },
    4: { a: "\u00e1", e: "\u00e9", i: "\u00ed", o: "\u00f3", u: "\u00fa" },
    5: { a: "\u01ce", e: "\u011b", i: "\u01d0", o: "\u01d2", u: "\u01d4" },
  };

  function applyToneMark(syl, toneNum) {
    if (toneNum <= 1 || RTGS_TONE_STYLE !== 'marks') return syl;
    var map = TONE_VOWELS[toneNum];
    if (!map) return syl;
    for (var i = 0; i < syl.length; i++) {
      var ch = syl[i];
      if (map[ch]) return syl.slice(0, i) + map[ch] + syl.slice(i + 1);
    }
    return syl;
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

  function parseSyllables(reading) {
    var parts = reading.split(' ');
    return parts.map(function(syl) {
      var tone = 0;
      var m = syl.match(/(\d)$/);
      if (m) {
        tone = parseInt(m[1], 10);
        syl = syl.slice(0, -1);
      }
      return { text: applyToneMark(syl, tone), tone: tone };
    });
  }

  function parseReadingWithTones(reading) {
    return parseSyllables(reading).map(function(s) {
      return wrapSyllable(s.text, s.tone);
    }).join(' ');
  }

  function plainReading(reading) {
    return parseSyllables(reading).map(function(s) {
      return s.text;
    }).join(' ');
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
        var displayRd = plainReading(reading);
        var coloredRd = parseReadingWithTones(reading);
        switch (displayType) {
          case 'thai':
            result += '<ruby><rb>' + displayRd + '</rb></ruby>';
            break;
          case 'coloredthai':
            result += '<ruby><rb>' + coloredRd + '</rb></ruby>';
            break;
          case 'reading':
            result += '<ruby><rb>' + displayRd + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'coloredreading':
            result += '<ruby><rb>' + coloredRd + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'thaithai':
            result += '<ruby><rb>' + displayRd + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'coloredthaithai':
            result += '<ruby><rb>' + coloredRd + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'hover':
            result += '<ruby class="unhovered-word"><rb>' + displayRd + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          case 'coloredhover':
            result += '<ruby class="unhovered-word"><rb>' + coloredRd + '</rb><rt class="pinyin-ruby"></rt></ruby>';
            break;
          default:
            result += displayRd;
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
