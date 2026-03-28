"""microcli CLI - Bootstrap and learn microcli microapps."""
from pathlib import Path
from typing import Annotated

from .core import command, main, ok, fail, info, write


@command
def new(name: Annotated[str, "Name"], title: Annotated[str, "Title"], commands: Annotated[str, "Commands"]):
    """Create a new microcli microapp.
    
    Example: microcli new notes "Notes Manager" create,list,delete
    
    Run `microcli learn templates` to understand the template structure.
    """
    cmd_list = [c.strip() for c in commands.split(",")]
    
    template = _generate_template(name, title, cmd_list)
    
    output_path = Path.cwd() / f"{name}.py"
    if output_path.exists():
        fail(f"File already exists: {output_path}")
    
    write(output_path, template)
    ok(f"Created {output_path}")
    info(f"Run `python {name}.py --help` to see available commands.")
    info("Run `python {name}.py --learn` to explore the app structure.")
    info("Run `microcli learn principles` to start learning microcli!")


def _generate_template(name: str, title: str, commands: list[str]) -> str:
    """Generate the microapp template."""
    cmd_functions = []
    for cmd in commands:
        cmd_functions.append(_generate_command(cmd))
    
    commands_str = ", ".join(f'"{c}"' for c in commands)
    
    template = f'''#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["microcli-toolkit"]
# ///

"""
{title}

This is a microcli microapp. You're an AI agent helping build it.
Run `microcli learn` to start your learning journey.

Quick start:
  microcli learn principles    → The three principles
  microcli learn parameters    → How commands work
  microcli learn ok-fail       → Output helpers
  microcli learn patterns      → Common patterns
  microcli learn utilities     → File ops, shell, etc.
"""

from typing import Annotated
from microcli import command, main, ok, fail, info, read, write, ls, glob, touch, rm, cp, mv, cd, sh, which, env


# ============================================================================
# COMMANDS
# ============================================================================

{chr(10).join(cmd_functions)}


if __name__ == "__main__":
    main()
'''
    return template


def _generate_command(cmd: str) -> str:
    """Generate a single command function."""
    return f"""
@command
def {cmd}():
    \"\"\"TODO: Describe what {cmd} does.
    
    This is a command. Commands are decorated with @command.
    Run `microcli learn parameters` to understand command structure.
    
    TODO: Implement {cmd} command here.
    \"\"\"
    ok("TODO: implement {cmd} command here")
"""


@command
def learn(topic: Annotated[str, "Topic to learn about"] = ""):
    """Learn about the microcli framework.
    
    Run without args to see available topics.
    Run with a topic name to learn about it.
    
    Topics:
      principles    → The three principles
      parameters    → How commands work
      ok-fail       → Output helpers
      utilities     → File ops, shell, etc.
      patterns      → Common patterns
      reference     → Quick reference card
    """
    from .learn_content import list_topics, show_topic
    
    if not topic:
        list_topics()
    else:
        show_topic(topic)


if __name__ == "__main__":
    main()
