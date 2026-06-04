import ast
import logging
from typing import Optional

logger = logging.getLogger("corecontext.pruner")


class DocstringStripper(ast.NodeTransformer):
    def _remove_docstring(self, node):
        if not hasattr(node, "body") or not node.body:
            return
        first = node.body[0]
        if (
            isinstance(first, ast.Expr) and 
            isinstance(first.value, ast.Constant) and 
            isinstance(first.value.value, str)
        ):
            node.body.pop(0)

    def visit_Module(self, node):
        self._remove_docstring(node)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        self._remove_docstring(node)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self._remove_docstring(node)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        self._remove_docstring(node)
        self.generic_visit(node)
        return node


class LoggingStripper(ast.NodeTransformer):
    def __init__(self, strip_print: bool = False):
        self.strip_print = strip_print
        
    def _is_logger_call(self, node) -> bool:
        if not isinstance(node, ast.Expr):
            return False
        call = node.value
        if not isinstance(call, ast.Call):
            return False
        
        func = call.func
        if isinstance(func, ast.Attribute):
            methods = {"debug", "info", "warning", "warn", "error", "critical", "exception", "log"}
            if func.attr in methods:
                caller = self._resolve_name(func.value)
                if caller:
                    caller_lower = caller.lower()
                    if (
                        caller_lower in {"logging", "logger", "log", "self.logger", "self.log"} or
                        caller_lower.endswith("logger") or 
                        caller_lower.endswith("log")
                    ):
                        return True
                        
        elif isinstance(func, ast.Name):
            if func.id == "print" and self.strip_print:
                return True
        return False

    def _resolve_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = self._resolve_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        return None

    def visit_Expr(self, node):
        if self._is_logger_call(node):
            return None
        return self.generic_visit(node)


class BodyPruner(ast.NodeTransformer):
    def __init__(self, critical_funcs: Optional[set[str]] = None, keep_init: bool = True):
        self.critical = critical_funcs or set()
        self.keep_init = keep_init

    def visit_FunctionDef(self, node):
        if node.name in self.critical or (self.keep_init and node.name == "__init__"):
            self.generic_visit(node)
            return node
        node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
        return node

    def visit_AsyncFunctionDef(self, node):
        if node.name in self.critical:
            self.generic_visit(node)
            return node
        node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
        return node


class ImportCollector(ast.NodeVisitor):
    def __init__(self):
        self.imported_names = set()

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            if not alias.asname and "." in name:
                name = name.split(".")[0]
            self.imported_names.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported_names.add(name)
        self.generic_visit(node)


class ReferencedNameFinder(ast.NodeVisitor):
    def __init__(self, imported_names: set[str]):
        self.imported = imported_names
        self.referenced = set()

    def visit_Import(self, node):
        pass

    def visit_ImportFrom(self, node):
        pass

    def visit_Name(self, node):
        self.referenced.add(node.id)
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            for name in self.imported:
                if name == node.value or f"'{name}'" in node.value or f'"{name}"' in node.value:
                    self.referenced.add(name)
        self.generic_visit(node)


class ImportOptimizer(ast.NodeTransformer):
    def __init__(self, referenced_names: set[str]):
        self.referenced = referenced_names

    def visit_Import(self, node):
        new_names = []
        for alias in node.names:
            bound = alias.asname or alias.name
            if not alias.asname and "." in bound:
                bound = bound.split(".")[0]
            if bound in self.referenced:
                new_names.append(alias)
        if not new_names:
            return None
        node.names = new_names
        return node

    def visit_ImportFrom(self, node):
        if len(node.names) == 1 and node.names[0].name == "*":
            return node
        new_names = [alias for alias in node.names if (alias.asname or alias.name) in self.referenced]
        if not new_names:
            return None
        node.names = new_names
        return node


def prune_ast(
    tree: ast.AST,
    critical_funcs: Optional[set[str]] = None,
    keep_init: bool = True,
    strip_logging: bool = True,
    strip_print: bool = False,
    optimize_imports: bool = True
) -> ast.AST:
    tree = DocstringStripper().visit(tree)
    if strip_logging:
        tree = LoggingStripper(strip_print=strip_print).visit(tree)
    tree = BodyPruner(critical_funcs=critical_funcs, keep_init=keep_init).visit(tree)
    if optimize_imports:
        collector = ImportCollector()
        collector.visit(tree)
        
        finder = ReferencedNameFinder(collector.imported_names)
        finder.visit(tree)
        
        tree = ImportOptimizer(finder.referenced).visit(tree)
        
    ast.fix_missing_locations(tree)
    return tree


def prune_code_string(
    code: str,
    critical_functions: Optional[set[str]] = None,
    keep_init: bool = True,
    strip_logging: bool = True,
    strip_print: bool = False,
    optimize_imports: bool = True,
    filename: str = "<string>"
) -> str:
    try:
        tree = ast.parse(code, filename=filename)
        pruned = prune_ast(
            tree,
            critical_funcs=critical_functions,
            keep_init=keep_init,
            strip_logging=strip_logging,
            strip_print=strip_print,
            optimize_imports=optimize_imports
        )
        return ast.unparse(pruned)
    except Exception as e:
        logger.error(f"Error pruning {filename}: {e}")
        raise

