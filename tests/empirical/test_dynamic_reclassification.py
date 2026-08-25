"""Empirical tests 2, 3, 4: Dynamic Reclassification, Profile Persistence & Stability (Sections 6, 7, 8)."""

import json
from pathlib import Path
from agent.profiling import (
    classify_user_profile,
    evaluate_disparity_and_reclassify,
    UserProfileCategory,
)

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "reclassification_sequences.json"


def run_dynamic_reclassification_experiment():
    """Run dynamic transitions, persistence, and stability against atypical questions."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        datasets = json.load(f)

    transitions = datasets["dynamic_transitions"]
    persistence_cases = datasets["persistence_tests"]
    stability_cases = datasets["stability_atypical_tests"]

    transition_results = []
    total_cases = 0
    successful_cases = 0
    total_interactions_to_reclassify = []

    for seq in transitions:
        current_profile = seq["initial_profile"]
        history = []
        seq_log = []
        reclassified_at_step = None

        for idx, step in enumerate(seq["steps"]):
            question = step["question"]
            inferred = classify_user_profile(question)
            final_p, is_reclassified, justification = evaluate_disparity_and_reclassify(
                current_profile, inferred, history
            )
            history.append({"role": "user", "content": question})

            if is_reclassified and reclassified_at_step is None:
                reclassified_at_step = idx + 1

            seq_log.append({
                "step": idx + 1,
                "question": question,
                "inferred": inferred,
                "profile_before": current_profile,
                "profile_after": final_p,
                "reclassified": is_reclassified,
                "justification": justification
            })
            current_profile = final_p

        total_cases += 1
        # Success criteria: reached O Técnico by the end of the sequence
        if current_profile == UserProfileCategory.TECNICO.value:
            successful_cases += 1
            if reclassified_at_step is not None:
                total_interactions_to_reclassify.append(reclassified_at_step)

        transition_results.append({
            "id": seq["id"],
            "initial": seq["initial_profile"],
            "final": current_profile,
            "reclassified_at_step": reclassified_at_step,
            "steps": seq_log
        })

    # Persistence experiment
    persistence_results = []
    for p_case in persistence_cases:
        current_profile = p_case["initial_profile"]
        history = []
        # Step 1: trigger reclassification
        q1 = p_case["trigger_question"]
        inferred1 = classify_user_profile(q1)
        p1, reclass1, just1 = evaluate_disparity_and_reclassify(current_profile, inferred1, history)
        history.append({"role": "user", "content": q1})

        # Step 2: next question
        q2 = p_case["post_trigger_question"]
        inferred2 = classify_user_profile(q2)
        p2, reclass2, just2 = evaluate_disparity_and_reclassify(p1, inferred2, history)

        persistence_results.append({
            "id": p_case["id"],
            "profile_after_trigger": p1,
            "profile_active_subsequent": p2,
            "persisted_correctly": p2 == p_case["expected_active_profile"]
        })

    # Stability against isolated atypical queries
    stability_results = []
    unwarranted_changes = 0
    for s_case in stability_cases:
        current_profile = s_case["current_profile"]
        depth = s_case.get("history_depth", 3)
        history = [{"role": "user", "content": "Pergunta técnica sobre V% e PRNT no solo."} for _ in range(depth)]
        atypical_q = s_case["atypical_question"]

        inferred = classify_user_profile(atypical_q)
        final_p, reclassified, justification = evaluate_disparity_and_reclassify(
            current_profile, inferred, history
        )

        is_stable = (final_p == s_case["expected_final_profile"])
        if reclassified and final_p != current_profile:
            unwarranted_changes += 1

        stability_results.append({
            "id": s_case["id"],
            "current_profile": current_profile,
            "atypical_question": atypical_q,
            "inferred_class": inferred,
            "final_profile": final_p,
            "maintained_stability": is_stable,
            "justification": justification
        })

    avg_interactions = (
        sum(total_interactions_to_reclassify) / len(total_interactions_to_reclassify)
        if total_interactions_to_reclassify else 0.0
    )

    return {
        "total_cases": total_cases,
        "successful_cases": successful_cases,
        "success_rate": round(successful_cases / total_cases, 4) if total_cases > 0 else 0.0,
        "average_interactions_to_reclassify": round(avg_interactions, 2),
        "unwarranted_change_count": unwarranted_changes,
        "transitions": transition_results,
        "persistence": persistence_results,
        "stability": stability_results
    }


def test_dynamic_reclassification_empirical():
    res = run_dynamic_reclassification_experiment()
    assert res["total_cases"] >= 1
    assert res["success_rate"] >= 0.80
    assert res["persistence"][0]["persisted_correctly"] is True
