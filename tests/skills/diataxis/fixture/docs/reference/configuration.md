# Configuration

Keys of `pipeline.toml`.

## Keys

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `source.url` | string | none | Where the dataset is fetched from. |
| `output.partition_by` | list of strings | `[]` | Columns to partition the output by. |

See the [CLI flags](cli.md#flags) for options set per run.
