<!--
Section landing page skeleton. Every section index does the same four jobs; only the words
change. Delete the comments and this block before shipping.

The nav already lists the children — this page's job is to tell a reader whether they are in
the right place, in the vocabulary of their situation rather than yours.
-->

# How-to guides

<!-- 1. What this section is for, in one sentence, in the reader's terms.
     Not "This section contains how-to guides." -->

Solutions to specific problems, for people who already have Toolkit running.

<!-- 2. Send away the readers who are in the wrong place. This one line prevents most
     misnavigation and is the cheapest quality improvement available in a doc set.
     Name the alternative and link it. -->

If you have never used Toolkit before, start with [Build your first pipeline](../tutorials/first-pipeline.md)
instead — these guides assume you already know how a pipeline is put together. If you are
looking for the full list of options for something rather than steps to do it, that is in the
[reference](../reference/index.md).

<!-- 3. Group the contents once there are more than about seven. Group by task family for
     how-tos, subsystem for reference, theme for explanation. Tutorials get a sequence
     instead, because order matters there and nowhere else.
     Annotate each entry with the situation it serves, not a restatement of its title. -->

## Getting data in and out

- [How to read from a private S3 bucket](read-from-private-s3.md) — credentials, region, and prefix handling
- [How to write partitioned Parquet](write-partitioned-parquet.md) — when one output file is too big

## Running in production

- [How to schedule pipeline runs](schedule-runs.md) — cron, systemd, and CI runners
- [How to deploy on Kubernetes](deploy-on-kubernetes.md) — Job and CronJob manifests, resource limits

<!-- 4. Say what is missing. REQUIRED whenever this section contains pages nobody has written
     yet, and worth having even when it does not. A section that silently implies completeness
     it does not have costs you the reader's trust in the whole nav — and an honest gap list
     costs nothing and buys credibility. Delete the heading only if the list is genuinely empty. -->

## Not yet written

- **How to migrate from 0.6 to 0.7** — the breaking changes are listed in the
  [changelog](../about/changelog.md) meanwhile.
- **How to write a custom source** — the extension API is not stable yet; ask in #toolkit-help.
