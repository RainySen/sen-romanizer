import io

import pytest

from sen_romanizer.cli import main


def run(argv, capsys, stdin=None, monkeypatch=None):
    if stdin is not None:
        monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin.encode("utf-8")), encoding="utf-8"))
    assert main(argv) == 0
    return capsys.readouterr().out


def test_text_arguments_are_romanized(capsys):
    assert run(["かんと"], capsys) == "kanto\n"
    assert run(["사랑", "해"], capsys) == "sarang hae\n"


def test_each_input_line_is_romanized_and_latin_lines_kept(capsys, monkeypatch):
    out = run([], capsys, stdin="かんと\nHello\n\n사랑\n", monkeypatch=monkeypatch)
    assert out == "kanto\nHello\n\nsarang\n"


def test_bom_in_front_of_piped_text_is_dropped(capsys, monkeypatch):
    # powershell pipes utf-8 with a BOM
    assert run([], capsys, stdin="﻿かんと\n", monkeypatch=monkeypatch) == "kanto\n"


def test_both_prints_the_original_above_its_romanization(capsys, monkeypatch):
    out = run(["--both"], capsys, stdin="かんと\nHello\n", monkeypatch=monkeypatch)
    assert out == "かんと\nkanto\nHello\n"


def test_file_is_read_as_utf8(capsys, tmp_path):
    lyrics = tmp_path / "lyrics.txt"
    lyrics.write_text("かんと\nさくら\n", encoding="utf-8")
    assert run(["--file", str(lyrics)], capsys) == "kanto\nsakura\n"


def test_unknown_language_is_rejected(capsys):
    with pytest.raises(SystemExit):
        main(["--lang", "xx", "かんと"])
