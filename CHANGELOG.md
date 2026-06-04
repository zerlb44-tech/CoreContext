# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-06-04

### Added
- Initial release of CoreContext
- AST-based code pruning for LLM context generation
- Docstring stripping (module, class, function)
- Logging call removal (logger.*, print)
- Function body pruning for non-critical functions
- Import optimization (unused import detection)
- Dependency graph building and topological sorting
- Token counting with tiktoken
- Rich terminal output (tables, progress bars, summary card)
- .gitignore respect for file discovery
- Full pytest test coverage (17 tests)
- CLI with multiple options (--critical, --exclude, etc.)

### Fixed
- Bare except clauses now properly catch Exception
- Type hints added to all public functions
- Error handling for file I/O operations
- UTF-8 encoding on Windows systems
- Parser error reporting with specific exception types

### Features
- Windows UTF-8 auto-reconfiguration
- Topological file ordering by dependency
- Relative import resolution
- Graceful fallback on unparsable files
- Token savings reporting (typically 80-95%)
