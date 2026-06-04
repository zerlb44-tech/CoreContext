import ast
import os
import logging
from pathlib import Path
from typing import Optional
import pathspec

logger = logging.getLogger("corecontext.parser")


class ParserError(Exception):
    pass


def load_gitignore(base_dir: Path) -> Optional[pathspec.PathSpec]:
    gi_path = base_dir / ".gitignore"
    if gi_path.exists() and gi_path.is_file():
        try:
            with open(gi_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            cleaned = [l for l in lines if l.strip() and not l.strip().startswith("#")]
            return pathspec.PathSpec.from_lines("gitignore", cleaned)
        except Exception as e:
            logger.warning(f"Failed to read .gitignore at {gi_path}: {e}")
    return None


def find_files(base_dir: Path, extra_excludes: Optional[list[str]] = None) -> list[Path]:
    spec = load_gitignore(base_dir)
    extra_spec = pathspec.PathSpec.from_lines("gitignore", extra_excludes) if extra_excludes else None
    
    default_ignores = {
        ".git", "__pycache__", ".venv", "venv", "node_modules", 
        ".idea", ".vscode", ".poetry", "dist", "build", "eggs", 
        "*.egg-info", ".mypy_cache", ".pytest_cache", ".tox"
    }
    
    found = []
    resolved_base = base_dir.resolve()
    
    for root, dirs, files in os.walk(resolved_base):
        root_path = Path(root)
        
        pruned_dirs = []
        for d in dirs:
            dir_path = root_path / d
            rel_path = str(dir_path.relative_to(resolved_base).as_posix()) + "/"
            
            is_default = d in default_ignores
            is_git = spec.match_file(rel_path) if spec else False
            is_extra = extra_spec.match_file(rel_path) if extra_spec else False
            
            if not (is_default or is_git or is_extra):
                pruned_dirs.append(d)
        
        dirs[:] = pruned_dirs
        
        for f in files:
            file_path = root_path / f
            rel_path = str(file_path.relative_to(resolved_base).as_posix())
            
            is_git = spec.match_file(rel_path) if spec else False
            is_extra = extra_spec.match_file(rel_path) if extra_spec else False
            
            is_default = any(
                part in default_ignores or part.endswith(".pyc") or part.endswith(".pyo")
                for part in file_path.relative_to(resolved_base).parts
            )
            
            if not (is_default or is_git or is_extra):
                found.append(file_path)
                
    return found


def parse_python_file(filepath: Path) -> ast.AST:
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return ast.parse(f.read(), filename=str(filepath))
        except SyntaxError as e:
            raise ParserError(f"Syntax error in {filepath}: {e}") from e
        except Exception as e:
            raise ParserError(f"Parse failed in {filepath}: {e}") from e


def parse_file(filepath: Path) -> ast.AST:
    ext = filepath.suffix.lower()
    if ext == ".py":
        return parse_python_file(filepath)
    raise NotImplementedError(f"No AST parser for '{ext}'")

