# Changelog

## [0.4.0] - 2026-05-03

### Features
- Add explicit `App` class with its own command registry. Enables multiple
  apps in one process and lets parents `mount(prefix, subapp)` to compose
  nested CLIs (`claude-toolkit image gen ...`).
- Sub-app mount semantics: prefix collisions raise at mount time; the same
  `App` instance can be mounted under multiple roots; mount nesting is
  supported (two levels recommended in practice).
- `Command.explain()` now prefixes its output with the active mount path so
  chained invocations rendered for agents reflect how the user invoked the
  parent app.
- `--tour` propagates: `<root> --tour` shows the root's tour and lists
  mounted sub-apps; `<root> <prefix> --tour` shows the sub-app's tour as if
  invoked standalone.
- New `App(..., tour_source=__file__)` override for cases where the App is
  constructed inside an `__init__.py` re-export shim.

### Back-compat
- The module-level `m.command` decorator and `m.main()` entry point keep
  working unchanged. Internally they delegate to a hidden `_default_app`.
- The legacy `microcli.core._commands` global remains as a thin alias of
  `_default_app._commands` for code that pokes it directly.

## [0.3.0] - 2026-03-28

### Features
- Add `stdin[T]` for complex JSON parsing from stdin
- Parse JSON to dict or Pydantic models
- Optional `pydantic` extra for model validation

### Documentation
- Add stdin[T] documentation to README

## [0.2.0] - 2026-03-28

### Initial Release

Lean CLI framework for AI-friendly micro-apps.

Features:
- `@m.command` decorator for registering commands
- Built-in `--learn` for auto-discovering command tours
- Status helpers: ok(), fail(), info(), warn()
- File utilities: read, write, ls, glob, cp, mv, rm
- Shell execution: sh() with Result object
- AST-based command tour discovery
