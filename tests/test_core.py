"""Tests for microcli core functionality."""
import pytest
from pathlib import Path


# =============================================================================
# Command Registration
# =============================================================================

def test_command_decorator_registers():
    from microcli.core import command, _commands
    _commands.clear()
    
    @command
    def test_cmd():
        """A test command."""
        pass
    
    assert 'test-cmd' in _commands
    assert _commands['test-cmd'].description == "A test command."


def test_command_name_hyphenation():
    from microcli.core import command, _commands
    
    @command
    def my_test_command():
        pass
    
    assert 'my-test-command' in _commands


def test_command_explain():
    from microcli.core import command, _commands
    
    @command
    def greet(name: str):
        """Greet someone."""
        pass
    
    result = _commands['greet'].explain(name='Alice')
    assert 'greet' in result and 'Alice' in result


# =============================================================================
# Status Helpers
# =============================================================================

def test_ok_prints_success(capsys):
    from microcli.core import ok
    ok("Test passed")
    assert "✓" in capsys.readouterr().out


def test_fail_exits_with_error():
    from microcli.core import fail
    with pytest.raises(SystemExit) as exc:
        fail("Test failed")
    assert exc.value.code == 1


def test_info_prints_message(capsys):
    from microcli.core import info
    info("Test info")
    assert "→" in capsys.readouterr().out


# =============================================================================
# File Utilities
# =============================================================================

def test_touch_creates_file(tmp_path):
    from microcli.core import touch
    path = tmp_path / "test.txt"
    touch(path)
    assert path.exists()


def test_write_read_roundtrip(tmp_path):
    from microcli.core import write, read
    path = tmp_path / "test.txt"
    write(path, "Hello, World!")
    assert read(path) == "Hello, World!"


def test_ls_lists_files(tmp_path):
    from microcli.core import ls
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    files = ls(tmp_path)
    assert "a.txt" in files and "b.txt" in files


def test_glob_finds_files(tmp_path):
    from microcli.core import glob, touch
    touch(tmp_path / "test1.txt")
    touch(tmp_path / "test2.txt")
    results = glob("test*.txt", tmp_path)
    assert len(results) == 2


def test_cp_copies_file(tmp_path):
    from microcli.core import cp, write
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    write(src, "content")
    cp(src, dst)
    assert dst.exists()


def test_mv_moves_file(tmp_path):
    from microcli.core import mv, write
    src = tmp_path / "old.txt"
    dst = tmp_path / "new.txt"
    write(src, "content")
    mv(src, dst)
    assert dst.exists() and not src.exists()


def test_rm_removes_file(tmp_path):
    from microcli.core import rm, touch
    path = tmp_path / "test.txt"
    touch(path)
    rm(path)
    assert not path.exists()


# =============================================================================
# Shell Utilities
# =============================================================================

def test_sh_executes_command():
    from microcli.core import sh
    result = sh("echo hello")
    assert result.ok is True
    assert "hello" in result.stdout


def test_sh_returns_result_object():
    from microcli.core import sh, Result
    result = sh("echo test")
    assert isinstance(result, Result)


def test_which_finds_command():
    from microcli.core import which
    result = which("python3")
    assert result is not None


# =============================================================================
# Version
# =============================================================================

def test_version_exists():
    from microcli import __version__
    assert __version__ == "0.4.0"
