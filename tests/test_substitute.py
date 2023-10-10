import pytest

from nested_json_annotator import substitute


def wrapped(value):
    return {"_content": value, "_type": str(type(value))}


@pytest.mark.parametrize(
    ("value", "type_name"),
    [
        ("hello", "<class 'str'>"),
        (42, "<class 'int'>"),
        (1.5, "<class 'float'>"),
        (True, "<class 'bool'>"),
        (None, "<class 'NoneType'>"),
        ([1, 2, 3], "<class 'list'>"),
    ],
)
def test_scalar_root_is_wrapped(value, type_name):
    assert substitute(value) == {"_content": value, "_type": type_name}


def test_flat_dict_values_are_wrapped():
    assert substitute({"a": 1, "b": "two"}) == {"a": wrapped(1), "b": wrapped("two")}


def test_nested_dicts_are_walked():
    assert substitute({"outer": {"inner": "value"}}) == {"outer": {"inner": wrapped("value")}}


def test_scalar_root_is_wrapped_even_at_depth_zero():
    assert substitute("x", depth=0) == wrapped("x")


def test_empty_dicts_stay_empty():
    assert substitute({}) == {}
    assert substitute({"a": {}}) == {"a": {}}


def test_list_is_a_leaf_and_its_dicts_are_not_visited():
    result = substitute({"rows": [{"id": 1}, {"id": 2}], "empty": []})
    assert result == {"rows": wrapped([{"id": 1}, {"id": 2}]), "empty": wrapped([])}


@pytest.mark.parametrize(
    ("depth", "expected"),
    [
        (0, {"a": 1, "b": {"c": 2}}),
        (1, {"a": wrapped(1), "b": {"c": 2}}),
        (2, {"a": wrapped(1), "b": {"c": wrapped(2)}}),
        (50, {"a": wrapped(1), "b": {"c": wrapped(2)}}),
        (None, {"a": wrapped(1), "b": {"c": wrapped(2)}}),
    ],
)
def test_depth_limits_dictionary_levels(depth, expected):
    assert substitute({"a": 1, "b": {"c": 2}}, depth=depth) == expected


def test_negative_depth_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        substitute({"a": 1}, depth=-1)


def test_deep_nesting_reaches_the_innermost_leaf():
    levels = 200
    data = innermost = {}
    for _ in range(levels):
        innermost["next"] = {}
        innermost = innermost["next"]
    innermost["leaf"] = "bottom"

    result = substitute(data)
    for _ in range(levels):
        result = result["next"]
    assert result == {"leaf": wrapped("bottom")}


def test_unicode_keys_and_values_are_preserved():
    assert substitute({"café": {"名前": "Zoë 🌍"}}) == {"café": {"名前": wrapped("Zoë 🌍")}}


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
