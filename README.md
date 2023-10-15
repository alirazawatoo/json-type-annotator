# SuperDuperDB_coding_task

This project provides a JSON substitution utility that recursively transforms dictionary structures by wrapping leaf values in a typed format: `{"_content": value, "_type": "<class '...'>"}`.

## Usage

From the project root:

```bash
python3 SuperDuperDB/substitute.py <input_file> [<max_depth>] <output_file>
```

- **input_file**: Path to a JSON file (e.g. `SuperDuperDB/input.json`).
- **max_depth**: Optional. Maximum recursion depth; beyond this, nested dicts are left unchanged.
- **output_file**: Path where the transformed JSON will be written.

### Examples

```bash
# Transform full structure (no depth limit)
python3 SuperDuperDB/substitute.py SuperDuperDB/input.json SuperDuperDB/output.json

# Limit substitution to depth 1
python3 SuperDuperDB/substitute.py SuperDuperDB/input.json 1 SuperDuperDB/output.json
```

## Running tests

```bash
pip install -r requirements.txt
pytest
```
