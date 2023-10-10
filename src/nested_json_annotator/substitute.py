"""Wrap the leaf values of a nested JSON document with their Python type."""

from typing import Any


def substitute(value: Any, depth: int | None = None) -> Any:
    """Return ``value`` with each leaf replaced by ``{"_content", "_type"}``.

    Dictionaries are walked recursively and rebuilt rather than mutated; every
    other value, lists included, is a leaf. ``depth`` counts dictionary levels:
    anything nested deeper than ``depth`` is returned as-is, so ``0`` leaves a
    dictionary untouched and ``None`` walks every level. A scalar root is always
    wrapped.
    """
    if depth is not None and depth < 0:
        raise ValueError("depth must be non-negative")
    return _substitute(value, depth, 0)


def _substitute(value: Any, depth: int | None, level: int) -> Any:
    if depth is not None and level > depth:
        return value
    if isinstance(value, dict):
        return {key: _substitute(child, depth, level + 1) for key, child in value.items()}
    return {"_content": value, "_type": str(type(value))}
