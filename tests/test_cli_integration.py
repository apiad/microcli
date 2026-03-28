"""Integration tests for microcli CLI app end-to-end workflow."""
import subprocess
import sys
import tempfile
import os
from pathlib import Path


MICROCLI_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"


def test_full_workflow():
    """Test the complete workflow: new → run → learn."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Create a new microapp
        result = subprocess.run(
            [str(MICROCLI_PYTHON), "-m", "microcli", "new",
             "notes", "Notes App", "create,list"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0, f"new failed: {result.stderr}"
        
        notes_py = Path(tmpdir) / "notes.py"
        assert notes_py.exists()
        
        # Step 2: Run the generated app's --help
        result = subprocess.run(
            [str(MICROCLI_PYTHON), notes_py, "--help"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        assert "create" in result.stdout
        assert "list" in result.stdout
        
        # Step 3: Run a command
        result = subprocess.run(
            [str(MICROCLI_PYTHON), notes_py, "create"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        assert "TODO" in result.stdout
        
        # Step 4: Run command tour
        result = subprocess.run(
            [str(MICROCLI_PYTHON), notes_py, "--tour"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        assert "COMMAND TOUR" in result.stdout
        
        # Step 5: Learn from microcli
        result = subprocess.run(
            [str(MICROCLI_PYTHON), "-m", "microcli", "learn", "--topic", "principles"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "principles" in result.stdout.lower()
        assert "validate" in result.stdout.lower()


def test_learn_all_topics():
    """Test that all learn topics are accessible."""
    topics = ["principles", "parameters", "ok-fail", "utilities", "patterns", "reference"]
    
    for topic in topics:
        result = subprocess.run(
            [str(MICROCLI_PYTHON), "-m", "microcli", "learn", "--topic", topic],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Topic {topic} failed: {result.stderr}"
        assert len(result.stdout) > 100, f"Topic {topic} has no content"


def test_new_creates_valid_python():
    """Test that new creates syntactically valid Python."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [str(MICROCLI_PYTHON), "-m", "microcli", "new",
             "testapp", "Test", "cmd1,cmd2,cmd3"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        
        # Check it can be compiled
        testapp_py = Path(tmpdir) / "testapp.py"
        with open(testapp_py) as f:
            code = f.read()
        
        compile(code, str(testapp_py), 'exec')


def test_new_with_special_commands():
    """Test new with various command names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with commands that have underscores
        result = subprocess.run(
            [str(MICROCLI_PYTHON), "-m", "microcli", "new",
             "tool", "Tool", "do_it,check_status"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        
        tool_py = Path(tmpdir) / "tool.py"
        content = tool_py.read_text()
        assert "do_it" in content
        assert "check_status" in content


def test_new_fails_if_file_exists():
    """Test that new fails if target file already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file with the same name
        (Path(tmpdir) / "existing.py").touch()
        
        result = subprocess.run(
            [str(MICROCLI_PYTHON), "-m", "microcli", "new",
             "existing", "Existing", "cmd"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "already exists" in result.stdout.lower() or "already exists" in result.stderr.lower()
