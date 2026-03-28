"""Learn mode - auto-discover command tours from source code."""
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .core import COLORS, _commands, fail


@dataclass
class LearnStep:
    """A step in the command tour."""
    command: str
    args: dict
    message: str
    guard: str = ""
    line: int = 0


@dataclass
class FailStep:
    """A failure mode in the command tour."""
    message: str
    guard: str = ""
    line: int = 0


@dataclass
class HappyStep:
    """A happy path (success) in the command tour."""
    message: str
    guard: str = ""
    line: int = 0


@dataclass
class CommandTour:
    """Tour information for a command."""
    name: str
    description: str
    steps: list[LearnStep] = field(default_factory=list)
    failures: list[FailStep] = field(default_factory=list)
    happy_paths: list[HappyStep] = field(default_factory=list)


class ExplainVisitor(ast.NodeVisitor):
    """AST visitor to find .explain(), m.fail(), and m.ok() calls."""

    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.explain_calls: list[dict] = []
        self.fail_calls: list[dict] = []
        self.ok_calls: list[dict] = []
        self._info_messages: list[tuple[int, str]] = []
        self._current_func: str = ""
        self._guard_stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track which command function we're in."""
        self._current_func = node.name
        self._info_messages = []
        self._guard_stack = []
        self.generic_visit(node)
        self._current_func = ""

    def _invert_guard(self, guard: str) -> str:
        """Invert a guard condition."""
        if guard.startswith("if not "):
            return "if " + guard[7:]
        elif guard.startswith("if "):
            return "if not " + guard[3:]
        return guard

    def visit_If(self, node: ast.If):
        """Track if conditions and their else blocks."""
        guard = ast.unparse(node.test) if hasattr(ast, 'unparse') else self._expr_to_str(node.test)

        self._guard_stack.append(f"if {guard}:")

        if_ends_with_return = (len(node.body) > 0 and isinstance(node.body[-1], ast.Return))

        for child in node.body:
            self.visit(child)

        self._guard_stack.pop()

        if node.orelse:
            self._guard_stack.append(self._invert_guard(f"if {guard}:"))
            for child in node.orelse:
                self.visit(child)
            self._guard_stack.pop()

    def visit_Call(self, node: ast.Call):
        """Find .explain(), m.info(), m.fail(), and m.ok() calls."""
        if self._is_m_info(node):
            msg = self._extract_string_arg(node)
            if msg:
                self._info_messages.append((node.lineno, msg))

        current_guard = self._guard_stack[-1] if self._guard_stack else ""

        if self._is_m_fail(node):
            msg = self._extract_fail_message(node)
            self.fail_calls.append({
                'message': msg,
                'guard': current_guard,
                'line': node.lineno,
                'func': self._current_func,
            })

        if self._is_m_ok(node):
            msg = self._extract_ok_message(node)
            self.ok_calls.append({
                'message': msg,
                'guard': current_guard,
                'line': node.lineno,
                'func': self._current_func,
            })

        if self._is_explain_call(node):
            cmd_name = self._get_explain_command(node)
            kwargs = self._extract_kwargs(node)
            line_no = node.lineno

            context = []
            for ln, msg in reversed(self._info_messages):
                if ln < line_no:
                    context.append(msg)
                    if len(context) >= 2:
                        break

            self.explain_calls.append({
                'command': cmd_name,
                'args': kwargs,
                'guard': current_guard,
                'message': context[0] if context else "",
                'line': line_no,
                'func': self._current_func,
            })

        self.generic_visit(node)

    def _is_explain_call(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'explain'
        if isinstance(node.func, ast.Subscript):
            if isinstance(node.func.value, ast.Attribute):
                return node.func.value.attr == 'explain'
        return False

    def _is_m_info(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in ('info', 'warn', 'ok')
        return False

    def _is_m_fail(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'fail'
        return False

    def _is_m_ok(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'ok'
        return False

    def _extract_ok_message(self, node: ast.Call) -> str:
        """Extract message from m.ok() call."""
        if not node.args:
            return "Success"
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        if isinstance(arg, ast.JoinedStr):
            parts = []
            for val in arg.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    parts.append(val.value)
                elif isinstance(val, ast.FormattedValue):
                    parts.append("{" + self._expr_to_str(val.value) + "}")
            return "".join(parts)
        if isinstance(arg, ast.BinOp):
            return self._expr_to_str(arg)
        return "Success (message depends on runtime values)"

    def _extract_fail_message(self, node: ast.Call) -> str:
        """Extract message from m.fail() call."""
        if not node.args:
            return "Unknown error"
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        if isinstance(arg, ast.JoinedStr):
            parts = []
            for val in arg.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    parts.append(val.value)
                elif isinstance(val, ast.FormattedValue):
                    parts.append("{" + self._expr_to_str(val.value) + "}")
            return "".join(parts)
        if isinstance(arg, ast.BinOp):
            return self._expr_to_str(arg)
        return "Error (message depends on runtime values)"

    def _get_explain_command(self, node: ast.Call) -> str:
        """Extract command name from .explain() call."""
        if isinstance(node.func, ast.Attribute):
            base = node.func.value
            if isinstance(base, ast.Name):
                return base.id
            if isinstance(base, ast.Attribute):
                return base.attr
        elif isinstance(node.func, ast.Subscript):
            if isinstance(node.func.value, ast.Attribute):
                return "??"
        return "unknown"

    def _extract_kwargs(self, node: ast.Call) -> dict:
        """Extract keyword arguments from .explain() call."""
        kwargs = {}
        for kw in node.keywords:
            val = kw.value
            if isinstance(val, ast.Name):
                kwargs[kw.arg] = val.id
            elif isinstance(val, ast.Constant):
                kwargs[kw.arg] = val.value
            else:
                kwargs[kw.arg] = "??"
        return kwargs

    def _extract_string_arg(self, node: ast.Call) -> str:
        """Extract string argument from m.info() call."""
        if not node.args:
            return ""
        val = node.args[0]
        if isinstance(val, ast.Constant):
            v = val.value
            if isinstance(v, str):
                return v
        if isinstance(val, ast.Str):
            return str(val.s)
        return ""

    def _expr_to_str(self, node) -> str:
        """Fallback for older Python versions."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._expr_to_str(node.value) + '.' + node.attr
        return "?"


class LearnMode:
    """Generate command tours by analyzing source code."""

    def __init__(self, source_file: str):
        self.source_file = source_file
        with open(source_file) as f:
            self.source = f.read()
            self.source_lines = self.source.split('\n')

        self.tree = ast.parse(self.source)
        self.visitor = ExplainVisitor(self.source_lines)
        self.visitor.visit(self.tree)
        self.tours = self._build_tours()

    def _build_tours(self) -> dict[str, CommandTour]:
        """Build tour info for each command."""
        tours = {}

        for cmd_name in _commands:
            source_func = self._find_function(cmd_name)
            desc = ""
            if source_func:
                doc = ast.get_docstring(source_func)
                if doc:
                    desc = doc.split('\n')[0]

            steps = []
            for call in self.visitor.explain_calls:
                if call['func'] == cmd_name:
                    steps.append(LearnStep(
                        command=call['command'],
                        args=call['args'],
                        message=call['message'],
                        guard=call['guard'],
                        line=call['line'],
                    ))

            failures = []
            for call in self.visitor.fail_calls:
                if call['func'] == cmd_name:
                    failures.append(FailStep(
                        message=call['message'],
                        guard=call['guard'],
                        line=call['line'],
                    ))

            happy_paths = []
            for call in self.visitor.ok_calls:
                if call['func'] == cmd_name:
                    happy_paths.append(HappyStep(
                        message=call['message'],
                        guard=call['guard'],
                        line=call['line'],
                    ))

            tours[cmd_name] = CommandTour(
                name=cmd_name,
                description=desc or _commands[cmd_name].description.split('\n')[0],
                steps=steps,
                failures=failures,
                happy_paths=happy_paths,
            )

        return tours

    def _find_function(self, name: str) -> Optional[ast.FunctionDef]:
        """Find function definition in AST."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None

    def _format_args(self, args: dict) -> str:
        """Format args for command line, handling booleans specially."""
        parts = []
        for k, v in args.items():
            if v is True:
                parts.append(f"--{k}")
            elif v is False:
                pass
            else:
                parts.append(f"--{k} {v}")
        return " ".join(parts)

    def show_all(self):
        """Show overview of all commands with their next steps."""
        bold = COLORS['bold']
        nc = COLORS['nc']
        cyan = COLORS['cyan']

        script_name = Path(self.source_file).name

        print(f"""
{bold}╔══════════════════════════════════════════════════════════════════════════════╗
║                            COMMAND TOUR: {script_name:<25}║
║                      Auto-discovered workflows and next steps                ║
╚══════════════════════════════════════════════════════════════════════════════╝{nc}
""")

        for name, tour in sorted(self.tours.items()):
            print(f"{bold}{name}{nc}")
            print(f"  {tour.description}")

            if tour.steps:
                print(f"  {cyan}Next steps from here:{nc}")
                for step in tour.steps:
                    args_str = self._format_args(step.args)
                    invocation = f"{step.command} {args_str}".strip()

                    if step.message:
                        print(f"    → {step.message}")
                    print(f"      {script_name} {invocation}")

            if tour.failures:
                print(f"  {COLORS['red']}Failure modes:{nc}")
                for fail_step in tour.failures:
                    print(f"    ✗ {fail_step.message}")

            if not tour.steps and not tour.failures:
                print(f"  (no next steps or failure modes discovered)")
            print()

        print(f"{bold}Run specific command tour:{nc}")
        print(f"  {script_name} --learn <command>")

    def show_command(self, cmd_name: str):
        """Show detailed tour for a specific command."""
        if cmd_name not in self.tours:
            fail(f"Unknown command: {cmd_name}")

        tour = self.tours[cmd_name]
        bold = COLORS['bold']
        nc = COLORS['nc']
        cyan = COLORS['cyan']
        green = COLORS['green']
        script_name = Path(self.source_file).name

        print(f"""
{bold}╔══════════════════════════════════════════════════════════════════════════════╗
║                         COMMAND: {cmd_name:<40}║
╚══════════════════════════════════════════════════════════════════════════════╝{nc}

{bold}Description:{nc}
  {tour.description}

{bold}Next steps (auto-discovered):{nc}
""")

        if not tour.steps:
            print(f"  (no next steps discovered)")
        else:
            for i, step in enumerate(tour.steps, 1):
                args_str = self._format_args(step.args)
                invocation = f"{step.command} {args_str}".strip()

                print(f"  {green}{i}.{nc}", end="")
                if step.guard:
                    print(f" {cyan}Condition:{nc} {step.guard}")
                else:
                    print()
                if step.message:
                    print(f"     {step.message}")
                print(f"     {bold}Run:{nc} {script_name} {invocation}")
                print()

        print(f"""{bold}Failure modes:{nc}
""")

        if not tour.failures:
            print(f"  (no failure modes discovered)")
        else:
            for i, fail_step in enumerate(tour.failures, 1):
                print(f"  {COLORS['red']}{i}.{nc}", end="")
                if fail_step.guard:
                    print(f" {cyan}Condition:{nc} {fail_step.guard}")
                else:
                    print()
                print(f"     {COLORS['red']}{fail_step.message}{nc}")
                print()

        print(f"""{bold}Happy paths:{nc}
""")

        if not tour.happy_paths:
            print(f"  (no happy paths discovered)")
        else:
            for i, happy in enumerate(tour.happy_paths, 1):
                print(f"  {green}{i}.{nc}", end="")
                if happy.guard:
                    print(f" {cyan}Condition:{nc} {happy.guard}")
                else:
                    print()
                print(f"     {happy.message}")
                print()
