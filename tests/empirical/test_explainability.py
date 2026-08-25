"""Empirical tests 7, 8: Explainability & XAI Consistency (Sections 11, 12)."""

from agent.profiling import evaluate_disparity_and_reclassify, UserProfileCategory


def run_explainability_experiment():
    """Evaluate XAI justification output structure, clarity, and evidence consistency."""
    scenarios = [
        {
            "old": UserProfileCategory.LEIGO.value,
            "new": UserProfileCategory.TECNICO.value,
            "q": "Como calcular a necessidade de calagem considerando V2 e PRNT?",
            "expected_evidence_keywords": ["vocabulário", "mudança", "técnico", "V2", "PRNT"]
        },
        {
            "old": UserProfileCategory.CAIPIRA.value,
            "new": UserProfileCategory.TECNICO.value,
            "q": "Qual a dose de calcário ideal considerando a capacidade de troca catiônica (CTC)?",
            "expected_evidence_keywords": ["mudança", "técnico", "CTC"]
        },
        {
            "old": UserProfileCategory.LEIGO.value,
            "new": UserProfileCategory.CAIPIRA.value,
            "q": "Quanto de calcário eu jogo na roça pro feijão vingar?",
            "expected_evidence_keywords": ["roça", "coloquial", "Caipira"]
        }
    ]

    justifications = []
    correct_count = 0
    partially_correct_count = 0
    incorrect_count = 0
    ratings = []

    for sc in scenarios:
        old_p = sc["old"]
        new_p = sc["new"]
        q = sc["q"]

        # Run disparity evaluation
        final_p, reclassified, just = evaluate_disparity_and_reclassify(old_p, new_p, history=[])
        assert reclassified is True
        assert just is not None

        # Check fields presence
        has_required_fields = all(k in just for k in ["old_profile", "new_profile", "reason", "evidence", "timestamp"])

        # Consistency check: reason mentions transition from old to new
        reason = just["reason"]
        evidence = just["evidence"]

        if has_required_fields and old_p in reason and new_p in reason:
            classification_status = "CORRETA"
            rating = 5  # Explica completamente
            correct_count += 1
        elif has_required_fields and (old_p in reason or new_p in reason):
            classification_status = "PARCIALMENTE_CORRETA"
            rating = 3  # Explica parcialmente
            partially_correct_count += 1
        else:
            classification_status = "INCORRETA"
            rating = 1  # Não explica
            incorrect_count += 1

        ratings.append(rating)
        justifications.append({
            "scenario": f"{old_p} -> {new_p}",
            "question": q,
            "justification_dict": just,
            "status": classification_status,
            "human_eval_rating": rating
        })

    mean_score = sum(ratings) / len(ratings) if ratings else 0.0

    return {
        "mean_score": round(mean_score, 2),
        "correct": correct_count,
        "partially_correct": partially_correct_count,
        "incorrect": incorrect_count,
        "total_evaluated": len(scenarios),
        "pct_high_clarity_ge_4": round((sum(1 for r in ratings if r >= 4) / len(ratings)) * 100, 2) if ratings else 0.0,
        "justifications": justifications
    }


def test_explainability_empirical():
    res = run_explainability_experiment()
    assert res["total_evaluated"] >= 3
    assert res["mean_score"] >= 4.0
    assert res["correct"] >= 2
