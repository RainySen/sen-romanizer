import os
import unicodedata

from sen_romanizer.alphabets import cyrillic_to_latin, greek_to_latin, is_cyrillic, is_greek
from sen_romanizer.dictionary import Dictionary, is_han
from sen_romanizer.hangul import hangul_to_roman, is_hangul
from sen_romanizer.kana import is_kana, kana_to_romaji

__all__ = ["Romanizer", "detect_language", "romanize"]

DICT_PATH = os.path.join(os.path.dirname(__file__), "dict.sqlite")
# lyrics come from the network: a giant line would hold the caller for seconds (20k chars ~4.5 s)
MAX_LINE_CHARS = 500
# particles read differently from their kana when they stand alone
PARTICLES = {"は": "wa", "へ": "e", "を": "wo"}
# a kana run after a noun starting with one of these opens with a particle: 僕ら|は|まだ
SPLIT_PARTICLES = set("はがをにのへも")
# sentence-final particles closing a conjugation: 呼ぶ|よ, 咲いた|ね
FINAL_PARTICLES = set("よねなわさぞ")
# kana that may follow each stem kind; godan rows include their contracted forms (歩いて, 待って, 読んで)
FOLLOWERS = {
    "adj": set("いくかさけきげ"), "suru": set("しさすせ"),
    "く": set("かきくけこい"), "ぐ": set("がぎぐげごい"), "す": set("さしすせそ"), "つ": set("たちつてとっ"),
    "ぬ": set("なにぬねのん"), "ぶ": set("ばびぶべぼん"), "む": set("まみむめもん"), "る": set("らりるれろっ"),
    "う": set("わいうえおっ"),
}
# honorific prefixes the dictionary stores with their word: お家 ouchi, ご飯 gohan
HONORIFICS = set("おご")
PUNCTUATION = {"、": ",", "。": ".", "！": "!", "？": "?", "「": '"', "」": '"', "『": '"', "』": '"', "・": " ",
               "，": ",", "：": ":", "；": ";", "（": "(", "）": ")"}


def _handled(ch: str) -> bool:
    return is_kana(ch) or is_han(ch) or is_hangul(ch) or is_cyrillic(ch) or is_greek(ch)


def _is_katakana(ch: str) -> bool:
    return "゠" <= ch <= "ヿ"


def _breaks_word(ch: str) -> bool:
    return ch.isspace() or is_han(ch) or is_kana(ch) or ch in PUNCTUATION or unicodedata.category(ch).startswith("P")


def detect_language(texts) -> str | None:
    # a whole song decides: one kana line makes its kanji-only lines japanese, not chinese
    joined = "".join(texts)
    if any(is_kana(ch) for ch in joined):
        return "ja"
    if any(is_han(ch) for ch in joined):
        return "zh"
    return None


class Romanizer:
    def __init__(self, dict_path: str | None = DICT_PATH):
        self._dictionary = Dictionary(dict_path)

    def romanize(self, text: str, lang: str | None = None) -> str:
        if len(text) > MAX_LINE_CHARS or not any(_handled(ch) for ch in text):
            return ""
        lang = lang or detect_language([text]) or "zh"
        line = self._join(self._tokens(text, lang))
        return greek_to_latin(cyrillic_to_latin(hangul_to_roman(line)))

    def _tokens(self, text: str, lang: str) -> list[tuple[str, str]]:
        tokens: list[tuple[str, str]] = []
        attach_next = False
        i = 0
        while i < len(text):
            ch = text[i]
            prefixed = self._prefixed(text, i, lang)
            if prefixed:
                size, reading, _common = prefixed
                tokens.append((kana_to_romaji(reading), "word"))
                attach_next, i = False, i + size
            elif is_han(ch):
                hit, attach_next = self._kanji(text, i, lang)
                if hit:
                    size, roman = hit
                    tokens.append((roman, "word"))
                    i += size
                    continue
                end = i + 1
                while end < len(text) and is_han(text[end]) and not self._kanji(text, end, lang)[0]:
                    end += 1
                tokens.append((text[i:end], "word"))
                i = end
            elif is_kana(ch):
                katakana = _is_katakana(ch)
                end = i + 1
                # を is never part of a word: it always stands alone
                while (ch != "を" and end < len(text) and is_kana(text[end]) and text[end] != "を"
                       and _is_katakana(text[end]) == katakana and not self._prefixed(text, end, lang)):
                    end += 1
                run = text[i:end]
                # は/へ closing a hiragana run are particles (のは, には, それは, こんにちは, もとへ)
                closing = PARTICLES.get(run[-1]) if not katakana and len(run) > 1 and run[-1] in "はへ" else None
                if closing:
                    run = run[:-1]
                if attach_next:
                    # okurigana after a verb/adjective stem: 咲 + いた -> saita
                    tail = run[-1] if len(run) > 1 and run[-1] in FINAL_PARTICLES else ""
                    tokens[-1] = (tokens[-1][0] + kana_to_romaji(run[:len(run) - len(tail)]), "word")
                    if tail:
                        tokens.append((kana_to_romaji(tail), "word"))
                elif len(run) > 1 and run[0] in SPLIT_PARTICLES and tokens and tokens[-1][1] == "word":
                    tokens.append((PARTICLES.get(run[0]) or kana_to_romaji(run[0]), "word"))
                    tokens.append((kana_to_romaji(run[1:]), "word"))
                else:
                    tokens.append((PARTICLES.get(run) or kana_to_romaji(run), "word"))
                if closing:
                    tokens.append((closing, "word"))
                attach_next, i = False, end
            elif ch.isspace():
                tokens.append((" ", "space"))
                attach_next, i = False, i + 1
            elif ch in PUNCTUATION or unicodedata.category(ch).startswith("P"):
                tokens.append((PUNCTUATION.get(ch, ch), "punct"))
                attach_next, i = False, i + 1
            else:
                end = i + 1
                while end < len(text) and not _breaks_word(text[end]):
                    end += 1
                tokens.append((text[i:end], "word"))
                attach_next, i = False, end
        return tokens

    def _prefixed(self, text: str, start: int, lang: str) -> tuple[int, str, bool] | None:
        if lang != "ja" or text[start] not in HONORIFICS or not is_han(text[start + 1:start + 2] or "a"):
            return None
        return self._dictionary.longest(lang, text, start)

    # (size, roman) of the kanji word at start, and whether following okurigana glues to it
    def _kanji(self, text: str, start: int, lang: str) -> tuple[tuple[int, str] | None, bool]:
        word = self._dictionary.longest(lang, text, start)
        if lang == "ja":
            for size, reading, kind in self._dictionary.stems(lang, text, start):
                # a word reaching past the okurigana into more kanji (在り方) beats the bare verb
                if word is not None and size < word[0] and (word[2] or word[0] > size + 1):
                    break
                if self._okurigana_follows(text, start + size, kind):
                    return (size, kana_to_romaji(reading)), True
        if word is None:
            return None, False
        size, reading, _common = word
        return (size, kana_to_romaji(reading) if lang == "ja" else reading), False

    @staticmethod
    def _okurigana_follows(text: str, at: int, kind: str) -> bool:
        after = text[at:at + 1]
        if not after or not is_kana(after) or _is_katakana(after):
            return False
        # も/に/の... alone are particles; followed by more kana they conjugate (歩もう, 死にたい)
        if after in SPLIT_PARTICLES and not (at + 1 < len(text) and is_kana(text[at + 1])):
            return False
        # ichidan stems take any ending (ない, ます, て, よう...)
        return kind == "v1" or after in FOLLOWERS.get(kind, ())

    @staticmethod
    def _join(tokens: list[tuple[str, str]]) -> str:
        out = ""
        for value, kind in tokens:
            if kind == "space":
                continue
            if kind == "word" and out and not out.endswith(" "):
                out += " "
            out += value
        return out.strip()


_default: Romanizer | None = None


def romanize(text: str, lang: str | None = None) -> str:
    global _default
    if _default is None:
        _default = Romanizer()
    return _default.romanize(text, lang)
