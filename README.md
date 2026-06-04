# CoreContext

[![Tests](https://img.shields.io/badge/tests-17%20passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![Token Savings](https://img.shields.io/badge/token%20savings-82.7%25-green)]()

AST-based token pruner for generating minimal LLM context files. Takes a codebase, analyzes import dependencies, and creates a compressed `.md` file with only the code needed for understanding.

## Features

- **Smart import analysis** — topological sort to include only necessary files
- **Docstring stripping** — removes module, class, and function docstrings
- **Logging removal** — strips `logger.*()` and `logging.*()` calls
- **Function body pruning** — replaces non-critical function bodies with `...`
- **Import optimization** — keeps only imports that are actually used
- **Token counting** — shows original vs. pruned token counts with % savings
- **Rich terminal output** — colored tables, progress bars, summary card
- **Respects .gitignore** — excludes files according to your project rules

## Install

```bash
pip install -e .
```

## Quick Start

```bash
corecontext prune --dir . --output context.md
```

This scans the current directory, builds a dependency graph, and writes `context.md` with pruned Python files.

## Options

```
--dir DIR                  Root directory to scan (default: .)
--output PATH              Output markdown file (default: context.md)
--critical FUNC            Keep function body intact (can repeat)
--keep-init/--prune-init   Keep or prune __init__ bodies (default: keep)
--no-strip-logging         Don't remove logging calls
--strip-print              Also remove print() statements
--no-optimize-imports      Keep all imports
--exclude PATTERN          Additional patterns to exclude (can repeat)
```

### Examples

```bash
# Generate context for current project
corecontext prune --dir .

# Keep specific functions intact
corecontext prune --dir . --critical main --critical setup

# Also strip print() calls
corecontext prune --dir . --strip-print

# Exclude additional directories
corecontext prune --dir . --exclude docs/ --exclude tests/
```

## How It Works

1. **File Discovery** — Recursively walks directory, respects .gitignore and default excludes
2. **Dependency Graph** — Parses import statements (regular + relative) to build file dependencies
3. **Topological Sort** — Orders files so dependencies come before dependents
4. **AST Pruning** — For each file in order:
   - Strip docstrings (module, class, function)
   - Remove logging statements
   - Replace non-critical function bodies with `...`
   - Remove unused imports
5. **Markdown Output** — Generates directory tree + annotated code sections

## Test Coverage

```bash
PYTHONPATH=. pytest -v
```

All 17 tests passing:
- Parser: gitignore loading, file discovery, syntax error handling
- Pruner: docstring removal, logging stripping, body pruning, import optimization
- Graph: module resolution, dependency graphs, topological sorting

## Real-World Metrics

Example run on a 10-file project:

```
Files: 10
Original: 7,541 tokens
Pruned:   1,307 tokens
Saved:    6,234 tokens (82.7%)
```

Per-file reduction:
- graph.py: 80.0%
- parser.py: 85.0%
- cli.py: 85.4%
- test files: 90-94%

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.

## License

MIT — see [LICENSE](LICENSE)


