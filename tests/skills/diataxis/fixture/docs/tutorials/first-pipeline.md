# Build your first pipeline

In this tutorial we will build a pipeline that fetches a dataset and publishes it.
By the end of this tutorial you will have a published dataset.

1. First, create `pipeline.toml`.
2. Next, run `toolkit run pipeline.toml`.
3. Finally, open `out/index.html`. You should see one table.

Congratulations. You used `toolkit run`; its flags are in the
[CLI reference](../reference/cli.md#flags). Curious why runs are single-threaded? Read
[about the architecture](../explanation/architecture.md).
