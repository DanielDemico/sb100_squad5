"""
Automatic LLM judging.

Compares SB100 answers with reference answers using an LLM judge.
The judge provides a numeric score (0-10), a justification and a verdict.

Usage:
    python eval/judge.py
    python eval/judge.py --model llama-3.3-70b-versatile --provider groq
"""

from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime

from tqdm import tqdm

# Allow `from eval._utils import ...` when run standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._utils import (
    DEFAULT_EVAL_RESULTS_PATH,
    DEFAULT_JUDGED_RESULTS_PATH,
    deterministic_sb100_position_is_a,
    validate_dataset_schema,
)

# Default provider
DEFAULT_PROVIDER = "groq"

# Default judge model (distinct from the reference models)
DEFAULT_JUDGE_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "ollama": "llama3:70b",
    "openrouter": "google/gemma-4-31b-it",
}

# OpenRouter configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Judge prompt - requests score, justification and verdict
JUDGE_PROMPT_TEMPLATE = """You are an evaluator specialized in agronomy. Your task is to compare
two answers to a technical question and decide which one is better.

**Question:**
{question}

**Answer A:**
{answer_a}

**Answer B:**
{answer_b}

**Evaluation instructions:**
1. Assess technical accuracy, completeness, clarity and practical usefulness
2. Check whether the information is correct for the Brazilian agricultural context
3. Penalize answers that are vague, incorrect or do not address the question

**Response format (strict JSON):**
{{
    "score_a": <0-10>,
    "score_b": <0-10>,
    "justification": "<2-3 sentence explanation, written in Portuguese (pt-BR)>",
    "verdict": "<A_better|B_better|equivalent>"
}}

Reply ONLY with the JSON, no extra text."""


def judge_groq(
    question: str,
    answer_a: str,
    answer_b: str,
    model: str,
) -> dict:
    """Run the judgment using the Groq API."""
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # Low temperature for consistency
        max_tokens=500,
    )

    return parse_judge_response(response.choices[0].message.content)


def judge_ollama(
    question: str,
    answer_a: str,
    answer_b: str,
    model: str,
) -> dict:
    """Run the judgment using local Ollama."""
    import ollama

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
    )

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return parse_judge_response(response["message"]["content"])


def judge_openrouter(
    question: str,
    answer_a: str,
    answer_b: str,
    model: str,
) -> dict:
    """Run the judgment using the OpenRouter API (Gemma 4, etc)."""
    from openai import OpenAI

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
    )

    return parse_judge_response(response.choices[0].message.content)


def parse_judge_response(content: str) -> dict:
    """Extract fields from the judge's JSON response."""
    # Try to extract JSON
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return {
                "score_a": float(data.get("score_a", 5)),
                "score_b": float(data.get("score_b", 5)),
                "justification": str(data.get("justification", "")),
                "verdict": str(data.get("verdict", "equivalent")),
            }
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: neutral values
    return {
        "score_a": 5.0,
        "score_b": 5.0,
        "justification": f"[PARSE ERROR] {content[:200]}",
        "verdict": "equivalent",
    }


def normalize_verdict(verdict: str, sb100_was_a: bool) -> str:
    """
    Normalize the verdict to the SB100 perspective.

    Args:
        verdict: Original verdict (A_better, B_better, equivalent)
        sb100_was_a: Whether SB100 was in position A

    Returns:
        Normalized verdict (better, worse, equivalent)
    """
    verdict = verdict.lower().strip()

    if "equivalent" in verdict or "equal" in verdict:
        return "equivalent"

    if "a_better" in verdict or "a better" in verdict:
        return "better" if sb100_was_a else "worse"

    if "b_better" in verdict or "b better" in verdict:
        return "worse" if sb100_was_a else "better"

    return "equivalent"


def run_judge(
    input_path: str = str(DEFAULT_EVAL_RESULTS_PATH),
    output_path: str = str(DEFAULT_JUDGED_RESULTS_PATH),
    provider: str = DEFAULT_PROVIDER,
    model: str | None = None,
    concurrent: int = 1,
) -> dict:
    """
    Run the judgment for every comparison.

    QUALITY: long-function-justification - provider selection, A/B assignment,
    judge invocation, SB100-perspective normalization, artifact write, and summary
    statistics are one deterministic judging transaction.

    Args:
        input_path: Path to the dataset with evaluation results
        output_path: Path to the output file
        provider: LLM provider (groq or ollama)
        model: Judge model
        concurrent: Number of concurrent workers (default: 1)

    Returns:
        Dataset with judgments
    """
    if model is None:
        model = DEFAULT_JUDGE_MODELS[provider]

    judge_fns = {
        "groq": judge_groq,
        "ollama": judge_ollama,
        "openrouter": judge_openrouter,
    }
    judge_fn = judge_fns[provider]

    # Load dataset
    with open(input_path, encoding="utf-8") as f:
        dataset = json.load(f)

    validate_dataset_schema(dataset, ["metadata", "results"])

    results = dataset["results"]
    print(f"Loaded {len(results)} results from {input_path}")
    print(f"Judge model: {model} ({provider}), concurrent workers: {concurrent}")

    # Load existing judged items for resume support
    existing_judged = {}
    out_file = Path(output_path)
    if out_file.exists():
        try:
            with open(out_file, encoding="utf-8") as f:
                prev_data = json.load(f)
                for r in prev_data.get("results", []):
                    if r.get("judgments"):
                        existing_judged[r["question_id"]] = r
            if existing_judged:
                print(f"Resuming judgment: {len(existing_judged)} items already judged.")
        except Exception:
            pass

    def process_result(result: dict) -> dict:
        """Process a single evaluation result with LLM judging.

        # QUALITY: long-function-justification - deterministic A/B position,
        # reference filtering, LLM judge execution, score normalization, and error
        # mapping are one judgment unit.
        """
        qid = result.get("question_id", "")
        if qid in existing_judged:
            return existing_judged[qid]

        sb100_answer = result.get("sb100_answer", "")
        reference_answers = result.get("reference_answers", [])

        if not result.get("sb100_success", True):
            return {
                **result,
                "judgments": [],
            }

        judgments = []

        for ref in reference_answers:
            ref_model = ref.get("reference_model") or ref.get("model", "unknown")
            ref_answer = ref.get("reference_answer") or ref.get("answer")
            ref_error = ref.get("error")

            if (
                ref_error is not None
                or not ref_answer
                or (isinstance(ref_answer, str) and ref_answer.startswith("[ERRO]"))
            ):
                continue

            sb100_is_a = deterministic_sb100_position_is_a(qid)

            if sb100_is_a:
                answer_a, answer_b = sb100_answer, ref_answer
            else:
                answer_a, answer_b = ref_answer, sb100_answer

            try:
                judge_result = judge_fn(
                    result["question"],
                    answer_a,
                    answer_b,
                    model,
                )

                if sb100_is_a:
                    sb100_score = judge_result["score_a"]
                    ref_score = judge_result["score_b"]
                else:
                    sb100_score = judge_result["score_b"]
                    ref_score = judge_result["score_a"]

                verdict = normalize_verdict(judge_result["verdict"], sb100_is_a)

                judgments.append(
                    {
                        "reference_model": ref_model,
                        "judge_score": sb100_score,
                        "reference_score": ref_score,
                        "judge_verdict": verdict,
                        "judge_justification": judge_result["justification"],
                        "sb100_position": "A" if sb100_is_a else "B",
                    }
                )

            except Exception as e:
                judgments.append(
                    {
                        "reference_model": ref_model,
                        "judge_score": None,
                        "reference_score": None,
                        "judge_verdict": "error",
                        "judge_justification": f"[ERROR] {str(e)}",
                        "sb100_position": "A" if sb100_is_a else "B",
                    }
                )

        top_score = judgments[0]["judge_score"] if judgments else None
        top_justification = judgments[0]["judge_justification"] if judgments else None
        return {
            **result,
            "judge_score": top_score,
            "judge_justification": top_justification,
            "judgments": judgments,
        }

    # Process each result with optional concurrency
    judged_results = []
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if concurrent > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            for item in tqdm(executor.map(process_result, results), total=len(results), desc="Judging answers"):
                judged_results.append(item)
                if len(judged_results) % 10 == 0:
                    tmp_dataset = {
                        "metadata": {
                            **dataset.get("metadata", {}),
                            "judge_model": model,
                            "judge_provider": provider,
                            "judged_at": datetime.now(UTC).isoformat(),
                        },
                        "results": judged_results,
                    }
                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(tmp_dataset, f, ensure_ascii=False, indent=2)
    else:
        for r in tqdm(results, desc="Judging answers"):
            item = process_result(r)
            judged_results.append(item)
            if len(judged_results) % 10 == 0:
                tmp_dataset = {
                    "metadata": {
                        **dataset.get("metadata", {}),
                        "judge_model": model,
                        "judge_provider": provider,
                        "judged_at": datetime.now(UTC).isoformat(),
                    },
                    "results": judged_results,
                }
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(tmp_dataset, f, ensure_ascii=False, indent=2)

    # Build final dataset
    judged_dataset = {
        "metadata": {
            **dataset.get("metadata", {}),
            "judge_model": model,
            "judge_provider": provider,
            "judged_at": datetime.now(UTC).isoformat(),
        },
        "results": judged_results,
    }

    # Save results
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(judged_dataset, f, ensure_ascii=False, indent=2)

    print(f"\nJudged results saved to: {output}")

    # Quick statistics
    all_judgments = [j for r in judged_results for j in r.get("judgments", [])]
    valid = [j for j in all_judgments if j.get("judge_score") is not None]

    if valid:
        avg_score = sum(j["judge_score"] for j in valid) / len(valid)
        better = sum(1 for j in valid if j["judge_verdict"] == "better")
        equiv = sum(1 for j in valid if j["judge_verdict"] == "equivalent")
        worse = sum(1 for j in valid if j["judge_verdict"] == "worse")

        print(f"SB100 average score: {avg_score:.2f}")
        print(f"Verdicts: better={better}, equivalent={equiv}, worse={worse}")

    return judged_dataset


def main():
    """Parse CLI options and run automatic judging.

    QUALITY: long-function-justification - argument parsing, credential validation,
    input validation, judge execution, and exit code are one CLI entrypoint.
    """
    parser = argparse.ArgumentParser(description="Run automatic judgment of the answers")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_EVAL_RESULTS_PATH),
        help=f"Path to the evaluation results (default: {DEFAULT_EVAL_RESULTS_PATH})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_JUDGED_RESULTS_PATH),
        help=f"Path to the output file (default: {DEFAULT_JUDGED_RESULTS_PATH})",
    )
    parser.add_argument(
        "--provider",
        choices=["groq", "ollama", "openrouter"],
        default=DEFAULT_PROVIDER,
        help=f"LLM provider (default: {DEFAULT_PROVIDER})",
    )
    parser.add_argument(
        "--model",
        help="Judge model (default depends on provider)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="Concurrent requests (default: 1)",
    )

    args = parser.parse_args()

    # Validate provider
    if args.provider == "groq" and not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not set. Use --provider ollama or set the variable.")
        return 1

    if args.provider == "openrouter" and not os.environ.get("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY not set. Use --provider ollama or set the variable.")
        return 1

    # Check that the input file exists
    if not Path(args.input).exists():
        print(f"Error: input file not found: {args.input}")
        print("Run first: python eval/run_evaluation.py")
        return 1

    # Run judgment
    run_judge(
        input_path=args.input,
        output_path=args.output,
        provider=args.provider,
        model=args.model,
        concurrent=args.concurrent,
    )

    return 0


if __name__ == "__main__":
    exit(main())
