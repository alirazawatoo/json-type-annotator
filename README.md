# Nested JSON annotator

A small Python command-line exercise that adds Python type labels to JSON leaf values. It recursively visits dictionaries; lists remain whole leaf values. The code lives in the `nested_json_annotator` package under `src/`.

## What it produces

Input:

```json
{"score":7,"profile":{"active":true},"tags":["demo"]}
```

Unlimited-depth output:

```json
{
  "score":{"_content":7,"_type":"<class 'int'>"},
  "profile":{"active":{"_content":true,"_type":"<class 'bool'>"}},
  "tags":{"_content":["demo"],"_type":"<class 'list'>"}
}
```

Type names are Python representations, not JSON Schema types. `null` becomes `<class 'NoneType'>`. Empty dictionaries remain empty; dictionaries inside a list are not traversed. A scalar root can also be wrapped.

## Run without dependencies

Use Python 3.12+ from the repository root:

```sh
PYTHONPATH=src python3 -m nested_json_annotator examples/input.json /tmp/annotated.json
PYTHONPATH=src python3 -m nested_json_annotator examples/input.json 1 /tmp/annotated-depth1.json
```

The positional order remains `input_file [max_depth] output_file`. Omit depth for full dictionary recursion; depth must be a nonnegative integer. The bundled input/output files use fictional sample data.

| Depth | Example `{"a":1,"b":{"c":2}}` |
| --- | --- |
| `0` | Unchanged |
| `1` | Wrap `a`; leave `b.c` unchanged |
| `2` or omitted | Wrap both `a` and `b.c` |

## Python use

```python
from nested_json_annotator import substitute

source = {"metrics": {"count": 3}}
result = substitute(source)
assert source == {"metrics": {"count": 3}}
```

Visited dictionaries are rebuilt instead of mutated. Unvisited values and leaf containers can still share references with the input; this is not a deep-copy API. Reapplying the transform wraps its own metadata, so it is not idempotent.

## Checks and limits

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

All 25 tests pass, covering leaf types, depth boundaries, existing CLI behavior, Unicode, non-mutating dictionaries and invalid input preserving an existing output. Runtime uses only the standard library; pytest is a development dependency.

The CLI reports input/read/encoding/transformation failures before opening its output. Nonfinite values such as `NaN` are rejected during serialization. Output is written to a temporary file and renamed into place, so a write failure leaves any previous output intact. The whole JSON document and rendered result live in memory, Python recursion limits apply, and the tool does not stream or validate an application schema.

This overlaps with `json-field-replacer`, but has different root-value, mutation and depth semantics. Keep one representative utility in a portfolio rather than presenting the two as separate large systems.
