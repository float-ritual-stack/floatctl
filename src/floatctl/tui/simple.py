"""Minimal terminal UI and automation loop for FloatCtl."""

from __future__ import annotations

import io
import shlex
import time
import traceback
from collections import deque
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from typing import Callable, Deque, List, Optional, Sequence

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from floatctl.plugin_manager import PluginManager


@dataclass
class CommandResult:
    """Container for command execution results."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float

    @property
    def success(self) -> bool:
        """Return True if the command exited successfully."""
        return self.exit_code == 0


@dataclass
class AgentStep:
    """Single step executed by the automation loop."""

    command: str
    result: CommandResult


class FloatCtlInvoker:
    """Helper that runs FloatCtl commands inside the current process."""

    def __init__(
        self,
        cli_app=None,
        plugin_manager: Optional[PluginManager] = None,
    ) -> None:
        from floatctl.cli import create_cli_app, load_and_register_plugins
        from floatctl.core.logging import setup_quiet_logging

        if cli_app is None:
            setup_quiet_logging()
            cli_app = create_cli_app()

        if plugin_manager is not None:
            cli_app.plugin_manager = plugin_manager

        if not hasattr(cli_app, "plugin_manager"):
            setup_quiet_logging()
            plugin_manager = load_and_register_plugins(cli_app)
            cli_app.plugin_manager = plugin_manager
        else:
            plugin_manager = getattr(cli_app, "plugin_manager")

        self.cli_app = cli_app
        self.plugin_manager = plugin_manager

    def invoke(self, command_line: str) -> CommandResult:
        """Execute a FloatCtl command and capture its output."""

        command_line = command_line.strip()
        if not command_line:
            return CommandResult("", 0, "", "", 0.0)

        args = shlex.split(command_line)
        if args and args[0] == "floatctl":
            args = args[1:]
        command_to_display = command_line if command_line else "<empty>"

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        exit_code = 0
        start = time.perf_counter()

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                self.cli_app.main(args=args, prog_name="floatctl", standalone_mode=False)
        except SystemExit as exc:
            if isinstance(exc.code, int):
                exit_code = exc.code
            elif exc.code is None:
                exit_code = 0
            else:
                exit_code = 1
        except Exception as exc:  # pragma: no cover - defensive logging
            exit_code = 1
            traceback.print_exception(exc.__class__, exc, exc.__traceback__, file=stderr_buffer)

        duration = time.perf_counter() - start
        return CommandResult(
            command=command_to_display,
            exit_code=exit_code,
            stdout=stdout_buffer.getvalue(),
            stderr=stderr_buffer.getvalue(),
            duration=duration,
        )


class SimpleAgentLoop:
    """Sequential automation loop that runs planned FloatCtl commands."""

    def __init__(self, invoker: FloatCtlInvoker, delay: float = 0.0) -> None:
        self.invoker = invoker
        self.delay = delay

    def run_commands(
        self,
        commands: Sequence[str],
        reporter: Optional[Callable[[AgentStep], None]] = None,
    ) -> List[AgentStep]:
        """Execute commands in order and optionally report each step."""

        steps: List[AgentStep] = []
        for raw_command in commands:
            command = self._normalise_command(raw_command)
            if not command:
                continue

            result = self.invoker.invoke(command)
            step = AgentStep(command=command, result=result)
            steps.append(step)

            if reporter:
                reporter(step)

            if self.delay:
                time.sleep(self.delay)

            if not result.success:
                break

        return steps

    def run_script(
        self,
        script: str,
        reporter: Optional[Callable[[AgentStep], None]] = None,
    ) -> List[AgentStep]:
        """Parse a multi-line script and execute it."""

        commands = [line for line in (line.strip() for line in script.splitlines()) if line and not line.startswith("#")]
        return self.run_commands(commands, reporter=reporter)

    @staticmethod
    def _normalise_command(command: str) -> str:
        """Return the command without redundant prefixes."""

        command = command.strip()
        if command.startswith("floatctl "):
            return command.split(" ", 1)[1]
        return command


class SimpleFloatCtlTUI:
    """Very small terminal UI for running FloatCtl commands interactively."""

    def __init__(
        self,
        invoker: Optional[FloatCtlInvoker] = None,
        agent_loop: Optional[SimpleAgentLoop] = None,
        history_limit: int = 12,
    ) -> None:
        self.console = Console()
        self.invoker = invoker or FloatCtlInvoker()
        self.agent_loop = agent_loop or SimpleAgentLoop(self.invoker)
        self.history: Deque[CommandResult] = deque(maxlen=history_limit)

    def run(self) -> None:
        """Start the interactive terminal UI."""

        self._render()
        while True:
            try:
                raw_command = self.console.input("[bold green]floatctl> [/bold green]").strip()
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[yellow]Session terminated.[/yellow]")
                break

            if not raw_command:
                continue

            if raw_command in {":q", "quit", "exit"}:
                break

            if raw_command in {":help", "help"}:
                self._show_help()
                continue

            if raw_command.startswith(":agent"):
                script = raw_command[len(":agent") :].strip()
                if not script:
                    script = self._collect_agent_script()
                self.console.print("[cyan]Running agent plan…[/cyan]")
                self.agent_loop.run_script(script, reporter=self._on_agent_step)
                self._render()
                continue

            result = self.invoker.invoke(raw_command)
            self.history.append(result)
            self._render()

        self.console.print("\n[green]Goodbye![/green]")

    def _on_agent_step(self, step: AgentStep) -> None:
        """Update UI when the agent completes a step."""

        self.history.append(step.result)
        self._render()
        status = "[green]success[/green]" if step.result.success else "[red]failed[/red]"
        self.console.print(f"[dim]agent[/dim] {step.command} → {status}")

    def _collect_agent_script(self) -> str:
        """Collect multi-line agent instructions from the user."""

        self.console.print("[dim]Enter commands for the agent (blank line to finish).[/dim]")
        lines: List[str] = []
        while True:
            try:
                line = self.console.input("[cyan]agent> [/cyan]")
            except (EOFError, KeyboardInterrupt):
                break
            if not line.strip():
                break
            lines.append(line)
        return "\n".join(lines)

    def _show_help(self) -> None:
        """Display inline usage instructions."""

        help_text = Text()
        help_text.append("Simple FloatCtl TUI\n", style="bold cyan")
        help_text.append("• Type FloatCtl subcommands just as you would in the shell.\n", style="dim")
        help_text.append("• Use ':agent' to run multiple commands automatically.\n", style="dim")
        help_text.append("• Type 'exit' to quit.\n", style="dim")
        self.console.print(Panel(help_text, border_style="cyan"))

    def _render(self) -> None:
        """Redraw the interface."""

        self.console.clear()
        self.console.print(self._build_header())
        self.console.print(self._build_history_panel())
        if self.history:
            self.console.print(self._build_output_panel(self.history[-1]))
        else:
            self.console.print(self._build_output_placeholder())

    def _build_header(self) -> Panel:
        """Create the header banner."""

        text = Text()
        text.append("🌲 FloatCtl Interactive Console\n", style="bold green")
        text.append("Enter ':help' for usage tips, ':agent' for automation.\n", style="dim")
        return Panel(Align.center(text), border_style="green")

    def _build_history_panel(self) -> Panel:
        """Render the history table."""

        table = Table(show_header=True, header_style="bold cyan", expand=True, box=box.ROUNDED)
        table.add_column("#", justify="right", style="dim", width=4)
        table.add_column("Command", style="white")
        table.add_column("Status", justify="center", style="magenta", width=10)
        table.add_column("Time", justify="right", style="green", width=8)

        for index, result in enumerate(self.history, start=1):
            status = "✅ ok" if result.success else f"❌ {result.exit_code}"
            table.add_row(str(index), result.command or "<empty>", status, f"{result.duration:.2f}s")

        return Panel(table, title="Command History", border_style="cyan")

    def _build_output_panel(self, result: CommandResult) -> Panel:
        """Create a panel showing the latest command output."""

        text = Text()
        if result.stdout:
            text.append("stdout\n", style="bold green")
            text.append(result.stdout.rstrip() or "<no output>")
        if result.stderr:
            if result.stdout:
                text.append("\n\n")
            text.append("stderr\n", style="bold red")
            text.append(result.stderr.rstrip())
        if not result.stdout and not result.stderr:
            text.append("<no output>", style="dim")

        title = f"Last Result — exit {result.exit_code}"
        return Panel(text, title=title, border_style="magenta")

    def _build_output_placeholder(self) -> Panel:
        """Placeholder panel when no commands have run yet."""

        text = Text("Run a command to see output here.", style="dim")
        return Panel(text, title="Last Result", border_style="magenta")


__all__ = [
    "CommandResult",
    "AgentStep",
    "FloatCtlInvoker",
    "SimpleAgentLoop",
    "SimpleFloatCtlTUI",
]
