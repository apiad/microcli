"""Core microcli functionality."""
import argparse
import ast
import contextlib
import inspect
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Annotated, Callable, Optional, Union

__version__ = "0.4.0"

try:
    from .stdin import is_stdin_type, parse_stdin, _StdinType
    STDIN_AVAILABLE = True
except ImportError:
    STDIN_AVAILABLE = False

# ============================================================================
# MARK: Types
# ============================================================================

from dataclasses import dataclass, field


@dataclass
class Result:
    """Result of a shell command."""
    ok: bool
    failed: bool
    returncode: int
    stdout: str
    stderr: str
    duration: float

    def __bool__(self):
        return self.ok


# ============================================================================
# MARK: Global State
# ============================================================================

_dry_run = False

# Invocation stack: each entry is the list of mount-prefix segments leading to
# the currently-dispatching App. Used by Command.explain() so that chained
# invocations rendered for an agent include the mount path the user actually
# typed (e.g. `claude-toolkit image render` rather than just `render`).
_invocation_stack: list[list[str]] = []


def _push_invocation(prefix_chain: list[str]) -> None:
    _invocation_stack.append(list(prefix_chain))


def _pop_invocation() -> list[str]:
    return _invocation_stack.pop()


def _current_prefix() -> list[str]:
    return _invocation_stack[-1] if _invocation_stack else []


# ============================================================================
# MARK: Colors
# ============================================================================

COLORS = {
    'red': '\033[0;31m',
    'green': '\033[0;32m',
    'yellow': '\033[1;33m',
    'cyan': '\033[0;36m',
    'bold': '\033[1m',
    'nc': '\033[0m',
}


def _color(name: str, text: str) -> str:
    return f"{COLORS.get(name, '')}{text}{COLORS['nc']}"


# ============================================================================
# MARK: Status Helpers
# ============================================================================

def ok(msg: str) -> None:
    """Print success message."""
    print(_color('green', f'✓ {msg}'))


def fail(msg: str) -> None:
    """Print error message and exit with code 1."""
    print(_color('red', f'✗ {msg}'), file=sys.stderr)
    sys.exit(1)


def info(msg: str) -> None:
    """Print info message."""
    print(_color('cyan', f'→ {msg}'))


def step(msg: str) -> None:
    """Print step message."""
    print(_color('cyan', f'→ {msg}'))


def warn(msg: str) -> None:
    """Print warning message."""
    print(_color('yellow', f'⚠ {msg}'))


# ============================================================================
# MARK: Shell
# ============================================================================

def sh(
    cmd: str,
    timeout: Optional[int] = None,
    env: Optional[dict] = None,
    cwd: Optional[Path] = None,
) -> Result:
    """
    Execute a shell command and return the result.

    Args:
        cmd: Command string to execute
        timeout: Optional timeout in seconds
        env: Optional environment variables to add
        cwd: Optional working directory

    Returns:
        Result object with ok, failed, stdout, stderr, returncode, duration
    """
    if _dry_run:
        info(f"DRY RUN: {cmd}")
        return Result(True, False, 0, cmd, "", 0.0)

    start = time.time()

    full_env = None
    if env:
        full_env = os.environ.copy()
        full_env.update(env)

    proc = None
    try:
        proc = subprocess.Popen(
            cmd if isinstance(cmd, list) else shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=full_env,
            cwd=cwd,
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        duration = time.time() - start

        return Result(
            ok=proc.returncode == 0,
            failed=proc.returncode != 0,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
        )

    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
            proc.communicate()
        fail(f"Command timed out after {timeout}s: {cmd}")
        return Result(False, True, -1, "", "Timeout", 0)  # unreachable
    except Exception as e:
        fail(f"Command failed: {cmd}\n{e}")
        return Result(False, True, -1, "", str(e), 0)  # unreachable


# ============================================================================
# MARK: File Utilities
# ============================================================================

def read(path: Union[str, Path]) -> str:
    """Read file contents and return as string."""
    with open(path) as f:
        return f.read()


def write(path: Union[str, Path], content: str) -> None:
    """Write content to file."""
    with open(path, 'w') as f:
        f.write(content)


def ls(path: Union[str, Path] = ".") -> list[str]:
    """List directory contents."""
    return sorted(os.listdir(path))


def glob(pattern: str, root: Optional[Path] = None) -> list[Path]:
    """Return list of paths matching glob pattern."""
    root = root or Path.cwd()
    return [Path(p) for p in root.glob(pattern)]


def touch(path: Union[str, Path]) -> Path:
    """Create empty file."""
    path = Path(path)
    path.touch()
    return path


def rm(path: Union[str, Path], recursive: bool = False) -> None:
    """Remove file or directory."""
    path = Path(path)
    if recursive:
        shutil.rmtree(path)
    else:
        path.unlink()


def cp(src: Union[str, Path], dst: Union[str, Path]) -> Path:
    """Copy file or directory."""
    src = Path(src)
    dst = Path(dst)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return dst


def mv(src: Union[str, Path], dst: Union[str, Path]) -> Path:
    """Move/rename file or directory."""
    src = Path(src)
    dst = Path(dst)
    shutil.move(src, dst)
    return dst


def which(cmd: str) -> Optional[Path]:
    """Find command in PATH, return Path or None."""
    path = shutil.which(cmd)
    return Path(path) if path else None


def env(name: str) -> Optional[str]:
    """Get environment variable value."""
    return os.environ.get(name)


@contextlib.contextmanager
def cd(path: Union[str, Path]):
    """Context manager for changing directory."""
    path = Path(path)
    original = Path.cwd()
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(original)


# ============================================================================
# MARK: YAML Support
# ============================================================================

try:
    import yaml
    yaml_module = yaml
except ImportError:
    yaml_module = None


class YamlStub:
    """Stub for when pyyaml is not installed."""
    def __getattr__(self, name):
        raise ImportError("pyyaml not installed: pip install pyyaml")


# ============================================================================
# MARK: Command Registration
# ============================================================================

class Command:
    """Represents a registered command."""

    def __init__(
        self,
        func: Callable,
        name: str,
        description: str,
        params: dict,
        stdin_params=None
    ):
        self.func = func
        self.name = name
        self.description = description
        self.params = params
        self.stdin_params = stdin_params or {}
        self._arg_names = list(params.keys())

    def explain(self, **kwargs) -> str:
        """Generate command invocation string for agents."""
        # Check required args
        for name in self._arg_names:
            param = self.params[name]
            if not param.has_default and name not in kwargs:
                raise TypeError(f"{name} is required")

        parts = []
        for name in self._arg_names:
            param = self.params[name]
            value = kwargs.get(name)

            if value is None and param.has_default:
                value = param.default

            # Skip empty strings and False
            if value is None or value is False:
                continue

            if value is True:
                # Boolean flag
                parts.append(f"--{name}")
            elif value:  # Non-empty, non-bool
                # Optional argument - use --name value format
                if param.has_default:
                    parts.append(f"--{name} {str(value)}")
                else:
                    # Positional argument
                    parts.append(str(value))

        # Use sys.argv[0] as the binary, then prepend any active mount prefix
        # so chained `explain()` output reflects how the user actually invoked
        # the parent app (e.g. `claude-toolkit image render`).
        invocation = sys.argv[0] if sys.argv else "app.py"
        prefix_segments = _current_prefix()
        cmd_path = " ".join([invocation, *prefix_segments, self.name])
        cmd = cmd_path
        if parts:
            cmd += " " + " ".join(parts)

        return f"`{cmd}`"

    def __call__(self, **kwargs):
        return self.func(**kwargs)


def _build_command(func: Callable) -> Command:
    """Inspect a callable and build the Command metadata for it.

    Pulled out of `App.command` so the construction is shared with the
    legacy module-level `command` decorator.
    """
    name = func.__name__.replace('_', '-')
    params = {}

    sig = inspect.signature(func)

    stdin_params = {}
    for param in sig.parameters.values():
        arg_name = param.name
        arg_annotation = param.annotation

        if STDIN_AVAILABLE and is_stdin_type(arg_annotation):  # type: ignore
            stdin_params[arg_name] = arg_annotation
            continue

        base_type = str  # Default to str
        help_text = ""
        is_flag = False

        if hasattr(arg_annotation, '__metadata__'):
            base_type = arg_annotation.__args__[0]
            metadata = arg_annotation.__metadata__
            for item in metadata:
                if isinstance(item, str):
                    help_text = item
            if base_type is bool:
                is_flag = True

        default = param.default
        has_default = default is not inspect.Parameter.empty

        params[arg_name] = argparse.Namespace(
            type=base_type,
            help=help_text,
            default=None if not has_default else default,
            has_default=has_default,
            is_flag=is_flag,
        )

    return Command(func, name, func.__doc__ or "", params, stdin_params)


# ============================================================================
# MARK: App
# ============================================================================

class App:
    """An explicit microcli application with its own command registry.

    Unlike the module-level `m.command` shorthand (which mutates a hidden
    default app), `App` lets multiple apps coexist in one process and lets
    apps mount each other under prefix keys to compose a nested CLI.

    Mount semantics
    ---------------
    * `app.mount(prefix, subapp)` exposes `subapp`'s commands under the
      `prefix` key. Argparse subparsers nest one level per mount.
    * Conflict policy: a prefix that collides with an existing top-level
      command name (or another mount key) raises `ValueError` at mount time.
      No implicit precedence.
    * Mounting the same `App` instance under multiple roots is fine: the
      sub-app's `_commands` dict is the source of truth; parents store only
      a reference.

    Tour source resolution
    ----------------------
    The `--tour` machinery walks the source file of the module that
    *constructed* the App. The constructor captures the caller's file via
    `inspect`. If the App is built inside an `__init__.py` re-export shim
    (where the caller is the wrong file), pass `tour_source=__file__`
    explicitly to override.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        tour_source: Optional[str] = None,
    ):
        self.name = name
        self.description = description or ""
        self._commands: dict[str, Command] = {}
        self._subapps: dict[str, "App"] = {}

        if tour_source is None:
            try:
                frame = inspect.currentframe()
                if frame is not None and frame.f_back is not None:
                    tour_source = inspect.getfile(frame.f_back)
            except (TypeError, ValueError):
                tour_source = None
        self.tour_source = tour_source

    # -- registration --------------------------------------------------------

    def command(self, func: Callable) -> Command:
        """Register `func` as a command on this app."""
        cmd = _build_command(func)
        self._commands[cmd.name] = cmd
        return cmd

    def mount(self, prefix: str, subapp: "App") -> "App":
        """Mount `subapp` under `prefix`. Raises on collision."""
        if prefix in self._commands:
            raise ValueError(
                f"mount prefix {prefix!r} collides with command name in "
                f"app {self.name!r}"
            )
        if prefix in self._subapps:
            raise ValueError(
                f"mount prefix {prefix!r} already mounted in app {self.name!r}"
            )
        self._subapps[prefix] = subapp
        return subapp

    # -- dispatch ------------------------------------------------------------

    def main(self) -> None:
        """Parse argv and dispatch a command.

        Walks `sys.argv` to find the deepest mounted sub-app referenced by
        the user, builds an argparse parser scoped to that sub-app's own
        commands, then dispatches normally. The mount prefix chain is pushed
        onto an invocation stack so `Command.explain()` can render the right
        path.
        """
        global _dry_run

        argv = sys.argv[1:]
        active_app, prefix_chain, remaining = self._resolve_active(argv)

        parser = active_app._build_parser(prefix_chain)
        args = parser.parse_args(remaining)

        # --tour: either the active app's full tour (`--tour`) or a single
        # command tour (`--tour <cmd>`).
        if getattr(args, "tour", None) is not None:
            from .learn import LearnMode
            tour_target = active_app.tour_source or (
                getattr(sys.modules.get("__main__"), "__file__", None)
            )
            if tour_target is None:
                fail("--tour requires a source file but none could be resolved")
            learn = LearnMode(str(tour_target))
            if isinstance(args.tour, str):
                learn.show_command(args.tour)
            else:
                learn.show_all()
                # Hint at mounted sub-apps so users know they can drill in.
                if active_app._subapps:
                    print()
                    print("Mounted sub-apps (use `<prefix> --tour` to drill in):")
                    for p, sub in sorted(active_app._subapps.items()):
                        desc = sub.description or sub.name
                        print(f"  {p:<15} {desc}")
            sys.exit(0)

        if getattr(args, "command", None) is None:
            parser.print_help()
            self._print_command_list(active_app)
            sys.exit(0)

        cmd = active_app._commands[args.command]
        _dry_run = getattr(args, "dry_run", False)

        kwargs = dict(vars(args))
        kwargs.pop("command", None)
        kwargs.pop("dry_run", None)
        kwargs.pop("tour", None)

        if cmd.stdin_params and STDIN_AVAILABLE:
            stdin_content = sys.stdin.read() if not sys.stdin.isatty() else ""
            for param_name, stdin_type in cmd.stdin_params.items():
                if param_name not in kwargs or kwargs[param_name] is None:
                    if stdin_content:
                        kwargs[param_name] = parse_stdin(  # type: ignore
                            stdin_content, stdin_type.inner_type
                        )
                    else:
                        kwargs[param_name] = None

        if cmd.description and sys.stdout.isatty() and not os.environ.get("MICROCLI_QUIET"):
            print(cmd.description)
            print("─" * 40)

        _push_invocation(prefix_chain)
        try:
            try:
                cmd(**kwargs)
            except TypeError as e:
                if "is required" in str(e):
                    print(f"\nError: {e}", file=sys.stderr)
                    invocation = " ".join([
                        sys.argv[0], *prefix_chain, args.command
                    ])
                    print(f"\nUsage: {invocation} ", end="")
                    required = [
                        n for n, p in cmd.params.items() if not p.has_default
                    ]
                    if required:
                        print(" ".join(required), end=" ")
                    print("\nUse --help for more information.")
                    sys.exit(1)
                raise
        finally:
            _pop_invocation()

    # -- helpers -------------------------------------------------------------

    def _resolve_active(
        self, argv: list[str]
    ) -> tuple["App", list[str], list[str]]:
        """Walk argv segments down through mounts to find the active app.

        Returns (active_app, prefix_chain, remaining_argv).
        Stops descending at the first segment that isn't a mount key.
        """
        active = self
        chain: list[str] = []
        i = 0
        while i < len(argv) and argv[i] in active._subapps:
            prefix = argv[i]
            chain.append(prefix)
            active = active._subapps[prefix]
            i += 1
        return active, chain, argv[i:]

    def _build_parser(self, prefix_chain: list[str]) -> argparse.ArgumentParser:
        """Build an argparse parser scoped to *this* app's commands.

        Sub-apps reachable via `mount(...)` are exposed as additional
        subparser entries that, when invoked, are intercepted earlier in
        `_resolve_active` (so they don't dispatch through here). They're
        listed here purely so `--help` shows them.
        """
        prog_parts = [Path(sys.argv[0]).name if sys.argv else "app", *prefix_chain]
        prog = " ".join(prog_parts)

        parser = argparse.ArgumentParser(
            prog=prog,
            description=self.description or None,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Print commands without executing",
        )
        parser.add_argument(
            "--tour", nargs="?", const=True, metavar="COMMAND",
            help="Show command tour and next steps",
        )
        parser.add_argument(
            "--help", "-h", action="help",
            default=argparse.SUPPRESS,
            help="show this help message",
        )

        if not self._commands and not self._subapps:
            return parser

        subparsers = parser.add_subparsers(dest="command", metavar="[command]")

        # Sub-app mount keys (drill-in hint only — actual dispatch happens
        # in _resolve_active, before this parser ever runs against them).
        for prefix, sub in sorted(self._subapps.items()):
            help_text = sub.description.split("\n")[0] if sub.description else f"{prefix} sub-app"
            subparsers.add_parser(prefix, help=help_text, add_help=False)

        # Real command parsers
        for name, cmd in self._commands.items():
            sub = subparsers.add_parser(
                name,
                help=cmd.description.split("\n")[0] if cmd.description else name,
                description=cmd.description,
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )
            positional = []
            optional = []
            for arg_name, param in cmd.params.items():
                if param.has_default:
                    optional.append((arg_name, param))
                else:
                    positional.append((arg_name, param))

            for arg_name, param in positional:
                sub.add_argument(arg_name, type=param.type, help=param.help)

            for arg_name, param in optional:
                if param.is_flag:
                    sub.add_argument(
                        f"--{arg_name}", action="store_true",
                        default=param.default,
                        help=param.help or argparse.SUPPRESS,
                    )
                else:
                    sub.add_argument(
                        f"--{arg_name}", type=param.type,
                        default=param.default,
                        help=param.help or argparse.SUPPRESS,
                    )

        return parser

    def _print_command_list(self, app: "App") -> None:
        if app._commands or app._subapps:
            print("\nCommands:")
            for name, cmd in sorted(app._commands.items()):
                desc = cmd.description.split("\n")[0] if cmd.description else ""
                print(f"  {name:<15} {desc}")
            for prefix, sub in sorted(app._subapps.items()):
                desc = sub.description.split("\n")[0] if sub.description else f"{prefix} sub-app"
                print(f"  {prefix:<15} → {desc}")


# ============================================================================
# MARK: Module-level shorthand (back-compat)
# ============================================================================

# A hidden default App is created so existing one-file scripts using
# `@m.command` and `m.main()` keep working without modification.
_default_app = App(name="microcli")

# `_commands` is preserved as a thin alias to the default app's registry for
# any code (or test) that pokes the legacy global directly.
_commands = _default_app._commands


def command(func: Callable) -> Command:
    """Decorator: register `func` as a command on the default app."""
    return _default_app.command(func)


def main() -> None:
    """Module-level entry point — dispatches against the default app."""
    _default_app.main()
