# Suíte de Testes Empíricos — Smart Boletim 100

Este diretório contém os scripts e testes empíricos responsáveis por produzir os resultados quantitativos da aplicação, cobrindo a classificação de perfis de usuário, reclassificação dinâmica, explicabilidade (XAI), rastreabilidade de fontes, personalização, robustez e métricas de desempenho.

## Estrutura dos Arquivos

- `runner.py`: Executor principal que roda toda a bateria de testes sequencialmente e gera os relatórios em `eval/results/`.
- `test_profile_classification.py`: Valida a acurácia, precisão, recall, F1-score e matriz de confusão sobre o dataset de 300 perguntas.
- `test_dynamic_reclassification.py`: Avalia as transições dinâmicas de perfil e a estabilidade contra consultas atípicas isoladas.
- `test_personalization.py`: Avalia a adaptação do tom e linguagem das respostas de acordo com o perfil ativo.
- `test_explainability.py`: Valida as justificativas de explicabilidade (XAI) geradas a cada alteração de perfil.
- `test_traceability.py`: Verifica os logs de auditoria e a vinculação de fontes bibliográficas às respostas agronômicas.
- `test_robustness.py`: Avalia a resiliência a expressões regionais/coloquiais, perguntas ambíguas e entradas de classes inválidas.
- `test_performance.py`: Mede latências e tempos de execução por etapa do pipeline (profiling, recuperação vetorial e geração).

## Pré-requisitos

1. Python 3.11 ou superior instalado no ambiente.
2. Pacotes e dependências do projeto instalados:
   ```bash
   pip install -r requirements.txt
   ```
3. Datasets empíricos presentes na pasta `eval/dataset/`:
   - `eval/dataset/profile_classification.json` (300 perguntas rotuladas)
   - `eval/dataset/reclassification_sequences.json` (sequências de teste dinâmico)

## Geração dos Datasets

Caso os arquivos de dataset não existam ou necessitem de regeneração, execute o script de construção na raiz do projeto:

```bash
python scripts/build_empirical_datasets.py
```

## Instruções de Execução

### 1. Execução Completa (Master Runner)

Para executar a suíte empírica completa e gerar os relatórios consolidados em JSON e Markdown:

```bash
python -m eval.empirical.runner
```

ou diretamente pelo caminho do arquivo:

```bash
python eval/empirical/runner.py
```

### 2. Execução de Módulos Individuais via Pytest

Você pode executar testes específicos utilizando o `pytest`:

- **Classificação de Perfis:**
  ```bash
  pytest eval/empirical/test_profile_classification.py
  ```

- **Reclassificação Dinâmica:**
  ```bash
  pytest eval/empirical/test_dynamic_reclassification.py
  ```

- **Personalização:**
  ```bash
  pytest eval/empirical/test_personalization.py
  ```

- **Explicabilidade (XAI):**
  ```bash
  pytest eval/empirical/test_explainability.py
  ```

- **Rastreabilidade e Auditoria:**
  ```bash
  pytest eval/empirical/test_traceability.py
  ```

- **Robustez:**
  ```bash
  pytest eval/empirical/test_robustness.py
  ```

- **Desempenho e Latência:**
  ```bash
  pytest eval/empirical/test_performance.py
  ```

- **Executar todos os testes empíricos via Pytest:**
  ```bash
  pytest eval/empirical/
  ```

## Relatórios e Saídas

Ao final da execução do `runner.py`, os seguintes relatórios são atualizados na pasta `eval/results/`:

- `eval/results/empirical_results.json`: Contém os resultados e métricas brutas em formato JSON.
- `eval/results/empirical_results.md`: Contém a compilação formatada em Markdown com tabelas de acurácia, matriz de confusão e latências.
