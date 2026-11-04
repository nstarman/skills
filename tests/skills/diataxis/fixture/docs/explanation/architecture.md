# About the architecture

Why is a run single-threaded? Because the design favours reproducible output over speed: the
reason is that parallel writers would make the order of rows depend on timing. The trade-off is
that large runs are slower, which is why `--jobs` exists (see the [CLI flags](../reference/cli.md#flags)).
