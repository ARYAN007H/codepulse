"""CodePulse CLI — the main entry point.

Usage:
    codepulse                          # analyze current directory
    codepulse --path /path/to/repo     # analyze a specific repo
    codepulse --ext py --ext ts        # filter by extension
    codepulse --depth 500              # more git history
    codepulse --no-git                 # skip git analysis
    codepulse --open                   # open report in browser
"""

from __future__ import annotations

import logging
import sys
import webbrowser
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from codepulse import __version__
from codepulse.analyzer import analyze_file
from codepulse.git_stats import get_churn, get_repo_name, init_repo
from codepulse.reporter import generate_report
from codepulse.scorer import compute_scores, generate_insights

app = typer.Typer(
    name="codepulse",
    help="🔬 X-ray your codebase — interactive complexity heatmaps for any Git repo.",
    add_completion=False,
    no_args_is_help=False,
)

console = Console()
logger = logging.getLogger(__name__)

# ── Supported extensions ──
DEFAULT_EXTENSIONS = {"py"}


def _discover_files(root: Path, extensions: set[str]) -> list[Path]:
    """Recursively find source files matching the given extensions."""
    files = []
    for ext in extensions:
        files.extend(root.rglob(f"*.{ext}"))
    # Filter out hidden dirs, __pycache__, node_modules, .git, venvs
    skip_dirs = {
        ".git", "__pycache__", "node_modules", ".venv", "venv",
        ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
        ".eggs", "*.egg-info", ".hg", ".svn",
    }
    filtered = []
    for f in files:
        parts = f.relative_to(root).parts
        if any(p.startswith(".") or p in skip_dirs for p in parts[:-1]):
            continue
        if f.is_file():
            filtered.append(f)
    return sorted(filtered)


def _risk_style(risk: float) -> str:
    """Return a Rich color string for a risk score."""
    if risk <= 30:
        return "green"
    elif risk <= 60:
        return "yellow"
    elif risk <= 80:
        return "red"
    return "bold red"


def _risk_emoji(tier: str) -> str:
    """Return an emoji for a risk tier."""
    return {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "💀"}.get(tier, "⚪")


def _mi_display(grade: str) -> Text:
    """Format MI grade with color."""
    colors = {"good": "green", "moderate": "yellow", "poor": "red"}
    labels = {"good": "Good", "moderate": "Mod.", "poor": "Poor"}
    return Text(labels.get(grade, grade), style=colors.get(grade, "white"))


def _cc_style(grade: str) -> str:
    """Return a Rich color for a CC grade."""
    return {
        "A": "green", "B": "cyan", "C": "yellow",
        "D": "dark_orange", "E": "red", "F": "bold red",
    }.get(grade, "white")


@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Option(
        ".", "--path", "-p",
        help="Path to the repository to analyze.",
    ),
    ext: Optional[list[str]] = typer.Option(
        None, "--ext", "-e",
        help="File extensions to analyze (e.g., py, ts, js). Default: py.",
    ),
    depth: int = typer.Option(
        200, "--depth", "-d",
        help="Number of recent git commits to consider for churn.",
    ),
    output: str = typer.Option(
        "codepulse-report.html", "--output", "-o",
        help="Output path for the HTML report.",
    ),
    no_git: bool = typer.Option(
        False, "--no-git",
        help="Skip git churn analysis (useful for non-git directories).",
    ),
    no_terminal_summary: bool = typer.Option(
        False, "--no-terminal-summary",
        help="Suppress the terminal summary table.",
    ),
    open_report: bool = typer.Option(
        False, "--open",
        help="Open the HTML report in your default browser after generation.",
    ),
    version: bool = typer.Option(
        False, "--version", "-v",
        help="Show version and exit.",
        is_eager=True,
    ),
) -> None:
    """Analyze a codebase and generate an interactive complexity heatmap."""
    if version:
        console.print(f"[cyan]codepulse[/] v{__version__}")
        raise typer.Exit()

    repo_path = Path(path).resolve()
    if not repo_path.exists():
        console.print(f"[red]Error:[/] Path does not exist: {repo_path}")
        raise typer.Exit(code=1)

    extensions = set(ext) if ext else DEFAULT_EXTENSIONS

    # ── Banner ──
    console.print()
    console.print(
        Panel(
            "[bold cyan]CodePulse[/bold cyan] [dim]— X-ray your codebase[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()

    # ── Discover files ──
    with console.status("[cyan]Discovering files...[/]"):
        files = _discover_files(repo_path, extensions)

    if not files:
        console.print(
            f"[yellow]No files found[/] matching extensions: "
            f"{', '.join(f'.{e}' for e in extensions)}\n"
            f"[dim]Try: codepulse --ext py --ext js --ext ts[/dim]"
        )
        raise typer.Exit(code=1)

    console.print(
        f"  [dim]Found[/] [bold]{len(files)}[/bold] [dim]files matching[/] "
        f"{', '.join(f'[cyan].{e}[/]' for e in extensions)}"
    )

    # ── Git setup ──
    use_git = not no_git
    repo = None
    repo_name = repo_path.name

    if use_git:
        repo = init_repo(repo_path)
        if repo is None:
            console.print(
                "[yellow]⚠ Not a git repository[/] — churn metrics will be skipped.\n"
                "[dim]Use --no-git to suppress this warning.[/dim]"
            )
            use_git = False
        else:
            repo_name = get_repo_name(repo)

    # ── Analyze files ──
    file_metrics_list = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Analyzing[/]"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TextColumn("•"),
        TextColumn("[dim]{task.fields[current_file]}[/dim]"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "analyze", total=len(files), current_file=""
        )
        for filepath in files:
            rel = str(filepath.relative_to(repo_path))
            progress.update(task, current_file=rel)
            metrics = analyze_file(filepath, repo_root=repo_path)
            if metrics is not None:
                file_metrics_list.append(metrics.to_dict())
            progress.advance(task)

    if not file_metrics_list:
        console.print("[yellow]No files could be analyzed.[/]")
        raise typer.Exit(code=1)

    # ── Git churn ──
    churn_stats: dict[str, dict] = {}
    if use_git and repo:
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Git history[/]"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TextColumn("[dim]{task.fields[current_file]}[/dim]"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "churn", total=len(file_metrics_list), current_file=""
            )
            for fm in file_metrics_list:
                progress.update(task, current_file=fm["path"])
                churn = get_churn(repo, fm["path"], depth=depth)
                churn_stats[fm["path"]] = churn.to_dict()
                progress.advance(task)

    # ── Score ──
    scored = compute_scores(file_metrics_list, churn_stats, use_git=use_git)
    insights = generate_insights(scored, use_git=use_git)

    # ── Terminal summary ──
    if not no_terminal_summary:
        _print_summary(scored, repo_name, use_git)

    # ── Generate report ──
    scored_data = [s.to_dict() for s in scored]
    report_path = generate_report(
        scored_data=scored_data,
        insights=insights,
        repo_name=repo_name,
        output_path=Path(output),
        use_git=use_git,
    )

    console.print()
    console.print(f"  [green]✓[/] Report saved → [bold cyan]{report_path}[/]")
    console.print()

    if open_report:
        webbrowser.open(f"file://{report_path}")


def _print_summary(scored: list, repo_name: str, use_git: bool) -> None:
    """Print a Rich summary panel and top-10 table to the terminal."""
    total = len(scored)
    hotspots = sum(1 for s in scored if s.risk_tier in ("high", "critical"))
    riskiest = scored[0] if scored else None
    avg_risk = sum(s.risk_score for s in scored) / total if total else 0

    # Summary panel
    lines = [
        f"  📁 Repo:       [bold]{repo_name}[/bold]",
        f"  🐍 Files:      [bold]{total}[/bold] files analyzed",
        f"  ⚠️  Hotspots:   [bold {'red' if hotspots > 0 else 'green'}]{hotspots}[/] "
        f"{'critical files found' if hotspots else 'none — looking clean!'}",
    ]
    if riskiest:
        style = _risk_style(riskiest.risk_score)
        lines.append(
            f"  💀 Riskiest:   [bold]{riskiest.path}[/]  "
            f"[{style}][Risk: {riskiest.risk_score}/100][/]"
        )
    lines.append(f"  📊 Avg Risk:   [bold]{avg_risk:.1f}[/]/100")

    console.print()
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold cyan]CodePulse Report[/]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # Top 10 table
    show_count = min(10, total)
    table = Table(
        title=f"\n  Top {show_count} Riskiest Files",
        show_header=True,
        header_style="bold",
        border_style="dim",
        pad_edge=True,
        expand=True,
    )
    table.add_column("File", style="bold", no_wrap=True, ratio=4)
    table.add_column("Risk", justify="center", width=6)
    table.add_column("CC", justify="center", width=5)
    table.add_column("MI", justify="center", width=8)
    if use_git:
        table.add_column("Churn", justify="center", width=7)
        table.add_column("Last Touch", justify="center", width=12)
    table.add_column("LOC", justify="right", width=6)

    for s in scored[:show_count]:
        emoji = _risk_emoji(s.risk_tier)
        risk_text = Text(str(int(s.risk_score)), style=_risk_style(s.risk_score))
        cc_text = Text(s.cc_grade, style=_cc_style(s.cc_grade))
        mi_text = _mi_display(s.mi_grade)

        row = [
            f"{emoji} {s.path}",
            risk_text,
            cc_text,
            mi_text,
        ]
        if use_git:
            row.append(str(s.commit_count))
            row.append(s.last_modified_human)
        row.append(str(s.loc))
        table.add_row(*row)

    console.print(table)


if __name__ == "__main__":
    app()

