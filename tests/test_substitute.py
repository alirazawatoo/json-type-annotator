import pytest

from nested_json_annotator import substitute


def wrapped(value):
    return {"_content": value, "_type": str(type(value))}


@pytest.mark.parametrize(
    ("value", "type_name"),
    [
        ("hello", "<class 'str'>"),
        (42, "<class 'int'>"),
        (True, "<class 'bool'>"),
        ([1, 2, 3], "<class 'list'>"),
    ],
)
def test_scalar_root_is_wrapped(value, type_name):
    assert substitute(value) == {"_content": value, "_type": type_name}


def test_flat_dict_values_are_wrapped():
    assert substitute({"a": 1, "b": "two"}) == {"a": wrapped(1), "b": wrapped("two")}


def test_nested_dicts_are_walked():
    assert substitute({"outer": {"inner": "value"}}) == {"outer": {"inner": wrapped("value")}}


def test_empty_dict_stays_empty():
    assert substitute({}) == {}


@pytest.mark.parametrize(
    ("depth", "expected"),
    [
        (0, {"a": 1, "b": {"c": 2}}),
        (1, {"a": wrapped(1), "b": {"c": 2}}),
        (None, {"a": wrapped(1), "b": {"c": wrapped(2)}}),
    ],
)
def test_depth_limits_dictionary_levels(depth, expected):
    assert substitute({"a": 1, "b": {"c": 2}}, depth=depth) == expected


def test_input_is_not_mutated():
    source = {"nested": {"value": 1}, "items": [1, 2]}
    result = substitute(source)
    assert source == {"nested": {"value": 1}, "items": [1, 2]}
    assert result["nested"] is not source["nested"]


def test_matches_bundled_example(examples_dir):
    import json

    source = json.loads((examples_dir / "input.json").read_text(encoding="utf-8"))
    expected = json.loads((examples_dir / "output.json").read_text(encoding="utf-8"))
    assert substitute(source) == expected
