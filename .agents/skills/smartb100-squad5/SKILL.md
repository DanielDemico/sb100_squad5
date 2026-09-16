---
name: smartb100-squad5
description: Manual operacional permanente da Squad 5 para o SmartB100, integrando arquitetura, TDD obrigatório, convenções e workflows.
---

# SmartB100 Squad 5 — Manual Operacional e Skill de Desenvolvimento TDD

Este é o manual operacional permanente do SmartB100 para o Squad 5. Ele é a fonte canônica de orientação para agentes de IA e desenvolvedores neste repositório.

> **Importante**: Este arquivo consolida as diretrizes de desenvolvimento com TDD, arquitetura do Monólito Modular, contratos em `core/schemas.py`, validação real e preservação de artefatos científicos.

---

## 1. Regras Fundamentais de Desenvolvimento
1. **Pergunte a Branch Primeiro**: Antes de qualquer modificação de código ou arquivos, pergunte ao usuário se a task deve rodar em uma nova branch e qual o nome da branch.
2. **TDD Obrigatório**: Toda task de desenvolvimento deve seguir o ciclo **RED → GREEN → REFACTOR**:
   - **RED**: Escrever o teste primeiro e validar sua falha com base no comportamento esperado.
   - **GREEN**: Implementar a alteração mínima para o teste passar.
   - **REFACTOR**: Refatorar o código mantendo 100% dos testes verdes e respeitando limites de linhas/qualidade.
3. **Contratos em `core/schemas.py`**: Todos os Schemas Pydantic públicos e intercamadas devem ser importados de `core.schemas`. Proibido duplicar schemas nas rotas ou módulos.
4. **Isolamento do `core`**: O pacote `core/` não pode depender de nenhuma outra camada do projeto. Validado via `tests/test_quality_architecture.py`.
5. **Validação Real de Integração**: Proibido utilizar mocks fictícios para simular sucesso de integração quando os componentes reais estiverem disponíveis.
6. **Preservação de Artefatos**: Não modificar datasets (`eval/dataset/`), resultados (`eval/results/`) ou o PDF em `archives/smart_boletim.pdf`.

---

## 2. Comandos Oficiais de Qualidade e Validação

```bash
# Execução da suíte de testes (sem testes que exigem infraestrutura externa ao vivo)
uv run --extra dev pytest tests/ -m "not requires_infra"

# Linter e análise estática (Ruff)
uv run --extra dev ruff check .

# Verificação estrita de tipos (MyPy)
uv run mypy retrieval generation memory verification --strict
```

---

## 3. Workflow Completo da Tarefa
1. **Perguntar a Branch**
2. **Ler a Documentação & Contratos** (`core/schemas.py`, `ARCHITECTURE.md`, `docs/project-audit.md`)
3. **Planejamento** (`implementation_plan.md` em Planning Mode)
4. **RED (Escrever Teste e Confirmar Falha)**
5. **GREEN (Implementar Código Mínimo e Passar Teste)**
6. **REFACTOR (Refatorar e Garantir Limpeza)**
7. **Validação Executável (Pytest + Ruff + MyPy)**
8. **Revisão de Diff & Entrega com Evidências**
