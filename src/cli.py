import sys
import logging
from pathlib import Path
import click
import tiktoken
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.parser import find_files
from src.pruner import prune_code_string
from src.graph import build_dependency_graph, topological_sort
from src.utils import fix_windows_encoding, setup_logging

fix_windows_encoding()
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("corecontext")


def count_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text, disallowed_special=()))
    except Exception:
        return len(text.split()) * 4 // 3


def generate_markdown_tree(base_dir: Path, files: list[Path]) -> str:
    tree: dict = {}
    for file in files:
        try:
            rel_path = file.resolve().relative_to(base_dir.resolve())
            parts = rel_path.parts
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        except Exception:
            pass
            
    lines = ["."]
    
    def format_tree(node: dict, prefix: str = "") -> None:
        sorted_keys = sorted(node.keys(), key=lambda k: (len(node[k]) == 0, k.lower()))
        for i, key in enumerate(sorted_keys):
            is_last = (i == len(sorted_keys) - 1)
            connector = "└── " if is_last else "├── "
            is_dir = len(node[key]) > 0
            name = f"{key}/" if is_dir else key
            lines.append(f"{prefix}{connector}{name}")
            if is_dir:
                new_prefix = prefix + ("    " if is_last else "│   ")
                format_tree(node[key], new_prefix)
                
    format_tree(tree)
    return "\n".join(lines)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--dir", "directory", default=".", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option("--output", default="context.md", type=click.Path(path_type=Path))
@click.option("--critical", multiple=True)
@click.option("--keep-init/--prune-init", default=True)
@click.option("--no-strip-logging", is_flag=True)
@click.option("--strip-print", is_flag=True)
@click.option("--no-optimize-imports", is_flag=True)
@click.option("--exclude", multiple=True)
def prune(
    directory: Path,
    output: Path,
    critical: tuple[str, ...],
    keep_init: bool,
    no_strip_logging: bool,
    strip_print: bool,
    no_optimize_imports: bool,
    exclude: tuple[str, ...]
) -> None:
    console = Console()
    base_dir = directory.resolve()
    critical_funcs = set(critical)
    
    console.print(f"[cyan]Scanning:[/cyan] {base_dir}")
    
    try:
        all_files = find_files(base_dir, extra_excludes=list(exclude))
    except Exception as e:
        console.print(f"[bold red]Error listing files:[/bold red] {e}")
        return

    py_files = [f for f in all_files if f.suffix.lower() == ".py"]
    if not py_files:
        console.print("[yellow]No Python files found.[/yellow]")
        return
        
    console.print(f"[green]Found {len(py_files)} Python files. Building graph...[/green]")
    
    dep_map = build_dependency_graph(py_files, base_dir)
    sorted_files = topological_sort(py_files, dep_map)
    
    stats: list[dict] = []
    pruned_contents: dict[Path, str] = {}
    total_before = 0
    total_after = 0
    
    with console.status("[bold blue]Processing ASTs..."):
        for file in sorted_files:
            rel_path = file.resolve().relative_to(base_dir)
            try:
                with open(file, "r", encoding="utf-8") as f:
                    code = f.read()
                    
                before = count_tokens(code)
                pruned = prune_code_string(
                    code,
                    critical_functions=critical_funcs,
                    keep_init=keep_init,
                    strip_logging=not no_strip_logging,
                    strip_print=strip_print,
                    optimize_imports=not no_optimize_imports,
                    filename=str(file)
                )
                after = count_tokens(pruned)
                
                total_before += before
                total_after += after
                savings = before - after
                pct = (savings / before * 100) if before > 0 else 0
                
                stats.append({
                    "file": str(rel_path.as_posix()),
                    "before": before,
                    "after": after,
                    "savings": savings,
                    "pct": pct
                })
                pruned_contents[file] = pruned
                
            except Exception as e:
                logger.warning(f"Unparsed/corrupted file {file}: {e}")
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        fallback = f.read()
                except Exception:
                    fallback = f"# Error reading {rel_path}"
                
                tokens = count_tokens(fallback)
                total_before += tokens
                total_after += tokens
                
                stats.append({
                    "file": str(rel_path.as_posix()),
                    "before": tokens,
                    "after": tokens,
                    "savings": 0,
                    "pct": 0.0,
                    "warning": str(e)
                })
                pruned_contents[file] = fallback

    tree_md = generate_markdown_tree(base_dir, sorted_files)
    out_lines = [
        "# Codebase Context",
        "\nGenerated by CoreContext.\n",
        "## Directory Tree",
        "```text",
        tree_md,
        "```",
        "\n## Code Repository Files\n"
    ]
    
    for file in sorted_files:
        rel = file.resolve().relative_to(base_dir).as_posix()
        out_lines.append(f"### File: `{rel}`")
        out_lines.append("```python")
        out_lines.append(pruned_contents[file])
        out_lines.append("```\n")
        
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
        console.print(f"\n[bold green]Wrote context: {output.resolve()}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error writing {output}: {e}[/bold red]")
        return

    table = Table(title="Pruning Summary", show_header=True, header_style="bold magenta")
    table.add_column("File", style="dim")
    table.add_column("Original", justify="right")
    table.add_column("Pruned", justify="right")
    table.add_column("Saved", justify="right", style="cyan")
    table.add_column("Reduction %", justify="right", style="green")
    
    for s in stats:
        warn = " (Warning)" if "warning" in s else ""
        table.add_row(
            s["file"] + warn,
            f"{s['before']:,}",
            f"{s['after']:,}",
            f"{s['savings']:,}",
            f"{s['pct']:.1f}%"
        )
    console.print(table)
    
    total_savings = total_before - total_after
    total_pct = (total_savings / total_before * 100) if total_before > 0 else 0
    
    bar_width = 40
    filled = int(round(total_pct / 100 * bar_width))
    empty = bar_width - filled
    bar_str = f"[green]{'█' * filled}[/green][grey37]{'░' * empty}[/grey37]"
    
    summary = (
        f"Files: [bold]{len(py_files)}[/bold]\n"
        f"Original: [bold red]{total_before:,}[/bold red] tokens\n"
        f"Pruned:   [bold green]{total_after:,}[/bold green] tokens\n"
        f"Saved:    [bold yellow]{total_savings:,}[/bold yellow] tokens ([bold green]{total_pct:.1f}%[/bold green])\n\n"
        f"Progress:\n"
        f"{bar_str} [bold green]{total_pct:.1f}%[/bold green]"
    )
    
    panel = Panel(
        summary,
        title="[bold green]CoreContext Stats[/bold green]",
        border_style="green",
        expand=False
    )
    console.print(panel)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

