"""Architecture and quality guards for the modular codebase."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDITED_MODULES = (
    "agent",
    "api",
    "core",
    "database",
    "eval",
    "generation",
    "memory",
    "retrieval",
    "scripts",
    "verification",
    "ui",
)
MAX_FUNCTION_LOGICAL_LINES = 20
LONG_FUNCTION_JUSTIFICATION = "QUALITY: long-function-justification"

FORBIDDEN_LAYER_IMPORTS = {
    "core": {"agent", "api", "database", "generation", "memory", "retrieval", "verification", "ui"},
    "database": {"agent", "api", "generation", "memory", "retrieval", "verification", "ui"},
    "generation": {"agent", "api", "database", "memory", "retrieval", "verification", "ui"},
    "memory": {"agent", "api", "database", "generation", "retrieval", "verification", "ui"},
    "retrieval": {"agent", "api", "database", "generation", "memory", "verification", "ui"},
    "verification": {"agent", "api", "database", "memory", "retrieval", "ui"},
}


def _python_files() -> list[Path]:
    return [
        path
        for module_name in AUDITED_MODULES
        for path in (PROJECT_ROOT / module_name).rglob("*.py")
    ]


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _logical_body_lines(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    docstring_node = node.body[0] if node.body and isinstance(node.body[0], ast.Expr) else None
    ignored_lines = set()
    if (
        docstring_node is not None
        and isinstance(docstring_node.value, ast.Constant)
        and isinstance(docstring_node.value.value, str)
    ):
        ignored_lines.update(range(docstring_node.lineno, docstring_node.end_lineno + 1))

    logical_lines = {
        child.lineno
        for child in ast.walk(node)
        if hasattr(child, "lineno")
        and child.lineno not in ignored_lines
        and child.lineno != node.lineno
    }
    return len(logical_lines)


def _has_long_function_justification(
    path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> bool:
    if node.end_lineno is None:
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    body_text = "\n".join(lines[node.lineno - 1 : node.end_lineno])
    return LONG_FUNCTION_JUSTIFICATION in body_text


def test_audited_functions_over_20_logical_lines_are_justified() -> None:
    violations: list[str] = []
    for path in _python_files():
        for node in ast.walk(_parse(path)):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            logical_lines = _logical_body_lines(node)
            if logical_lines <= MAX_FUNCTION_LOGICAL_LINES:
                continue
            if _has_long_function_justification(path, node):
                continue
            relative_path = path.relative_to(PROJECT_ROOT)
            violations.append(f"{relative_path}:{node.lineno} {node.name} ({logical_lines})")

    assert not violations, (
        "Functions over 20 logical lines need explicit justification:\n" + "\n".join(violations)
    )


def test_core_and_service_layers_do_not_import_outer_layers() -> None:
    violations: list[str] = []
    for path in _python_files():
        layer = path.relative_to(PROJECT_ROOT).parts[0]
        forbidden = FORBIDDEN_LAYER_IMPORTS.get(layer, set())
        if not forbidden:
            continue
        for node in ast.walk(_parse(path)):
            imported_module: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_module = alias.name.split(".")[0]
                    if imported_module in forbidden:
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)} imports {imported_module}"
                        )
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_module = node.module.split(".")[0]
                if imported_module in forbidden:
                    violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {imported_module}")

    assert not sorted(set(violations))
