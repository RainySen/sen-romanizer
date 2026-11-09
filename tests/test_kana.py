import pytest

from sen_romanizer.kana import is_kana, kana_to_romaji


@pytest.mark.parametrize("text, expected", [
    ("きいろい", "kiiroi"),
    ("がっこう", "gakkou"),
    ("きゃく", "kyaku"),
    ("しゃしん", "shashin"),
    ("コーヒー", "koohii"),
    ("ほんや", "hon'ya"),
    ("ティーン", "tiin"),
    ("まっちゃ", "matcha"),
    ("ファン", "fan"),
    ("ヴァイオリン", "vaiorin"),
    ("ちいさい つ", "chiisai tsu"),
])
def test_kana_to_hepburn(text, expected):
    assert kana_to_romaji(text) == expected


def test_sokuon_edge_cases():
    assert kana_to_romaji("あっ") == "a"
    assert kana_to_romaji("っ!") == "!"


def test_other_characters_pass_through():
    assert kana_to_romaji("ABC 123") == "ABC 123"


def test_is_kana():
    assert is_kana("あ") and is_kana("ア") and is_kana("ー")
    assert not is_kana("花") and not is_kana("a")
