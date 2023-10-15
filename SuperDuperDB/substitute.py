"""Substitute module: recursively transforms dict values into typed wrapper structures."""

import json
import sys
from typing import Any, Dict, Optional, Union


def substitute(
    dictionary: Union[Dict[str, Any], Any],
    depth: Optional[int] = None,
    current_depth: int = 0,
) -> Union[Dict[str, Any], Any]:
    """
    Recursively substitute the input dictionary: at each level, non-dict values
    are replaced with a wrapper {"_content": value, "_type": str(type(value))}.
    Dict values are recursed into until max depth (if set) is reached.

    Args:
        dictionary: Input structure (dict or leaf value).
        depth: Optional max recursion depth; beyond this, dicts are returned as-is.
        current_depth: Current recursion level (used internally).

    Returns:
        Transformed structure with leaf values wrapped in _content/_type.
    """
    # Beyond max depth: return structure unchanged to avoid unnecessary processing
    if depth is not None and current_depth > depth:
        return dictionary

    if isinstance(dictionary, dict):
        return {
            key: substitute(value, depth, current_depth + 1)
            for key, value in dictionary.items()
        }
    # Non-dict leaf: wrap for consistent type-preserving serialization
    return {"_content": dictionary, "_type": str(type(dictionary))}


def main() -> int:
    """
    CLI entry point: read JSON input, run substitute, write JSON output.
    Usage: substitute.py <input_file> [<max_depth>] <output_file>
    """
    if not 3 <= len(sys.argv) <= 4:
        print("Error: Wrong number of arguments", file=sys.stderr)
        print(
            "Usage: python substitute.py <input_file> [<max_depth>] <output_file>",
            file=sys.stderr,
        )
        return 1

    input_path = sys.argv[1]
    output_path = sys.argv[-1]
    max_depth = None
    if len(sys.argv) == 4:
        try:
            max_depth = int(sys.argv[2])
        except ValueError:
            print("Error: max_depth must be an integer", file=sys.stderr)
            return 1
        if max_depth < 0:
            print("Error: max_depth must be non-negative", file=sys.stderr)
            return 1

    try:
        with open(input_path, encoding="utf-8") as f:
            input_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        return 1

    result = substitute(input_data, max_depth)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f)
    except OSError as e:
        print(f"Error: Cannot write output file: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
