"""Tests for microcli stdin parsing."""
import pytest


# =============================================================================
# Stdin marker type
# =============================================================================

def test_stdin_type_exists():
    """Test that stdin marker type exists."""
    from microcli.stdin import stdin
    assert stdin is not None


def test_stdin_generic_syntax():
    """Test that stdin[T] syntax works."""
    from microcli.stdin import stdin
    
    # stdin[str], stdin[dict], stdin[int] should all work
    result = stdin[dict]
    assert result is not None


def test_stdin_type_has_inner_type():
    """Test that stdin[T] stores the inner type."""
    from microcli.stdin import stdin
    
    marker = stdin[dict]
    assert hasattr(marker, 'inner_type')
    assert marker.inner_type is dict


# =============================================================================
# Stdin parsing
# =============================================================================

def test_parse_stdin_basic_json():
    """Test parsing basic JSON."""
    from microcli.stdin import parse_stdin
    
    result = parse_stdin('{"name": "test", "value": 42}', dict)
    assert result == {"name": "test", "value": 42}


def test_parse_stdin_with_pydantic():
    """Test parsing JSON to Pydantic model."""
    from microcli.stdin import stdin, parse_stdin
    from pydantic import BaseModel
    
    class Note(BaseModel):
        title: str
        tags: list[str] = []
    
    result = parse_stdin('{"title": "Test", "tags": ["a", "b"]}', Note)
    assert isinstance(result, Note)
    assert result.title == "Test"
    assert result.tags == ["a", "b"]


def test_parse_stdin_invalid_json():
    """Test that invalid JSON raises error."""
    from microcli.stdin import parse_stdin
    from microcli.core import fail
    
    with pytest.raises(SystemExit):
        parse_stdin('not valid json', dict)


def test_parse_stdin_pydantic_validation_error():
    """Test that Pydantic validation errors raise."""
    from microcli.stdin import stdin, parse_stdin
    from pydantic import BaseModel
    
    class Note(BaseModel):
        title: str
        count: int
    
    with pytest.raises(SystemExit):
        parse_stdin('{"title": "Test"}', Note)  # missing required 'count'


# =============================================================================
# Command with stdin parameter
# =============================================================================

def test_command_with_stdin_param():
    """Test that commands can have stdin parameters."""
    from microcli.core import command, _commands
    from microcli.stdin import stdin
    
    _commands.clear()
    
    received_data = {}
    
    @command
    def create(
        name: str,
        data: stdin[dict],
    ):
        """Create something."""
        received_data['name'] = name
        received_data['data'] = data
    
    assert 'create' in _commands
    cmd = _commands['create']
    assert cmd.stdin_params is not None
    assert 'data' in cmd.stdin_params
