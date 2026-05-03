"""Tests for the explicit App API and sub-app mounting (microcli 0.4)."""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# App: own command registry
# ---------------------------------------------------------------------------

def test_app_registers_command_in_own_namespace():
    from microcli import App

    a = App(name="alpha")

    @a.command
    def greet(name: str):
        """Say hi."""
        pass

    assert "greet" in a._commands
    assert a._commands["greet"].description == "Say hi."


def test_two_apps_have_independent_registries():
    from microcli import App

    a = App(name="alpha")
    b = App(name="beta")

    @a.command
    def foo():
        pass

    @b.command
    def bar():
        pass

    assert "foo" in a._commands and "foo" not in b._commands
    assert "bar" in b._commands and "bar" not in a._commands


def test_app_command_name_hyphenation():
    from microcli import App

    a = App(name="alpha")

    @a.command
    def my_cmd():
        pass

    assert "my-cmd" in a._commands


# ---------------------------------------------------------------------------
# Module-level shorthand back-compat
# ---------------------------------------------------------------------------

def test_default_app_command_alias_still_works():
    """`m.command` continues to register on a module-global default app."""
    from microcli import command
    from microcli.core import _default_app

    @command
    def shorthand_cmd():
        """Shim cmd."""
        pass

    assert "shorthand-cmd" in _default_app._commands


def test_module_level_commands_dict_aliases_default_app():
    """The legacy `_commands` global mirrors `_default_app._commands`."""
    from microcli.core import _commands, _default_app

    assert _commands is _default_app._commands


# ---------------------------------------------------------------------------
# Mount semantics
# ---------------------------------------------------------------------------

def test_mount_attaches_subapp_under_prefix():
    from microcli import App

    root = App(name="root")
    sub = App(name="sub")

    root.mount("image", sub)
    assert root._subapps["image"] is sub


def test_mount_prefix_collides_with_command_name_raises():
    from microcli import App

    root = App(name="root")

    @root.command
    def image():
        pass

    sub = App(name="sub")
    with pytest.raises(ValueError, match="image"):
        root.mount("image", sub)


def test_mount_same_prefix_twice_raises():
    from microcli import App

    root = App(name="root")
    a, b = App(name="a"), App(name="b")
    root.mount("x", a)
    with pytest.raises(ValueError, match="x"):
        root.mount("x", b)


def test_mounting_same_subapp_under_two_roots_is_allowed():
    from microcli import App

    sub = App(name="sub")

    @sub.command
    def ping():
        pass

    r1, r2 = App(name="r1"), App(name="r2")
    r1.mount("a", sub)
    r2.mount("b", sub)

    # Source of truth is the sub-app's registry.
    assert "ping" in r1._subapps["a"]._commands
    assert "ping" in r2._subapps["b"]._commands
    assert r1._subapps["a"] is r2._subapps["b"]


# ---------------------------------------------------------------------------
# Invocation stack: Command.explain() respects mount path
# ---------------------------------------------------------------------------

def test_explain_uses_invocation_stack_for_mount_prefix(monkeypatch):
    from microcli import App
    from microcli.core import _push_invocation, _pop_invocation

    monkeypatch.setattr(sys, "argv", ["claude-toolkit"])

    sub = App(name="mosaico")

    @sub.command
    def render(project: str):
        pass

    cmd = sub._commands["render"]

    # No prefix on the stack: bare invocation.
    bare = cmd.explain(project="x.yml")
    assert "render" in bare and "x.yml" in bare
    assert "image" not in bare

    # Push prefix, explain should include it.
    _push_invocation(["image"])
    try:
        prefixed = cmd.explain(project="x.yml")
        assert "image render" in prefixed
        assert "x.yml" in prefixed
    finally:
        _pop_invocation()


# ---------------------------------------------------------------------------
# End-to-end: app.main() dispatches mounted commands
# ---------------------------------------------------------------------------

MICROCLI_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"


def _run_app_script(tmp_path: Path, body: str, *args: str):
    script = tmp_path / "app_under_test.py"
    script.write_text(textwrap.dedent(body))
    return subprocess.run(
        [str(MICROCLI_PYTHON), str(script), *args],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )


MOUNT_SCRIPT = """
    import microcli as m

    root = m.App(name="root", description="Root app.")
    child = m.App(name="child", description="Child app.")

    @child.command
    def greet(name: str):
        '''Greet someone from the child app.'''
        m.ok(f"Hello, {name}!")

    @root.command
    def hello():
        '''Hello at root.'''
        m.ok("hello-root")

    root.mount("child", child)

    if __name__ == "__main__":
        root.main()
"""


def test_mounted_command_dispatch(tmp_path):
    result = _run_app_script(tmp_path, MOUNT_SCRIPT, "child", "greet", "Alice")
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    assert "Hello, Alice!" in result.stdout


def test_root_command_still_dispatches(tmp_path):
    result = _run_app_script(tmp_path, MOUNT_SCRIPT, "hello")
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    assert "hello-root" in result.stdout


def test_mounted_help_lists_child_commands(tmp_path):
    result = _run_app_script(tmp_path, MOUNT_SCRIPT, "child", "--help")
    assert result.returncode == 0
    assert "greet" in result.stdout
