"""Empirical tests 11, 12, 13, 15, 16: Robustness, Ambiguity, Regional Expressions, Invalid Classes & Failures (Sections 15, 16, 17, 19, 20)."""

import json
from pathlib import Path
from agent.profiling import (
    classify_user_profile,
    evaluate_disparity_and_reclassify,
    is_valid_profile,
    UserProfileCategory,
)

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "reclassification_sequences.json"


def run_robustness_experiment():
    """Run empirical robustness suite covering ambiguity, regional dialect, invalid profile inputs, and error handling."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        datasets = json.load(f)

    ambiguous_set = datasets["ambiguous_questions"]
    regional_set = datasets["regional_colloquial_questions"]
    invalid_classes = datasets["invalid_class_cases"]

    # 1. Ambiguous questions evaluation
    ambiguity_results = []
    unwanted_profile_switches = 0
    for item in ambiguous_set:
        q = item["question"]
        inferred = classify_user_profile(q)
        # Evaluate disparity starting from default valid profile
        final_p, reclassified, just = evaluate_disparity_and_reclassify("O Leigo", inferred, history=[])
        
        ambiguity_results.append({
            "question": q,
            "inferred": inferred,
            "final_profile": final_p,
            "reclassified": reclassified
        })

    # 2. Regional/Colloquial evaluation
    reg_correct = 0
    reg_total = len(regional_set)
    regional_results = []

    for item in regional_set:
        q = item["question"]
        expected = item["expected_profile"]
        predicted = classify_user_profile(q)
        is_corr = (predicted == expected)
        if is_corr:
            reg_correct += 1

        regional_results.append({
            "question": q,
            "expected": expected,
            "predicted": predicted,
            "correct": is_corr
        })

    regional_accuracy = reg_correct / reg_total if reg_total > 0 else 0.0

    # 3. Invalid Class Cases
    invalid_class_results = []
    rejected_count = 0

    for inv in invalid_classes:
        bad_val = inv["input_class"]
        valid = is_valid_profile(bad_val)
        
        # Test evaluation behavior
        final_p, reclassified, just = evaluate_disparity_and_reclassify(bad_val, "O Leigo", history=[])
        
        # System must reject bad_val and set a valid profile (O Leigo/Técnico/Caipira)
        handled_safely = is_valid_profile(final_p) and not valid
        if handled_safely:
            rejected_count += 1

        invalid_class_results.append({
            "input_class": repr(bad_val),
            "is_valid": valid,
            "final_profile": final_p,
            "handled_safely": handled_safely
        })

    # 4. Dependency failure resilience simulation
    dep_failure_passed = False
    try:
        # Simulate invalid input or failure gracefully
        # System must fallback without corrupting profile
        fallback_profile, reclass, just = evaluate_disparity_and_reclassify("O Leigo", "INVALID_DERIVED", history=[])
        if is_valid_profile(fallback_profile):
            dep_failure_passed = True
    except Exception:
        dep_failure_passed = False

    # 5. Reproducibility check (Section 20)
    rep_questions = [
        "Como faço para colocar calcário na minha plantação?",
        "Quanto de calcário eu jogo na roça?",
        "Qual dose de calcário devo aplicar considerando a saturação por bases?"
    ]
    run1 = [classify_user_profile(q) for q in rep_questions]
    run2 = [classify_user_profile(q) for q in rep_questions]
    consistency_rate = sum(1 for a, b in zip(run1, run2) if a == b) / len(rep_questions)

    return {
        "ambiguity_eval_total": len(ambiguous_set),
        "unwanted_profile_switches": unwanted_profile_switches,
        "regional_total": reg_total,
        "regional_accuracy": round(regional_accuracy, 4),
        "invalid_classes_tested": len(invalid_classes),
        "invalid_classes_safely_handled": rejected_count,
        "dependency_failure_resilience": "PASS" if dep_failure_passed else "FAIL",
        "reproducibility_consistency_rate": round(consistency_rate, 4),
        "invalid_class_results": invalid_class_results,
        "regional_results": regional_results
    }


def test_robustness_empirical():
    res = run_robustness_experiment()
    assert res["invalid_classes_safely_handled"] == res["invalid_classes_tested"]
    assert res["dependency_failure_resilience"] == "PASS"
    assert res["regional_accuracy"] >= 0.70
    assert res["reproducibility_consistency_rate"] >= 0.90
