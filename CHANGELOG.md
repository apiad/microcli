# Changelog

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
