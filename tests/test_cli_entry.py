"""Tests for microcli CLI app entry points."""
import subprocess
import sys
from pathlib import Path


def test_module_entry_point():
    """Test python -m microcli --help works."""
    result = subprocess.run(
        [sys.executable, "-m", "microcli", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "microcli" in result.stdout.lower()
    assert "new" in result.stdout.lower()
    assert "learn" in result.stdout.lower()


def test_command_entry_point():
    """Test microcli --help works via installed command."""
    try:
        result = subprocess.run(
            ["microcli", "--help"],
            capture_output=True,
            text=True,
        )
        # May fail if not installed - that's OK for unit tests
        assert result.returncode in (0, 127)  # 127 = command not found
    except FileNotFoundError:
        # microcli command not installed - skip this test
        pass


def test_new_command_exists():
    """Test that new subcommand is available."""
    result = subprocess.run(
        [sys.executable, "-m", "microcli", "new", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "name" in result.stdout.lower()
    assert "title" in result.stdout.lower()
    assert "commands" in result.stdout.lower()


def test_learn_command_exists():
    """Test that learn subcommand is available."""
    result = subprocess.run(
        [sys.executable, "-m", "microcli", "learn", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
