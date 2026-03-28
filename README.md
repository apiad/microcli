# microcli

> Lean CLI framework for AI-friendly micro-apps

Microcli is a decorator-based CLI framework designed for building tools that agents can use. Unlike traditional CLIs that return data, microcli tools return *instructions* that guide the next step.

## Installation

```bash
pip install microcli
# or
uv add microcli
```

## Quick Start

```python
#!/usr/bin/env python3
from typing import Annotated
import microcli as m

@m.command
def hello(name: Annotated[str, "Your name"]):
    """Greet a user."""
    m.ok(f"Hello, {name}!")

if __name__ == "__main__":
    m.main()
```

```bash
python hello.py hello Alice
# ✓ Hello, Alice!
```

## The Three Principles

1. **Validate before acting** — Check inputs before executing
2. **Return descriptive messages** — Tell the agent what to do next
3. **Use two-phase patterns** — Draft → Save for safety

## Parameters

| Style | Becomes |
|-------|---------|
| No default | Positional argument (required) |
| Has default | `--flag` optional argument |
| `bool` type | Boolean flag (`--flag` or nothing) |

```python
def cmd(name):                    # python cmd.py cmd John
def cmd(name="World"):            # python cmd.py cmd --name John  
def cmd(verbose: bool = False):  # python cmd.py cmd --verbose
```

Use `Annotated[type, "help text"]` to add help documentation.

## Utilities

### Status Helpers
- `m.ok(msg)` — ✓ Success message
- `m.fail(msg)` — ✗ Error message + exit(1)
- `m.info(msg)` — → Informational message
- `m.warn(msg)` — ⚠ Warning message
- `m.step(msg)` — → Step indicator

### File Operations
- `m.read(path)` — Read file contents
- `m.write(path, content)` — Write to file
- `m.ls()` / `m.glob(pattern)` — List files
- `m.touch(path)` — Create empty file
- `m.rm(path, recursive)` — Remove file/directory
- `m.cp(src, dst)` — Copy file/directory
- `m.mv(src, dst)` — Move/rename

### Shell
- `m.sh(cmd, timeout)` — Run shell command, returns `Result`
- `m.which(cmd)` — Find command in PATH

### Navigation
- `with m.cd(path):` — Context manager for directory changes
- `m.env(name)` — Get environment variable

## Design Patterns

### Two-Phase (Safety)
```python
if not save:
    m.info("Draft mode. Rerun with --save to persist")
    return
# ... save operation
```

### Validation First
```python
content = sys.stdin.read().strip()
if not content:
    m.fail("No content provided via stdin")
```

### Descriptive Outputs
```python
# Bad:  return  # silent
# Good: m.ok("Saved to: " + str(filepath))
```

### Follow-up Commands (.explain)
```python
if not save:
    m.info("Draft mode. Rerun with --save:")
    m.info("  " + create.explain(title=title, save=True))
    return
```

## `--learn` Mode

Auto-discovers command tours by analyzing source code:

```bash
python tool.py --learn              # Show all commands
python tool.py --learn create       # Show focused view for 'create'
```

Output includes:
- **Next steps** — Commands discovered via `.explain()` calls
- **Failure modes** — Errors discovered via `m.fail()` calls
- **Happy paths** — Success messages via `m.ok()` calls

## License

MIT
