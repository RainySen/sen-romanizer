_BASE = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "wo", "ん": "n", "ゔ": "vu",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o", "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa",
}

_YOON_STEMS = {"き": "k", "ぎ": "g", "し": "sh", "じ": "j", "ち": "ch", "ぢ": "j", "に": "n", "ひ": "h",
               "び": "b", "ぴ": "p", "み": "m", "り": "r"}
_COMBOS = {stem + small: (cons + vowel if cons in ("sh", "ch", "j") else cons + "y" + vowel)
           for stem, cons in _YOON_STEMS.items()
           for small, vowel in (("ゃ", "a"), ("ゅ", "u"), ("ょ", "o"))}
# katakana loanword sounds
_COMBOS.update({
    "てぃ": "ti", "でぃ": "di", "とぅ": "tu", "どぅ": "du",
    "ふぁ": "fa", "ふぃ": "fi", "ふぇ": "fe", "ふぉ": "fo", "ふゅ": "fyu",
    "うぃ": "wi", "うぇ": "we", "うぉ": "wo",
    "ゔぁ": "va", "ゔぃ": "vi", "ゔぇ": "ve", "ゔぉ": "vo",
    "しぇ": "she", "じぇ": "je", "ちぇ": "che", "つぁ": "tsa", "つぃ": "tsi", "つぇ": "tse", "つぉ": "tso",
})

_SOKUON = "っ"
_LONG = "ー"
_VOWELS = "aeiou"
_BEFORE_N_APOSTROPHE = set("あいうえおやゆよぁぃぅぇぉゃゅょ")


def _to_hiragana(text: str) -> str:
    # katakana block sits 0x60 above hiragana
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in text)


def is_kana(ch: str) -> bool:
    return "ぁ" <= ch <= "ゟ" or "゠" <= ch <= "ヿ"


def kana_to_romaji(text: str) -> str:
    source = _to_hiragana(text)
    out: list[str] = []
    double_next = False
    i = 0
    while i < len(source):
        ch = source[i]
        if ch == _SOKUON:
            double_next = True
            i += 1
            continue
        pair = source[i:i + 2]
        if pair in _COMBOS:
            roman, i = _COMBOS[pair], i + 2
        elif ch == "ん":
            following = source[i + 1:i + 2]
            roman, i = ("n'" if following in _BEFORE_N_APOSTROPHE else "n"), i + 1
        elif ch in _BASE:
            roman, i = _BASE[ch], i + 1
        elif ch == _LONG:
            last = out[-1][-1:] if out else ""
            roman, i = (last if last in _VOWELS else ""), i + 1
        else:
            roman, i = ch, i + 1
        if double_next:
            double_next = False
            if roman[:1].isalpha() and roman[0] not in _VOWELS:
                roman = ("t" if roman.startswith("ch") else roman[0]) + roman
        out.append(roman)
    return "".join(out)
