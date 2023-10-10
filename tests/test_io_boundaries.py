import json
from unittest.mock import patch
from SuperDuperDB.substitute import main, substitute


def test_nonmutating_dictionary_transform():
    source = {"nested": {"value": 1}, "items": [1, 2]}
    result = substitute(source)
    assert source == {"nested": {"value": 1}, "items": [1, 2]}
    assert result["nested"] is not source["nested"]


def test_unicode_cli_roundtrip(tmp_path):
    source, target = tmp_path / "in.json", tmp_path / "out.json"
    source.write_text('{"label":"café"}', encoding="utf-8")
    with patch("sys.argv", ["substitute.py", str(source), str(target)]):
        assert main() == 0
    assert json.loads(target.read_text(encoding="utf-8"))["label"]["_content"] == "café"


def test_input_directory_is_clean_cli_error(tmp_path):
    with patch("sys.argv", ["substitute.py", str(tmp_path), str(tmp_path / "out")]):
        assert main() == 1


def test_invalid_utf8_preserves_existing_output(tmp_path):
    source, target = tmp_path / "in.json", tmp_path / "out.json"
    source.write_bytes(b"\xff")
    target.write_text("keep")
    with patch("sys.argv", ["substitute.py", str(source), str(target)]):
        assert main() == 1
    assert target.read_text() == "keep"


def test_nonfinite_json_preserves_existing_output(tmp_path):
    source, target = tmp_path / "in.json", tmp_path / "out.json"
    source.write_text('{"value":NaN}')
    target.write_text("keep")
    with patch("sys.argv", ["substitute.py", str(source), str(target)]):
        assert main() == 1
    assert target.read_text() == "keep"
