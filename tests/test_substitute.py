"""Unit tests for the substitute module (substitute function and CLI)."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Allow importing from project root when running tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from SuperDuperDB.substitute import substitute, main


class TestSubstituteFunction:
    """Tests for the substitute() function."""

    def test_leaf_string_wrapped(self):
        """Non-dict value is wrapped with _content and _type."""
        result = substitute("hello")
        assert result == {"_content": "hello", "_type": "<class 'str'>"}

    def test_leaf_int_wrapped(self):
        """Integer leaf is correctly wrapped."""
        result = substitute(42)
        assert result["_content"] == 42
        assert "int" in result["_type"]

    def test_leaf_bool_wrapped(self):
        """Boolean leaf is correctly wrapped."""
        result = substitute(True)
        assert result["_content"] is True
        assert "bool" in result["_type"]

    def test_leaf_list_wrapped_as_leaf(self):
        """List is treated as leaf and wrapped (no recursion into list items)."""
        result = substitute([1, 2, 3])
        assert result["_content"] == [1, 2, 3]
        assert "list" in result["_type"]

    def test_flat_dict_all_values_wrapped(self):
        """Flat dict has each value wrapped."""
        data = {"a": 1, "b": "two"}
        result = substitute(data)
        assert result["a"] == {"_content": 1, "_type": "<class 'int'>"}
        assert result["b"] == {"_content": "two", "_type": "<class 'str'>"}

    def test_nested_dict_recursed(self):
        """Nested dicts are recursed into and leaves wrapped."""
        data = {"outer": {"inner": "value"}}
        result = substitute(data)
        assert result["outer"]["inner"] == {
            "_content": "value",
            "_type": "<class 'str'>",
        }

    def test_empty_dict_unchanged(self):
        """Empty dict returns empty dict."""
        assert substitute({}) == {}

    def test_depth_zero_returns_unchanged(self):
        """When current_depth > depth, dict is returned unchanged."""
        data = {"a": 1, "b": {"c": 2}}
        result = substitute(data, depth=0)
        assert result == data

    def test_depth_one_stops_after_first_level(self):
        """With depth=1, first-level values are substituted; nested dict values are unchanged."""
        data = {"a": 1, "b": {"c": 2}}
        result = substitute(data, depth=1)
        assert result["a"] == {"_content": 1, "_type": "<class 'int'>"}
        # Nested dict is entered at current_depth=1; its value "c": 2 is at depth 2 > 1, so returned unchanged
        assert result["b"] == {"c": 2}

    def test_depth_none_full_recursion(self):
        """With depth=None, full recursion (existing behavior)."""
        data = {"a": {"b": {"c": 3}}}
        result = substitute(data, depth=None)
        assert result["a"]["b"]["c"] == {
            "_content": 3,
            "_type": "<class 'int'>",
        }

    def test_matches_expected_output_format(self):
        """Output structure matches the expected format from sample input."""
        data = {
            "name": "John Doe",
            "age": 30,
            "address": {"city": "Anytown", "zip": "12345"},
        }
        result = substitute(data)
        assert result["name"]["_content"] == "John Doe"
        assert result["age"]["_content"] == 30
        assert result["address"]["city"]["_content"] == "Anytown"
        assert result["address"]["zip"]["_content"] == "12345"


class TestSubstituteCLI:
    """Tests for the command-line interface."""

    def test_three_args_success(self, tmp_path):
        """CLI with input and output path (no max_depth) succeeds."""
        input_file = tmp_path / "in.json"
        output_file = tmp_path / "out.json"
        input_file.write_text('{"x": 1}')
        with patch("sys.argv", ["substitute.py", str(input_file), str(output_file)]):
            exit_code = main()
        assert exit_code == 0
        out = json.loads(output_file.read_text())
        assert out == {"x": {"_content": 1, "_type": "<class 'int'>"}}

    def test_four_args_with_max_depth_success(self, tmp_path):
        """CLI with input, max_depth, and output succeeds."""
        input_file = tmp_path / "in.json"
        output_file = tmp_path / "out.json"
        input_file.write_text('{"a": {"b": 2}}')
        with patch(
            "sys.argv",
            ["substitute.py", str(input_file), "0", str(output_file)],
        ):
            exit_code = main()
        assert exit_code == 0
        out = json.loads(output_file.read_text())
        assert out == {"a": {"b": 2}}

    def test_too_few_args_returns_one(self):
        """Too few arguments returns exit code 1."""
        with patch("sys.argv", ["substitute.py", "only_one"]):
            exit_code = main()
        assert exit_code == 1

    def test_too_many_args_returns_one(self):
        """Too many arguments returns exit code 1."""
        with patch("sys.argv", ["substitute.py", "a", "b", "c", "d"]):
            exit_code = main()
        assert exit_code == 1

    def test_missing_input_file_returns_one(self, tmp_path):
        """Missing input file returns exit code 1."""
        output_file = tmp_path / "out.json"
        with patch(
            "sys.argv",
            ["substitute.py", str(tmp_path / "nonexistent.json"), str(output_file)],
        ):
            exit_code = main()
        assert exit_code == 1

    def test_invalid_json_returns_one(self, tmp_path):
        """Invalid JSON in input file returns exit code 1."""
        input_file = tmp_path / "in.json"
        output_file = tmp_path / "out.json"
        input_file.write_text("not valid json {")
        with patch("sys.argv", ["substitute.py", str(input_file), str(output_file)]):
            exit_code = main()
        assert exit_code == 1

    def test_invalid_max_depth_returns_one(self, tmp_path):
        """Non-integer max_depth returns exit code 1."""
        input_file = tmp_path / "in.json"
        output_file = tmp_path / "out.json"
        input_file.write_text("{}")
        with patch(
            "sys.argv",
            ["substitute.py", str(input_file), "not_a_number", str(output_file)],
        ):
            exit_code = main()
        assert exit_code == 1

    def test_negative_max_depth_returns_one(self, tmp_path):
        """Negative max_depth returns exit code 1."""
        input_file = tmp_path / "in.json"
        output_file = tmp_path / "out.json"
        input_file.write_text("{}")
        with patch(
            "sys.argv",
            ["substitute.py", str(input_file), "-1", str(output_file)],
        ):
            exit_code = main()
        assert exit_code == 1
