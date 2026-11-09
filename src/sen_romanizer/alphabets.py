import unicodedata

_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya", "і": "i", "ї": "yi", "є": "ye", "ґ": "g", "ў": "w",
}

# ukrainian reads и/г/е differently; its own letters (і ї є ґ) tell it apart from russian
_UKRAINIAN = {**_CYRILLIC, "и": "y", "г": "h", "е": "e"}
_UKRAINIAN_LETTERS = set("іїєґІЇЄҐ")

_GREEK = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i", "θ": "th", "ι": "i", "κ": "k",
    "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t",
    "υ": "y", "φ": "f", "χ": "ch", "ψ": "ps", "ω": "o",
}
_GREEK_PAIRS = {"ου": "ou", "αι": "ai", "ει": "ei", "οι": "oi"}


def is_cyrillic(ch: str) -> bool:
    return "Ѐ" <= ch <= "ӿ"


def is_greek(ch: str) -> bool:
    return "Ͱ" <= ch <= "Ͽ" or "ἀ" <= ch <= "῿"


def _cased(roman: str, upper: bool) -> str:
    return roman[:1].upper() + roman[1:] if upper else roman


def cyrillic_to_latin(text: str) -> str:
    table = _UKRAINIAN if _UKRAINIAN_LETTERS & set(text) else _CYRILLIC
    return "".join(_cased(table.get(ch.lower(), ch), ch.isupper()) if is_cyrillic(ch) else ch for ch in text)


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def greek_to_latin(text: str) -> str:
    # only greek letters lose their accents: pinyin tone marks in the same line must survive
    plain = "".join(_strip_accents(ch) if is_greek(ch) else ch for ch in text)
    out: list[str] = []
    i = 0
    while i < len(plain):
        pair = plain[i:i + 2]
        if pair.lower() in _GREEK_PAIRS:
            out.append(_cased(_GREEK_PAIRS[pair.lower()], pair[0].isupper()))
            i += 2
            continue
        ch = plain[i]
        out.append(_cased(_GREEK.get(ch.lower(), ch), ch.isupper()) if is_greek(ch) else ch)
        i += 1
    return "".join(out)
