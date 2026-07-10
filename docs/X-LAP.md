# `x-lap-*` OpenAPI extensions — a strawman

_Status: **strawman, v0** (2026-07-10). Nothing here is implemented as a requirement;
`lap` works fully without these. Feedback via
[issues](https://github.com/lCrazyblindl/lap/issues) — including "this is a bad idea"._

## Why

`lap score`'s B/C figures are **structural lower bounds**: it guesses a page size
(`--page-size 20`), detects projection/pagination affordances by parameter-name
conventions (rules R1/R3), and cannot know which operations the author considers
heavy. The author knows all of this. OpenAPI's `x-*` extension mechanism is the
standard, zero-risk place to declare it (every consumer that doesn't understand an
extension must ignore it), and a declared number beats a guessed one — the same
reasoning that made us prefer a schema's real `example` over synthetic placeholders
(which moved the leaderboard's C estimates ~41%).

## Proposed keys

| key | where | type | declares |
| --- | --- | --- | --- |
| `x-lap-page-max` | operation or its limit-param | integer | the real maximum page size — C estimates use it instead of the `--page-size` guess |
| `x-lap-projection` | operation | string | the *name* of the field-projection parameter — makes projected-C exact where R1's name list (`fields`, `$select`, …) misses a custom name |
| `x-lap-heavy` | operation | boolean | "defer me": exclude from compact/default menus, load via tool-search tier only |
| `x-lap-workflow` | document root (`info` or top level) | string (URL/path) | pointer to an [Arazzo](https://github.com/OAI/Arazzo-Specification) document whose workflows should be advertised as macro tools ([measured](ARAZZO.md): menu 50–97% below naive; intermediate results never enter context) |

Example:

```yaml
paths:
  /pets:
    get:
      x-lap-page-max: 100
      x-lap-projection: fieldMask
      parameters: [ ... ]
  /pets/export:
    get:
      x-lap-heavy: true
```

## What `lap` would do with each

- **`score`**: honor `x-lap-page-max` and `x-lap-projection` in the C table (exact
  instead of guessed/name-matched); render `x-lap-heavy` ops only in the tool-search
  tier; report the Arazzo macro-tool figure next to the menu forms.
- **`lint`**: new *info*-level consistency checks only — e.g. `x-lap-projection`
  naming a parameter that doesn't exist, or `x-lap-page-max` contradicting the limit
  param's declared `maximum`. Absence of `x-lap-*` is **never** a finding.
- **`fix`**: emit the keys as part of the Overlay when the underlying affordance is
  added (e.g. R3's new `limit` param ships with its `x-lap-page-max`).

## What is deliberately NOT proposed

No semantic rewriting (descriptions stay the author's), no runtime behavior, no
required adoption (scores never penalize the extension's absence), no vendor coupling
(plain JSON keys, MIT-specified here; any tool may read them). If the MCP/OpenAPI
ecosystems standardize equivalent fields (e.g. a future spec-level page-size
declaration), these keys retire in their favor — the point is the declared data, not
the `lap` prefix.

## Adoption cost

A few lines of YAML per API; legal in every OpenAPI 3.x document today ("This object
MAY be extended with Specification Extensions"); invisible to every other consumer.
