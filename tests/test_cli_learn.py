"""Tests for microcli learn command."""
import os
import subprocess
import sys
from pathlib import Path


MICROCLI_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"
SRC_PATH = str(Path(__file__).parent.parent / "src")


def test_learn_shows_topics():
    """Test learn without args shows available topics."""
    result = subprocess.run(
        [str(MICROCLI_PYTHON), "-m", "microcli", "learn"],
        capture_output=True,
        text=True,
        cwd=SRC_PATH,
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    # Should show available topics
    assert "principles" in result.stdout.lower()
    assert "parameters" in result.stdout.lower()
    assert "ok-fail" in result.stdout.lower()


def test_learn_principles():
    """Test learn principles shows principles content."""
    result = subprocess.run(
        [str(MICROCLI_PYTHON), "-m", "microcli", "learn", "--topic", "principles"],
        capture_output=True,
        text=True,
        cwd=SRC_PATH,
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "principles" in result.stdout.lower()
    assert "validate" in result.stdout.lower() or "three" in result.stdout.lower()


def test_learn_unknown_topic():
    """Test learn with unknown topic shows error."""
    result = subprocess.run(
        [str(MICROCLI_PYTHON), "-m", "microcli", "learn", "--topic", "nonexistent"],
        capture_output=True,
        text=True,
        cwd=SRC_PATH,
    )
    assert result.returncode != 0, "Should fail for unknown topic"
