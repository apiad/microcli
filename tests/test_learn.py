"""Tests for microcli learn mode."""
import pytest
import ast


# =============================================================================
# ExplainVisitor
# =============================================================================

def test_finds_explain_calls():
    from microcli.learn import ExplainVisitor
    
    code = '''
def my_command():
    if not save:
        return
    other_cmd.explain(name=name)
'''
    visitor = ExplainVisitor(code.split('\n'))
    visitor.visit(ast.parse(code))
    
    assert len(visitor.explain_calls) == 1
    assert visitor.explain_calls[0]['command'] == 'other_cmd'


def test_finds_fail_calls():
    from microcli.learn import ExplainVisitor
    
    code = '''
def my_command():
    if not content:
        m.fail("No content provided")
'''
    visitor = ExplainVisitor(code.split('\n'))
    visitor.visit(ast.parse(code))
    
    assert len(visitor.fail_calls) == 1
    assert "No content provided" in visitor.fail_calls[0]['message']


def test_finds_ok_calls():
    from microcli.learn import ExplainVisitor
    
    code = '''
def my_command():
    m.ok("Success!")
'''
    visitor = ExplainVisitor(code.split('\n'))
    visitor.visit(ast.parse(code))
    
    assert len(visitor.ok_calls) == 1
    assert "Success!" in visitor.ok_calls[0]['message']


def test_extracts_guard_conditions():
    from microcli.learn import ExplainVisitor
    
    code = '''
def my_command():
    if not save:
        m.fail("Not saved")
    else:
        m.ok("Saved")
'''
    visitor = ExplainVisitor(code.split('\n'))
    visitor.visit(ast.parse(code))
    
    assert 'not save' in visitor.fail_calls[0]['guard']
    assert 'if save' in visitor.ok_calls[0]['guard']


def test_extracts_kwargs():
    from microcli.learn import ExplainVisitor
    
    code = '''
def my_command():
    cmd.explain(name="Alice", save=True)
'''
    visitor = ExplainVisitor(code.split('\n'))
    visitor.visit(ast.parse(code))
    
    kwargs = visitor.explain_calls[0]['args']
    assert kwargs['name'] == 'Alice'
    assert kwargs['save'] is True


# =============================================================================
# LearnMode
# =============================================================================

def test_show_command_unknown_raises(tmp_path):
    import microcli.core
    microcli.core._commands.clear()
    
    tool_file = tmp_path / "tool.py"
    tool_file.write_text('''
from microcli import command

@command
def hello():
    """A greeting."""
    pass
''')
    
    from microcli.learn import LearnMode
    learn = LearnMode(str(tool_file))
    
    with pytest.raises(SystemExit):
        learn.show_command("nonexistent")


def test_format_args_handles_booleans():
    from microcli.learn import LearnMode
    # Just test the _format_args helper directly
    assert LearnMode._format_args(None, {"save": True}) == "--save"
    assert LearnMode._format_args(None, {"name": "Alice"}) == "--name Alice"
    assert LearnMode._format_args(None, {"save": True, "name": "Bob"}) == "--save --name Bob"
