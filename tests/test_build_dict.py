import io
import sqlite3
from contextlib import closing

from tools.build_dict import build, numbered_to_marked

JMDICT = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE JMdict [
<!ENTITY n "noun (common) (futsuumeishi)">
<!ENTITY v5k "Godan verb with 'ku' ending">
<!ENTITY v5b "Godan verb with 'bu' ending">
<!ENTITY adj-i "adjective (keiyoushi)">
<!ENTITY n-suf "noun, used as a suffix">
<!ENTITY ctr "counter">
<!ENTITY vs-s "suru verb - special class">
<!ENTITY v1 "Ichidan verb">
<!ENTITY v5m "Godan verb with 'mu' ending">
<!ENTITY v5u "Godan verb with 'u' ending">
<!ENTITY v5r "Godan verb with 'ru' ending">
<!ENTITY sK "search-only kanji form">
]>
<JMdict>
<entry><k_ele><keb>花</keb><ke_pri>ichi1</ke_pri></k_ele>
  <r_ele><reb>はな</reb><re_pri>ichi1</re_pri></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>咲く</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>さく</reb><re_pri>ichi1</re_pri></r_ele>
  <sense><pos>&v5k;</pos></sense></entry>
<entry><k_ele><keb>呼ぶ</keb></k_ele><r_ele><reb>よぶ</reb></r_ele><sense><pos>&v5b;</pos></sense></entry>
<entry><k_ele><keb>黄色い</keb></k_ele><r_ele><reb>きいろい</reb></r_ele><sense><pos>&adj-i;</pos></sense></entry>
<entry><k_ele><keb>今日</keb><ke_pri>news1</ke_pri></k_ele>
  <r_ele><reb>こんにち</reb></r_ele><r_ele><reb>きょう</reb><re_pri>news1</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><r_ele><reb>ありがとう</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>笑い</keb><ke_pri>ichi1</ke_pri></k_ele><k_ele><keb>咲い</keb><ke_inf>&sK;</ke_inf></k_ele>
  <r_ele><reb>わらい</reb><re_pri>ichi1</re_pri></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>街</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>がい</reb><re_pri>ichi1</re_pri></r_ele>
  <sense><pos>&n-suf;</pos></sense></entry>
<entry><k_ele><keb>街</keb></k_ele><r_ele><reb>まち</reb><re_pri>ichi1</re_pri><re_pri>news1</re_pri><re_pri>nf02</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>花が咲く</keb></k_ele><r_ele><reb>はながさく</reb></r_ele><sense><pos>&v5k;</pos></sense></entry>
<entry><k_ele><keb>歩</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>ほ</reb><re_pri>ichi1</re_pri></r_ele><sense><pos>&ctr;</pos></sense></entry>
<entry><k_ele><keb>歩く</keb></k_ele><r_ele><reb>あるく</reb></r_ele><sense><pos>&v5k;</pos></sense></entry>
<entry><k_ele><keb>愛</keb></k_ele><r_ele><reb>あい</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>愛する</keb></k_ele><r_ele><reb>あいする</reb></r_ele><sense><pos>&vs-s;</pos></sense></entry>
<entry><k_ele><keb>愛しい</keb></k_ele><r_ele><reb>いとしい</reb></r_ele><sense><pos>&adj-i;</pos></sense></entry>
<entry><k_ele><keb>床</keb><ke_pri>news1</ke_pri></k_ele><r_ele><reb>とこ</reb><re_pri>news1</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>空</keb><ke_pri>news1</ke_pri></k_ele><r_ele><reb>から</reb><re_pri>news1</re_pri><re_pri>nf03</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>家</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>いえ</reb><re_pri>ichi1</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>お家</keb><ke_pri>spec1</ke_pri></k_ele><r_ele><reb>おうち</reb><re_pri>spec1</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>七</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>しち</reb><re_pri>ichi1</re_pri></r_ele>
  <r_ele><reb>なな</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>在り方</keb></k_ele><r_ele><reb>ありかた</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>在る</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>ある</reb><re_pri>ichi1</re_pri></r_ele>
  <sense><pos>&v5r;</pos></sense></entry>
<entry><k_ele><keb>良い</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>よい</reb><re_pri>ichi1</re_pri></r_ele>
  <r_ele><reb>いい</reb></r_ele><sense><pos>&adj-i;</pos></sense></entry>
<entry><k_ele><keb>戯言</keb><ke_pri>spec1</ke_pri></k_ele><r_ele><reb>たわごと</reb><re_pri>spec1</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>恋</keb><ke_pri>ichi1</ke_pri></k_ele><r_ele><reb>こい</reb><re_pri>ichi1</re_pri></r_ele>
  <sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>恋をする</keb></k_ele><r_ele><reb>こいをする</reb></r_ele><sense><pos>&vs-s;</pos></sense></entry>
<entry><k_ele><keb>胸ぐらを掴む</keb></k_ele><r_ele><reb>むなぐらをつかむ</reb></r_ele><sense><pos>&v5m;</pos></sense></entry>
</JMdict>
"""

CEDICT = """# CC-CEDICT
你好 你好 [ni3 hao3] /hello/
北京 北京 [Bei3 jing1] /Beijing/
了 了 [le5] /particle/
了 了 [liao3] /to finish/
綠 绿 [lu:4] /green/
"""


def rows(path):
    with closing(sqlite3.connect(path)) as db:
        words = {(lang, word): reading for lang, word, reading, _c in db.execute("SELECT * FROM words")}
        stems = {(lang, word): reading for lang, word, reading, _kind, _p in db.execute("SELECT * FROM stems")}
        meta = dict(db.execute("SELECT key, value FROM meta"))
    return words, meta, stems


def test_build_keeps_kanji_words_with_their_reading_and_stems(tmp_path):
    out = tmp_path / "dict.sqlite"
    build(io.StringIO(JMDICT), io.StringIO(CEDICT), str(out))
    words, meta, stems = rows(out)
    assert words[("ja", "花")] == "はな" and words[("ja", "咲く")] == "さく"
    assert stems[("ja", "咲")] == "さ" and stems[("ja", "呼")] == "よ" and stems[("ja", "黄色")] == "きいろ"
    assert stems[("ja", "歩")] == "ある" and stems[("ja", "愛")] == "あい"
    assert ("ja", "咲") not in words
    assert words[("ja", "今日")] == "きょう"
    assert ("ja", "ありがとう") not in words
    assert meta["max_len_ja"] == "3"


def test_build_prefers_frequent_readings_and_skips_phrases(tmp_path):
    out = tmp_path / "dict.sqlite"
    build(io.StringIO(JMDICT), io.StringIO(CEDICT), str(out))
    words, _meta, _stems = rows(out)
    assert words[("ja", "街")] == "まち"
    assert ("ja", "花が咲く") not in words
    # leading honorific kana is part of the word, not a phrase
    assert words[("ja", "お家")] == "おうち"
    # okurigana between kanji is part of the word; only particles make a phrase
    assert words[("ja", "在り方")] == "ありかた"
    # expressions with を or a particle before the next kanji are phrases, not words
    assert ("ja", "恋をする") not in words and ("ja", "胸ぐらを掴む") not in words
    assert ("ja", "咲い") not in words and words[("ja", "笑い")] == "わらい"
    assert words[("ja", "歩")] == "ほ"


def test_lyrics_overrides_beat_dictionary_frequency(tmp_path):
    out = tmp_path / "dict.sqlite"
    build(io.StringIO(JMDICT), io.StringIO(CEDICT), str(out))
    words, _meta, _stems = rows(out)
    assert words[("ja", "空")] == "そら"
    assert words[("ja", "床")] == "ゆか"
    assert words[("ja", "七")] == "なな"
    assert words[("ja", "良い")] == "いい"
    assert words[("ja", "戯言")] == "ざれごと"


def test_build_converts_cedict_pinyin_and_prefers_common_entries(tmp_path):
    out = tmp_path / "dict.sqlite"
    build(io.StringIO(JMDICT), io.StringIO(CEDICT), str(out))
    words, meta, _stems = rows(out)
    assert words[("zh", "你好")] == "nǐhǎo"
    assert words[("zh", "北京")] == "Běijīng"
    assert words[("zh", "了")] == "le"
    assert words[("zh", "綠")] == words[("zh", "绿")] == "lǜ"
    assert meta["max_len_zh"] == "2"


def test_tone_marks_follow_the_standard_placement():
    assert numbered_to_marked("hao3") == "hǎo"
    assert numbered_to_marked("dou1") == "dōu"
    assert numbered_to_marked("gui4") == "guì"
    assert numbered_to_marked("nu:3") == "nǚ"
    assert numbered_to_marked("ma5") == "ma"


def test_downloads_refuse_plain_http(tmp_path):
    import pytest
    from tools.build_dict import _download
    with pytest.raises(ValueError):
        _download("http://example.com/JMdict_e.gz", str(tmp_path))


def test_oversized_source_is_rejected(monkeypatch):
    import pytest
    from tools import build_dict
    monkeypatch.setattr(build_dict, "MAX_SOURCE_CHARS", 100)
    with pytest.raises(ValueError):
        build_dict._jmdict(io.StringIO(JMDICT))
