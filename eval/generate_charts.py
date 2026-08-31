"""Generate scientific charts from evaluation results.

Reads raw_experiment_results.json and creates confusion matrix, latency,
and perturbation scores plots under eval/results/.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = Path("eval/results")
RESULTS_JSON = RESULTS_DIR / "raw_experiment_results.json"


def generate_confusion_matrix(data: dict) -> None:
    """Generate confusion matrix plot for agricultural intent classifier.

    QUALITY: long-function-justification - metric extraction, matrix creation, labels,
    annotations, file save, and close are one matplotlib chart recipe.
    """
    tp, fp, tn, fn = 0, 0, 0, 0
    proposed_raw = data.get("proposed_raw", [])

    refusal_keywords = [
        "Desculpe",
        "não posso responder",
        "só posso responder perguntas relacionadas",
        "I cannot answer this topic with confidence",
        "Só respondo sobre temas agrícolas",
    ]

    for r in proposed_raw:
        is_agri = r["category"] == "agricultura_valida"
        answer = r["response"]["answer"]
        refused = any(kw in answer for kw in refusal_keywords)

        if is_agri:
            if not refused:
                tp += 1
            else:
                fn += 1
        else:  # extracampo
            if refused:
                tn += 1
            else:
                fp += 1

    cm = np.array([[tn, fp], [fn, tp]])

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Greens)
    ax.figure.colorbar(im, ax=ax)

    classes = ["Fora de Escopo", "Agrícola Válida"]
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=classes,
        yticklabels=classes,
        title="Matriz de Confusão do Filtro de Domínio",
        ylabel="Classe Real",
        xlabel="Classe Predita",
    )

    # Loop over data dimensions and create text annotations
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                format(cm[i, j], "d"),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=14,
                fontweight="bold",
            )

    fig.tight_layout()
    plt.savefig(RESULTS_DIR / "confusion_matrix.png", dpi=150)
    plt.close()
    print("confusion_matrix.png generated.")


def generate_latency_comparison(data: dict) -> None:
    """Generate bar chart comparing Baseline vs Proposed latency.

    QUALITY: long-function-justification - metric extraction, bar creation, annotation,
    file save, and close are one matplotlib chart recipe.
    """
    metrics = data.get("metrics", {})
    avg_b = metrics.get("latencia_media_baseline", 0)
    avg_p = metrics.get("latencia_media_proposto", 0)

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(
        ["Baseline (Sem Validação)", "Pipeline Proposto (Com Validação)"],
        [avg_b, avg_p],
        color=["#3b82f6", "#10b981"],
        width=0.5,
    )

    ax.set_ylabel("Latência Média por Consulta (segundos)", fontsize=11)
    ax.set_title("Impacto da Validação Multiagente na Latência", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.2f}s",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),  # 3 points vertical offset
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    fig.tight_layout()
    plt.savefig(RESULTS_DIR / "latency_comparison.png", dpi=150)
    plt.close()
    print("latency_comparison.png generated.")


def generate_latency_distribution(data: dict) -> None:
    """Generate boxplot showing latency distributions."""
    b_raw = data.get("baseline_raw", [])
    p_raw = data.get("proposed_raw", [])

    b_lats = [r["response"]["latency"] for r in b_raw if r["response"]["success"]]
    p_lats = [r["response"]["latency"] for r in p_raw if r["response"]["success"]]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.boxplot(
        [b_lats, p_lats],
        patch_artist=True,
        boxprops={"facecolor": "#bfdbfe", "color": "#1d4ed8"},
        medianprops={"color": "#1d4ed8", "linewidth": 2},
    )
    ax.set_xticklabels(["Baseline", "Pipeline Proposto"])

    ax.set_ylabel("Distribuição de Latência (segundos)", fontsize=11)
    ax.set_title("Distribuição Estatística da Latência", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    fig.tight_layout()
    plt.savefig(RESULTS_DIR / "latency_distribution.png", dpi=150)
    plt.close()
    print("latency_distribution.png generated.")


def generate_perturbation_scores(data: dict) -> None:
    """Generate chart comparing hallucination scores on C1 vs C2.

    QUALITY: long-function-justification - perturbation extraction, grouped bars,
    threshold reference, annotations, file save, and close are one chart recipe.
    """
    p_raw = data.get("perturbation_raw", [])
    if not p_raw:
        return

    case_ids = [r["case_id"] for r in p_raw]
    c1_scores = [r["c1_response"]["hallucination_score"] for r in p_raw]
    c2_scores = [r["c2_response"]["hallucination_score"] for r in p_raw]

    x = np.arange(len(case_ids))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))
    rects1 = ax.bar(x - width / 2, c1_scores, width, label="C1 (Contexto Correto)", color="#10b981")
    rects2 = ax.bar(
        x + width / 2, c2_scores, width, label="C2 (Contexto Perturbado)", color="#ef4444"
    )

    ax.set_ylabel("Incerteza / Score de Alucinação", fontsize=11)
    ax.set_title("Detecção de Distorções Factuais em Contexto", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(case_ids)
    ax.set_ylim(0.0, 1.1)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Threshold line
    ax.axhline(y=0.5, color="gray", linestyle=":", label="Threshold (0.5)")

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(
            f"{h:.2f}",
            xy=(rect.get_x() + rect.get_width() / 2, h),
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(
            f"{h:.2f}",
            xy=(rect.get_x() + rect.get_width() / 2, h),
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    plt.savefig(RESULTS_DIR / "perturbation_scores.png", dpi=150)
    plt.close()
    print("perturbation_scores.png generated.")


def main():
    if not RESULTS_JSON.exists():
        print(f"Error: {RESULTS_JSON} not found. Run the evaluation script first.")
        return 1

    with open(RESULTS_JSON, encoding="utf-8") as f:
        data = json.load(f)

    generate_confusion_matrix(data)
    generate_latency_comparison(data)
    generate_latency_distribution(data)
    generate_perturbation_scores(data)
    print("All charts successfully generated!")
    return 0


if __name__ == "__main__":
    main()
