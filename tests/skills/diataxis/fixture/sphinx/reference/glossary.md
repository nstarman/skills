# Glossary

The cross-referencing forms of the reference's "Cross-referencing" section; with nitpicky and
-W, any that stops resolving fails the build.

(glossary-terms)=
## Terms

```{glossary}
idempotent
  An operation that produces the same result whether applied once or many times.
```

{#config-precedence}
Settings given on the command line win over `pipeline.toml`.

:::{seealso}
- {doc}`/explanation/architecture` — why the scheduler is single-threaded
- {doc}`the CLI reference </reference/cli>`
- {ref}`glossary-terms` and {ref}`Explicit text <glossary-terms>`
- {term}`idempotent`
- [precedence](#config-precedence), [CLI flags](cli.md#flags), <project:/reference/cli.md#flags>
:::

Toolkit
: A deflist entry, as reference pages use.
