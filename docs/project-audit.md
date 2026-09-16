# Relatório de Auditoria Técnica Completa — SmartB100 (Squad 5)

**Data da Auditoria:** 16 de Setembro de 2026  
**Auditor:** Staff Software Engineer & Software Architect AI  
**Escopo:** Auditoria completa de código, arquitetura, testes, modelo de dados, regras de negócio, convenções e infraestrutura.

---

## 1. Resumo Executivo

O **SmartB100** é um assistente RAG (Retrieval-Augmented Generation) especializado no domínio agrícola. Ele permite a agrônomos, técnicos de extensão rural e produtores realizar perguntas em linguagem natural e receber respostas fundamentadas em manuais e boletins técnicos em PDF (por exemplo, materiais da Embrapa), com respostas personalizadas ao nível de conhecimento do usuário (`beginner`, `intermediate`, `expert`) e acompanhadas de uma pontuação contínua de alucinação (0.0 a 1.0) calculada por **Entropia Semântica Multi-provedor**.

### Principais Achados
1. **Arquitetura Sólida de Monólito Modular**: O sistema é implementado como um único processo FastAPI que executa chamadas de função diretas em memória entre 8 camadas internas bem delimitadas (`api`, `core`, `database`, `retrieval`, `generation`, `memory`, `verification`, `agent`).
2. **Fonte Única de Verdade de Contratos**: Todos os contratos e DTOs públicos e intercamadas estão centralizados em `core/schemas.py`.
3. **Isolamento Estrito da Camada `core`**: O teste arquitetural automatizado `tests/test_quality_architecture.py` garante que `core` não importe nenhuma camada externa ou de infraestrutura.
4. **Qualidade e Testes de Alta Cobertura**: A suíte de testes possui **344 testes** com cobertura de código de **78.71%** (limiar do CI configurado em 23%).
5. **Débito Técnico Identificado**: Um teste de qualidade (`test_quality_architecture.py::test_audited_functions_over_20_logical_lines_are_justified`) falha devido a 10 funções em `agent/profiling.py` e `eval/empirical/` que excedem 20 linhas lógicas sem a marcação explicita `# QUALITY: long-function-justification`.

---

## 2. Inventário do Repositório

### 2.1. Estrutura de Diretórios
* `api/`: Processo web FastAPI, dependências de autenticação (JWT/bcrypt) e rotas (`/chat`, `/auth/register`, `/auth/token`, `/conversations`, `/health`).
* `core/`: Schemas Pydantic centralizados (`schemas.py`), configurações de ambiente (`config.py`), clientes Ollama (`ollama_clients.py`) e utilitários de embedding (`embeddings.py`).
* `database/`: Conexão SQLite (`db.py`), modelos SQLAlchemy (`models.py`) e pipeline de fragmentação semântica de PDFs (`semantic_chunker.py`).
* `retrieval/`: Integração com o banco vetorial Qdrant (`vector_store.py`) na coleção `archives_v2` (768 dimensões) e gerador de embeddings (`embedder.py`).
* `generation/`: Gerador de respostas LLM via Ollama (`llama3.2:3b`) com prompts adaptativos por nível de expertise (`llm.py`).
* `memory/`: Buffer circular em memória (`conversation.py`) utilizando `collections.deque(maxlen=10)` para manter o histórico por sessão.
* `verification/`: Avaliador de incerteza por Entropia Semântica (`entropy.py`) e Verification Gate com fallback neutro (`0.5`) e retentativas (`gate.py`).
* `agent/`: Orquestração avançada com agentes (`runner.py`), classificação de intenção de domínio agrícola (`intent.py`), ferramentas (`tools.py`) e profiling dinâmico (`profiling.py`).
* `ui/`: Interface web Gradio (`chat_ui.py`) que consome a API HTTP `/chat`.
* `eval/`: Pipeline de avaliação empírica de 5 etapas para acurácia, relevância, alucinação e profiling.
* `tests/`: Suíte completa de testes unitários, de integração e de arquitetura.
* `.agents/skills/`: Diretório de habilidades permanentes do projeto.

---

## 3. Arquitetura Detalhada e Fluxo de Dados

### 3.1. Visão Arquitetural
```
   [ Interface UI Gradio / Cliente HTTP ]
                     │
                     ▼
           [ API Layer (FastAPI) ]
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
 [ Autenticação JWT ]    [ RAG / Agent Handler ]
 (SQLite DB: Users)               │
                                  ├──────────────────────────┐
                                  ▼                          ▼
                         [ Retrieval Layer ]        [ Memory Layer ]
                         (Qdrant archives_v2)       (FIFO Deque maxlen=10)
                                  │                          │
                                  └────────────┬─────────────┘
                                               ▼
                                   [ Generation Layer ]
                                   (Ollama llama3.2:3b)
                                               │
                                               ▼
                                  [ Verification Layer ]
                              (Entropia Semântica Multi-provedor)
                                               │
                                               ▼
                                      [ ChatResponse ]
                               {answer, hallucination_score}
```

### 3.2. Fluxo Ponta a Ponta do `/chat`
1. **Recepção**: O cliente envia `POST /chat` com JWT, `session_id`, `question` e `profile`.
2. **Autenticação e Taxa Limite**: O token JWT é validado via `api/dependencies.py`.
3. **Histórico de Conversa**: O histórico recente é recuperado ou inicializado em `memory/conversation.py`.
4. **Recuperação Vetorial (Retrieval)**: A pergunta é convertida em vetor de 768 dims via `nomic-embed-text` e o Qdrant busca os `top_k` chunks mais similares na coleção `archives_v2`.
5. **Geração Personalizada**: O módulo `generation/llm.py` monta o prompt do sistema injetando o nível de expertise (`beginner`, `intermediate`, `expert`), contexto dos PDFs e aviso anti-injeção.
6. **Verificação de Alucinação**: Se `VERIFICATION_ENABLED=true`, o `verification/gate.py` chama a incerteza de entropia semântica (`verification/entropy.py`). Se a incerteza for alta, realiza retentativas. Se o serviço de verificação falhar, retorna o Score Neutro (`0.5`) sem derrubar a resposta.
7. **Persistência e Retorno**: A pergunta, resposta e fontes recuperadas são registradas no SQLite e o `ChatResponse` é retornado ao cliente.

---

## 4. Auditoria da Suíte de Testes e Qualidade

### 4.1. Cobertura e Resultados Reais
* **Ferramenta de Execução**: `uv run --extra dev pytest tests/ -m "not requires_infra"`
* **Total de Testes**: 344 coletados.
* **Resultado**: 330 APROVADOS, 13 IGNORADOS (requerem infraestrutura ativa Qdrant/Ollama), 1 FALHA.
* **Cobertura Global de Código**: **78.71%** (superior ao mínimo de 23% exigido no `pyproject.toml`).
* **Linter (Ruff)**: `uv run --extra dev ruff check .` -> **0 erros encontrados**.
* **Type Checker (MyPy)**: `uv run mypy retrieval generation memory verification --strict` -> **0 erros encontrados**.

### 4.2. Falha de Qualidade Identificada
* **Teste Afetado**: `tests/test_quality_architecture.py::test_audited_functions_over_20_logical_lines_are_justified`
* **Causa**: Funções que excedem 20 linhas lógicas sem anotação `# QUALITY: long-function-justification`:
  - `agent/profiling.py:172 classify_user_profile (60 linhas)`
  - `agent/profiling.py:250 evaluate_disparity_and_reclassify (33 linhas)`
  - `eval/empirical/runner.py:32 main (132 linhas)`
  - Múltiplas funções em `eval/empirical/test_*.py`

---

## 5. Matriz de Riscos e Débitos Técnicos

| ID | Descrição do Risco / Débito | Severidade | Impacto | Recomendação |
|---|---|---|---|---|
| **DT-01** | Funções com >20 linhas lógicas reprovando no teste de arquitetura | Média | Impede que a suíte passe 100% limpa no CI | Refatorar funções ou adicionar anotação `# QUALITY: long-function-justification` |
| **DT-02** | Banco de dados SQLite é single-writer | Média | Limita escalabilidade horizontal em múltiplos pods | Manter SQLite no MVP; migrar para PostgreSQL em produção massiva |
| **DT-03** | Latência de inferência local Ollama em CPU | Média | Requisições podem estourar timeout HTTP padrão | Manter `CHAT_TIMEOUT=600` e suporte a provedores de cloud (Groq/OpenRouter) |
| **DT-04** | Dependência de `dev` opcional para rodar cobertura/ruff no env base | Baixa | Desenvolvedor pode ter erro de import se não usar `uv run --extra dev` | Padronizar uso do `uv` na documentação e scripts |

---

## 6. Conclusão da Auditoria

O projeto SmartB100 apresenta excelente organização modular, regras de contrato bem definidas em `core/schemas.py`, rigor na separação de responsabilidades e cobertura de testes sólida. A aplicação das diretrizes de TDD e o respeito ao isolamento da camada `core` garantem a sustentabilidade do sistema para novas evoluções.
