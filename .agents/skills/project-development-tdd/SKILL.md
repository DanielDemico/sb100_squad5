---
name: project-development-tdd
description: Manual operacional permanente e reutilizável de desenvolvimento com TDD obrigatório, regras arquiteturais e fluxo de trabalho do SmartB100 (Squad 5).
---

# SmartB100 — Project Development & TDD Skill

Este documento é o manual operacional obrigatório para qualquer agente de IA ou desenvolvedor executando tarefas neste repositório. Ele estabelece as regras de arquitetura, desenvolvimento orientado a testes (TDD), validação funcional e workflow padronizado.

---

## 1. Contexto Geral do Projeto

### 1.1. Propósito do Sistema
O **SmartB100** é um assistente de suporte técnico agrícola baseado em RAG (Retrieval-Augmented Generation). Ele converte manuais e boletins técnicos em PDF em uma IA conversacional fundamentada que:
1. Responde a dúvidas sobre manejo de culturas, solos e pragas utilizando exclusivamente trechos recuperados dos manuais indexados.
2. Adapta o nível de detalhamento e vocabulário ao perfil de expertise do usuário (`beginner`, `intermediate`, `expert`).
3. Atribui uma pontuação contínua de alucinação (0.0 a 1.0) a cada resposta via **Entropia Semântica Multi-provedor**.
4. Oferece API REST autenticada (JWT + bcrypt) e interface web Gradio.

### 1.2. Stack Tecnológica
* **Linguagem & Runtime**: Python 3.12+ (gerenciado via `uv`).
* **API / Backend**: FastAPI + Uvicorn.
* **Banco Vetorial**: Qdrant (`archives_v2`, 768 dimensões, modelo `nomic-embed-text`).
* **Inexistência / Inferência LLM**: Ollama (`llama3.2:3b`) local, com suporte a Groq e OpenRouter.
* **Banco de Dados Relacional**: SQLite (`smartb100_v2.db`, SQLAlchemy ORM).
* **Autenticação**: bcrypt + JWT (Passlib, PyJWT, SlowAPI rate-limiting).
* **Qualidade & Testes**: Pytest, Pytest-cov, Ruff, MyPy (`--strict`).

### 1.3. Pontos de Entrada (Entry Points)
* `api/main.py`: Aplicação FastAPI principal (`uvicorn api.main:app`).
* `ui/chat_ui.py`: Interface web Gradio.
* `database/semantic_chunker.py`: Pipeline de ingestão e indexação de PDFs em CLI (`python database/semantic_chunker.py index ./archives/`).
* `eval/empirical/runner.py`: Executor do pipeline empírico de testes e métricas.

---

## 2. Como Explorar o Projeto

Antes de alterar qualquer código ou planejar alterações:
1. **Contratos Públicos**: Consulte obrigatoriamente `core/schemas.py`. É a fonte única da verdade para DTOs e tipos trocados entre módulos.
2. **Arquitetura & ADRs**: Leia `ARCHITECTURE.md` e as decisões arquiteturais em `docs/adr/`.
3. **Mapeamento de Fluxo**:
   - Rotas HTTP: `api/routes/` (`chat.py`, `auth.py`, `conversations.py`, `health.py`).
   - Busca Vetorial: `retrieval/vector_store.py` e `retrieval/embedder.py`.
   - Geração: `generation/llm.py`.
   - Verificação: `verification/gate.py` e `verification/entropy.py`.
   - Agentes & Profiling: `agent/runner.py`, `agent/intent.py` e `agent/profiling.py`.
4. **Localização de Testes**: Todo módulo sob `[modulo]/` possui testes correspondentes em `tests/test_[modulo].py`.

---

## 3. Regras Arquiteturais e Restrições

### 3.1. Padrão Monólito Modular
* Todo o código de produção executa no mesmo processo Python.
* A comunicação entre camadas ocorre via **chamadas de função diretas**, sem filas de mensagens ou rede interna.

### 3.2. Regra Estrita de Dependência de Camadas
A direção de dependência permitida é:
`api -> core`, `database`, `retrieval`, `generation`, `verification`, `agent`

**Regra Crítica**: A camada `core/` NÃO PODE importar nenhuma outra camada (`api`, `database`, `retrieval`, `generation`, `memory`, `verification`, `agent`, `ui`). Essa regra é auditada automaticamente por `tests/test_quality_architecture.py`.

### 3.3. Preservação Arquitetural e de Artefatos Científicos
A menos que a task solicite explicitamente:
* NUNCA altere a estrutura de diretórios ou renomeie/mova arquivos.
* NUNCA substitua a arquitetura existente nem adicione dependências pesadas sem aprovação.
* NUNCA modifique, apague ou regenerar artefatos científicos:
  - `eval/dataset/`
  - `eval/results/`
  - `archives/smart_boletim.pdf`

---

## 4. TDD Obrigatório (RED → GREEN → REFACTOR)

Toda nova funcionalidade, correção de bug ou alteração comportamental DEVE seguir estritamente o ciclo TDD:

```
    ┌──────────┐      1. Escrever o teste que representa o requisito.
    │   RED    │ ───► 2. Executar e confirmar a falha pela razão esperada.
    └────┬─────┘
         │
         ▼
    ┌──────────┐      3. Implementar a MENOR mudança possível no código.
    │  GREEN   │ ───► 4. Executar e confirmar que o teste agora passa.
    └────┬─────┘
         │
         ▼
    ┌──────────┐      5. Limpar o código mantendo todos os testes passando.
    │ REFACTOR │ ───► 6. Garantir zero regressões na suíte completa.
    └──────────┘
```

### 4.1. Regras do Ciclo RED
* Entenda o comportamento esperado antes de escrever o teste.
* Crie ou adapte um teste em `tests/test_*.py`.
* Execute o teste isoladamente e confirme que ele falha (RED) exatamente pela razão esperada.
* **Proibição de Mocks Fictícios**: É proibido considerar uma task concluída com testes que mockam o próprio comportamento implementado ou retornam valores hardcoded sem executar o fluxo real. Testes de integração devem exercitar componentes reais quando disponíveis.

### 4.2. Regras do Ciclo GREEN
* Implemente a menor quantidade de código necessária para satisfazer o teste.
* Respeite os contratos em `core/schemas.py`.
* Confirme a passagem do teste (GREEN).

### 4.3. Regras do Ciclo REFACTOR
* Elimine duplicações e melhore a legibilidade.
* Se uma função exceder 20 linhas lógicas, adicione o comentário `# QUALITY: long-function-justification` ou refatore-a.
* Re-execute a suíte completa de testes.

---

## 5. Workflow Passo a Passo para Futuras Tarefas

Toda e qualquer tarefa neste repositório DEVE seguir este workflow de 8 etapas:

### Etapa 1 — Pergunta Obrigatória de Branch
Antes de criar ou alterar qualquer arquivo, pergunte ao usuário:
1. Se a task deve ser executada em uma nova branch.
2. Qual o nome da branch (sugira um nome conservador se necessário).

### Etapa 2 — Entendimento & Investigação
* Ler atentamente os requisitos.
* Consultar `core/schemas.py`, `ARCHITECTURE.md` e ADRs relevantes.
* Identificar os arquivos e testes afetados.

### Etapa 3 — Plano de Implementação
* Criar/Atualizar o artefato `implementation_plan.md` em Planning Mode.
* Apresentar arquivos envolvidos, estratégia TDD e plano de verificação.
* Aguardar a aprovação do usuário.

### Etapa 4 — Etapa RED (TDD)
* Escrever/adaptar o teste que valida o requisito real.
* Executar o teste e registrar a falha esperada (RED).

### Etapa 5 — Etapa GREEN (TDD)
* Escrever o código mínimo de produção.
* Executar o teste e registrar o sucesso (GREEN).

### Etapa 6 — Etapa REFACTOR (TDD)
* Refatorar se necessário mantendo a arquitetura e os testes verdes.

### Etapa 7 — Validação de Qualidade
Executar os comandos oficiais do projeto:
```bash
# 1. Suíte de testes automatizados
uv run --extra dev pytest tests/ -m "not requires_infra"

# 2. Linter Ruff
uv run --extra dev ruff check .

# 3. Type Checking MyPy
uv run mypy retrieval generation memory verification --strict
```

### Etapa 8 — Revisão Final & Evidências
* Executar `git status` e `git diff` para garantir que apenas os arquivos de escopo foram alterados.
* Apresentar relatório final contendo evidências concretas dos ciclos RED, GREEN, testes de regressão e validação.

---

## 6. Checklist Obrigatório de Aceite

Use este checklist em todas as tarefas:

- [ ] Pergunta sobre a branch realizada e confirmada antes de alterar arquivos.
- [ ] Leitura prévia realizada em `core/schemas.py` e documentação relevante.
- [ ] Nenhuma dependência indevida inserida na camada `core/`.
- [ ] Teste automatizado criado/ajustado ANTES do código de produção (RED confirmado).
- [ ] Menor alteração possível implementada para fazer o teste passar (GREEN confirmado).
- [ ] Refatoração realizada preservando comportamentos (REFACTOR).
- [ ] NENHUM mock fictício utilizado para simular sucesso falso de integração.
- [ ] `uv run --extra dev pytest tests/ -m "not requires_infra"` executado com sucesso.
- [ ] `uv run --extra dev ruff check .` sem erros.
- [ ] `uv run mypy retrieval generation memory verification --strict` sem erros.
- [ ] Artefatos científicos (`eval/dataset`, `eval/results`, `archives/smart_boletim.pdf`) intactos.
- [ ] `git status` revisado e escopo estritamente mantido.
