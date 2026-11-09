_SYLLABLE_FIRST, _SYLLABLE_LAST = 0xAC00, 0xD7A3
_LEADS = ("g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h")
_VOWELS = ("a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we", "wi",
           "yu", "eu", "ui", "i")
# final sound when the syllable closes a word or precedes a consonant
_TAILS = ("", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p", "t", "t",
          "ng", "t", "t", "k", "t", "p", "t")
# before a silent ㅇ the tail moves to the next syllable: (what stays, what moves)
_LIAISON = {1: ("", "g"), 2: ("", "kk"), 3: ("k", "s"), 4: ("", "n"), 5: ("n", "j"), 6: ("", "n"), 7: ("", "d"),
            8: ("", "r"), 9: ("l", "g"), 10: ("l", "m"), 11: ("l", "b"), 12: ("l", "s"), 13: ("l", "t"),
            14: ("l", "p"), 15: ("", "r"), 16: ("", "m"), 17: ("", "b"), 18: ("p", "s"), 19: ("", "s"),
            20: ("", "ss"), 21: ("ng", ""), 22: ("", "j"), 23: ("", "ch"), 24: ("", "k"), 25: ("", "t"),
            26: ("", "p"), 27: ("", "")}
_SILENT_LEAD = 11
_L_TAIL = 8
# ㄹ tail before ㄹ or ㄴ assimilates to ll
_L_ASSIMILATES = {5, 2}

_JAMO = {"ㄱ": "g", "ㄲ": "kk", "ㄴ": "n", "ㄷ": "d", "ㄸ": "tt", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b", "ㅃ": "pp",
         "ㅅ": "s", "ㅆ": "ss", "ㅇ": "ng", "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p",
         "ㅎ": "h", "ㅏ": "a", "ㅐ": "ae", "ㅑ": "ya", "ㅒ": "yae", "ㅓ": "eo", "ㅔ": "e", "ㅕ": "yeo", "ㅖ": "ye",
         "ㅗ": "o", "ㅘ": "wa", "ㅙ": "wae", "ㅚ": "oe", "ㅛ": "yo", "ㅜ": "u", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi",
         "ㅠ": "yu", "ㅡ": "eu", "ㅢ": "ui", "ㅣ": "i"}


def is_hangul(ch: str) -> bool:
    return _SYLLABLE_FIRST <= ord(ch) <= _SYLLABLE_LAST or "ㄱ" <= ch <= "ㆎ" or "ᄀ" <= ch <= "ᇿ"


def _split(ch: str) -> tuple[int, int, int] | None:
    code = ord(ch) - _SYLLABLE_FIRST
    if not 0 <= code <= _SYLLABLE_LAST - _SYLLABLE_FIRST:
        return None
    return code // 588, (code % 588) // 28, code % 28


def hangul_to_roman(text: str) -> str:
    parts = [_split(ch) for ch in text]
    out: list[str] = []
    carried = None
    previous_tail = 0
    for index, ch in enumerate(text):
        syllable = parts[index]
        if syllable is None:
            out.append(_JAMO.get(ch, ch))
            carried = None
            previous_tail = 0
            continue
        lead, vowel, tail = syllable
        nxt = parts[index + 1] if index + 1 < len(parts) else None
        lead_roman = carried if carried is not None else _LEADS[lead]
        if previous_tail == _L_TAIL and lead in _L_ASSIMILATES and carried is None:
            lead_roman = "l"
        carried = None
        tail_roman = _TAILS[tail]
        if tail and nxt is not None and nxt[0] == _SILENT_LEAD:
            tail_roman, carried = _LIAISON[tail]
        previous_tail = tail if carried is None else 0
        out.append(lead_roman + _VOWELS[vowel] + tail_roman)
    return "".join(out)
