# Evaluation Pipeline and Empirical Test Suite - SB100

Automated pipeline for evaluating the SB100 Science RAG system and running empirical profile classification and dynamic reclassification benchmarks.

## Repository Structure

```
eval/
├── dataset/
│   ├── .gitkeep
│   ├── questions.json                  # Generated questions (generate_questions.py)
│   ├── reference_answers.json          # Questions + reference answers
│   ├── profile_classification.json     # 300 labeled profile questions
│   └── reclassification_sequences.json # Dynamic reclassification test sequences
├── datasets/
│   ├── .gitkeep
│   ├── questions.json
│   ├── reference_answers.json
│   ├── profile_classification.json
│   └── reclassification_sequences.json
├── results/
│   ├── .gitkeep
│   ├── evaluation_results.json         # SB100 evaluation answers
│   ├── judged_results.json             # LLM judgments
│   ├── report.md                       # Summary report
│   ├── human_sample.csv                # Sample for human validation
│   ├── empirical_results.json          # Empirical tests output (JSON)
│   └── empirical_results.md            # Empirical tests report (Markdown)
├── empirical/
│   ├── runner.py                       # Master runner for empirical tests
│   ├── test_profile_classification.py # 300 questions classification test
│   ├── test_dynamic_reclassification.py # Reclassification & hysteresis test
│   ├── test_personalization.py        # Answer personalization test
│   ├── test_explainability.py         # XAI justifications test
│   ├── test_traceability.py           # Source traceability test
│   ├── test_robustness.py             # Robustness & edge cases test
│   ├── test_performance.py            # Latency and performance test
│   └── README.md
├── generate_questions.py               # Generates questions from documents
├── collect_references.py               # Collects answers from reference models
├── run_evaluation.py                   # Runs questions against the SB100
├── judge.py                            # Automatic LLM judging
├── report.py                           # Generates report and human sample
└── README.md
```

## Requirements

- Python 3.11+
- Project dependencies (`pip install -r requirements.txt` or `pip install -e .`)
- **For Groq API**: `GROQ_API_KEY` environment variable set
- **For Ollama**: Local Ollama server running with required models installed
- **For `run_evaluation.py`**: evaluation credentials, since `POST /chat` is authenticated — `EVAL_API_TOKEN`, or `EVAL_USERNAME`/`EVAL_PASSWORD` for a user registered via `POST /auth/register`

## Full Evaluation Workflow

### 1. Generate Questions

Extracts agriculture-domain questions from PDF/TXT documents and formats them into a structured dataset:

```bash
# Using PDF document argument
python eval/generate_questions.py ./archives/smart_boletim.pdf --num-questions 300

# Using directory input and local Ollama
python eval/generate_questions.py ./archives/ --num-questions 300 --provider ollama
```

**Output:** `eval/dataset/questions.json`

### 2. Collect Reference Answers

Iterates over generated questions and collects reference answers from open-source models:

```bash
# Using Groq API (default)
python eval/collect_references.py

# Using Ollama
python eval/collect_references.py --provider ollama

# Custom models
python eval/collect_references.py --models llama3:8b,mistral:7b --provider ollama
```

**Output:** `eval/dataset/reference_answers.json`

### 3. Run SB100 System Evaluation

Executes questions against the authenticated `POST /chat` endpoint:

```bash
# Ensure API server is running (e.g. uvicorn api.main:app or start.bat)
export EVAL_USERNAME=your_eval_user
export EVAL_PASSWORD=your_eval_password

python eval/run_evaluation.py
```

**Output:** `eval/results/evaluation_results.json`

### 4. Automatic LLM Judging

Compares SB100 answers with reference models using an LLM judge:

```bash
python eval/judge.py
```

**Output:** `eval/results/judged_results.json`

### 5. Generate Evaluation Report

Generates statistical summary reports and human validation samples:

```bash
python eval/report.py --sample-size 30
```

**Outputs:**
- `eval/results/report.md`
- `eval/results/human_sample.csv`

---

## Running Empirical Tests (`eval/empirical`)

The empirical test suite evaluates user profile classification (Leigo, Caipira, Técnico), dynamic profile reclassification, XAI explainability, traceability, robustness, and performance metrics.

### Run All Empirical Tests (Master Runner)

```bash
python -m eval.empirical.runner
```

or:

```bash
python eval/empirical/runner.py
```

### Run Individual Empirical Test Modules

```bash
# Profile Classification (300 questions)
pytest eval/empirical/test_profile_classification.py

# Dynamic Reclassification and Hysteresis
pytest eval/empirical/test_dynamic_reclassification.py

# Personalization
pytest eval/empirical/test_personalization.py

# XAI Justifications
pytest eval/empirical/test_explainability.py

# Traceability
pytest eval/empirical/test_traceability.py

# Robustness and Edge Cases
pytest eval/empirical/test_robustness.py

# Performance Metrics
pytest eval/empirical/test_performance.py
```

**Empirical Outputs:**
- `eval/results/empirical_results.json`
- `eval/results/empirical_results.md`

---

## Script Options Reference

### generate_questions.py

| Option | Description | Default |
|--------|-------------|---------|
| `input` | File or directory with documents | (required) |
| `--num-questions` | Number of questions to generate | 300 |
| `--provider` | LLM provider (groq/ollama/openrouter) | groq |
| `--model` | LLM model | (depends on provider) |
| `--output` | Output file | eval/dataset/questions.json |

### collect_references.py

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Question dataset | eval/dataset/questions.json |
| `--output` | Output file | eval/dataset/reference_answers.json |
| `--provider` | LLM provider (groq/ollama/openrouter) | groq |
| `--models` | Comma-separated models | (depends on provider) |

### run_evaluation.py

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Dataset with references | eval/dataset/reference_answers.json |
| `--output` | Output file | eval/results/evaluation_results.json |
| `--api-url` | SB100 API URL | http://localhost:8000 |
| `--concurrent` | Concurrent requests | 1 |

### judge.py

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Evaluation results | eval/results/evaluation_results.json |
| `--output` | Output file | eval/results/judged_results.json |
| `--provider` | LLM provider (groq/ollama) | groq |
| `--model` | Judge model | llama-3.1-70b-versatile |

### report.py

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Judged results | eval/results/judged_results.json |
| `--report` | Report file | eval/results/report.md |
| `--sample` | Sample CSV file | eval/results/human_sample.csv |
| `--sample-size` | Sample size | 30 |

## Notes

- The evaluation pipeline uses deterministic seeding (`random.seed(42)`) for reproducible runs.
- The judge alternates position assignments (50%/50%) to prevent position bias.
- Directory `.gitkeep` files are maintained in `eval/dataset/` and `eval/results/` to ensure workspace integrity in Git.
