import json

import pytest

from nested_json_annotator.cli import main


@pytest.fixture
def paths(tmp_path):
    return tmp_path / "in.json", tmp_path / "out.json"


def test_annotates_every_level_by_default(paths):
    source, target = paths
    source.write_text('{"x": 1}')
    assert main([str(source), str(target)]) == 0
    assert json.loads(target.read_text()) == {"x": {"_content": 1, "_type": "<class 'int'>"}}


def test_max_depth_argument_sits_between_paths(paths):
    source, target = paths
    source.write_text('{"a": {"b": 2}}')
    assert main([str(source), "0", str(target)]) == 0
    assert json.loads(target.read_text()) == {"a": {"b": 2}}


@pytest.mark.parametrize("argv", [["only_one"], ["a", "1", "b", "c"], ["in", "x", "out"], ["in", "-1", "out"]])
def test_bad_arguments_are_usage_errors(argv, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code == 2
    assert "usage: nested-json-annotator" in capsys.readouterr().err


def test_unicode_round_trip(paths):
    source, target = paths
    source.write_text('{"label":"café"}', encoding="utf-8")
    assert main([str(source), str(target)]) == 0
    assert json.loads(target.read_text(encoding="utf-8"))["label"]["_content"] == "café"
    assert "café" in target.read_text(encoding="utf-8")


def test_missing_input_file(paths, capsys):
    source, target = paths
    assert main([str(source), str(target)]) == 1
    assert "input file not found" in capsys.readouterr().err
    assert not target.exists()


def test_input_directory_is_a_clean_error(tmp_path):
    assert main([str(tmp_path), str(tmp_path / "out.json")]) == 1


@pytest.mark.parametrize(
    "raw",
    [b"not valid json {", b"\xff", b'{"value":NaN}'],
    ids=["syntax", "invalid-utf8", "nan"],
)
def test_bad_input_preserves_existing_output(paths, raw):
    source, target = paths
    source.write_bytes(raw)
    target.write_text("keep")
    assert main([str(source), str(target)]) == 1
    assert target.read_text() == "keep"


def test_failed_write_keeps_previous_output_and_no_temp_file(paths, monkeypatch):
    source, target = paths
    source.write_text('{"a": 1}')
    target.write_text("keep")

    def fail(*_args):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("nested_json_annotator.cli.os.replace", fail)
    assert main([str(source), str(target)]) == 1
    assert target.read_text() == "keep"
    assert sorted(p.name for p in source.parent.iterdir()) == ["in.json", "out.json"]
