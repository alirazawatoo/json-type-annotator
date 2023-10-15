# JSON Type Annotator

A small Python CLI that recursively replaces JSON leaf values with explicit content/type records while preserving dictionary structure.

```json
{"name": "Ada", "active": true}
```

becomes:

```json
{
  "name": {"_content": "Ada", "_type": "<class 'str'>"},
  "active": {"_content": true, "_type": "<class 'bool'>"}
}
```

## Usage

```bash
python3 SuperDuperDB/substitute.py INPUT [MAX_DEPTH] OUTPUT
```

Without `MAX_DEPTH`, nested dictionaries are traversed fully. With a depth limit, dictionaries below that boundary remain unmodified. The repository includes input/output fixtures and pytest coverage for substitution behavior.

```bash
pip install -r requirements.txt
pytest
```

## Boundaries

- The transformation targets dictionary structures; it is not a general schema inference engine.
- Type names use Python's string representation and are intended for inspection rather than a stable cross-language contract.
- Files are rewritten to the requested output path; preserve the source file when comparing transformations.
