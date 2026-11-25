from __future__ import annotations

import argparse
import sys

from sen_romanizer import detect_language, romanize

LANGUAGES = ("ja", "zh")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sen-romanizer",
        description="Romanize Japanese, Chinese, Korean, Cyrillic and Greek text.",
        epilog="examples:\n  sen-romanizer 君の名前を呼ぶよ\n  sen-romanizer --both --file lyrics.txt\n"
               "  cat lyrics.txt | sen-romanizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("text", nargs="*", help="text to romanize; without it, lines are read from --file or stdin")
    parser.add_argument("-f", "--file", help="read lines from this UTF-8 file")
    parser.add_argument("-l", "--lang", choices=LANGUAGES,
                        help="language of kanji-only text (default: detected from the whole input)")
    parser.add_argument("-b", "--both", action="store_true", help="print each original line above its romanization")
    return parser


def _read_lines(args) -> list[str]:
    if args.text:
        return [" ".join(args.text)]
    if args.file:
        with open(args.file, encoding="utf-8-sig") as source:
            return source.read().splitlines()
    return sys.stdin.read().splitlines()


# sen-romanizer command: text arguments, a file or each line of stdin
def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    # redirected input/output must not depend on the console code page (cp1252 on many windows setups);
    # utf-8-sig drops the BOM powershell puts in front of piped text
    for stream, encoding in ((sys.stdin, "utf-8-sig"), (sys.stdout, "utf-8")):
        if hasattr(stream, "reconfigure") and not stream.isatty():
            stream.reconfigure(encoding=encoding)
    lines = _read_lines(args)
    # the whole input picks the language: kanji-only lines of a japanese song are not chinese
    lang = args.lang or detect_language(lines)
    for line in lines:
        roman = romanize(line, lang) if line.strip() else ""
        if args.both and roman:
            print(line)
        print(roman or line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
