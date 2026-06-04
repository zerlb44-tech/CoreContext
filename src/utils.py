import sys
import logging
import tiktoken


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)]
    )


def count_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text, disallowed_special=()))
    except Exception:
        return len(text.split()) * 4 // 3


def fix_windows_encoding() -> None:
    if sys.platform.startswith("win"):
        if sys.stdout.encoding != "utf-8":
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if sys.stderr.encoding != "utf-8":
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

