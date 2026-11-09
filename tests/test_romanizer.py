import io

import pytest

from sen_romanizer import Romanizer
from tests.test_build_dict import CEDICT, JMDICT
from tools.build_dict import build

EXTRA = """<entry><k_ele><keb>君</keb></k_ele><r_ele><reb>きみ</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>名前</keb></k_ele><r_ele><reb>なまえ</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>私</keb></k_ele><r_ele><reb>わたし</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>世界</keb></k_ele><r_ele><reb>せかい</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>僕ら</keb></k_ele><r_ele><reb>ぼくら</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>寝床</keb></k_ele><r_ele><reb>ねどこ</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>見上げる</keb></k_ele><r_ele><reb>みあげる</reb></r_ele><sense><pos>&v1;</pos></sense></entry>
<entry><k_ele><keb>歩む</keb><ke_pri>news1</ke_pri></k_ele><r_ele><reb>あゆむ</reb><re_pri>news1</re_pri></r_ele>
  <sense><pos>&v5m;</pos></sense></entry>
<entry><k_ele><keb>咲い</keb></k_ele><r_ele><reb>わらい</reb></r_ele><sense><pos>&n;</pos></sense></entry>
<entry><k_ele><keb>咲う</keb></k_ele><r_ele><reb>わらう</reb></r_ele><sense><pos>&v5u;</pos></sense></entry>
</JMdict>"""


@pytest.fixture(scope="module")
def romanizer(tmp_path_factory):
    path = tmp_path_factory.mktemp("dict") / "dict.sqlite"
    build(io.StringIO(JMDICT.replace("</JMdict>", EXTRA)), io.StringIO(CEDICT), str(path))
    return Romanizer(str(path))


@pytest.mark.parametrize("text, expected", [
    ("君の名前を呼ぶよ", "kimi no namae wo yobu yo"),
    ("黄色い花が咲いた", "kiiroi hana ga saita"),
    ("私は", "watashi wa"),
    ("今日、世界へ", "kyou, sekai e"),
    ("コーヒーを", "koohii wo"),
    ("空を見上げて歩こう", "sora wo miagete arukou"),
    ("愛してる", "aishiteru"),
    ("歩もう", "ayumou"),
    ("咲いたね", "saita ne"),
    ("僕らはまだ", "bokura wa mada"),
    ("東京の街で", "東京 no machi de"),
])
def test_japanese_lines(romanizer, text, expected):
    assert romanizer.romanize(text) == expected


def test_mixed_latin_and_kanji_line(romanizer):
    assert romanizer.romanize("君と Dance") == "kimi to Dance"


def test_chinese_line(romanizer):
    assert romanizer.romanize("你好北京") == "nǐhǎo Běijīng"


def test_other_scripts_go_through_their_rules(romanizer):
    assert romanizer.romanize("사랑해요") == "saranghaeyo"
    assert romanizer.romanize("Привет") == "Privet"


def test_latin_only_lines_need_no_romanization(romanizer):
    assert romanizer.romanize("Hello world") == ""


def test_missing_dictionary_degrades_to_rules(tmp_path):
    plain = Romanizer(str(tmp_path / "missing.sqlite"))
    assert plain.romanize("사랑") == "sarang"
    assert plain.romanize("花が") == "花 ga"


def test_unknown_kanji_stays_as_is(romanizer):
    assert romanizer.romanize("龘") == "龘"


def test_outdated_dictionary_is_ignored_once(tmp_path, caplog):
    import sqlite3
    from contextlib import closing
    path = tmp_path / "old.sqlite"
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE words(lang TEXT, word TEXT)")
        db.execute("CREATE TABLE meta(key TEXT, value TEXT)")
    old = Romanizer(str(path))
    assert old.romanize("花が") == "花 ga"
    assert old.romanize("花が") == "花 ga"
    assert len([r for r in caplog.records if r.levelname == "WARNING"]) == 1


def test_language_hint_keeps_kanji_only_japanese_lines_japanese(romanizer):
    assert romanizer.romanize("寝床", lang="ja") == "nedoko"
    assert romanizer.romanize("你好", lang="zh") == "nǐhǎo"


def test_detect_language_uses_the_whole_lyrics():
    from sen_romanizer import detect_language
    assert detect_language(["寝床", "君の名前"]) == "ja"
    assert detect_language(["我爱你", "你好"]) == "zh"
    assert detect_language(["Hello", "사랑해"]) is None
