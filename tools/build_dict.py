import argparse
import gzip
import os
import re
import sqlite3
import urllib.request
from contextlib import closing
import xml.etree.ElementTree as ET
from typing import IO

JMDICT_URL = "https://www.edrdg.org/pub/Nihongo/JMdict_e.gz"
CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "src", "sen_romanizer", "dict.sqlite")
# limits against a tampered or broken download: real sources are ~11 MB compressed, ~60 MB of text
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
MAX_SOURCE_CHARS = 300 * 1024 * 1024
DOWNLOAD_TIMEOUT_S = 60

COMMON_TAGS = {"news1", "ichi1", "spec1", "spec2", "gai1"}
SUFFIX_POS = {"n-suf", "suf", "ctr", "pref"}
# verbs and i-adjectives also get a stem row, so 咲 + いた reads sa + ita
STEM_POS = re.compile(r"^(v1|v5.*|adj-i)$")
SURU_POS = {"vs-s", "vs-i"}
# search-only, rare, outdated and irregular spellings (咲い for 笑い) must not compete with real words
HIDDEN_SPELLINGS = {"sK", "rK", "oK", "iK", "io"}
# dictionary frequency follows news text; songs favour these readings (空 sora, not kara)
LYRICS_READINGS = {
    "空": "そら", "街": "まち", "君": "きみ", "僕": "ぼく", "私": "わたし", "俺": "おれ", "心": "こころ", "夢": "ゆめ",
    "愛": "あい", "涙": "なみだ", "星": "ほし", "光": "ひかり", "声": "こえ", "明日": "あした", "今日": "きょう",
    "世界": "せかい", "歌": "うた", "花": "はな", "風": "かぜ", "雨": "あめ", "夜": "よる", "時": "とき", "人": "ひと",
    "手": "て", "胸": "むね", "側": "そば", "今": "いま", "日": "ひ", "月": "つき", "色": "いろ", "中": "なか",
    "上": "うえ", "下": "した", "前": "まえ", "後": "あと", "道": "みち", "海": "うみ", "一人": "ひとり",
    "二人": "ふたり", "何": "なに", "誰": "だれ", "僕ら": "ぼくら", "私達": "わたしたち", "瞳": "ひとみ", "未来": "みらい", "床": "ゆか",
    "七": "なな", "良い": "いい", "戯言": "ざれごと",
}
PHRASE_PARTICLES = {"が", "を", "の", "に", "は", "へ", "と", "で", "も"}
# keep entity names: expat would expand &v5k; into its english description
ENTITY = re.compile(r"&([\w-]+);")
XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}
CEDICT_LINE = re.compile(r"^(\S+) (\S+) \[([^\]]+)\]")
TONE_MARKS = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def _has_han(text: str) -> bool:
    return any("一" <= ch <= "鿿" or "㐀" <= ch <= "䶿" or "豈" <= ch <= "﫿" for ch in text)


def _score(tags: set[str], pos: set[str]) -> tuple[int, int, int]:
    common = sum(tag in COMMON_TAGS for tag in tags)
    rank = min((int(tag[2:]) for tag in tags if tag.startswith("nf")), default=99)
    # suffix/counter-only senses (街 as -gai) lose to the standalone word
    standalone = 0 if pos and pos <= SUFFIX_POS else 1
    return standalone, common, -rank


def _texts(element, tag: str) -> set[str]:
    return {node.text or "" for node in element.iter(tag)}


def _is_phrase(keb: str) -> bool:
    # kana ending in a particle between kanji means a set phrase (花が咲く, 胸ぐらを掴む) whose particles
    # must stay separate; okurigana (在り方, 思い出) and leading prefixes (お家) belong to the word.
    # を is never inside a word: any entry with it is an expression (恋をする)
    if "を" in keb:
        return True
    seen_han, between = False, ""
    for ch in keb:
        if "\u3040" <= ch <= "\u30ff":
            between += ch if seen_han else ""
        elif _has_han(ch):
            if between and between[-1] in PHRASE_PARTICLES:
                return True
            seen_han, between = True, ""
    return False


# (stem, reading, kind); kind says which kana may follow: "v1", "adj", "suru" or the godan ending (く, む...)
def _stem(keb: str, reading: str, pos: set[str]) -> tuple[str, str, str] | None:
    if pos & SURU_POS and keb.endswith("する") and reading.endswith("する"):
        return keb[:-2], reading[:-2], "suru"
    if len(keb) < 2 or keb[-1] != reading[-1:]:
        return None
    if "adj-i" in pos:
        return keb[:-1], reading[:-1], "adj"
    if "v1" in pos:
        return keb[:-1], reading[:-1], "v1"
    if any(p.startswith("v5") for p in pos):
        return keb[:-1], reading[:-1], keb[-1]
    return None


def _jmdict(source: IO[str]) -> tuple[dict[str, tuple[str, int]], dict[tuple[str, str], tuple[str, int]]]:
    raw = source.read(MAX_SOURCE_CHARS + 1)
    if len(raw) > MAX_SOURCE_CHARS:
        raise ValueError("JMdict source is larger than expected; refusing to parse it")
    text = ENTITY.sub(lambda m: m.group(0) if m.group(1) in XML_ENTITIES else m.group(1), raw)
    text = re.sub(r"<!DOCTYPE.*?\]>", "", text, flags=re.S)
    words: dict[str, tuple[tuple[int, int, int], str]] = {}
    stems: dict[tuple[str, str], tuple[tuple[int, int, int], str]] = {}
    for entry in ET.fromstring(text).iter("entry"):
        pos = _texts(entry, "pos")
        readings = list(entry.iter("r_ele"))
        for index, k_ele in enumerate(entry.iter("k_ele")):
            keb = k_ele.findtext("keb") or ""
            if not _has_han(keb) or _is_phrase(keb) or _texts(k_ele, "ke_inf") & HIDDEN_SPELLINGS:
                continue
            allowed = [r for r in readings if not r.findall("re_restr")
                       or keb in {x.text for x in r.findall("re_restr")}] or readings
            best = max(allowed, key=lambda r: _score(_texts(r, "re_pri"), pos))
            reading = best.findtext("reb") or ""
            spelling_tags = _texts(k_ele, "ke_pri")
            # a secondary spelling inherits the reading's frequency only when it is marked common itself
            score = _score(spelling_tags | (_texts(best, "re_pri") if index == 0 or spelling_tags else set()), pos)
            if keb not in words or score > words[keb][0]:
                words[keb] = (score, reading)
            stem = _stem(keb, reading, pos)
            if stem and _has_han(stem[0]):
                key = (stem[0], stem[2])
                if key not in stems or score > stems[key][0]:
                    stems[key] = (score, stem[1])
    # common=0: a rare word (咲い "warai") must not hide a common verb stem
    plain = {word: (reading, int(score[1] > 0 or score[2] > -99)) for word, (score, reading) in words.items()}
    plain.update({word: (reading, 1) for word, reading in LYRICS_READINGS.items() if word in plain})
    # one int to rank stems sharing a kanji (咲く saku over rare 咲う warau)
    return plain, {key: (reading, score[0] * 1000 + score[1] * 100 + 99 + score[2])
                   for key, (score, reading) in stems.items()}


def numbered_to_marked(syllable: str) -> str:
    syllable = syllable.replace("u:", "ü").replace("v", "ü")
    if not syllable or not syllable[-1].isdigit():
        return syllable
    tone, base = int(syllable[-1]), syllable[:-1]
    if tone not in (1, 2, 3, 4):
        return base
    lower = base.lower()
    if "a" in lower:
        index = lower.index("a")
    elif "e" in lower:
        index = lower.index("e")
    elif "ou" in lower:
        index = lower.index("o")
    else:
        index = max(i for i, ch in enumerate(lower) if ch in "aeiouü") if any(ch in "aeiouü" for ch in lower) else -1
    if index < 0:
        return base
    mark = TONE_MARKS[lower[index]][tone - 1]
    mark = mark.upper() if base[index].isupper() else mark
    return base[:index] + mark + base[index + 1:]


def _cedict(source: IO[str]) -> dict[str, tuple[str, int]]:
    result: dict[str, str] = {}
    proper: dict[str, str] = {}
    for line in source:
        match = CEDICT_LINE.match(line)
        if not match or line.startswith("#"):
            continue
        traditional, simplified, pinyin = match.groups()
        reading = "".join(numbered_to_marked(s) for s in pinyin.split())
        # surnames and places are capitalized; a common reading wins over them
        target = proper if pinyin[:1].isupper() else result
        for word in (traditional, simplified):
            if _has_han(word):
                target.setdefault(word, reading)
    for word, reading in proper.items():
        result.setdefault(word, reading)
    return {word: (reading, 1) for word, reading in result.items()}


def build(jmdict: IO[str], cedict: IO[str], out_path: str) -> dict[str, int]:
    ja_words, ja_stems = _jmdict(jmdict)
    tables = {"ja": ja_words, "zh": _cedict(cedict)}
    tmp_path = out_path + ".tmp"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    # closing() matters on windows: a connection's `with` commits but keeps the file locked
    with closing(sqlite3.connect(tmp_path)) as db:
        with db:
            db.execute("CREATE TABLE words(lang TEXT, word TEXT, reading TEXT, common INTEGER, PRIMARY KEY(lang, word))"
                       " WITHOUT ROWID")
            # verb/adjective stems: used when okurigana follows the kanji in the text
            db.execute("CREATE TABLE stems(lang TEXT, word TEXT, reading TEXT, kind TEXT, priority INTEGER,"
                       " PRIMARY KEY(lang, word, kind)) WITHOUT ROWID")
            db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
            for lang, words in tables.items():
                db.executemany("INSERT INTO words VALUES (?, ?, ?, ?)",
                               ((lang, w, r, common) for w, (r, common) in words.items()))
                db.execute("INSERT INTO meta VALUES (?, ?)", (f"max_len_{lang}", str(max(map(len, words), default=0))))
            db.executemany("INSERT INTO stems VALUES ('ja', ?, ?, ?, ?)",
                           ((word, reading, kind, rank) for (word, kind), (reading, rank) in ja_stems.items()))
            db.execute("INSERT INTO meta VALUES ('max_stem_ja', ?)",
                       (str(max((len(word) for word, _kind in ja_stems), default=0)),))
        db.execute("VACUUM")
    os.replace(tmp_path, out_path)
    return {lang: len(words) for lang, words in tables.items()}


def _download(url: str, cache_dir: str) -> str:
    # plain http lets anyone on the network rewrite the dictionary
    if not url.startswith("https://"):
        raise ValueError(f"refusing non-https download: {url}")
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, os.path.basename(url))
    if os.path.exists(path):
        return path
    tmp_path = path + ".part"
    with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as response, open(tmp_path, "wb") as out:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                out.close()
                os.remove(tmp_path)
                raise ValueError(f"download larger than {MAX_DOWNLOAD_BYTES} bytes: {url}")
            out.write(chunk)
    os.replace(tmp_path, path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the sen-romanizer dictionary from JMdict and CC-CEDICT")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--cache", default=os.path.join(os.path.dirname(__file__), "..", ".cache"))
    args = parser.parse_args()
    with gzip.open(_download(JMDICT_URL, args.cache), "rt", encoding="utf-8") as jmdict, \
            gzip.open(_download(CEDICT_URL, args.cache), "rt", encoding="utf-8") as cedict:
        counts = build(jmdict, cedict, os.path.abspath(args.out))
    print(f"{counts} -> {os.path.abspath(args.out)} ({os.path.getsize(args.out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
