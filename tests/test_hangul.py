import pytest

from sen_romanizer.hangul import hangul_to_roman, is_hangul


@pytest.mark.parametrize("text, expected", [
    ("사랑해요", "saranghaeyo"),
    ("한국", "hanguk"),
    ("음악", "eumak"),
    ("안녕", "annyeong"),
    ("설날", "seollal"),
    ("사랑 해", "sarang hae"),
])
def test_revised_romanization(text, expected):
    assert hangul_to_roman(text) == expected


def test_lone_jamo():
    assert hangul_to_roman("ㅋㅋ") == "kk"


def test_is_hangul():
    assert is_hangul("한") and is_hangul("ㅋ")
    assert not is_hangul("a") and not is_hangul("あ")
