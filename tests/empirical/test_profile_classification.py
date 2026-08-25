"""Empirical test 1: Profile Classification (Section 5 of testesEmpiricos.md).

Evaluates classification accuracy, precision, recall, F1-score, and confusion matrix
across 300 agronomic questions (100 Leigo, 100 Caipira, 100 Técnico).
"""

import json
from pathlib import Path
from agent.profiling import classify_user_profile, UserProfileCategory

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "profile_classification.json"


def run_classification_experiment():
    """Run empirical evaluation over the 300-question dataset."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    y_true = []
    y_pred = []
    results = []

    classes = [UserProfileCategory.LEIGO.value, UserProfileCategory.CAIPIRA.value, UserProfileCategory.TECNICO.value]

    for item in dataset:
        q_id = item["id"]
        question = item["question"]
        expected = item["expected_profile"]

        predicted = classify_user_profile(question)

        y_true.append(expected)
        y_pred.append(predicted)

        results.append({
            "id": q_id,
            "question": question,
            "expected": expected,
            "predicted": predicted,
            "correct": expected == predicted
        })

    # Calculate metrics
    total = len(y_true)
    correct_count = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    incorrect_count = total - correct_count
    accuracy = correct_count / total if total > 0 else 0.0

    # Per-class metrics & confusion matrix
    # Matrix format: rows = expected (true), cols = predicted
    confusion_matrix = {c_true: {c_pred: 0 for c_pred in classes} for c_true in classes}
    for t, p in zip(y_true, y_pred):
        if t in confusion_matrix and p in confusion_matrix[t]:
            confusion_matrix[t][p] += 1

    per_class_metrics = {}
    precisions, recalls, f1s, supports = [], [], [], []

    for c in classes:
        tp = confusion_matrix[c][c]
        fp = sum(confusion_matrix[other][c] for other in classes if other != c)
        fn = sum(confusion_matrix[c][other] for other in classes if other != c)
        support = sum(confusion_matrix[c].values())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        per_class_metrics[c] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support
        }
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        supports.append(support)

    macro_avg = {
        "precision": round(sum(precisions) / len(classes), 4),
        "recall": round(sum(recalls) / len(classes), 4),
        "f1": round(sum(f1s) / len(classes), 4),
        "support": total
    }

    weighted_precision = sum(p * s for p, s in zip(precisions, supports)) / total if total > 0 else 0.0
    weighted_recall = sum(r * s for r, s in zip(recalls, supports)) / total if total > 0 else 0.0
    weighted_f1 = sum(f * s for f, s in zip(f1s, supports)) / total if total > 0 else 0.0

    weighted_avg = {
        "precision": round(weighted_precision, 4),
        "recall": round(weighted_recall, 4),
        "f1": round(weighted_f1, 4),
        "support": total
    }

    return {
        "total_questions": total,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "accuracy": round(accuracy, 4),
        "per_class": per_class_metrics,
        "macro_avg": macro_avg,
        "weighted_avg": weighted_avg,
        "confusion_matrix": confusion_matrix,
        "raw_results": results
    }


def test_profile_classification_empirical():
    metrics = run_classification_experiment()
    assert metrics["total_questions"] == 300
    assert metrics["accuracy"] >= 0.70, f"Expected accuracy >= 0.70, got {metrics['accuracy']}"
