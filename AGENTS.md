# SmartB100 - Instrucoes permanentes do Codex

Este arquivo define instrucoes obrigatorias para o Codex neste repositorio inteiro.
Ele deve ser lido automaticamente em novas sessoes abertas na raiz ou em qualquer
subdiretorio deste projeto.

## Fonte canonica obrigatoria

Antes de analisar, planejar ou executar qualquer task neste repositorio, o Codex
DEVE localizar e ler integralmente o manual operacional permanente:

`./.agents/skills/smartb100-squad5/SKILL.md`

Esse `SKILL.md` e a fonte canonica e detalhada de conhecimento do SmartB100. Suas
regras, arquitetura, contratos, ADRs, convencoes, restricoes e protocolos sao
normativos, nao documentacao opcional. Este `AGENTS.md` nao substitui o manual:
ele apenas torna obrigatorio seu uso permanente e explicita regras criticas que
devem guiar qualquer trabalho antes de implementacao.

Se a documentacao parecer desatualizada ou incompleta, confira o codigo real,
testes e ADRs relevantes antes de decidir. Nunca assuma o funcionamento de um
componente apenas pelo nome.

## Escopo e branch

Para toda nova task que possa resultar em alteracao de codigo ou arquivos, antes
de planejar alteracoes ou modificar qualquer arquivo, pergunte ao usuario:

- se a task deve ser executada em uma nova branch;
- qual deve ser o nome da branch.

Se o usuario nao fornecer nome, sugira um nome conservador. Nao crie a branch
sem essa definicao. Esta pergunta e obrigatoria para cada nova task de
implementacao.

## Preservacao arquitetural

A menos que a task solicite explicitamente:

- nao alterar estrutura de diretorios;
- nao renomear, mover ou reorganizar arquivos;
- nao substituir a arquitetura do sistema ou padroes existentes;
- nao adicionar dependencias;
- nao criar abstracoes desnecessarias;
- nao modificar contratos publicos, schemas, interfaces, rotas ou assinaturas
  sem verificar todos os consumidores e testes relacionados.

Implemente sempre o menor conjunto de alteracoes necessario. Nao faca
refatoracoes oportunistas, nao corrija problemas fora do escopo sem autorizacao
e preserve comportamentos nao relacionados.

## ADRs e contratos

As decisoes em `docs/adr/` sao decisoes arquiteturais deliberadas. Antes de
alterar arquitetura, persistencia, inferencia, RAG, verificacao, agentes,
integracoes ou contratos entre modulos, leia as ADRs relevantes e nao as
contradiga silenciosamente.

Antes de alterar funcoes publicas, schemas Pydantic, rotas FastAPI, modelos,
interfaces entre modulos ou formatos de request/response, investigue todos os
consumidores e testes relacionados.

## Artefatos cientificos

Nao modificar, apagar ou regenerar sem solicitacao explicita:

- datasets de avaliacao;
- resultados experimentais;
- relatorios cientificos;
- arquivos em `eval/dataset/`;
- arquivos em `eval/results/`;
- documentos-fonte de pesquisa;
- `archives/smart_boletim.pdf`.

Esses itens sao artefatos cientificos do projeto.

## Qualidade de codigo

Respeite os padroes definidos pelo projeto e pelo `SKILL.md`, incluindo Python
3.12+, type hints explicitos, MyPy strict, Ruff, Pytest, Pydantic, FastAPI,
logging e tratamento de excecoes existentes. Nao introduza outro padrao de
implementacao por preferencia pessoal.

## TDD obrigatorio para desenvolvimento

Toda task que envolva desenvolvimento, correcao de bug, alteracao de
comportamento, criacao/modificacao de funcionalidade, endpoints, pipeline RAG,
persistencia, autenticacao, agentes, retrieval, geracao, verificacao, contratos
entre modulos ou refatoracao autorizada com impacto comportamental DEVE seguir
TDD: RED -> GREEN -> REFACTOR.

### RED - reproduzir primeiro

Antes de implementar:

1. entenda o comportamento esperado;
2. identifique testes existentes relacionados;
3. reproduza o comportamento atual;
4. crie ou adapte um teste que represente o requisito real;
5. execute o teste antes da implementacao;
6. confirme que ele falha pela razao esperada.

Nao escreva primeiro a implementacao e depois um teste apenas para justifica-la.
Se o teste passar antes da implementacao, investigue se a funcionalidade ja
existe, se o teste esta incorreto, se o cenario nao reproduz o requisito ou se a
task ja foi parcialmente implementada.

### GREEN - implementacao minima

Depois de comprovar o RED:

1. implemente a menor alteracao possivel;
2. preserve a arquitetura existente;
3. nao amplie o escopo;
4. execute novamente o teste;
5. confirme que o cenario anteriormente falho agora passa.

### REFACTOR - somente quando necessario

Depois que os testes estiverem passando, faca apenas refatoracoes diretamente
necessarias, preserve comportamento, nao realize melhorias oportunistas e execute
novamente todos os testes afetados.

## Testes reais e validacao funcional

A validacao funcional da task deve representar o comportamento real do sistema.
E proibido considerar uma task concluida exclusivamente porque passaram testes
que:

- mockam o proprio comportamento implementado;
- substituem a funcionalidade central por respostas artificiais;
- retornam valores hardcoded apenas para satisfazer assertions;
- simulam sucesso sem executar o fluxo real;
- testam implementacao ficticia diferente daquela usada pelo sistema;
- criam mocks que simplesmente reproduzem o resultado esperado;
- ignoram integracoes essenciais ao comportamento validado.

Mocks, stubs, fakes e monkeypatches podem ser usados em testes unitarios
auxiliares quando apropriado e alinhado a estrategia do projeto, mas um teste com
mock NAO substitui validacao funcional real quando o comportamento depende de
integracao entre componentes.

Quando a task alterar um fluxo executavel do SmartB100, apos RED -> GREEN deve
existir validacao no sistema funcionando sempre que a infraestrutura estiver
disponivel. Conforme a area afetada, exercite componentes reais como FastAPI,
SQLite de teste, Ollama, Qdrant local/cloud de desenvolvimento/testes, pipeline
RAG, geracao, verificacao de alucinacao, endpoints HTTP reais, persistencia real
e demais servicos do projeto.

Nao invente respostas de Ollama, Qdrant, banco de dados, API ou outros
componentes e apresente isso como evidencia de integracao funcionando.

## Infraestrutura indisponivel

Se uma integracao real necessaria nao estiver disponivel:

1. detecte e informe claramente qual infraestrutura esta indisponivel;
2. tente identificar, sem alterar configuracoes arbitrariamente, se o projeto
   fornece forma documentada de inicia-la;
3. nao substitua silenciosamente a integracao real por mocks;
4. nao fabrique resultados;
5. execute os testes unitarios ainda validos;
6. informe explicitamente que a validacao integrada/funcional nao pode ser
   realizada;
7. nao declare a funcionalidade completamente validada.

Uma task pode estar tecnicamente implementada, mas deve ser reportada como
pendente de validacao integrada quando a infraestrutura necessaria nao puder ser
executada.

## Protocolo obrigatorio para tasks de desenvolvimento

Depois da definicao de branch e antes de escrever codigo:

1. ler integralmente `./.agents/skills/smartb100-squad5/SKILL.md`;
2. entender criterios de aceitacao;
3. localizar componentes afetados;
4. ler arquivos envolvidos;
5. ler testes relacionados;
6. identificar consumidores dos contratos afetados;
7. consultar ADRs relevantes;
8. verificar estado atual do repositorio;
9. executar testes existentes relevantes antes de alterar codigo;
10. registrar falhas preexistentes;
11. criar/adaptar teste que representa o requisito real;
12. executar o teste e confirmar RED;
13. implementar a menor mudanca necessaria;
14. executar novamente o teste e confirmar GREEN;
15. executar testes relacionados e suite completa quando viavel;
16. executar Ruff/MyPy conforme configuracao do projeto;
17. validar o fluxo real no sistema funcionando quando houver comportamento
    integrado;
18. executar `git status` e `git diff`;
19. confirmar que somente arquivos de escopo foram alterados;
20. confirmar que nenhum artefato cientifico ou alteracao estrutural nao
    autorizada foi tocado.

## Evidencia obrigatoria na resposta final

Ao concluir uma task de desenvolvimento, informe evidencias concretas:

- RED: teste criado/alterado, comportamento representado, comando executado,
  falha observada e causa esperada;
- GREEN: alteracao minima realizada e resultado do mesmo teste;
- REGRESSAO: testes adicionais, resultado de Pytest e resultado de Ruff/MyPy
  quando aplicavel;
- VALIDACAO REAL: componentes reais executados, fluxo funcional exercitado,
  integracoes realmente usadas e resultado observado;
- DIFF: arquivos alterados e confirmacao de escopo.

Nao diga apenas "todos os testes passaram"; apresente os comandos e validacoes
relevantes.
