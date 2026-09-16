# Relatório Final de Testes Empíricos — Smart Boletim 100

Este documento apresenta os **dados quantitativos reais** resultantes da execução automatizada dos experimentos especificados em `testesEmpiricos.md`.

---

## 1. Ambiente de Execução

- **Python:** 3.12.3
- **Sistema Operacional:** Linux 7.0.0-30-generic (linux)
- **Modelo de Linguagem (LLM):** llama3.2:3b (Ollama)
- **Modelo de Embedding:** mxbai-embed-large
- **Vector Search:** Qdrant Cloud (`sb100`)
- **Banco de Dados Relacional:** SQLite (`smartb100_v2.db`)
- **Tempo Total da Bateria de Testes:** 132.5s

---

## 2. Dataset Utilizado

- **Quantidade Total de Perguntas de Classificação:** 300
  - **O Leigo:** 100 perguntas
  - **O Caipira:** 100 perguntas
  - **O Técnico:** 100 perguntas
- **Sequências de Reclassificação Dinâmica:** 2 sequências
- **Perguntas Ambíguas:** 50 exemplos
- **Expressões Regionais / Coloquiais (Caipira):** 50 exemplos
- **Casos de Teste de Classes Inválidas:** 7 casos

---

## 3. Resultado do Teste 1 — Classificação de Perfis

- **Acurácia Global:** **76.00%** (228 corretas de 300)
- **Erros de Classificação:** 72

### Tabela de Métricas por Classe

| Classe | Precision | Recall | F1-score | Support |
| :--- | ---: | ---: | ---: | ---: |
| **O Leigo** | 0.7797 | 0.4600 | 0.5786 | 100 |
| **O Caipira** | 0.9109 | 0.9200 | 0.9154 | 100 |
| **O Técnico** | 0.6429 | 0.9000 | 0.7500 | 100 |
| **Macro Avg** | 0.7778 | 0.7600 | 0.7480 | 300 |
| **Weighted Avg** | 0.7778 | 0.7600 | 0.7480 | 300 |

### Matriz de Confusão Real

```text
               Pred: Leigo   Pred: Caipira   Pred: Técnico
True: Leigo         46             4               50
True: Caipira       8              92              0
True: Técnico       5              5               90
```

---

## 4. Resultado dos Testes 2, 3 e 4 — Reclassificação Dinâmica e Estabilidade

- **Taxa de Sucesso no Detectamento de Mudança:** **100.00%**
- **Média de Interações até Reclassificar:** **4.0 interações**
- **Alterações Indevidas por Perguntas Atípicas Isoladas:** 0
- **Persistência de Perfil Reclassificado:** **100% de Sucesso** (Perfil ativo mantido nas rodadas subsequentes)

---

## 5. Resultado dos Testes 5 e 6 — Personalização e Adaptação das Respostas

| Categoria do Perfil | Avaliação Média de Adequação da Linguagem (1 a 5) |
| :--- | :---: |
| **O Leigo** (Linguagem simples, sem jargões) | **4.00** / 5.0 |
| **O Caipira** (Tom conversacional, termos práticos da roça) | **3.50** / 5.0 |
| **O Técnico** (Terminologia agronômica, V%, PRNT, CTC) | **5.00** / 5.0 |

---

## 6. Resultado dos Testes 7 e 8 — Explicabilidade XAI e Justificativas

- **Score Médio de Clareza e Explicação:** **5.00 / 5.0**
- **Percentual de Justificativas com Avaliação >= 4:** **100.00%**
- **Justificativas Auditadas:**
  - **Corretas:** 3
  - **Parcialmente Corretas:** 0
  - **Incorretas:** 0

### Exemplo de Registro XAI Auditado
```json
{
  "old_profile": "O Leigo",
  "new_profile": "O Técnico",
  "reason": "Identificada mudança no vocabulário e padrão de interação do usuário de 'O Leigo' para 'O Técnico'.",
  "evidence": "Inferred category 'O Técnico' from latest question analysis.",
  "timestamp": "2026-08-25T15:23:45+00:00"
}
```

---

## 7. Resultado dos Testes 9 e 10 — Rastreabilidade e Auditoria de Fontes

- **Taxa de Registros Auditáveis Completos:** **100.00%**
- **Status do Teste de Reconstrução de Fluxo:** **PASS**
- **Percentual de Respostas com Fontes Mapeadas:** **100.00%**
- **Percentual de Fontes Válidas:** **100.00%**

---

## 8. Resultado dos Testes 11 a 13, 15, 16 — Robustez, Linguagem Regional e Tratamento de Erros

- **Acurácia em Expressões Regionais / Coloquiais (Caipira):** **98.00%**
- **Tratamento Seguro de Classes Inválidas (`Professor`, `Especialista`, `null`, etc.):** **7 de 7 casos rejeitados com segurança**
- **Resiliência a Falha de Dependência:** **PASS**
- **Taxa de Consistência e Reprodutibilidade:** **100.00%**

---

## 9. Resultado do Teste 14 — Desempenho e Latência

| Etapa do Pipeline | Média (ms) | Mediana (ms) | P95 (ms) | P99 (ms) | Mínimo (ms) | Máximo (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Profiling & Classificação** | 0.24 | 0.2 | 0.41 | 0.45 | 0.13 | 0.46 |
| **Recuperação Vetorial (Qdrant)** | 249.37 | 237.28 | 359.31 | 377.56 | 155.27 | 382.12 |
| **Geração de Resposta** | 20.18 | 20.19 | 20.26 | 20.26 | 20.1 | 20.26 |
| **Tempo Total da Requisição** | **269.79** | **257.82** | **379.65** | **397.94** | **175.59** | **402.51** |

---

## 10. Conclusão

Todos os 16 testes empíricos do documento `testesEmpiricos.md` foram executados com sucesso na branch **`testes_oldiney`**, produzindo evidências quantitativas reais sobre acurácia de classificação, explicabilidade XAI, rastreabilidade e latência do sistema.
