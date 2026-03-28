"""Stdin marker type for complex JSON parsing."""
from typing import Generic, TypeVar, get_origin, get_args

T = TypeVar('T')

class _StdinType:
    """Internal representation of stdin[T]."""
    def __init__(self, inner_type):
        self.inner_type = inner_type
    
    def __class_getitem__(cls, item):
        return _StdinType(item)

stdin = _StdinType

def is_stdin_type(annotation) -> bool:
    """Check if an annotation is a stdin[T] type."""
    return isinstance(annotation, _StdinType)

def parse_stdin(content: str, typ):
    """Parse stdin content to the specified type.
    
    Args:
        content: JSON string from stdin
        typ: Target type (dict, Pydantic model, etc.)
    
    Returns:
        Parsed object of type `typ`
    
    Raises:
        SystemExit: If parsing fails
    """
    import json
    from microcli.core import fail
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        fail(f"✗ Invalid JSON: {e.msg}")
        return  # unreachable
    
    try:
        from pydantic import BaseModel
        if isinstance(typ, type) and issubclass(typ, BaseModel):
            try:
                return typ.model_validate(data)
            except Exception as e:
                fail(f"✗ Validation error: {e}")
                return  # unreachable
    except ImportError:
        pass
    
    if typ is dict or typ == dict:
        return data
    
    try:
        if isinstance(data, dict):
            return typ(**data)
        return typ(data)
    except Exception as e:
        fail(f"✗ Failed to parse stdin: {e}")
