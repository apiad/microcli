"""Learning content for microcli framework."""
from .core import COLORS


def _section(title: str) -> str:
    bold = COLORS['bold']
    yellow = COLORS['yellow']
    nc = COLORS['nc']
    return f"\n{bold}{title}{nc}\n{yellow}{'─' * len(title)}{nc}"


def _code(code: str) -> str:
    cyan = COLORS['cyan']
    nc = COLORS['nc']
    return f"{cyan}{code}{nc}"


def _example(label: str, code: str) -> str:
    green = COLORS['green']
    nc = COLORS['nc']
    return f"  {green}{label}:{nc} {code}"


def _bullet(text: str, indent: int = 2) -> str:
    green = COLORS['green']
    nc = COLORS['nc']
    return f"{' ' * indent}{green}•{nc} {text}"


def _note(text: str) -> str:
    yellow = COLORS['yellow']
    nc = COLORS['nc']
    return f"  {yellow}→{nc} {text}"


def principles() -> None:
    """Print the three core principles."""
    green = COLORS['green']
    bold = COLORS['bold']
    cyan = COLORS['cyan']
    nc = COLORS['nc']
    
    print(f"""
{bold}THE THREE PRINCIPLES{_section('THE THREE PRINCIPLES')}

Microcli tools follow three principles that make them reliable and
agent-friendly:

{green}1. VALIDATE BEFORE ACTING{cyan}
   ─────────────────────────────{nc}
   Always check inputs and state before making changes.

   {green}✗{nc} Bad:
   {_code('read(path)')}
   {_code('write(path, content)  # what if path is invalid?')}

   {green}✓{nc} Good:
   {_code('if not path.exists():')}
   {_code('    fail(f"Path not found: {{path}}")')}
   {_code('write(path, content)  # safe to proceed')}

{green}2. RETURN DESCRIPTIVE MESSAGES{cyan}
   ─────────────────────────────────{nc}
   Output tells users what happened and what to do next.

   {green}✗{nc} Bad: Silent success, return None
   {green}✓{nc} Good: {_code('ok(f"Created {{file}} ({{size}} bytes)")')}

{green}3. TWO-PHASE PATTERNS{cyan}
   ─────────────────────{nc}
   Draft first, then confirm. Safety through review.

   {_code('@command')}
   {_code('def create(save: bool = False):')}
   {_code('    """Create new project."""')}
   {_code('    if not save:')}
   {_code('        info("Preview mode. Run with --save to confirm")')}
   {_code('        return')}
   {_code('    # ... actual creation')}
""")


def parameters() -> None:
    """Print how command parameters work."""
    green = COLORS['green']
    bold = COLORS['bold']
    cyan = COLORS['cyan']
    yellow = COLORS['yellow']
    nc = COLORS['nc']
    
    print(f"""
{bold}COMMAND PARAMETERS{_section('COMMAND PARAMETERS')}

Parameters define what arguments your commands accept. Microcli
infers the argument style from the function signature:

{cyan}POSITIONAL ARGUMENTS{cyan}
   ─────────────────────{nc}
   No default value = required positional argument

   {_code('def greet(name):              # cmd.py greet Alice')}
   {_code('    ok(f"Hello, {{name}}!")')}
   
   Run: {_code('mytool.py greet Alice')}
   Output: {_code('✓ Hello, Alice!')}

{cyan}OPTIONAL ARGUMENTS{cyan}
   ───────────────────{nc}
   Has default value = optional --flag argument

   {_code('def greet(name="World"):      # cmd.py greet --name Alice')}
   {_code('    ok(f"Hello, {{name}}!")')}
   
   Run: {_code('mytool.py greet --name Alice')}
   Output: {_code('✓ Hello, Alice!')}

{cyan}BOOLEAN FLAGS{cyan}
   ─────────────{nc}
   bool type = on/off flag (--flag or nothing)

   {_code('def build(verbose: bool = False):')}
   {_code('    if verbose:')}
   {_code('        info("Building...")')}
   
   Run: {_code('mytool.py build --verbose')}
   Output: {_code('→ Building...')}

{cyan}HELP TEXT (Annotated){cyan}
   ──────────────────────{nc}
   Use Annotated[type, "help text"] for documentation

   {_code('from typing import Annotated')}
   {_code('@command')}
   {_code('def deploy(')}
   {_code('    app: Annotated[str, "Application name"],')}
   {_code('    env: Annotated[str, "Target environment"] = "prod"')}
   {_code('):')}
   
   Run: {_code('mytool.py --help deploy')}
   Shows: Help text for each parameter

{yellow}RULES SUMMARY:{nc}
   • No default     → Positional (required)
   • Has default    → Optional --flag
   • bool + default → Boolean flag
   • Annotated[type, "help"] → Adds help text
""")


def ok_fail() -> None:
    """Print status helper documentation."""
    green = COLORS['green']
    red = COLORS['red']
    cyan = COLORS['cyan']
    yellow = COLORS['yellow']
    bold = COLORS['bold']
    nc = COLORS['nc']
    
    print(f"""
{bold}STATUS HELPERS{_section('STATUS HELPERS')}

Use these functions to communicate results clearly:

{green}ok(msg){cyan} - Success message{cyan}
   ─────────────────────────{nc}
   Print a green checkmark with a success message.
   
   {_code('ok("File created successfully")')}
   {_code('# Output: ✓ File created successfully')}

{red}fail(msg){cyan} - Error message (exits){cyan}
   ─────────────────────────────{nc}
   Print a red X with an error message and exit with code 1.
   Use for unrecoverable errors.
   
   {_code('if not file.exists():')}
   {_code('    fail(f"File not found: {{file}}")')}
   {_code('# Output: ✗ File not found: config.yaml')}
   {_code('# Exit code: 1')}

{cyan}info(msg) / step(msg) - Information{cyan}
   ─────────────────────────────────{nc}
   Print an arrow with an informational message.
   Use info() for general info, step() for progress.
   
   {_code('info("Processing {{count}} files...")')}
   {_code('# Output: → Processing 42 files...')}
   
   {_code('step("Step 1 of 3: Validate input")')}
   {_code('# Output: → Step 1 of 3: Validate input')}

{yellow}warn(msg) - Warning message{cyan}
   ────────────────────────────{nc}
   Print a warning triangle with a yellow message.
   
   {_code('warn("Using default config")')}
   {_code('# Output: ⚠ Using default config')}

{cyan}EXAMPLES IN CONTEXT{cyan}
   ────────────────────{nc}

   {_code('@command')}
   {_code('def process(input_path: str, dry_run: bool = False):')}
   {_code('    """Process a file with optional preview."""')}
   {_code('    if dry_run:')}
   {_code('        info("DRY RUN - no changes will be made")')}
   {_code('    ')}
   {_code('    if not Path(input_path).exists():')}
   {_code('        fail(f"Input not found: {{input_path}}")')}
   {_code('    ')}
   {_code('    ok(f"Processed {{input_path}}")')}
""")


def utilities() -> None:
    """Print utility function documentation."""
    cyan = COLORS['cyan']
    green = COLORS['green']
    bold = COLORS['bold']
    yellow = COLORS['yellow']
    nc = COLORS['nc']
    
    print(f"""
{bold}UTILITY FUNCTIONS{_section('UTILITY FUNCTIONS')}

Microcli provides a toolkit of shell and file utilities.

{cyan}FILE OPERATIONS{cyan}
   ────────────────{nc}

{green}read(path){nc} - Read file contents
   {_code('content = read("config.yaml")')}
   {_code('# Returns: str with file contents')}

{green}write(path, content){nc} - Write to file
   {_code('write("output.txt", "Hello world")')}
   {_code('# Creates or overwrites file')}

{green}ls(path="."){nc} - List directory
   {_code('files = ls("/tmp")')}
   {_code('# Returns: list[str] of filenames')}

{green}glob(pattern){nc} - Find files by pattern
   {_code('py_files = glob("**/*.py")')}
   {_code('# Returns: list[Path] matching pattern')}

{green}touch(path){nc} - Create empty file
   {_code('touch(".gitkeep")')}
   {_code('# Returns: Path object')}

{green}rm(path, recursive=False){nc} - Remove file/directory
   {_code('rm("temp.txt")')}
   {_code('rm("build/", recursive=True)  # removes directories')}

{green}cp(src, dst){nc} - Copy file or directory
   {_code('cp("src.txt", "dst.txt")')}

{green}mv(src, dst){nc} - Move/rename
   {_code('mv("old.txt", "new.txt")')}

{cyan}SHELL EXECUTION{cyan}
   ──────────────────{nc}

{green}sh(cmd, timeout=None, env=None, cwd=None){nc} - Run shell command
   {_code('result = sh("git status")')}
   {_code('if result.ok:')}
   {_code('    print(result.stdout)')}
   {_code('else:')}
   {_code('    print(result.stderr)')}
   
   {_note('result.ok        → True if returncode == 0')}
   {_note('result.failed    → True if returncode != 0')}
   {_note('result.stdout    → Standard output string')}
   {_note('result.stderr    → Standard error string')}
   {_note('result.returncode → Exit code')}
   {_note('result.duration  → Execution time in seconds')}

   Example with timeout:
   {_code('result = sh("sleep 5", timeout=2)  # fails after 2s')}

   Example with env:
   {_code('result = sh("echo $MY_VAR", env={{"MY_VAR": "hello"}})')}

{cyan}NAVIGATION{cyan}
   ────────────{nc}

{green}with cd(path):{nc} - Change directory (context manager)
   {_code('with cd("/tmp"):')}
   {_code('    files = ls()  # lists /tmp contents')}
   {_code('# Automatically returns to original directory')}

{green}which(cmd){nc} - Find command in PATH
   {_code('git_path = which("git")')}
   {_code('# Returns: Path or None')}
   {_code('if not which("git"):')}
   {_code('    fail("git not installed")')}

{green}env(name){nc} - Get environment variable
   {_code('home = env("HOME")')}
   {_code('# Returns: str or None if not set')}
""")


def patterns() -> None:
    """Print common design patterns."""
    cyan = COLORS['cyan']
    green = COLORS['green']
    bold = COLORS['bold']
    yellow = COLORS['yellow']
    nc = COLORS['nc']
    
    print(f"""
{bold}COMMON PATTERNS{_section('COMMON PATTERNS')}

{cyan}TWO-PHASE PATTERN (DRAFT MODE){cyan}
   ───────────────────────────────{nc}
   Safety first: preview changes before applying them.

   {_code('@command')}
   {_code('def update_config(')}
   {_code('    key: str,')}
   {_code('    value: str,')}
   {_code('    save: bool = False,')}
   {_code('):')}
   {_code('    """Update configuration. Use --save to persist."""')}
   {_code('    config = read("config.yaml")')}
   {_code('    new_config = modify(config, key, value)')}
   {_code('    ')}
   {_code('    if not save:')}
   {_code('        info("Preview mode. Run with --save to apply.")')}
   {_code('        print(new_config)')}
   {_code('        return')}
   {_code('    ')}
   {_code('    write("config.yaml", new_config)')}
   {_code('    ok("Configuration updated")')}
   
   {_note('Run: mytool.py update-config api_key newvalue')}
   {_note('Output: → Preview mode. Run with --save to apply.')}
   {_note('         (shows what would change)')}
   {_note('Run: mytool.py update-config api_key newvalue --save')}
   {_note('Output: ✓ Configuration updated')}

{cyan}VALIDATION-FIRST PATTERN{cyan}
   ──────────────────────────{nc}
   Check everything before doing anything.

   {_code('@command')}
   {_code('def deploy(app: str):')}
   {_code('    """Deploy application."""')}
   {_code('    ')}
   {_code('    # 1. Validate inputs')}
   {_code('    if not app:')}
   {_code('        fail("App name is required")')}
   {_code('    ')}
   {_code('    # 2. Validate environment')}
   {_code('    if not which("docker"):')}
   {_code('        fail("Docker not installed")')}
   {_code('    ')}
   {_code('    # 3. Validate resources')}
   {_code('    result = sh("df -h /")')}
   {_code('    if "100%" in result.stdout:')}
   {_code('        fail("Disk full, cannot deploy")')}
   {_code('    ')}
   {_code('    # 4. All checks passed - proceed')}
   {_code('    ok(f"Deployed {{app}}")')}

{cyan}FOLLOW-UP WITH .explain(){cyan}
   ────────────────────────────{nc}
   Generate exact command strings with hydrated arguments.

   {_code('@command')}
   {_code('def create(')}
   {_code('    title: Annotated[str, "Post title"],')}
   {_code('    slug: Annotated[str, "URL slug"],')}
   {_code('    save: bool = False,')}
   {_code('):')}
   {_code('    """Create a new blog post."""')}
   {_code('    if not save:')}
   {_code('        info("Preview: Run this command to publish:")')}
   {_code('        print(f"  {create.explain(title=title, slug=slug, save=True)}")')}
   {_code('        return')}
   {_code('    # ... create post ...')}
   {_code('    ok(f"Created post: {{title}}")')}
   
   {_note('Run: mytool.py create "Hello World" hello-world')}
   {_note('Output: → Preview: Run this command to publish:')}
   {_note('           mytool.py create "Hello World" hello-world --save')}
   
   {_note('.explain() auto-handles quoting and escaping!')}

{cyan}STREAM PROCESSING (pipelines){cyan}
   ───────────────────────────────{nc}
   Process data from stdin in chunks.

   {_code('@command')}
   {_code('def transform(text: str):  # or use stdin type')}
   {_code('    """Transform each line of input."""')}
   {_code('    for line in text.strip().split("\\n"):')}
   {_code('        processed = process(line)')}
   {_code('        ok(f"Processed: {{processed}}")')}
   
   {_note('cat data.csv | mytool.py transform')}

{cyan}ERROR RECOVERY{cyan}
   ────────────────{nc}
   Graceful degradation with informative messages.

    {_code('def safe_read(path: Path) -> Optional[str]:')}
    {_code('    try:')}
    {_code('        return read(path)')}
    {_code('    except FileNotFoundError:')}
    {_code('        warn(f"File not found: {{path}}, using defaults")')}
    {_code('        return None')}
    {_code('    except PermissionError:')}
    {_code('        fail(f"Permission denied: {{path}}")')}
""")


def complex_inputs() -> None:
    """Print complex input handling documentation."""
    cyan = COLORS['cyan']
    bold = COLORS['bold']
    yellow = COLORS['yellow']
    nc = COLORS['nc']
    
    print(f"""
{bold}COMPLEX INPUTS{_section('COMPLEX INPUTS')}

Handle complex data from JSON, files, or piped input.

{cyan}JSON FROM STDIN{cyan}
   ──────────────────{nc}
   Use stdin[T] to read JSON from stdin. Requires pydantic extra.

   {_code('uv add microcli-toolkit --extra pydantic')}

   {_code('from microcli import stdin')}
   {_code('@command')}
   {_code('def create(title: str, data: stdin[dict]):')}
   {_code('    ok(f"Creating {{title}} with {{len(data)}} items")')}
   
   Usage: {_code('echo \'{{"items": [1, 2, 3]}}\' | mytool.py create "My Item"')}

{cyan}PYDANTIC MODELS{cyan}
   ────────────────{nc}
   Validate JSON against a Pydantic model.

   {_code('class Config(BaseModel):')}
   {_code('    name: str')}
   {_code('    tags: list[str] = []')}
   
   {_code('@command')}
   {_code('def setup(cfg: stdin[Config]):')}
   {_code('    ok(f"Configured {{cfg.name}}")')}

{yellow}INVALID JSON SHOWS ERRORS:{nc}
   {_code('✗ Invalid JSON: Expecting value')}
""")




def reference() -> None:
    """Print quick reference card."""
    cyan = COLORS['cyan']
    green = COLORS['green']
    yellow = COLORS['yellow']
    bold = COLORS['bold']
    nc = COLORS['nc']
    
    print(f"""
{bold}QUICK REFERENCE{_section('QUICK REFERENCE')}

{cyan}COMMAND DECORATOR{cyan}
   ──────────────────{nc}
   {_code('from microcli import command')}
   {_code('@command')}
   {_code('def my_command(args):')}
   {_code('    """Description here."""')}
   {_code('    ...')}
   {_code('main()  # in __main__ block')}

{cyan}PARAMETER TYPES{cyan}
   ────────────────{nc}
   {_code('def req(name):          # positional: cmd.py req value')}
   {_code('def opt(name="default"): # --flag:   cmd.py opt --name value')}
   {_code('def flag(flag: bool = False): # --flag: cmd.py cmd --flag')}
   {_code('def with_help(x: Annotated[str, "Help text"]):')}

{cyan}STATUS HELPERS{cyan}
   ────────────────{nc}
   {_code('ok("Success message")      # ✓ green')}
   {_code('fail("Error message")      # ✗ red + exit(1)')}
   {_code('info("Info message")       # → cyan')}
   {_code('warn("Warning message")    # ⚠ yellow')}
   {_code('step("Step indicator")     # → cyan')}

{cyan}FILE UTILITIES{cyan}
   ────────────────{nc}
   {_code('read(path)                 # → str')}
   {_code('write(path, content)       # → None')}
   {_code('ls(path=".")               # → list[str]')}
   {_code('glob("**/*.py")            # → list[Path]')}
   {_code('touch(path)                # → Path')}
   {_code('rm(path, recursive=False)  # → None')}
   {_code('cp(src, dst)              # → Path')}
   {_code('mv(src, dst)              # → Path')}

{cyan}SHELL & NAVIGATION{cyan}
   ────────────────────{nc}
   {_code('sh(cmd)                    # → Result(ok, stdout, ...)')}
   {_code('sh(cmd, timeout=30)        # with timeout')}
   {_code('sh(cmd, env={{"VAR": "x"}}) # with env vars')}
   {_code('with cd(path):             # context manager')}
   {_code('which(cmd)                 # → Path or None')}
   {_code('env(name)                  # → str or None')}

{cyan}RESULT OBJECT{cyan}
   ──────────────{nc}
   {_code('result.ok          # True if success')}
   {_code('result.failed      # True if failure')}
   {_code('result.returncode  # Exit code (0 = success)')}
   {_code('result.stdout      # Standard output')}
   {_code('result.stderr      # Standard error')}
   {_code('result.duration    # Seconds elapsed')}

{cyan}COMMAND.explain(){cyan}
   ──────────────────{nc}
   {_code('cmd.explain(arg=value)  # → exact invocation string')}
   {_code('# Perfect for follow-up instructions')}

{cyan}BOOLEAN OPERATORS ON RESULT{cyan}
   ──────────────────────────────{nc}
   {_code('result = sh("git status")')}
   {_code('if result:               # same as result.ok')}
   {_code('    ok("Clean")')}
   {_code('else:')}
   {_code('    fail("Not clean")')}

{yellow}LEARNING COMMANDS{cyan}
   ────────────────────{nc}
   {_code('mytool.py --learn           # Show all topics')}
   {_code('mytool.py --learn principles  # Show specific topic')}
""")


TOPICS = {
    'principles': principles,
    'parameters': parameters,
    'ok-fail': ok_fail,
    'ok_fail': ok_fail,
    'utilities': utilities,
    'patterns': patterns,
    'complex-inputs': complex_inputs,
    'complex_inputs': complex_inputs,
    'reference': reference,
}


def list_topics() -> None:
    """Print all available learning topics."""
    bold = COLORS['bold']
    cyan = COLORS['cyan']
    green = COLORS['green']
    nc = COLORS['nc']
    
    print(f"""
{bold}AVAILABLE TOPICS{_section('AVAILABLE TOPICS')}
Use {_code('--learn <topic>')} to view a specific topic.

{green}Fundamentals:{nc}
   {cyan}principles{nc}   - The three core principles
   {cyan}parameters{nc}   - How command parameters work
   {cyan}reference{nc}    - Quick reference card

{green}Utilities:{nc}
   {cyan}utilities{nc}    - File ops, shell, navigation

{green}Patterns:{nc}
   {cyan}patterns{nc}     - Common design patterns
   {cyan}ok-fail{nc}      - Status helpers (ok, fail, info, warn)

Examples:
   {_code('mytool.py --learn')}
   {_code('mytool.py --learn principles')}
   {_code('mytool.py --learn utilities')}
""")


def show_topic(name: str) -> bool:
    """Show a specific topic by name. Returns True if found."""
    from .core import fail
    
    topic = TOPICS.get(name)
    
    if topic is None:
        fail(f"Unknown topic: {name}")
        return False
    
    topic()
    return True
