import ast
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("corecontext.graph")


def resolve_module_to_path(
    module_name: str, 
    current_file: Path, 
    base_dir: Path, 
    level: int = 0
) -> Optional[Path]:
    base_resolved = base_dir.resolve()
    current_resolved = current_file.resolve()
    
    if level > 0:
        target_dir = current_resolved.parent
        for _ in range(level - 1):
            target_dir = target_dir.parent
            
        if module_name:
            parts = module_name.split(".")
            target_path = target_dir.joinpath(*parts)
        else:
            target_path = target_dir
    else:
        if not module_name:
            return None
        parts = module_name.split(".")
        target_path = base_resolved.joinpath(*parts)

    py_file = target_path.with_suffix(".py")
    init_file = target_path / "__init__.py"

    if py_file.exists() and py_file.is_file():
        return py_file.resolve()
    if init_file.exists() and init_file.is_file():
        return init_file.resolve()
        
    return None


class DependencyVisitor(ast.NodeVisitor):
    def __init__(self, current_file: Path, base_dir: Path):
        self.current_file = current_file
        self.base_dir = base_dir
        self.dependencies = set()

    def visit_Import(self, node):
        for alias in node.names:
            path = resolve_module_to_path(alias.name, self.current_file, self.base_dir, level=0)
            if path:
                self.dependencies.add(path)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        path = resolve_module_to_path(node.module or "", self.current_file, self.base_dir, level=node.level)
        if path:
            self.dependencies.add(path)
            
        if node.module:
            for alias in node.names:
                full_module = f"{node.module}.{alias.name}"
                path = resolve_module_to_path(full_module, self.current_file, self.base_dir, level=node.level)
                if path:
                    self.dependencies.add(path)
        else:
            for alias in node.names:
                path = resolve_module_to_path(alias.name, self.current_file, self.base_dir, level=node.level)
                if path:
                    self.dependencies.add(path)
                    
        self.generic_visit(node)


def build_dependency_graph(files: list[Path], base_dir: Path) -> dict[Path, set[Path]]:
    dep_map = {}
    file_set = {f.resolve() for f in files}
    
    for file in files:
        resolved_file = file.resolve()
        dep_map[resolved_file] = set()
        
        try:
            with open(resolved_file, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(resolved_file))
            
            visitor = DependencyVisitor(resolved_file, base_dir)
            visitor.visit(tree)
            
            filtered = {dep for dep in visitor.dependencies if dep in file_set}
            dep_map[resolved_file] = filtered
            
        except Exception as e:
            logger.warning(f"Failed to analyze imports for {file}: {e}")
            
    return dep_map


def topological_sort(files: list[Path], dependency_map: dict[Path, set[Path]]) -> list[Path]:
    visited = {f.resolve(): 0 for f in files}
    ordered = []
    file_set = {f.resolve() for f in files}

    def dfs(node: Path):
        node_resolved = node.resolve()
        if visited.get(node_resolved, 0) == 1:
            return
        if visited.get(node_resolved, 0) == 2:
            return

        visited[node_resolved] = 1
        
        deps = dependency_map.get(node_resolved, set())
        for dep in sorted(deps):
            dep_resolved = dep.resolve()
            if dep_resolved in file_set:
                dfs(dep_resolved)

        visited[node_resolved] = 2
        ordered.append(node)

    for file in sorted(files, key=lambda p: str(p.as_posix())):
        file_resolved = file.resolve()
        if visited.get(file_resolved, 0) == 0:
            dfs(file_resolved)

    return ordered

