import pytest

from sen_romanizer.alphabets import cyrillic_to_latin, greek_to_latin, is_cyrillic, is_greek


@pytest.mark.parametrize("text, expected", [
    ("Привет мир", "Privet mir"),
    ("Щука", "Shchuka"),
    ("ёж", "yozh"),
    ("Київ", "Kyyiv"),
])
def test_cyrillic(text, expected):
    assert cyrillic_to_latin(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("Καλημέρα", "Kalimera"),
    ("ουρανός", "ouranos"),
    ("Ψυχή", "Psychi"),
])
def test_greek(text, expected):
    assert greek_to_latin(text) == expected


def test_detection():
    assert is_cyrillic("Ж") and not is_cyrillic("Z")
    assert is_greek("λ") and not is_greek("l")


def test_greek_leaves_other_accents_alone():
    assert greek_to_latin("nǐhǎo καλά") == "nǐhǎo kala"
