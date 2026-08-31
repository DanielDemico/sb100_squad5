"""Real experimental evaluation of the SmartB100 anti-hallucination pipeline.

This script executes the evaluation battery against the running FastAPI server.
It handles user registration, Baseline vs Proposed settings reloading, Qdrant-injected
context perturbation (Condition C1 vs C2), and metric calculation.
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import PointIdsList, PointStruct

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings
from retrieval.embedder import generate_embedding

API_URL = "http://localhost:8000"
DATASET_PATH = Path("eval/dataset/experimental_questions.json")
RESULTS_DIR = Path("eval/results")
ENV_PATH = Path(".env")
MAIN_PATH = Path("api/main.py")

TEST_USERNAME = "eval_user"
TEST_PASSWORD = "eval_password_123"


def update_env_variable(updates: dict[str, str]) -> None:
    """Update variables in the .env file and touch api/main.py to reload the server.

    QUALITY: long-function-justification - preserves comments/order, applies updates,
    appends missing keys, persists the file, and touches Uvicorn in one operator-visible step.
    """
    if not ENV_PATH.exists():
        print(f"Error: {ENV_PATH} not found.")
        return

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    new_lines = []
    updated_keys = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        key, sep, val = line.partition("=")
        key_stripped = key.strip()
        if key_stripped in updates:
            new_lines.append(f"{key_stripped}={updates[key_stripped]}")
            updated_keys.add(key_stripped)
        else:
            new_lines.append(line)

    for k, v in updates.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Touch api/main.py to force reload
    if MAIN_PATH.exists():
        os.utime(str(MAIN_PATH), None)
        print(
            f"Updated .env keys {list(updates.keys())} and touched {MAIN_PATH} for Uvicorn reload."
        )
    else:
        print(f"Warning: {MAIN_PATH} not found to touch.")


def wait_for_server_healthy() -> str:
    """Wait for server to reload and register/login the evaluator user.

    QUALITY: long-function-justification - health polling, best-effort registration,
    login, retry delay, and final failure are one readiness gate for the experiment.
    """
    print("Waiting for server to become healthy...")
    token = None
    for _attempt in range(15):
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{API_URL}/health")
                if r.status_code == 200 and r.json().get("status") == "ok":
                    print("Server is healthy.")

                    # Register (will fail if already exists, which is fine)
                    client.post(
                        f"{API_URL}/auth/register",
                        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                    )

                    # Login
                    login_resp = client.post(
                        f"{API_URL}/auth/token",
                        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                    )
                    if login_resp.status_code == 200:
                        token = login_resp.json()["access_token"]
                        break
        except Exception:
            pass
        time.sleep(1.0)

    if not token:
        raise RuntimeError("Failed to connect or authenticate with the API.")
    return token


def run_chat_query(token: str, question: str, conversation_id: int | None = None) -> dict:
    """Execute a chat query and return the response metadata + latency.

    QUALITY: long-function-justification - request construction, timing, success mapping,
    HTTP error mapping, and connection error mapping are the atomic measurement unit.
    """
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": question, "conversation_id": conversation_id}

    start_time = time.time()
    try:
        with httpx.Client(timeout=300.0) as client:
            r = client.post(f"{API_URL}/chat", json=payload, headers=headers)
            latency = time.time() - start_time
            if r.status_code == 200:
                data = r.json()
                return {
                    "success": True,
                    "answer": data["answer"],
                    "hallucination_score": data["hallucination_score"],
                    "conversation_id": data["conversation_id"],
                    "sources": data.get("sources", []),
                    "latency": latency,
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "answer": f"[HTTP {r.status_code}] {r.text}",
                    "hallucination_score": 0.0,
                    "conversation_id": None,
                    "sources": [],
                    "latency": latency,
                    "error": f"HTTP status {r.status_code}",
                }
    except Exception as e:
        latency = time.time() - start_time
        return {
            "success": False,
            "answer": f"[ERROR] {str(e)}",
            "hallucination_score": 0.0,
            "conversation_id": None,
            "sources": [],
            "latency": latency,
            "error": str(e),
        }


def check_refusal(answer: str) -> bool:
    """Check if the answer represents a block/refusal or fallback."""
    refusal_keywords = [
        "Desculpe",
        "não posso responder",
        "só posso responder perguntas relacionadas",
        "I cannot answer this topic with confidence",
        "Só respondo sobre temas agrícolas",
    ]
    return any(kw in answer for kw in refusal_keywords)


def main():
    """Run the full experimental protocol.

    QUALITY: long-function-justification - baseline, proposed, perturbation, metrics,
    artifact writing, and environment restore form one auditable experiment transaction.
    """
    print("=== INICIANDO AVALIAÇÃO EXPERIMENTAL REAL ===")

    if not DATASET_PATH.exists():
        print(f"Erro: Dataset não encontrado em {DATASET_PATH}")
        return 1

    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)

    questions = dataset["questions"]
    perturbation_cases = dataset["perturbation_cases"]

    # Salvar estado original do .env
    original_env_content = ENV_PATH.read_text(encoding="utf-8")

    try:
        # =====================================================================
        # 1. BATERIA BASELINE (VERIFICATION_ENABLED=false)
        # =====================================================================
        print("\n--- Configurando Baseline (Sem Validação) ---")
        update_env_variable(
            {
                "VERIFICATION_ENABLED": "false",
                "LLM_MAX_TOKENS": "96",  # Otimizar velocidade na CPU
            }
        )
        token = wait_for_server_healthy()

        baseline_results = []
        for q in questions:
            print(f"Executando Baseline [{q['question_id']}] -> {q['question'][:40]}...")
            res = run_chat_query(token, q["question"])
            baseline_results.append(
                {
                    "question_id": q["question_id"],
                    "category": q["category"],
                    "question": q["question"],
                    "expected_concepts": q["expected_concepts"],
                    "response": res,
                }
            )
            time.sleep(1.0)  # Respeitar rate-limit / CPU cool-off

        # =====================================================================
        # 2. BATERIA PROPOSTO (VERIFICATION_ENABLED=true, PROVIDER=ollama)
        # =====================================================================
        print("\n--- Configurando Pipeline Proposto (Com Validação Local Ollama) ---")
        update_env_variable(
            {
                "VERIFICATION_ENABLED": "true",
                "VERIFICATION_PROVIDER": "ollama",
                "VERIFICATION_CHAT_MODEL": "llama3.2:3b",
                "LLM_MAX_TOKENS": "96",
            }
        )
        token = wait_for_server_healthy()

        proposed_results = []
        for q in questions:
            print(f"Executando Proposto [{q['question_id']}] -> {q['question'][:40]}...")
            res = run_chat_query(token, q["question"])
            proposed_results.append(
                {
                    "question_id": q["question_id"],
                    "category": q["category"],
                    "question": q["question"],
                    "expected_concepts": q["expected_concepts"],
                    "response": res,
                }
            )
            time.sleep(1.0)

        # =====================================================================
        # 3. EXPERIMENTO DE PERTURBAÇÃO DE CONTEXTO (C1 vs C2)
        # =====================================================================
        print("\n--- Executando Experimento de Perturbação de Contexto (Qdrant) ---")

        # Conectar ao Qdrant real
        qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

        perturbation_results = []
        for case in perturbation_cases:
            case_id = case["case_id"]
            question_text = case["question"]
            print(f"\nCaso de Perturbação [{case_id}] -> {question_text}")

            # Gerar embedding real da pergunta
            print("Gerando embedding da pergunta...")
            vector = generate_embedding(question_text)

            # C1 - Contexto Correto
            print("Injetando Contexto Correto (C1)...")
            point_id_c1 = str(uuid.uuid4())
            qdrant_client.upsert(
                collection_name=settings.collection_name,
                points=[
                    PointStruct(
                        id=point_id_c1,
                        vector={settings.qdrant_vector_name: vector}
                        if settings.qdrant_vector_name
                        else vector,
                        payload={
                            "content": case["correct_context"],
                            "source_file": "eval_temp_correct.pdf",
                            "pagina_pdf": 1,
                            "chunk_index": 0,
                        },
                    )
                ],
            )

            print("Executando query C1...")
            res_c1 = run_chat_query(token, question_text)

            # Deletar ponto C1
            qdrant_client.delete(
                collection_name=settings.collection_name,
                points_selector=PointIdsList(points=[point_id_c1]),
            )

            # C2 - Contexto Perturbado
            print("Injetando Contexto Perturbado (C2)...")
            point_id_c2 = str(uuid.uuid4())
            qdrant_client.upsert(
                collection_name=settings.collection_name,
                points=[
                    PointStruct(
                        id=point_id_c2,
                        vector={settings.qdrant_vector_name: vector}
                        if settings.qdrant_vector_name
                        else vector,
                        payload={
                            "content": case["perturbed_context"],
                            "source_file": "eval_temp_perturbed.pdf",
                            "pagina_pdf": 1,
                            "chunk_index": 0,
                        },
                    )
                ],
            )

            print("Executando query C2...")
            res_c2 = run_chat_query(token, question_text)

            # Deletar ponto C2
            qdrant_client.delete(
                collection_name=settings.collection_name,
                points_selector=PointIdsList(points=[point_id_c2]),
            )

            perturbation_results.append(
                {
                    "case_id": case_id,
                    "question": question_text,
                    "correct_context": case["correct_context"],
                    "perturbed_context": case["perturbed_context"],
                    "c1_response": res_c1,
                    "c2_response": res_c2,
                }
            )
            time.sleep(2.0)

        # =====================================================================
        # 4. PROCESSAMENTO E CÁLCULO DE MÉTRICAS REAIS
        # =====================================================================
        print("\n--- Calculando Métricas Experimentais ---")

        # Filtro de Intenção (Domínio) - A1-A5 devem ser SIM, B1-B5 devem ser NAO
        # No sistema real, perguntas B1-B5 são bloqueadas e respondem com a mensagem padrão de extracampo.
        # Portanto, se recusar a responder B1-B5 é True Negative (TN), e responder A1-A5 é True Positive (TP).

        # Proposto Domain Metrics
        tp, fp, tn, fn = 0, 0, 0, 0
        for r in proposed_results:
            is_agri = r["category"] == "agricultura_valida"
            refused = check_refusal(r["response"]["answer"])
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

        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        # Taxa de Recusa Correta (extracampo)
        extracampo_count = sum(1 for r in proposed_results if r["category"] == "extracampo")
        correct_refusal_count = sum(
            1
            for r in proposed_results
            if r["category"] == "extracampo" and check_refusal(r["response"]["answer"])
        )
        taxa_recusa_correta = (
            correct_refusal_count / extracampo_count if extracampo_count > 0 else 0
        )

        # Taxa de Aceitação Correta (agricultura_valida)
        valida_count = sum(1 for r in proposed_results if r["category"] == "agricultura_valida")
        correct_acceptance_count = sum(
            1
            for r in proposed_results
            if r["category"] == "agricultura_valida" and not check_refusal(r["response"]["answer"])
        )
        taxa_aceitacao_correta = correct_acceptance_count / valida_count if valida_count > 0 else 0

        # Taxa de Detecção de Alucinação (Grupo C - premissa falsa)
        # O pipeline deve recusar (retornar fallback / desculpas) ou indicar que o fato não existe.
        adversarial_count = sum(1 for r in proposed_results if r["category"] == "premissa_falsa")
        detected_adversarial = sum(
            1
            for r in proposed_results
            if r["category"] == "premissa_falsa"
            and (
                check_refusal(r["response"]["answer"])
                or any(
                    kw in r["response"]["answer"].lower()
                    for kw in ["não existe", "não há", "falso", "criptonita", "urânio"]
                )
            )
        )
        taxa_detecao_alucinacao = (
            detected_adversarial / adversarial_count if adversarial_count > 0 else 0
        )

        # Latência e Custos
        baseline_latencies = [
            r["response"]["latency"] for r in baseline_results if r["response"]["success"]
        ]
        proposed_latencies = [
            r["response"]["latency"] for r in proposed_results if r["response"]["success"]
        ]

        avg_lat_baseline = (
            sum(baseline_latencies) / len(baseline_latencies) if baseline_latencies else 0
        )
        avg_lat_proposed = (
            sum(proposed_latencies) / len(proposed_latencies) if proposed_latencies else 0
        )

        # Salvar resultados e métricas
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        summary_results = {
            "metrics": {
                "domain_accuracy": accuracy,
                "domain_precision": precision,
                "domain_recall": recall,
                "domain_f1": f1,
                "taxa_recusa_correta_extracampo": taxa_recusa_correta,
                "taxa_aceitacao_correta_agri": taxa_aceitacao_correta,
                "taxa_deteccao_alucinacao_adversarial": taxa_detecao_alucinacao,
                "latencia_media_baseline": avg_lat_baseline,
                "latencia_media_proposto": avg_lat_proposed,
                "amostras_avaliadas": len(questions),
            },
            "baseline_raw": baseline_results,
            "proposed_raw": proposed_results,
            "perturbation_raw": perturbation_results,
        }

        output_json = RESULTS_DIR / "raw_experiment_results.json"
        with open(output_json, "w", encoding="utf-8") as out_f:
            json.dump(summary_results, out_f, ensure_ascii=False, indent=2)

        print(f"\nResultados brutos e métricas salvos em: {output_json}")

        # Salvar um resumo CSV das execuções
        output_csv = RESULTS_DIR / "experiment_summary.csv"
        with open(output_csv, "w", encoding="utf-8") as out_c:
            out_c.write(
                "question_id,category,baseline_answer,proposed_answer,baseline_latency,proposed_latency,proposed_score\n"
            )
            for br, pr in zip(baseline_results, proposed_results, strict=True):
                qid = br["question_id"]
                cat = br["category"]
                b_ans = br["response"]["answer"].replace("\n", " ").replace(",", ";")[:60]
                p_ans = pr["response"]["answer"].replace("\n", " ").replace(",", ";")[:60]
                b_lat = f"{br['response']['latency']:.2f}"
                p_lat = f"{pr['response']['latency']:.2f}"
                p_score = f"{pr['response']['hallucination_score']:.2f}"
                out_c.write(f"{qid},{cat},{b_ans},{p_ans},{b_lat},{p_lat},{p_score}\n")

        print(f"Resumo CSV salvo em: {output_csv}")

        # Imprimir estatísticas resumidas
        print("\n================ STATS SUMMARY ================")
        print(f"Acurácia do Filtro de Domínio:  {accuracy:.2%}")
        print(f"Precisão do Filtro de Domínio: {precision:.2%}")
        print(f"Recall do Filtro de Domínio:    {recall:.2%}")
        print(f"F1-Score do Filtro de Domínio:  {f1:.2%}")
        print(f"Taxa de Recusa Correta (B):    {taxa_recusa_correta:.2%}")
        print(f"Taxa de Aceitação Correta (A): {taxa_aceitacao_correta:.2%}")
        print(f"Taxa de Detecção de Alucinação:{taxa_detecao_alucinacao:.2%}")
        print(f"Latência Média Baseline:       {avg_lat_baseline:.2f}s")
        print(f"Latência Média Proposto:       {avg_lat_proposed:.2f}s")
        print("===============================================")

    finally:
        # Restaurar .env original e recarregar
        print("\nRestaurando configurações originais do .env...")
        ENV_PATH.write_text(original_env_content, encoding="utf-8")
        if MAIN_PATH.exists():
            os.utime(str(MAIN_PATH), None)
        print("Ambiente restaurado e servidor Uvicorn recarregado.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
