# sen-romanizer

Lightweight lyrics romanizer for Python, with no dependencies.

```
pip install sen-romanizer
```

```python
from sen_romanizer import romanize

romanize("君の名前を呼ぶよ")   # 'kimi no namae wo yobu yo'
romanize("黄色い花が咲いた")   # 'kiiroi hana ga saita'
romanize("月亮代表我的心")     # 'yuèliang dàibiǎo wǒ de xīn'
romanize("사랑해요")           # 'saranghaeyo'
romanize("Я люблю тебя")       # 'Ya lyublyu tebya'
```

A line with only kanji is ambiguous (Japanese or Chinese). Detect the language once from the whole song and pass it:

```python
from sen_romanizer import detect_language, romanize

lang = detect_language(lines)              # 'ja' if any line has kana, 'zh' if only hanzi
romaji = [romanize(line, lang) for line in lines]
```

## What it does

| Script | Method |
|---|---|
| Japanese kana | Modified Hepburn rules (っ, ー, ん', loanword sounds) |
| Japanese kanji | Longest dictionary match + verb/adjective stems checked against the following kana (咲 + いた → saita, 歩 + こう → arukou) |
| Chinese | Longest dictionary match, tone-marked pinyin |
| Korean | Revised Romanization with liaison and ㄹ assimilation |
| Cyrillic, Greek | Letter tables (Ukrainian detected by its own letters) |

The dictionary is a read-only SQLite file queried line by line, so memory stays small (about 12 MB more while in use, where
loading a full dictionary into Python objects costs 100+ MB).

Readings follow the most common use; context-dependent readings (今日 kyou / konnichi) take the frequent one.
A short list of song-friendly readings (空 sora, 明日 ashita…) overrides news-text frequency.

## Command line

Installing the package also adds a `sen-romanizer` command:

```console
$ sen-romanizer かんと
kanto
$ sen-romanizer --both --file lyrics.txt
君の名前を呼ぶよ
kimi no namae wo yobu yo
I love you
$ cat lyrics.txt | sen-romanizer
kimi no namae wo yobu yo
I love you
```

- Without text arguments it reads `--file` (UTF-8) or standard input, one line at a time. Latin lines are printed as they are.
- `--both` prints each original line above its romanization, handy for lyrics.
- `--lang ja|zh` forces the language of kanji-only text; by default the whole input decides.
- `python -m sen_romanizer` works the same.

On Windows PowerShell 5.1 a pipe re-encodes text with `$OutputEncoding`, which is ASCII by default and loses
non-Latin characters before they reach the command. Use `--file`, or run
`$OutputEncoding = [System.Text.UTF8Encoding]::new()` first. cmd's `type lyrics.txt | sen-romanizer` works as is.

## Accuracy and limits

Measured against human-written romaji for 1,618 lines of 40 Japanese pop songs, sen-romanizer gives the same reading
for about **87 %** of the lines (ignoring spacing, `wo`/`o` and vowel length).

It reads words, not sentences, so it cannot pick readings that depend on context or on the songwriter:

- context readings take the common one (今日 kyou, 居る oru/iru);
- artistic readings written with furigana in the booklet (泡 abuku, 本気 maji) come out with the dictionary reading;
- numbers with counters keep the digits (1番 → 1 ban).

When lyrics already carry an official romanization, prefer it and use sen-romanizer for the rest.

## Building the dictionary

The wheel ships `dict.sqlite`. From source, build it once:

```
python tools/build_dict.py
```

It downloads JMdict and CC-CEDICT and writes `src/sen_romanizer/dict.sqlite`.

## Credits and licenses

- Code: MIT, see `LICENSE`.
- The bundled dictionary is derived from:
  - **JMdict** — © Electronic Dictionary Research and Development Group (EDRDG), used under
    [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). <https://www.edrdg.org/jmdict/j_jmdict.html>
  - **CC-CEDICT** — © MDBG, used under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
    <https://www.mdbg.net/chinese/dictionary?page=cc-cedict>
- `dict.sqlite` is therefore distributed under CC BY-SA 4.0. See `NOTICE`, shipped with the package.
- This package uses the JMdict/EDICT dictionary files. These files are the property of the Electronic Dictionary
  Research and Development Group, and are used in conformance with the Group's licence.
