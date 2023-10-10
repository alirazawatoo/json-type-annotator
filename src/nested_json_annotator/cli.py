"""Command-line interface: ``nested-json-annotator INPUT [MAX_DEPTH] OUTPUT``."""

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from nested_json_annotator import __version__
from nested_json_annotator.substitute import substitute

EPILOG = """\
examples:
  nested-json-annotator input.json output.json      annotate every level
  nested-json-annotator input.json 1 output.json    annotate top-level keys only

Lists are leaves: their items are not visited. The output file is replaced
atomically, so a failed run never leaves a truncated or half-written file.
"""


class CLIError(Exception):
    """A user-facing failure that maps to exit status 1."""


def non_negative_int(text: str) -> int:
    try:
        number = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be an integer, got {text!r}") from None
    if number < 0:
        raise argparse.ArgumentTypeError(f"must be non-negative, got {number}")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nested-json-annotator",
        description=(
            'Replace every leaf value of a JSON document with {"_content": value, '
            '"_type": "<class \'...\'>"}, recursing into nested objects.'
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="JSON file to read (UTF-8)")
    parser.add_argument(
        "max_depth",
        nargs="?",
        type=non_negative_int,
        help="number of object levels to annotate; omit for unlimited, 0 copies objects unchanged",
    )
    parser.add_argument("output", type=Path, help="file to write; replaced only on success")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def read_json(path: Path) -> object:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle, parse_constant=_reject_constant)
    except FileNotFoundError:
        raise CLIError(f"input file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise CLIError(f"invalid JSON in {path}: {exc}") from None
    except UnicodeDecodeError as exc:
        raise CLIError(f"{path} is not valid UTF-8: {exc.reason}") from None
    except RecursionError:
        raise CLIError(f"{path} is nested too deeply to parse") from None
    except OSError as exc:
        raise CLIError(f"cannot read {path}: {exc.strerror or exc}") from None


def _reject_constant(name: str) -> float:
    raise CLIError(f"{name} is not valid JSON")


def render(document: object, depth: int | None) -> str:
    try:
        return json.dumps(substitute(document, depth), ensure_ascii=False, allow_nan=False)
    except RecursionError:
        raise CLIError("document is nested too deeply to annotate") from None
    except ValueError as exc:
        raise CLIError(f"cannot serialise result: {exc}") from None


def _target_mode(path: Path) -> int:
    """Keep an existing file's permissions; otherwise honour the umask."""
    try:
        return path.stat().st_mode & 0o777
    except OSError:
        umask = os.umask(0)
        os.umask(umask)
        return 0o666 & ~umask


def write_atomically(path: Path, text: str) -> None:
    """Write to a temporary sibling file, then rename it over ``path``."""
    directory = path.parent
    try:
        fd, temp_name = tempfile.mkstemp(dir=directory, prefix=f".{path.name}.", suffix=".tmp")
    except OSError as exc:
        raise CLIError(f"cannot write {path}: {exc.strerror or exc}") from None
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, _target_mode(path))
        os.replace(temp_name, path)
    except OSError as exc:
        Path(temp_name).unlink(missing_ok=True)
        raise CLIError(f"cannot write {path}: {exc.strerror or exc}") from None


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = render(read_json(args.input), args.max_depth)
        write_atomically(args.output, rendered)
    except CLIError as exc:
        print(f"nested-json-annotator: error: {exc}", file=sys.stderr)
        return 1
    return 0
