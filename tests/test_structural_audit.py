"""Structural guards for the documented modular MVP layout."""

from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENTED_MODULE_FILES = {
    "agent": {
        "__init__.py",
        "factory.py",
        "intent.py",
        "prompt.py",
        "runner.py",
        "tools.py",
    },
    "api": {
        "__init__.py",
        "dependencies.py",
        "main.py",
        "routes/__init__.py",
        "routes/auth.py",
        "routes/chat.py",
        "routes/conversations.py",
        "routes/health.py",
    },
    "core": {
        "__init__.py",
        "config.py",
        "embeddings.py",
        "ollama_clients.py",
        "schemas.py",
    },
    "database": {
        "__init__.py",
        "db.py",
        "models.py",
        "semantic_chunker.py",
    },
    "eval": {
        "__init__.py",
        "_utils.py",
        "collect_references.py",
        "generate_charts.py",
        "generate_questions.py",
        "judge.py",
        "report.py",
        "run_evaluation.py",
        "run_experimental_evaluation.py",
    },
    "generation": {"__init__.py", "llm.py"},
    "memory": {"__init__.py", "conversation.py"},
    "retrieval": {
        "__init__.py",
        "embedder.py",
        "ollama_embeddings.py",
        "vector_store.py",
    },
    "scripts": {"ingest.py"},
    "tests": {"conftest.py"},
    "ui": {"__init__.py", "chat_ui.py"},
    "verification": {"__init__.py", "entropy.py", "gate.py"},
}


def _git_check_ignore(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
    )
    return result.returncode == 0


def test_documented_mvp_module_core_files_exist() -> None:
    missing: list[str] = []
    for module_name, expected_files in DOCUMENTED_MODULE_FILES.items():
        module_path = PROJECT_ROOT / module_name
        if not module_path.is_dir():
            missing.append(module_name)
            continue

        for relative_file in expected_files:
            expected_path = module_path / relative_file
            if not expected_path.is_file():
                missing.append(f"{module_name}/{relative_file}")

    assert not missing


def test_out_of_scope_and_runtime_directories_are_git_ignored() -> None:
    paths_that_must_be_ignored = (
        "AUTH/placeholder.txt",
        "Auth/placeholder.txt",
        "auth/placeholder.txt",
        "FRONTEND/placeholder.txt",
        "Frontend/placeholder.txt",
        "frontend/placeholder.txt",
        "NGINX/placeholder.txt",
        "Nginx/placeholder.txt",
        "nginx/placeholder.txt",
        "qdrant_storage/placeholder.txt",
        "pytest_tmp/placeholder.txt",
    )

    not_ignored = [path for path in paths_that_must_be_ignored if not _git_check_ignore(path)]

    assert not not_ignored


def test_archives_remains_documented_scientific_source_at_project_root() -> None:
    assert (PROJECT_ROOT / "archives" / "smart_boletim.pdf").is_file()
    assert not _git_check_ignore("archives/smart_boletim.pdf")
