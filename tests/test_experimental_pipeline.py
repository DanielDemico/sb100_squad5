"""Tests for the experimental evaluation pipeline helpers and dataset."""

import json
from pathlib import Path

import pytest

from eval.run_experimental_evaluation import check_refusal, update_env_variable

DATASET_PATH = Path("eval/dataset/experimental_questions.json")


def test_experimental_dataset_schema() -> None:
    """Verify that the experimental dataset exists and has the correct keys and format."""
    assert DATASET_PATH.exists()

    with open(DATASET_PATH, encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "questions" in data
    assert "perturbation_cases" in data

    questions = data["questions"]
    assert len(questions) > 0
    for q in questions:
        assert "question_id" in q
        assert "category" in q
        assert "question" in q
        assert "expected_concepts" in q
        assert q["category"] in ["agricultura_valida", "extracampo", "premissa_falsa"]

    perturbations = data["perturbation_cases"]
    assert len(perturbations) > 0
    for p in perturbations:
        assert "case_id" in p
        assert "question" in p
        assert "correct_context" in p
        assert "perturbed_context" in p


@pytest.mark.parametrize(
    "answer,expected",
    [
        ("Desculpe, mas eu sou um assistente especializado em agricultura...", True),
        ("Só respondo sobre temas agrícolas cobertos...", True),
        ("I cannot answer this topic with confidence.", True),
        ("A recomendação de calagem para o café segundo o Boletim 100 é...", False),
        ("A profundidade recomendada para amostragem é...", False),
    ],
)
def test_check_refusal(answer: str, expected: bool) -> None:
    """Verify that check_refusal correctly flags agent/system refusals."""
    assert check_refusal(answer) == expected


def test_update_env_variable(tmp_path: Path) -> None:
    """Verify that update_env_variable correctly modifies the config file."""
    mock_env = tmp_path / ".env"
    mock_env.write_text("VAR1=old_val\n# Comment\nVAR2=other_val\n", encoding="utf-8")

    # Monkeypatch paths in run_experimental_evaluation
    import eval.run_experimental_evaluation as ree

    ree.ENV_PATH = mock_env
    ree.MAIN_PATH = tmp_path / "main.py"
    ree.MAIN_PATH.write_text("print('main')", encoding="utf-8")

    # Update existing
    update_env_variable({"VAR1": "new_val", "VAR3": "added_val"})

    content = mock_env.read_text(encoding="utf-8")
    assert "VAR1=new_val" in content
    assert "VAR2=other_val" in content
    assert "VAR3=added_val" in content
    assert "# Comment" in content
