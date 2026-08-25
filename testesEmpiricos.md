# Plano de Testes Empíricos

## Gerenciamento Dinâmico de Perfis de Usuário, Rastreabilidade e Explicabilidade Baseada em Agentes Inteligentes no Contexto do Smart Boletim 100

## 1. Objetivo

Este documento define os testes que devem ser implementados e executados para produzir resultados empíricos para o trabalho **"Gerenciamento Dinâmico de Perfis de Usuário, Rastreabilidade e Explicabilidade Baseada em Agentes Inteligentes no Contexto do Smart Boletim 100"**.

O objetivo é validar experimentalmente as principais funcionalidades descritas no relatório:

1. classificação de usuários nas categorias:

   * O Leigo;
   * O Caipira;
   * O Técnico;
2. reclassificação dinâmica do perfil;
3. adaptação da resposta ao perfil ativo;
4. geração de justificativa para alterações de perfil;
5. rastreabilidade das decisões;
6. rastreabilidade das fontes utilizadas na resposta agronômica;
7. robustez do mecanismo de classificação;
8. desempenho do fluxo de execução.

Os testes devem produzir **dados quantitativos reais** que possam ser incorporados posteriormente à seção **6. Resultados** do artigo.

---

# 2. Contexto do sistema

O relatório descreve uma arquitetura na qual o usuário envia uma pergunta através da API, o agente de profiling realiza uma inferência semântica, o sistema verifica possíveis divergências em relação ao perfil atual e, quando necessário, atualiza a categoria.

O fluxo descrito no relatório é:

```text
Usuário
   |
   v
POST /chat
   |
   v
Agente de Profiling
   |
   v
Inferência da categoria
   |
   v
Avaliação de disparidade
   |
   +----> Perfil mantido
   |
   +----> Perfil atualizado
             |
             v
       Justificativa XAI
             |
             v
      Geração personalizada
             |
             v
       Resposta + fontes
```

A implementação descrita utiliza Python, `UserProfile`, LangGraph e um agente baseado em Gemini para inferência semântica.

---

# 3. Regra fundamental

## NÃO INVENTAR RESULTADOS

O agente executor **não deve preencher resultados hipotéticos**.

Os valores apresentados no artigo devem ser obtidos a partir da execução real dos testes.

Exemplo:

```text
ERRADO:
Accuracy = 94,2%

CERTO:
Accuracy = resultado calculado após execução do dataset.
```

Caso algum teste não possa ser executado por falta de infraestrutura, dataset, API ou dependência, registrar:

```text
STATUS: BLOQUEADO

Motivo:
<explicação objetiva>

Dependência necessária:
<dependência>
```

---

# 4. Organização dos testes

Os testes devem ser divididos em:

```text
tests/
├── empirical/
│   ├── test_profile_classification.py
│   ├── test_dynamic_reclassification.py
│   ├── test_personalization.py
│   ├── test_explainability.py
│   ├── test_traceability.py
│   ├── test_robustness.py
│   └── test_performance.py
│
├── datasets/
│   ├── profile_classification.json
│   └── reclassification_sequences.json
│
└── reports/
    └── empirical_results.json
```

Caso a estrutura atual do projeto seja diferente, adaptar os caminhos sem alterar o objetivo dos testes.

---

# 5. Teste 1 — Classificação dos perfis

## Objetivo

Avaliar a capacidade do agente de classificar perguntas nas três categorias definidas pelo relatório:

```text
O Leigo
O Caipira
O Técnico
```

O relatório afirma que a classificação considera características linguísticas, incluindo vocabulário técnico e expressões regionais.

---

## 5.1 Dataset

Criar um dataset contendo perguntas agronômicas classificadas previamente.

O dataset deve conter, no mínimo:

```text
100 exemplos — O Leigo
100 exemplos — O Caipira
100 exemplos — O Técnico
```

Total mínimo:

```text
300 perguntas
```

Se houver quantidade suficiente de dados, utilizar 500 perguntas, conforme a proposta original do relatório.

---

## 5.2 Estrutura do dataset

Utilizar uma estrutura semelhante a:

```json
[
  {
    "id": 1,
    "question": "Como faço para colocar calcário na minha plantação?",
    "expected_profile": "O Leigo"
  },
  {
    "id": 2,
    "question": "Quanto de calcário devo jogar na terra antes de plantar?",
    "expected_profile": "O Caipira"
  },
  {
    "id": 3,
    "question": "Qual dose de calcário devo aplicar considerando a saturação por bases?",
    "expected_profile": "O Técnico"
  }
]
```

O dataset deve ser separado do código para permitir reprodução do experimento.

---

## 5.3 Métricas

Calcular:

* Accuracy;
* Precision;
* Recall;
* F1-score;
* matriz de confusão;
* quantidade de classificações corretas;
* quantidade de classificações incorretas.

Calcular as métricas:

```text
globalmente
```

e

```text
individualmente por classe
```

---

## 5.4 Resultado esperado

Gerar uma tabela:

| Classe       | Precision | Recall | F1-score | Support |
| ------------ | --------: | -----: | -------: | ------: |
| O Leigo      |         — |      — |        — |       — |
| O Caipira    |         — |      — |        — |       — |
| O Técnico    |         — |      — |        — |       — |
| Macro Avg    |         — |      — |        — |       — |
| Weighted Avg |         — |      — |        — |       — |

Gerar também uma matriz de confusão.

---

# 6. Teste 2 — Reclassificação dinâmica

## Objetivo

Verificar se o sistema consegue detectar que o comportamento linguístico do usuário mudou e atualizar o perfil.

Este teste é fundamental porque o diferencial do trabalho não é apenas classificar o usuário uma vez, mas permitir o gerenciamento dinâmico do perfil.

---

## 6.1 Cenário A — Leigo → Técnico

Criar uma sessão iniciada com perguntas simples:

```text
"Como faço para melhorar a terra?"

"O que é calcário?"

"Quando devo colocar calcário?"
```

O perfil inicial deve ser:

```text
O Leigo
```

Depois enviar perguntas progressivamente mais técnicas:

```text
"Como calculo a necessidade de calagem considerando V2?"

"Como determinar a dose de calcário pelo método de saturação por bases?"

"Como o PRNT interfere na dose recomendada?"
```

Verificar:

1. classificação de cada pergunta;
2. perfil atual;
3. momento da mudança;
4. justificativa da mudança;
5. histórico da sessão.

---

# 7. Teste 3 — Persistência do perfil

## Objetivo

Verificar se o perfil atualizado permanece disponível nas interações seguintes.

Procedimento:

1. iniciar usuário como `O Leigo`;
2. provocar reclassificação para `O Técnico`;
3. enviar nova pergunta;
4. verificar se o sistema utiliza `O Técnico` como perfil ativo.

Registrar:

```text
perfil_anterior
perfil_atual
perfil_detectado
timestamp
motivo
```

---

# 8. Teste 4 — Evitar reclassificação indevida

## Objetivo

Verificar se uma única pergunta atípica não provoca uma mudança incorreta de perfil.

Cenário:

```text
Perfil atual:
O Técnico
```

Enviar uma pergunta simples:

```text
"Como faço para colocar calcário?"
```

O sistema deve avaliar a discrepância sem necessariamente alterar o perfil imediatamente.

Executar múltiplas variações.

Registrar:

```text
perfil inicial
pergunta
classe inferida
perfil final
houve alteração?
justificativa
```

O objetivo é medir a estabilidade do mecanismo de reclassificação.

---

# 9. Teste 5 — Adaptação das respostas

## Objetivo

Verificar se o perfil ativo realmente influencia a resposta final.

Utilizar uma pergunta agronômica equivalente para os três perfis:

```text
"Como devo realizar a calagem do solo?"
```

Executar a pergunta utilizando:

```text
O Leigo
O Caipira
O Técnico
```

Comparar as respostas.

---

## 9.1 Critérios

Avaliar:

### O Leigo

Verificar se utiliza:

* linguagem simples;
* explicações básicas;
* menor quantidade de jargões;
* exemplos compreensíveis.

### O Caipira

Verificar se utiliza:

* linguagem direta;
* tom conversacional;
* expressões coloquiais quando apropriado;
* analogias simples.

### O Técnico

Verificar se apresenta:

* terminologia agronômica;
* dados técnicos;
* dosagens quando suportadas pela fonte;
* conceitos como saturação por bases;
* maior profundidade técnica.

Esses critérios devem ser derivados da própria descrição das categorias presente no relatório.

---

# 10. Teste 6 — Avaliação humana da personalização

## Objetivo

Medir quantitativamente se as respostas personalizadas são percebidas como mais adequadas.

Criar um formulário com escala Likert de 1 a 5.

Para cada resposta, solicitar avaliação de:

```text
1. Clareza
2. Adequação da linguagem
3. Profundidade técnica
4. Facilidade de compreensão
5. Utilidade
```

Escala:

```text
1 = Muito ruim
2 = Ruim
3 = Regular
4 = Boa
5 = Muito boa
```

Calcular:

* média;
* mediana;
* desvio padrão;
* distribuição das respostas.

Se houver grupos suficientes, comparar respostas personalizadas contra respostas sem personalização.

---

# 11. Teste 7 — Explicabilidade da alteração de perfil

## Objetivo

Verificar se o sistema explica adequadamente por que alterou o perfil.

O relatório define que o sistema deve produzir uma justificativa em linguagem natural para a alteração da categoria.

Para cada alteração, armazenar:

```json
{
  "old_profile": "O Leigo",
  "new_profile": "O Técnico",
  "reason": "...",
  "evidence": "...",
  "timestamp": "..."
}
```

---

## 11.1 Avaliação humana

Solicitar que avaliadores respondam:

```text
A justificativa explica por que o perfil foi alterado?
```

Escala:

```text
1 — Não explica
2 — Explica pouco
3 — Explica parcialmente
4 — Explica bem
5 — Explica completamente
```

Calcular:

```text
média
mediana
desvio padrão
percentual de avaliações >= 4
```

---

# 12. Teste 8 — Consistência da explicabilidade

## Objetivo

Verificar se a explicação realmente corresponde aos dados utilizados para tomar a decisão.

Exemplo:

```text
Perfil anterior:
O Leigo

Perfil novo:
O Técnico
```

A justificativa deve mencionar elementos relacionados à mudança, como:

```text
uso recorrente de terminologia agronômica
solicitação de dosagens
uso de conceitos técnicos
```

Não aceitar justificativas que apresentem evidências que não aparecem nas interações.

Criar uma avaliação:

```text
CORRETA
PARCIALMENTE_CORRETA
INCORRETA
```

Calcular o percentual de cada categoria.

---

# 13. Teste 9 — Rastreabilidade

## Objetivo

Verificar se todas as alterações de perfil geram um registro auditável.

Para cada interação verificar se existe:

```text
ID da sessão
ID do usuário
perfil anterior
perfil inferido
perfil final
motivo
timestamp
fontes utilizadas
resposta gerada
```

Calcular:

```text
taxa de registros completos =
registros completos / total de interações
```

---

## 13.1 Teste de integridade

Criar uma interação e verificar se é possível reconstruir:

```text
Pergunta
   ↓
Perfil detectado
   ↓
Decisão
   ↓
Alteração de perfil
   ↓
Justificativa
   ↓
Resposta
   ↓
Fontes
```

O resultado deve indicar:

```text
PASS
```

somente quando todos os elementos puderem ser relacionados.

---

# 14. Teste 10 — Rastreabilidade das fontes

## Objetivo

Verificar se as respostas agronômicas possuem referência à informação utilizada na base do Smart Boletim 100.

Para cada resposta:

1. registrar chunks/documentos recuperados;
2. registrar identificadores das fontes;
3. verificar se as fontes realmente participaram do contexto utilizado pelo LLM.

Métricas:

```text
percentual de respostas com fonte
percentual de fontes válidas
percentual de respostas sem rastreabilidade
```

---

# 15. Teste 11 — Robustez contra linguagem ambígua

## Objetivo

Verificar o comportamento do classificador diante de perguntas que não apresentam características claras de uma categoria.

Criar perguntas:

```text
"Esse negócio de calcário funciona mesmo?"

"Qual é a melhor maneira de cuidar da terra?"

"Quanto eu uso?"

"Pode colocar calcário antes da chuva?"
```

Registrar:

```text
classe inferida
confiança, se disponível
perfil anterior
perfil final
justificativa
```

Verificar principalmente se o sistema evita mudanças arbitrárias.

---

# 16. Teste 12 — Linguagem regional e coloquial

## Objetivo

Avaliar especificamente a capacidade descrita no relatório de identificar expressões regionais e coloquiais associadas ao perfil `O Caipira`.

Criar um conjunto específico contendo expressões coloquiais relacionadas ao contexto agrícola.

Exemplos:

```text
"Quanto de calcário eu jogo na roça?"

"Como ponho o calcário na terra?"

"Tem que jogar o calcário antes de plantar?"

"Quanto eu boto de calcário?"
```

Comparar a classificação do sistema com os rótulos definidos previamente.

Calcular:

```text
Accuracy
Precision
Recall
F1-score
```

somente para esse subconjunto.

---

# 17. Teste 13 — Casos de classe inválida

O código apresentado no relatório contém explicitamente uma validação das classes permitidas.

As únicas classes válidas são:

```text
O Leigo
O Caipira
O Técnico
```

Testar valores como:

```text
"Professor"
"Especialista"
"Administrador"
""
null
"técnico"
"TECNICO"
```

Verificar se o sistema:

1. rejeita a classe;
2. não altera o perfil;
3. gera registro adequado;
4. não interrompe a aplicação.

O comportamento deve ser documentado.

---

# 18. Teste 14 — Desempenho

## Objetivo

Medir o custo do mecanismo de profiling e reclassificação.

Executar múltiplas requisições e medir:

```text
tempo de classificação
tempo de reclassificação
tempo total da requisição
```

Calcular:

```text
média
mediana
p95
p99
mínimo
máximo
```

Separar:

```text
profiling
retrieval
geração
tempo total
```

quando for possível medir individualmente.

---

# 19. Teste 15 — Falha de dependências externas

Como o sistema depende de componentes como LLM e infraestrutura de recuperação, testar comportamento quando uma dependência falha.

Simular:

```text
LLM indisponível
Qdrant indisponível
timeout
resposta inválida do agente
classe inválida
banco indisponível
```

Verificar se:

```text
a aplicação retorna erro controlado;
o perfil anterior não é corrompido;
o log da falha é registrado;
nenhuma alteração parcial é persistida.
```

---

# 20. Teste 16 — Reprodutibilidade

Executar o mesmo conjunto de perguntas mais de uma vez.

Registrar os resultados:

```text
execução_1
execução_2
execução_3
```

Comparar:

```text
classe inferida
perfil final
justificativa
```

Calcular a taxa de consistência:

```text
consistência =
classificações iguais / total de classificações
```

Se o modelo for não determinístico, registrar essa característica e utilizar configuração determinística quando suportada.

---

# 21. Dataset mínimo recomendado

O agente deve tentar construir um dataset com:

```text
300 perguntas
100 Leigo
100 Caipira
100 Técnico
```

E, separadamente:

```text
50 sequências para reclassificação
```

E:

```text
50 casos ambíguos
```

E:

```text
50 casos de linguagem regional/coloquial
```

Os conjuntos devem ser identificados separadamente para evitar contaminação entre os experimentos.

---

# 22. Resultados que devem ser gerados automaticamente

Ao finalizar os testes, gerar um arquivo:

```text
tests/reports/empirical_results.json
```

Estrutura sugerida:

```json
{
  "classification": {
    "accuracy": null,
    "precision": null,
    "recall": null,
    "f1": null,
    "confusion_matrix": null
  },
  "dynamic_reclassification": {
    "total_cases": null,
    "successful_cases": null,
    "success_rate": null,
    "average_interactions_to_reclassify": null
  },
  "personalization": {
    "leigo_mean": null,
    "caipira_mean": null,
    "tecnico_mean": null
  },
  "explainability": {
    "mean_score": null,
    "correct": null,
    "partially_correct": null,
    "incorrect": null
  },
  "traceability": {
    "complete_logs": null,
    "total_logs": null,
    "completeness_rate": null
  },
  "performance": {
    "mean_latency_ms": null,
    "p95_latency_ms": null,
    "p99_latency_ms": null
  }
}
```

Os valores `null` devem ser substituídos somente após a execução real.

---

# 23. Relatório final dos testes

Além do JSON, gerar:

```text
tests/reports/empirical_results.md
```

O relatório deve conter:

## 23.1 Ambiente

Registrar:

```text
Python:
Sistema operacional:
Modelo utilizado:
Versão do modelo:
Versão do Qdrant:
Configuração:
Hardware:
```

## 23.2 Dataset

Informar:

```text
Quantidade total:
Quantidade por classe:
Origem:
Critério de classificação:
```

## 23.3 Classificação

Apresentar:

* accuracy;
* precision;
* recall;
* F1;
* matriz de confusão.

## 23.4 Reclassificação

Apresentar:

* quantidade de sessões;
* mudanças corretas;
* mudanças incorretas;
* média de interações até mudança;
* casos de alteração indevida.

## 23.5 Personalização

Apresentar:

* médias;
* medianas;
* desvio padrão;
* comparação entre categorias.

## 23.6 Explicabilidade

Apresentar:

* avaliação média;
* percentual de justificativas corretas;
* exemplos de justificativas;
* casos de falha.

## 23.7 Rastreabilidade

Apresentar:

* percentual de logs completos;
* percentual de respostas com fonte;
* casos sem rastreabilidade.

## 23.8 Desempenho

Apresentar:

* média;
* p95;
* p99;
* quantidade de erros;
* tempo total.

---

# 24. Critérios para considerar os testes concluídos

O trabalho experimental somente deve ser considerado concluído quando:

* [ ] Dataset de classificação criado.
* [ ] Dataset revisado/rotulado.
* [ ] Teste de classificação executado.
* [ ] Matriz de confusão gerada.
* [ ] Accuracy calculada.
* [ ] Precision calculada.
* [ ] Recall calculado.
* [ ] F1-score calculado.
* [ ] Teste de reclassificação executado.
* [ ] Persistência de perfil testada.
* [ ] Alterações indevidas avaliadas.
* [ ] Personalização avaliada.
* [ ] Explicabilidade avaliada.
* [ ] Consistência das justificativas avaliada.
* [ ] Logs de rastreabilidade avaliados.
* [ ] Rastreabilidade das fontes avaliada.
* [ ] Casos ambíguos testados.
* [ ] Linguagem regional testada.
* [ ] Classes inválidas testadas.
* [ ] Desempenho medido.
* [ ] Falhas de dependências testadas.
* [ ] Reprodutibilidade avaliada.
* [ ] `empirical_results.json` gerado.
* [ ] `empirical_results.md` gerado.

---

# 25. Regras para o agente executor

1. Não modificar a lógica do sistema apenas para obter resultados melhores.

2. Não criar resultados fictícios.

3. Não remover casos em que o modelo errou.

4. Registrar todos os erros de classificação.

5. Manter o dataset utilizado para permitir reprodução.

6. Registrar versões das dependências e do modelo.

7. Separar claramente:

   * teste automatizado;
   * avaliação humana;
   * teste de integração;
   * teste de desempenho.

8. Sempre que possível, salvar os resultados brutos.

9. Caso uma métrica não possa ser calculada, explicar o motivo.

10. Não alterar silenciosamente os critérios definidos neste documento.

---

# 26. Objetivo final para o artigo

Os testes devem produzir evidências que permitam substituir a seção atualmente descritiva de resultados por uma seção experimental.

A seção final do artigo deverá conseguir responder quantitativamente:

```text
1. O sistema classifica corretamente os perfis?

2. O sistema consegue detectar mudanças de comportamento?

3. O perfil realmente altera a forma de resposta?

4. A explicação da mudança de perfil é compreensível?

5. As decisões podem ser auditadas?

6. As fontes utilizadas podem ser rastreadas?

7. O sistema mantém estabilidade diante de entradas ambíguas?

8. Qual é o custo de execução do mecanismo?
```

O resultado final deve permitir apresentar **tabelas, gráficos, métricas e análise dos erros**, e não apenas afirmar que o framework "funciona".

A prioridade deve ser:

```text
PRIORIDADE 1
Classificação + matriz de confusão

PRIORIDADE 2
Reclassificação dinâmica

PRIORIDADE 3
Explicabilidade

PRIORIDADE 4
Rastreabilidade

PRIORIDADE 5
Personalização

PRIORIDADE 6
Robustez e desempenho
```

Esses experimentos estão diretamente alinhados aos resultados que o próprio relatório estabelece como necessários: matriz de confusão para 500 perguntas, avaliação da compreensão das justificativas por produtores e análise dos logs de rastreabilidade/XAI.
