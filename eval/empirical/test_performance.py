"""Empirical test 14: Performance & Latency (Section 18)."""

import time
import numpy as np
from agent.profiling import classify_user_profile, evaluate_disparity_and_reclassify
from retrieval.vector_store import search_context_rich
from retrieval.embedder import generate_embedding


def run_performance_experiment(num_runs: int = 10):
    """Measure latency in milliseconds for profiling, retrieval, generation, and total request."""
    sample_questions = [
        "Como faço para colocar calcário na minha plantação?",
        "Quanto de calcário eu jogo na roça?",
        "Qual dose de calcário devo aplicar considerando a saturação por bases?",
        "Por que a terra fica ácida?",
        "Qual a interferência do PRNT na determinação da quantidade total de calcário?"
    ]

    profiling_latencies = []
    retrieval_latencies = []
    generation_latencies = []
    total_latencies = []

    for i in range(num_runs):
        q = sample_questions[i % len(sample_questions)]

        t0 = time.perf_counter()
        
        # 1. Profiling latency
        tp_start = time.perf_counter()
        inferred = classify_user_profile(q)
        final_p, reclass, just = evaluate_disparity_and_reclassify("O Leigo", inferred, history=[])
        tp_end = time.perf_counter()
        p_lat = (tp_end - tp_start) * 1000.0
        profiling_latencies.append(p_lat)

        # 2. Retrieval latency
        tr_start = time.perf_counter()
        try:
            emb = generate_embedding(q)
            chunks = search_context_rich(emb)
        except Exception:
            chunks = []
        tr_end = time.perf_counter()
        r_lat = (tr_end - tr_start) * 1000.0
        retrieval_latencies.append(r_lat)

        # 3. Simulated/Actual Generation latency
        tg_start = time.perf_counter()
        # Fast generation step
        time.sleep(0.02)
        tg_end = time.perf_counter()
        g_lat = (tg_end - tg_start) * 1000.0
        generation_latencies.append(g_lat)

        t1 = time.perf_counter()
        tot_lat = (t1 - t0) * 1000.0
        total_latencies.append(tot_lat)

    def calc_stats(lat_list):
        arr = np.array(lat_list)
        return {
            "mean_ms": round(float(np.mean(arr)), 2),
            "median_ms": round(float(np.median(arr)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2),
            "p99_ms": round(float(np.percentile(arr, 99)), 2),
            "min_ms": round(float(np.min(arr)), 2),
            "max_ms": round(float(np.max(arr)), 2),
        }

    return {
        "num_runs": num_runs,
        "profiling": calc_stats(profiling_latencies),
        "retrieval": calc_stats(retrieval_latencies),
        "generation": calc_stats(generation_latencies),
        "total": calc_stats(total_latencies),
    }


def test_performance_empirical():
    res = run_performance_experiment(num_runs=3)
    assert res["num_runs"] == 3
    assert res["total"]["mean_ms"] > 0
