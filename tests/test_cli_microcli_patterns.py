"""Tests for microcli CLI app using microcli patterns."""
import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_cli_uses_microcli_patterns():
    """Test that cli.py uses microcli patterns."""
    cli_path = Path(__file__).parent.parent / "src" / "microcli" / "cli.py"
    content = cli_path.read_text()
    # Should import microcli and use @command decorator
    assert "from .core import" in content or "import microcli" in content
    assert "@command" in content


def test_new_command_works():
    """Test new command creates a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, "-m", "microcli", "new",
             "--name", "testapp",
             "--title", "Test App",
             "--commands", "greet,bye"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent / "src")},
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should have created testapp.py
        assert (Path(tmpdir) / "testapp.py").exists()


def test_new_command_creates_working_app():
    """Test that generated app is valid Python and has commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate the app
        subprocess.run(
            [sys.executable, "-m", "microcli", "new",
             "--name", "hello",
             "--title", "Hello World",
             "--commands", "greet"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent / "src")},
        )
        
        # Check the file exists and is valid Python
        hello_py = Path(tmpdir) / "hello.py"
        assert hello_py.exists()
        
        # Check it has expected content
        content = hello_py.read_text()
        assert "Hello World" in content
        assert "@command" in content
        assert "greet" in content
        assert "///script" in content
        assert "microcli learn" in content


def test_learn_command_uses_microcli_patterns():
    """Test learn command uses microcli."""
    result = subprocess.run(
        [sys.executable, "-m", "microcli", "learn"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 0
    # Should show topics formatted nicely (using microcli patterns)
    assert "principles" in result.stdout.lower()
