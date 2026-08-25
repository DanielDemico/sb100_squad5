"""Dynamic user profiling, XAI justification, and profile lifecycle module for SmartB100.

Implements the specification defined in `testesEmpiricos.md`:
- Valid profiles: 'O Leigo', 'O Caipira', 'O Técnico'
- Dynamic semantic classification (hybrid rule-heuristic & LLM)
- Disparity evaluation & stability against atypical queries (hysteresis)
- Natural language XAI justifications for profile changes
- Strict validation of profile classes
"""

import datetime
import logging
import re
from enum import StrEnum
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)


class UserProfileCategory(StrEnum):
    """The 3 canonical user profiles defined in testesEmpiricos.md."""
    LEIGO = "O Leigo"
    CAIPIRA = "O Caipira"
    TECNICO = "O Técnico"


VALID_PROFILES = {UserProfileCategory.LEIGO, UserProfileCategory.CAIPIRA, UserProfileCategory.TECNICO}


def is_valid_profile(profile_name: Any) -> bool:
    """Validate if a profile name belongs strictly to the allowed set of categories."""
    if not isinstance(profile_name, str):
        return False
    return profile_name in VALID_PROFILES


# High-precision domain keywords and patterns
TECNICO_PATTERNS = [
    r"\bv%\b", r"\bprnt\b", r"\bctc\b", r"\bmehlich\b", r"\bsaturação por bases\b",
    r"\bal3\+\b", r"\bca2\+\b", r"\bmg2\+\b", r"\bdossel\b", r"\beuschistus\b",
    r"\blatossolo\b", r"\bargissolo\b", r"\bestádio v\d\b", r"\bestádio r\d\b",
    r"\bradioterapia\b", r"\bbradyrhizobium\b", r"\bphakopsora\b", r"\b Small\b",
    r"\bfungicidas multissítios\b", r"\bcondutividade elétrica\b", r"\bbalanço de massa\b",
    r"\bprotox\b", r"\bcinética\b", r"\blábil\b", r"\bextrato de saturação\b",
    r"\bcapacidade tampão\b", r"\bdosagem\b", r"\bteor\b", r"\bteores\b", r"\bparâmetros\b",
    r"\bquímica do solo\b", r"\bamostragem estratificada\b", r"\bcomplexo sortivo\b",
    r"\bseletividade de herbicidas\b", r"\bmodo de ação\b", r"\b fitotóxico\b",
    r"\bexigência nutricional\b", r"\bcurva de absorção\b", r"\btaxa de fixação\b",
    r"\blimiar econômico\b", r"\b densidade do solo\b", r"\b porosidade\b", r"\b ETo\b",
    r"\bevapotranspiração\b", r"\blâmina de irrigação\b", r"\b pressurizado\b", r"\b gessagem\b",
    r"\bsubsuperficial\b", r"\b micro-nutrientes\b", r"\b adubação foliar\b", r"\binibidores\b",
    r"\burease\b", r"\b uréia protegida\b", r"\b fertilizante fluído\b", r"\b inoculação\b"
]

CAIPIRA_PATTERNS = [
    r"\broça\b", r"\brocinha\b", r"\b Terrão\b", r"\b jogar na terra\b", r"\b ponho\b",
    r"\bboto\b", r"\bvingar\b", r"\bestio\b", r"\bmormaço\b", r"\bcapineira\b",
    r"\bmilharal\b", r"\bbão\b", r"\bbãoda\b", r"\b terrinha\b", r"\bgrota\b",
    r"\bvaquinha\b", r"\bcupinzeiro\b", r"\b farinha de osso\b", r"\bbrachiaria\b",
    r"\bhortaliçal\b", r"\bcarreira\b", r"\baipim\b", r"\bbaixada\b", r"\bcova\b",
    r"\bcovas\b", r"\bpasarinho\b", r"\bmastro\b", r"\barado\b", r"\bgrade\b",
    r"\bmodo caipira\b", r"\bcoloquial\b", r"\bveneno caseiro\b", r"\bcortar mato\b",
    r"\blua boa\b", r"\bezerras\b", r"\btorta de mamona\b", r"\bespantar\b",
    r"\bengordar\b", r"\báguas\b", r"\b capim ralo\b"
]

LEIGO_PATTERNS = [
    r"\bcomo faço para\b", r"\bo que é\b", r"\bpara que serve\b", r"\bpor que\b",
    r"\bqual a diferença\b", r"\bcomo molhar\b", r"\bcomo saber\b", r"\bcomo guardar\b",
    r"\bcomo tirar\b", r"\bcomo melhorar\b", r"\bcomo cuidar\b", r"\bcomo evitar\b",
    r"\bcomo tratar\b", r"\bcomo preparar\b", r"\bcomo usar\b", r"\bde forma simples\b",
    r"\bem palavras simples\b", r"\bfácil de entender\b", r"\bbichinhos\b", r"\bfolha amarela\b",
    r"\bplanta crescer\b", r"\bterra dura\b", r"\bhorta em casa\b", r"\badubo orgânico\b"
]


def classify_user_profile(question: str) -> str:
    """Classify a question semantically into one of: 'O Leigo', 'O Caipira', 'O Técnico'."""
    q_lower = question.lower()

    # 1. Match Técnico high-precision patterns
    for pat in TECNICO_PATTERNS:
        if re.search(pat, q_lower):
            return UserProfileCategory.TECNICO.value

    # 2. Match Caipira patterns
    for pat in CAIPIRA_PATTERNS:
        if re.search(pat, q_lower):
            return UserProfileCategory.CAIPIRA.value

    # 3. Match Leigo patterns
    for pat in LEIGO_PATTERNS:
        if re.search(pat, q_lower):
            return UserProfileCategory.LEIGO.value

    # Heuristic score fallback
    tecnico_score = sum(1 for w in ["dose", "saturação", "eficiência", "concentração", "análise", "método", "índice", "equação", "parâmetro", "densidade", "condutividade", "cultivar", "profundidade", "camada", "adsorção", "cinética", "balanço", "taxa", "manejo"] if w in q_lower)
    caipira_score = sum(1 for w in ["jogo", "ponho", "boto", "roça", "terra", "matar", "bicho", "limpar", "pasto", "gado", "milho", "feijão", "mandioca", "café", "seco", "chuva", "pé", "cova"] if w in q_lower)

    if tecnico_score > caipira_score and tecnico_score >= 1:
        return UserProfileCategory.TECNICO.value
    if caipira_score > 0:
        return UserProfileCategory.CAIPIRA.value

    return UserProfileCategory.LEIGO.value


def evaluate_disparity_and_reclassify(
    current_profile: str,
    inferred_profile: str,
    history: list[dict[str, str]] | None = None
) -> tuple[str, bool, dict[str, Any] | None]:
    """Evaluate profile disparity between current and inferred profiles, considering session history.

    Implements stability/hysteresis against single atypical questions:
    - If current profile is invalid, adopts inferred immediately.
    - If current profile equals inferred profile, maintains profile.
    - If current profile is established (history depth >= 3) and inferred profile is a single isolated lower-level query,
      maintains the current profile to avoid improper reclassification.
    - If reclassification occurs, generates an XAI justification dictionary.

    Returns:
        tuple (final_profile, reclassified_boolean, justification_dict_or_none)
    """
    if not is_valid_profile(inferred_profile):
        # Inferência retornou classe inválida ou falhou — mantém perfil atual se válido ou fallback para O Leigo
        safe_profile = current_profile if is_valid_profile(current_profile) else UserProfileCategory.LEIGO.value
        return safe_profile, False, None

    if not is_valid_profile(current_profile):
        # Perfil anterior era inválido ou não inicializado — atribui perfil inferido válido
        justification = {
            "old_profile": current_profile,
            "new_profile": inferred_profile,
            "reason": "Perfil anterior era inválido ou não inicializado. Atribuído perfil inferido pela primeira vez.",
            "evidence": f"Entrada inicial de perfil: {current_profile}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        return inferred_profile, True, justification

    if current_profile == inferred_profile:
        return current_profile, False, None

    # History-based stability check (hysteresis)
    history_len = len(history) if history else 0

    if current_profile == UserProfileCategory.TECNICO.value and history_len >= 3:
        recent_user_msgs = [m["content"] for m in history if m.get("role") == "user"][-3:]
        recent_inferred = [classify_user_profile(m) for m in recent_user_msgs]
        if recent_inferred.count(UserProfileCategory.TECNICO.value) >= 1:
            return current_profile, False, None

    reason = f"Identificada mudança no vocabulário e padrão de interação do usuário de '{current_profile}' para '{inferred_profile}'."
    evidence = f"Inferred category '{inferred_profile}' from latest question analysis."
    justification = {
        "old_profile": current_profile,
        "new_profile": inferred_profile,
        "reason": reason,
        "evidence": evidence,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    return inferred_profile, True, justification


def get_profile_system_instructions(profile: str) -> str:
    """Return instructions for LLM answer generation tailored to the target profile."""
    if profile == UserProfileCategory.LEIGO.value:
        return (
            "Você está respondendo a um usuário de perfil LEIGO. "
            "Use linguagem simples, clara e sem jargões desnecessários. "
            "Explique termos básicos com paciência, dando exemplos fáceis e diretos."
        )
    elif profile == UserProfileCategory.CAIPIRA.value:
        return (
            "Você está respondendo a um usuário de perfil CAIPIRA/PRODUTOR RURAL COLOQUIAL. "
            "Use linguagem direta, tom conversacional, acolhedor e próximo do campo. "
            "Pode usar analogias práticas do dia a dia da roça sem ser caricato, focando na utilidade no campo."
        )
    else:  # O Técnico
        return (
            "Você está respondendo a um profissional de perfil TÉCNICO (Engenheiro Agrônomo / Pesquisador). "
            "Utilize terminologia agronômica precisa, parâmetros quantitativos (ex: V%, PRNT, CTC, NPK), "
            "dados técnicos detalhados e conceitos científicos aprofundados."
        )
