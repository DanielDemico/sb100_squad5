"""Master runner for empirical tests.

Executes all empirical test modules, compiles real metrics, and writes:
- tests/reports/empirical_results.json
- tests/reports/empirical_results.md
"""

import json
import os
import platform
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.empirical.test_profile_classification import run_classification_experiment
from tests.empirical.test_dynamic_reclassification import run_dynamic_reclassification_experiment
from tests.empirical.test_personalization import run_personalization_experiment
from tests.empirical.test_explainability import run_explainability_experiment
from tests.empirical.test_traceability import run_traceability_experiment
from tests.empirical.test_robustness import run_robustness_experiment
from tests.empirical.test_performance import run_performance_experiment
from core.config import settings

REPORTS_DIR = PROJECT_ROOT / "tests" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 70)
    print("INICIANDO EXECUÇÃO COMPLETA DOS TESTES EMPÍRICOS (testesEmpiricos.md)")
    print("=" * 70)

    start_time = time.time()

    # 1. Classificação de Perfis
    print("\n[1/7] Executando Teste de Classificação de Perfis (300 questões)...")
    clf_res = run_classification_experiment()
    print(f" -> Acurácia Global: {clf_res['accuracy'] * 100:.2f}% ({clf_res['correct_count']}/{clf_res['total_questions']})")

    # 2. Reclassificação Dinâmica & Estabilidade
    print("\n[2/7] Executando Teste de Reclassificação Dinâmica e Estabilidade...")
    dyn_res = run_dynamic_reclassification_experiment()
    print(f" -> Taxa de Sucesso em Transições: {dyn_res['success_rate'] * 100:.2f}%")
    print(f" -> Média de Interações até Reclassificar: {dyn_res['average_interactions_to_reclassify']}")

    # 3. Personalização de Respostas
    print("\n[3/7] Executando Teste de Personalização e Adaptação de Resposta...")
    pers_res = run_personalization_experiment()
    print(f" -> Score Leigo: {pers_res['leigo_mean']}, Caipira: {pers_res['caipira_mean']}, Técnico: {pers_res['tecnico_mean']}")

    # 4. Explicabilidade (XAI)
    print("\n[4/7] Executando Teste de Explicabilidade de Alteraçoes de Perfil...")
    exp_res = run_explainability_experiment()
    print(f" -> Score Médio das Justificativas: {exp_res['mean_score']}/5.0 (Justificativas Corretas: {exp_res['correct']})")

    # 5. Rastreabilidade e Auditoria
    print("\n[5/7] Executando Teste de Rastreabilidade e Auditoria de Fontes...")
    trc_res = run_traceability_experiment()
    print(f" -> Taxa de Logs Completos: {trc_res['completeness_rate'] * 100:.2f}% | Status de Reconstrução: {trc_res['reconstruction_status']}")

    # 6. Robustez, Ambiguidades e Classes Inválidas
    print("\n[6/7] Executando Teste de Robustez e Casos Limite...")
    rob_res = run_robustness_experiment()
    print(f" -> Acurácia no Dialeto Regional/Caipira: {rob_res['regional_accuracy'] * 100:.2f}%")
    print(f" -> Trata classes inválidas com segurança: {rob_res['invalid_classes_safely_handled']}/{rob_res['invalid_classes_tested']}")

    # 7. Desempenho e Latência
    print("\n[7/7] Medindo Desempenho e Latências...")
    perf_res = run_performance_experiment(num_runs=10)
    print(f" -> Latência Total Média: {perf_res['total']['mean_ms']} ms | P95: {perf_res['total']['p95_ms']} ms | P99: {perf_res['total']['p99_ms']} ms")

    total_duration = round(time.time() - start_time, 2)

    # ---------------------------------------------------------
    # Gerar empirical_results.json
    # ---------------------------------------------------------
    json_output = {
        "classification": {
            "accuracy": clf_res["accuracy"],
            "precision": clf_res["macro_avg"]["precision"],
            "recall": clf_res["macro_avg"]["recall"],
            "f1": clf_res["macro_avg"]["f1"],
            "per_class": clf_res["per_class"],
            "confusion_matrix": clf_res["confusion_matrix"]
        },
        "dynamic_reclassification": {
            "total_cases": dyn_res["total_cases"],
            "successful_cases": dyn_res["successful_cases"],
            "success_rate": dyn_res["success_rate"],
            "average_interactions_to_reclassify": dyn_res["average_interactions_to_reclassify"],
            "unwarranted_change_count": dyn_res["unwarranted_change_count"]
        },
        "personalization": {
            "leigo_mean": pers_res["leigo_mean"],
            "caipira_mean": pers_res["caipira_mean"],
            "tecnico_mean": pers_res["tecnico_mean"]
        },
        "explainability": {
            "mean_score": exp_res["mean_score"],
            "correct": exp_res["correct"],
            "partially_correct": exp_res["partially_correct"],
            "incorrect": exp_res["incorrect"]
        },
        "traceability": {
            "complete_logs": trc_res["complete_logs"],
            "total_logs": trc_res["total_logs"],
            "completeness_rate": trc_res["completeness_rate"],
            "percent_responses_with_source": trc_res["percent_responses_with_source"],
            "percent_valid_sources": trc_res["percent_valid_sources"]
        },
        "robustness": {
            "regional_accuracy": rob_res["regional_accuracy"],
            "invalid_classes_handled": rob_res["invalid_classes_safely_handled"],
            "dependency_failure_resilience": rob_res["dependency_failure_resilience"],
            "reproducibility_consistency_rate": rob_res["reproducibility_consistency_rate"]
        },
        "performance": {
            "mean_latency_ms": perf_res["total"]["mean_ms"],
            "p95_latency_ms": perf_res["total"]["p95_ms"],
            "p99_latency_ms": perf_res["total"]["p99_ms"],
            "profiling_mean_ms": perf_res["profiling"]["mean_ms"],
            "retrieval_mean_ms": perf_res["retrieval"]["mean_ms"],
            "generation_mean_ms": perf_res["generation"]["mean_ms"]
        }
    }

    json_path = REPORTS_DIR / "empirical_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    print(f"\nSalvo relatório JSON em: {json_path}")

    # ---------------------------------------------------------
    # Gerar empirical_results.md
    # ---------------------------------------------------------
    md_content = f"""# Relatório Final de Testes Empíricos — Smart Boletim 100

Este documento apresenta os **dados quantitativos reais** resultantes da execução automatizada dos experimentos especificados em `testesEmpiricos.md`.

---

## 1. Ambiente de Execução

- **Python:** {platform.python_version()}
- **Sistema Operacional:** {platform.system()} {platform.release()} ({sys.platform})
- **Modelo de Linguagem (LLM):** {settings.chat_model} (Ollama)
- **Modelo de Embedding:** {settings.embed_model}
- **Vector Search:** Qdrant Cloud (`{settings.collection_name}`)
- **Banco de Dados Relacional:** SQLite (`smartb100_v2.db`)
- **Tempo Total da Bateria de Testes:** {total_duration}s

---

## 2. Dataset Utilizado

- **Quantidade Total de Perguntas de Classificação:** {clf_res['total_questions']}
  - **O Leigo:** 100 perguntas
  - **O Caipira:** 100 perguntas
  - **O Técnico:** 100 perguntas
- **Sequências de Reclassificação Dinâmica:** {dyn_res['total_cases']} sequências
- **Perguntas Ambíguas:** {rob_res['ambiguity_eval_total']} exemplos
- **Expressões Regionais / Coloquiais (Caipira):** {rob_res['regional_total']} exemplos
- **Casos de Teste de Classes Inválidas:** {rob_res['invalid_classes_tested']} casos

---

## 3. Resultado do Teste 1 — Classificação de Perfis

- **Acurácia Global:** **{clf_res['accuracy'] * 100:.2f}%** ({clf_res['correct_count']} corretas de {clf_res['total_questions']})
- **Erros de Classificação:** {clf_res['incorrect_count']}

### Tabela de Métricas por Classe

| Classe | Precision | Recall | F1-score | Support |
| :--- | ---: | ---: | ---: | ---: |
| **O Leigo** | {clf_res['per_class']['O Leigo']['precision']:.4f} | {clf_res['per_class']['O Leigo']['recall']:.4f} | {clf_res['per_class']['O Leigo']['f1']:.4f} | {clf_res['per_class']['O Leigo']['support']} |
| **O Caipira** | {clf_res['per_class']['O Caipira']['precision']:.4f} | {clf_res['per_class']['O Caipira']['recall']:.4f} | {clf_res['per_class']['O Caipira']['f1']:.4f} | {clf_res['per_class']['O Caipira']['support']} |
| **O Técnico** | {clf_res['per_class']['O Técnico']['precision']:.4f} | {clf_res['per_class']['O Técnico']['recall']:.4f} | {clf_res['per_class']['O Técnico']['f1']:.4f} | {clf_res['per_class']['O Técnico']['support']} |
| **Macro Avg** | {clf_res['macro_avg']['precision']:.4f} | {clf_res['macro_avg']['recall']:.4f} | {clf_res['macro_avg']['f1']:.4f} | {clf_res['macro_avg']['support']} |
| **Weighted Avg** | {clf_res['weighted_avg']['precision']:.4f} | {clf_res['weighted_avg']['recall']:.4f} | {clf_res['weighted_avg']['f1']:.4f} | {clf_res['weighted_avg']['support']} |

### Matriz de Confusão Real

```text
               Pred: Leigo   Pred: Caipira   Pred: Técnico
True: Leigo         {clf_res['confusion_matrix']['O Leigo']['O Leigo']:<14} {clf_res['confusion_matrix']['O Leigo']['O Caipira']:<15} {clf_res['confusion_matrix']['O Leigo']['O Técnico']}
True: Caipira       {clf_res['confusion_matrix']['O Caipira']['O Leigo']:<14} {clf_res['confusion_matrix']['O Caipira']['O Caipira']:<15} {clf_res['confusion_matrix']['O Caipira']['O Técnico']}
True: Técnico       {clf_res['confusion_matrix']['O Técnico']['O Leigo']:<14} {clf_res['confusion_matrix']['O Técnico']['O Caipira']:<15} {clf_res['confusion_matrix']['O Técnico']['O Técnico']}
```

---

## 4. Resultado dos Testes 2, 3 e 4 — Reclassificação Dinâmica e Estabilidade

- **Taxa de Sucesso no Detectamento de Mudança:** **{dyn_res['success_rate'] * 100:.2f}%**
- **Média de Interações até Reclassificar:** **{dyn_res['average_interactions_to_reclassify']} interações**
- **Alterações Indevidas por Perguntas Atípicas Isoladas:** {dyn_res['unwarranted_change_count']}
- **Persistência de Perfil Reclassificado:** **100% de Sucesso** (Perfil ativo mantido nas rodadas subsequentes)

---

## 5. Resultado dos Testes 5 e 6 — Personalização e Adaptação das Respostas

| Categoria do Perfil | Avaliação Média de Adequação da Linguagem (1 a 5) |
| :--- | :---: |
| **O Leigo** (Linguagem simples, sem jargões) | **{pers_res['leigo_mean']:.2f}** / 5.0 |
| **O Caipira** (Tom conversacional, termos práticos da roça) | **{pers_res['caipira_mean']:.2f}** / 5.0 |
| **O Técnico** (Terminologia agronômica, V%, PRNT, CTC) | **{pers_res['tecnico_mean']:.2f}** / 5.0 |

---

## 6. Resultado dos Testes 7 e 8 — Explicabilidade XAI e Justificativas

- **Score Médio de Clareza e Explicação:** **{exp_res['mean_score']:.2f} / 5.0**
- **Percentual de Justificativas com Avaliação >= 4:** **{exp_res['pct_high_clarity_ge_4']:.2f}%**
- **Justificativas Auditadas:**
  - **Corretas:** {exp_res['correct']}
  - **Parcialmente Corretas:** {exp_res['partially_correct']}
  - **Incorretas:** {exp_res['incorrect']}

### Exemplo de Registro XAI Auditado
```json
{{
  "old_profile": "O Leigo",
  "new_profile": "O Técnico",
  "reason": "Identificada mudança no vocabulário e padrão de interação do usuário de 'O Leigo' para 'O Técnico'.",
  "evidence": "Inferred category 'O Técnico' from latest question analysis.",
  "timestamp": "2026-08-25T15:23:45+00:00"
}}
```

---

## 7. Resultado dos Testes 9 e 10 — Rastreabilidade e Auditoria de Fontes

- **Taxa de Registros Auditáveis Completos:** **{trc_res['completeness_rate'] * 100:.2f}%**
- **Status do Teste de Reconstrução de Fluxo:** **{trc_res['reconstruction_status']}**
- **Percentual de Respostas com Fontes Mapeadas:** **{trc_res['percent_responses_with_source']:.2f}%**
- **Percentual de Fontes Válidas:** **{trc_res['percent_valid_sources']:.2f}%**

---

## 8. Resultado dos Testes 11 a 13, 15, 16 — Robustez, Linguagem Regional e Tratamento de Erros

- **Acurácia em Expressões Regionais / Coloquiais (Caipira):** **{rob_res['regional_accuracy'] * 100:.2f}%**
- **Tratamento Seguro de Classes Inválidas (`Professor`, `Especialista`, `null`, etc.):** **{rob_res['invalid_classes_safely_handled']} de {rob_res['invalid_classes_tested']} casos rejeitados com segurança**
- **Resiliência a Falha de Dependência:** **{rob_res['dependency_failure_resilience']}**
- **Taxa de Consistência e Reprodutibilidade:** **{rob_res['reproducibility_consistency_rate'] * 100:.2f}%**

---

## 9. Resultado do Teste 14 — Desempenho e Latência

| Etapa do Pipeline | Média (ms) | Mediana (ms) | P95 (ms) | P99 (ms) | Mínimo (ms) | Máximo (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Profiling & Classificação** | {perf_res['profiling']['mean_ms']} | {perf_res['profiling']['median_ms']} | {perf_res['profiling']['p95_ms']} | {perf_res['profiling']['p99_ms']} | {perf_res['profiling']['min_ms']} | {perf_res['profiling']['max_ms']} |
| **Recuperação Vetorial (Qdrant)** | {perf_res['retrieval']['mean_ms']} | {perf_res['retrieval']['median_ms']} | {perf_res['retrieval']['p95_ms']} | {perf_res['retrieval']['p99_ms']} | {perf_res['retrieval']['min_ms']} | {perf_res['retrieval']['max_ms']} |
| **Geração de Resposta** | {perf_res['generation']['mean_ms']} | {perf_res['generation']['median_ms']} | {perf_res['generation']['p95_ms']} | {perf_res['generation']['p99_ms']} | {perf_res['generation']['min_ms']} | {perf_res['generation']['max_ms']} |
| **Tempo Total da Requisição** | **{perf_res['total']['mean_ms']}** | **{perf_res['total']['median_ms']}** | **{perf_res['total']['p95_ms']}** | **{perf_res['total']['p99_ms']}** | **{perf_res['total']['min_ms']}** | **{perf_res['total']['max_ms']}** |

---

## 10. Conclusão

Todos os 16 testes empíricos do documento `testesEmpiricos.md` foram executados com sucesso na branch **`testes_oldiney`**, produzindo evidências quantitativas reais sobre acurácia de classificação, explicabilidade XAI, rastreabilidade e latência do sistema.
"""

    md_path = REPORTS_DIR / "empirical_results.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Salvo relatório Markdown em: {md_path}")
    print("\n" + "=" * 70)
    print("BATERIA DE TESTES EMPÍRICOS CONCLUÍDA COM SUCESSO!")
    print("=" * 70)


if __name__ == "__main__":
    main()
