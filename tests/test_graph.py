import pytest
from pathlib import Path
from src.graph import (
    resolve_module_to_path,
    build_dependency_graph,
    topological_sort,
    DependencyVisitor,
)


def test_resolve_module_to_path_simple(tmp_path):
    # For level=0 (absolute imports), module "utils" -> tmp_path/utils.py
    (tmp_path / "utils.py").write_text("x = 1")
    
    current_file = tmp_path / "main.py"
    resolved = resolve_module_to_path("utils", current_file, tmp_path, level=0)
    
    assert resolved is not None
    assert resolved.name == "utils.py"


def test_resolve_module_to_path_relative(tmp_path):
    # For relative imports (level > 0)
    utils_dir = tmp_path / "utils"
    utils_dir.mkdir()
    (utils_dir / "__init__.py").write_text("")
    (utils_dir / "helpers.py").write_text("x = 1")
    
    current_file = tmp_path / "main.py"
    resolved = resolve_module_to_path("utils", current_file, tmp_path, level=0)
    
    assert resolved is not None
    assert resolved.name == "__init__.py"


def test_resolve_module_to_path_not_found(tmp_path):
    current_file = tmp_path / "main.py"
    resolved = resolve_module_to_path("nonexistent", current_file, tmp_path, level=0)
    assert resolved is None


def test_build_dependency_graph(tmp_path):
    (tmp_path / "a.py").write_text("import b")
    (tmp_path / "b.py").write_text("import c")
    (tmp_path / "c.py").write_text("x = 1")
    
    files = [tmp_path / f for f in ["a.py", "b.py", "c.py"]]
    graph = build_dependency_graph(files, tmp_path)
    
    assert graph is not None
    assert len(graph) == 3


def test_topological_sort(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    (tmp_path / "b.py").write_text("import a")
    (tmp_path / "c.py").write_text("import b")
    
    files = [tmp_path / f for f in ["a.py", "b.py", "c.py"]]
    graph = build_dependency_graph(files, tmp_path)
    sorted_files = topological_sort(files, graph)
    
    assert len(sorted_files) == 3
    # a should come before b, b before c
    idx_a = next(i for i, f in enumerate(sorted_files) if f.name == "a.py")
    idx_b = next(i for i, f in enumerate(sorted_files) if f.name == "b.py")
    idx_c = next(i for i, f in enumerate(sorted_files) if f.name == "c.py")
    
    assert idx_a < idx_b < idx_c

