# CLI

`toolkit run <file>` runs a pipeline.

## Flags

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--dry-run` | bool | `false` | Parse and validate only. |
| `--jobs` | int | `1` | Number of worker processes. |

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success. |
| 1 | The pipeline failed. |
