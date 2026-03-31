"""
microcli - Lean CLI framework for AI-friendly micro-apps.

Usage:
    import microcli as m

    @m.command
    def hello(name: Annotated[str, "Your name"]):
        \"\"\"Greet a user.\"\"\"
        m.ok(f"Hello, {name}!")

    if __name__ == "__main__":
        m.main()

Run: python hello.py hello Alice
"""

__version__ = "0.2.0"

from .core import (
    command,
    main,
    sh,
    ok,
    fail,
    info,
    warn,
    step,
    read,
    write,
    ls,
    glob,
    touch,
    rm,
    cp,
    mv,
    cd,
    which,
    env,
    Result,
    COLORS,
    yaml_module as yaml,
)

try:
    from .stdin import stdin, is_stdin_type, parse_stdin
except ImportError:
    stdin = None
    is_stdin_type = None
    parse_stdin = None

__all__ = [
    "command",
    "main",
    "sh",
    "ok",
    "fail",
    "info",
    "warn",
    "step",
    "read",
    "write",
    "ls",
    "glob",
    "touch",
    "rm",
    "cp",
    "mv",
    "cd",
    "which",
    "env",
    "Result",
    "COLORS",
    "yaml",
    "print_framework_help",
    "stdin",
    "is_stdin_type",
    "parse_stdin",
]
