# microcli-toolkit

> Lean CLI framework for AI-friendly micro-apps

Microcli is a decorator-based CLI framework designed for building tools that agents can use. Unlike traditional CLIs that return data, microcli tools return *instructions* that guide the next step.

## Installation

```bash
pip install microcli-toolkit
# or
uv add microcli-toolkit
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

## Composing apps with `App` + `mount`

The module-level `m.command` / `m.main()` shorthand is fine for one-file
scripts. When you want to compose multiple sub-CLIs under one entry point,
construct explicit `App` instances and mount them under prefix keys:

```python
import microcli as m
from mosaico import app as mosaico_app
from mira import app as mira_app

root = m.App(name="claude-toolkit", description="Alex's agent toolbox.")
root.mount("image", mosaico_app)   # claude-toolkit image gen ...
root.mount("mira", mira_app)       # claude-toolkit mira search ...

@root.command
def hello(name: str):
    m.ok(f"Hello, {name}!")

if __name__ == "__main__":
    root.main()
```

Each `App` owns its own command registry — there are no name clashes between
sub-apps. Mount-prefix collisions raise at mount time. `--tour` propagates
naturally: `claude-toolkit --tour` shows the root tour and lists mounts;
`claude-toolkit image --tour` shows mosaico's tour as if invoked standalone.

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

## Complex Types from stdin

For complex data structures, use `stdin[T]` to read JSON from stdin. Requires `pydantic` extra:

```bash
uv add microcli-toolkit --extra pydantic
```

### Basic Usage

```python
from microcli import command, stdin

@command
def create(
    title: str,
    metadata: stdin[dict],
):
    """Create a resource with metadata."""
    m.ok(f"Creating {title} with {len(metadata)} properties")
```

```bash
echo '{"tags": ["a", "b"], "priority": 1}' | python cmd.py create "My Title"
```

### With Pydantic Models

```python
from microcli import command, stdin
from pydantic import BaseModel

class NoteMetadata(BaseModel):
    title: str
    tags: list[str] = []
    priority: int = 1

@command
def create(
    content: str,
    metadata: stdin[NoteMetadata],
):
    """Create a note with metadata."""
    m.ok(f"Creating note: {metadata.title} (priority: {metadata.priority})")
```

```bash
echo '{"title": "My Note", "tags": ["work", "urgent"]}' | python note.py create "Note body"
```

### Error Handling

Invalid JSON:
```
✗ Invalid JSON: Expecting value
```

Pydantic validation errors:
```
✗ Validation error: 2 validation errors
```

## License

MIT
