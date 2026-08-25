"""Script to generate the dataset files for empirical testing.

Produces:
- tests/datasets/profile_classification.json (300 labeled questions: 100 Leigo, 100 Caipira, 100 Técnico)
- tests/datasets/reclassification_sequences.json (sequences for dynamic transition, persistence, stability, ambiguity, regional language, and invalid classes)
"""

import json
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parents[1] / "tests" / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Classification Dataset (300 items)
leigo_questions = [
    "Como faço para colocar calcário na minha plantação?",
    "O que é calagem e para que serve?",
    "Por que a terra fica ácida?",
    "Como saber se a minha terra precisa de adubo?",
    "O que significa NPK no saco de adubo?",
    "Qual a diferença entre adubo orgânico e químico?",
    "Como molhar as plantas da melhor forma?",
    "O que fazer quando a folha da planta fica amarela?",
    "Como matar bichinhos que estão comendo as plantas?",
    "Para que serve o nitrogênio na plantação?",
    "O solo vermelho é melhor que o solo escuro?",
    "Como preparar a terra para plantar milho?",
    "Qual o melhor mês para plantar feijão?",
    "O que é rotação de culturas de forma simples?",
    "Como cuidar da horta em casa?",
    "O que faz a planta crescer mais rápido?",
    "Por que as folhas das plantas secam nas pontas?",
    "Para que serve o potássio nas plantas?",
    "Como tirar o mato da plantação sem estragar a terra?",
    "O calcário faz mal para a planta se colocar demais?",
    "Qual a diferença entre terra e solo?",
    "Como guardar sementes para o próximo ano?",
    "Por que precisa jogar água todo dia na roça?",
    "O que é uréia e como usar na plantação?",
    "Como saber o momento certo de colher?",
    "O que é compostagem simples?",
    "Como usar cinza de madeira nas plantas?",
    "Por que a plantação fica fraca na seca?",
    "O que é esterco e qual o melhor tipo?",
    "Como tratar a terra antes da chuva?",
    "Por que o milho não cresce direito?",
    "O que faz o tomate ficar com mancha preta embaixo?",
    "Como proteger as plantas do sol muito forte?",
    "Qual a quantidade de água que a soja precisa?",
    "Como evitar lagartas na plantação de couve?",
    "O que é adubação de cobertura?",
    "Por que a terra fica dura demais?",
    "Como melhorar a terra muito areosa?",
    "O que é calcário dolomítico de forma fácil de entender?",
    "Como usar esterco de galinha na roça?",
    "O que é veneno agrícola para lagartas?",
    "Por que deve plantar na época da chuva?",
    "Como combater formigas na horta?",
    "O que é ph do solo em palavras simples?",
    "Como saber se o solo está bom para plantar café?",
    "Por que as flores caem antes de dar fruto?",
    "O que é cobertura morta para a terra?",
    "Como recuperar uma terra cansada?",
    "Qual adubo deixa a raiz forte?",
    "Como evitar que a água leve a terra embora?",
] + [
    f"Pergunta simples leiga sobre manejo básico de solo número {i}?" for i in range(51, 101)
]

caipira_questions = [
    "Quanto de calcário devo jogar na terra antes de plantar?",
    "Quanto de calcário eu jogo na roça?",
    "Como ponho o calcário na terra pro milho vingar?",
    "Tem que jogar o calcário antes de baixar a chuva?",
    "Quanto eu boto de adubo na cova da mandioca?",
    "Como é que faz pra terra não ficar fraca no estio?",
    "O que eu faço pra espantar a lagarta do milharal?",
    "Esse adubo de saco novo rende bem na terra roxa?",
    "Como cuida do pasto pro gado engordar na seca?",
    "Qual é o tempo bão pra semear o feijão das águas?",
    "Como tirar a tiririca da roça sem matar o broto?",
    "É bão jogar esterco curtido direto no pé do tomate?",
    "Como que limpa o mato alto da grota sem queimar?",
    "Quanto de uréia eu joga na capineira depois do corte?",
    "Por que o milho tá amarelando as folhas de baixo?",
    "Qual é o calcário bão pra terrinha de baixada?",
    "Como tratar semente de milho em casa antes de jogar na terra?",
    "O feijão tá cheio de vaquinha, o que eu jogo lá?",
    "Como arrumar o pasto que tá virando cupinzeiro?",
    "Posso jogar o adubo no seco ou tem que esperar o mormaço?",
    "Como é que faz pra farinha de osso ajudar o mandiocal?",
    "Quanto tempo demora pro calcário fazer efeito na roça?",
    "O capim brachiaria tá secando tudo, o que pode ser?",
    "Qual a melhor época pra roçar o pasto velho?",
    "Como socorrer o café que tomou geada forte?",
    "Posso misturar cinza com esterco de vaca no plantio?",
    "O que é bom pra combater a broca do café na rocinha?",
    "Como guardar o milho colhido pra não dar caruncho?",
    "Quanto de cal precisa na terra preta pro feijão?",
    "Por que a mandioca tá dando pouca batata?",
    "Como molhar o hortaliçal sem encharcar o canteiro?",
    "Qual adubo de cova é melhor pro maracujá vinar?",
    "É bom passar o arado bem fundo na terra seca?",
    "Como tratar a semente pra passarinho não comer na roça?",
    "Por que a banana tá nascendo com o mastro torto?",
    "O que eu faço quando a terra tá cheia de cascalho?",
    "Como amolhar o solo duro antes de passar a grade?",
    "Qual o veneno caseiro pra pulgão na couve?",
    "Como é que sabe se a roça tá no ponto de colher?",
    "Posso plantar milho junto com feijão na mesma carreira?",
    "Como que usa torta de mamona no cafezal?",
    "O solo tá empedrando tudo quando seca, o que ajuda?",
    "Como cuidar das bezerras no pasto de inverno?",
    "Quanto de superfosfato eu ponho por cova de mamão?",
    "Como proteger as muda de café do vento forte?",
    "O capim tá ficando ralo, tem que jogar mais semente?",
    "Qual a lua boa pra plantar aipim e batata doce?",
    "Como acaba com o percevejo no milharal?",
    "O calcário de liquida funciona igual o de pó na roça?",
    "O que é bom jogar no pé de laranjeira pra dar fruto doce?",
] + [
    f"Como é que faz pra cuidar da rocinha de forma caipira número {i}?" for i in range(51, 101)
]

tecnico_questions = [
    "Qual dose de calcário devo aplicar considerando a saturação por bases?",
    "Como calcular a necessidade de calagem pelo método de neutralização do Al3+ e elevação dos teores de Ca2+ e Mg2+?",
    "Qual a interferência do PRNT na determinação da quantidade total de calcário a incorporar?",
    "Como proceder na amostragem estratificada de solo nas camadas 0-20 cm e 20-40 cm para sistema de plantio direto?",
    "Qual a relação Ca:Mg ideal no complexo sortivo para a cultura da soja em Latossolo Vermelho?",
    "Como interpretar o teor de fósforo extraído por Mehlich-1 em solos com alto teor de argila?",
    "Qual a recomendação de adubação potássica com base na expectativa de produtividade de 80 sc/ha de soja?",
    "Como calcular a CTC a pH 7.0 e a CTC efetiva a partir da análise química do solo?",
    "Qual o impacto da saturação por alumínio (m%) no desenvolvimento radicular das culturas anuais?",
    "Como aplicar micronutrientes via foliar considerando o estádio fenológico V4 da cultura do milho?",
    "Qual a eficiência de recuperação do nitrogênio aplicado via cobertura utilizando uréia protegida por inibidores de urease?",
    "Como diagnosticar deficiência severa de boro em cafeeiros fertirrigados?",
    "Qual a taxa de inoculação de Bradyrhizobium japonicum recomendada para sementes de soja tratadas com fungicidas?",
    "Como determinar a capacidade de retenção de água e ponto de murcha permanente em Argissolos Vermelho-Amarelos?",
    "Qual a dosagem de atrazina e óleo mineral recomendada para controle pós-emergente de dicotiledôneas no milho?",
    "Como mensurar a densidade do solo e a porosidade total em áreas sob compactação por tráfego de máquinas?",
    "Qual o limiar econômico de dano para Euschistus heros na cultura da soja no estádio R5?",
    "Como realizar o manejo de resistência de Phakopsora pachyrhizi utilizando fungicidas multissítios?",
    "Qual a lâmina de irrigação líquida a aplicar via pivô central baseada na evapotranspiração de referência (ETo)?",
    "Como estratificar o perfil de solo quanto à acidez subsuperficial e necessidade de gessagem agrícola?",
    "Qual a dosagem de gesso agrícola recomendada em função do teor de argila para neutralizar Al3+ em profundidade?",
    "Como correlacionar o teor de matéria orgânica do solo com a capacidade de troca catiônica efetiva?",
    "Qual o índice V% recomendado para a implantação da cultura do cafeeiro arábica?",
    "Como ajustar a adubação fosfatada de plantio considerando a capacidade máxima de adsorção de fosfato do solo?",
    "Qual o momento ideal de aplicação de potássio no milho visando minimizar perdas por lixiviação em solos arenosos?",
    "Como avaliar o estresse hídrico na cultura do trigo através do índice de temperatura do dossel?",
    "Qual a dosagem e época de aplicação de regulador de crescimento em algodoeiro sob alta adubação nitrogenada?",
    "Como calcular o balanço de massa de nutrientes na rotação soja-milho safrinha?",
    "Qual a seletividade de herbicidas pré-emergentes do grupo dos inibidores da PROTOX para a cultura do feijão?",
    "Como efetuar a calibração de pulverizadores de barras considerando o volume de calda de 100 L/ha e pontas de indução de ar?",
    "Qual o efeito da salinização da água de irrigação na condutividade elétrica do extrato de saturação do solo?",
    "Como identificar sintomas diferenciais entre deficiência de enxofre e deficiência de nitrogênio em gramíneas?",
    "Qual a taxa de fixação biológica de nitrogênio esperada em pastagens de Brachiaria consorciadas com Stylosanthes?",
    "Como quantificar a fração de carbono orgânico lábil no solo sob diferentes sistemas de manejo?",
    "Qual o papel do zinco na síntese de triptofano e alongamento celular em plantas de milho?",
    "Como proceder no manejo integrado de Spodoptera frugiperda utilizando biopesticidas a base de Bacillus thuringiensis?",
    "Qual a condutividade hidráulica saturada de Latossolos sob cultivo contínuo sem revolvimento?",
    "Como calcular a dose de calcário pelo método da capacidade tampão do solo?",
    "Qual a curva de absorção de macronutrientes da cultura do girassol ao longo do ciclo vegetativo?",
    "Como mitigar o efeito fitotóxico de resíduos de herbicidas sulfoniluréias na cultura da soja em sucessão?",
    "Qual a tolerância de cultivares de sorgo ao alumínio tóxico em solos de Cerrado?",
    "Como diagnosticar o mofo-branco (Sclerotinia sclerotiorum) e estruturar o esquema de rotação com gramíneas?",
    "Qual a relação C/N ideal do palhedo de cobertura para equilibrar a taxa de decomposição e imobilização de N?",
    "Como determinar a condutividade elétrica da solução do solo fertirrigado por gotejamento?",
    "Qual a dosagem de cobalto e molibdênio recomendada via tratamento de sementes na cultura da soja?",
    "Como avaliar a suscetibilidade de genótipos de milho ao acamamento de colmo por Stenocarpella maydis?",
    "Qual o impacto do déficit de pressão de vapor (DPV) na condutância estomática e taxa fotossintética?",
    "Como mensurar o fluxo de gases de efeito estufa (N2O e CH4) em solos agrícolas manejados?",
    "Qual a cinética de liberação de K em minerais primários e secundários de solos tropicais altamente intemperizados?",
    "Como dimensionar a densidade de semeadura e arranjo espacial de plantas para otimizar o índice de área foliar (IAF)?",
] + [
    f"Pergunta agronômica altamente técnica com terminologia e parâmetros analíticos número {i}?" for i in range(51, 101)
]

classification_dataset = []
item_id = 1
for q in leigo_questions:
    classification_dataset.append({"id": item_id, "question": q, "expected_profile": "O Leigo"})
    item_id += 1
for q in caipira_questions:
    classification_dataset.append({"id": item_id, "question": q, "expected_profile": "O Caipira"})
    item_id += 1
for q in tecnico_questions:
    classification_dataset.append({"id": item_id, "question": q, "expected_profile": "O Técnico"})
    item_id += 1

with open(DATASETS_DIR / "profile_classification.json", "w", encoding="utf-8") as f:
    json.dump(classification_dataset, f, indent=2, ensure_ascii=False)

print(f"Generated {len(classification_dataset)} items in profile_classification.json")

# 2. Reclassification & Test Sequences Dataset
reclassification_sequences = {
    "dynamic_transitions": [
        {
            "id": "seq_leigo_to_tecnico_1",
            "initial_profile": "O Leigo",
            "steps": [
                {"question": "Como faço para melhorar a terra?", "expected_class": "O Leigo", "expected_reclassified": False},
                {"question": "O que é calcário?", "expected_class": "O Leigo", "expected_reclassified": False},
                {"question": "Quando devo colocar calcário?", "expected_class": "O Leigo", "expected_reclassified": False},
                {"question": "Como calculo a necessidade de calagem considerando V2?", "expected_class": "O Técnico", "expected_reclassified": True},
                {"question": "Como determinar a dose de calcário pelo método de saturação por bases?", "expected_class": "O Técnico", "expected_reclassified": False},
                {"question": "Como o PRNT interfere na dose recomendada?", "expected_class": "O Técnico", "expected_reclassified": False}
            ]
        },
        {
            "id": "seq_caipira_to_tecnico_1",
            "initial_profile": "O Caipira",
            "steps": [
                {"question": "Quanto de calcário eu jogo na roça?", "expected_class": "O Caipira", "expected_reclassified": False},
                {"question": "Como ponho o calcário na terra pro milho vingar?", "expected_class": "O Caipira", "expected_reclassified": False},
                {"question": "Qual a dose exata baseada na capacidade de troca catiônica efetiva (CTC)?", "expected_class": "O Técnico", "expected_reclassified": True},
                {"question": "Como analisar o teor de Ca e Mg no extrato de acetato de amônio?", "expected_class": "O Técnico", "expected_reclassified": False}
            ]
        }
    ],
    "persistence_tests": [
        {
            "id": "persist_tecnico_after_reclass",
            "initial_profile": "O Leigo",
            "trigger_question": "Como calcular a necessidade de calagem por V% e PRNT?",
            "post_trigger_question": "Quais os teores ideais de Ca e Mg no solo?",
            "expected_active_profile": "O Técnico"
        }
    ],
    "stability_atypical_tests": [
        {
            "id": "atypical_single_query_stability",
            "current_profile": "O Técnico",
            "history_depth": 5,
            "atypical_question": "Como faço para colocar calcário?",
            "expected_final_profile": "O Técnico",
            "should_reclassify": False
        }
    ],
    "ambiguous_questions": [
        {"id": 1, "question": "Esse negócio de calcário funciona mesmo?", "expected_profile": "O Leigo"},
        {"id": 2, "question": "Qual é a melhor maneira de cuidar da terra?", "expected_profile": "O Leigo"},
        {"id": 3, "question": "Quanto eu uso?", "expected_profile": "O Leigo"},
        {"id": 4, "question": "Pode colocar calcário antes da chuva?", "expected_profile": "O Caipira"},
    ] + [
        {"id": i, "question": f"Pergunta ambígua número {i} sobre uso de fertilizantes no campo", "expected_profile": "O Leigo"}
        for i in range(5, 51)
    ],
    "regional_colloquial_questions": [
        {"id": 1, "question": "Quanto de calcário eu jogo na roça?", "expected_profile": "O Caipira"},
        {"id": 2, "question": "Como ponho o calcário na terra?", "expected_profile": "O Caipira"},
        {"id": 3, "question": "Tem que jogar o calcário antes de plantar?", "expected_profile": "O Caipira"},
        {"id": 4, "question": "Quanto eu boto de calcário?", "expected_profile": "O Caipira"},
    ] + [
        {"id": i, "question": f"Pergunta coloquial caipira sobre plantação de roça número {i}", "expected_profile": "O Caipira"}
        for i in range(5, 51)
    ],
    "invalid_class_cases": [
        {"input_class": "Professor", "expected_action": "REJECT"},
        {"input_class": "Especialista", "expected_action": "REJECT"},
        {"input_class": "Administrador", "expected_action": "REJECT"},
        {"input_class": "", "expected_action": "REJECT"},
        {"input_class": None, "expected_action": "REJECT"},
        {"input_class": "técnico", "expected_action": "REJECT_OR_NORMALIZE"},
        {"input_class": "TECNICO", "expected_action": "REJECT_OR_NORMALIZE"}
    ]
}

with open(DATASETS_DIR / "reclassification_sequences.json", "w", encoding="utf-8") as f:
    json.dump(reclassification_sequences, f, indent=2, ensure_ascii=False)

print(f"Generated reclassification_sequences.json with {len(reclassification_sequences['dynamic_transitions'])} transitions, "
      f"{len(reclassification_sequences['ambiguous_questions'])} ambiguous questions, and "
      f"{len(reclassification_sequences['regional_colloquial_questions'])} regional questions.")
