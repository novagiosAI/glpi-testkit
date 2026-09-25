"""Phrasing that carries urgency and impact into the ticket text.

Without this the generator samples urgency and impact, writes a body chosen
only by category, and the two never meet — so priority is unpredictable from
the text by construction. That was measured: a classifier trained on the older
output scored 0.47 on priority against a 0.51 majority baseline, i.e. worse
than guessing, because there was nothing to learn.

Real tickets do not work that way. A user who is blocked says so, and a user
reporting something cosmetic says that too:

* **impact** is about *how many people* — one person, a team, a whole site;
* **urgency** is about *how soon* — blocking work now, or "when you have time".

Each generated ticket therefore gets one impact marker and one urgency marker
drawn from the band its sampled levels fall into. The markers do not name the
level, so the task stays a real inference rather than a lookup.
"""

from __future__ import annotations

from .models import Language

#: Impact markers by band: 1-2 (individual), 3 (team), 4-5 (site-wide).
IMPACT_MARKERS: dict[Language, dict[str, tuple[str, ...]]] = {
    Language.FRENCH: {
        "low": (
            "Cela ne concerne que mon poste.",
            "Je suis le seul touché pour l'instant.",
            "Un seul utilisateur est concerné.",
        ),
        "medium": (
            "Deux collègues de mon service ont le même souci.",
            "Toute mon équipe est touchée.",
            "Cela concerne le service comptabilité.",
        ),
        "high": (
            "Tout le site est bloqué, personne ne peut travailler.",
            "L'ensemble des agences est concerné.",
            "Plus de trente personnes sont à l'arrêt.",
        ),
    },
    Language.ARABIC: {
        "low": (
            "المشكل يخص جهازي فقط.",
            "أنا الوحيد المتأثر حتى الآن.",
        ),
        "medium": (
            "المشكل يخص فريقي بالكامل.",
            "زميلان في نفس المصلحة لديهما نفس المشكل.",
        ),
        "high": (
            "جميع الموظفين متوقفون عن العمل.",
            "المشكل يخص كل الوكالات.",
        ),
    },
    Language.DARIJA: {
        "low": (
            "ghir l pc dyali li 3ando had l mouchkil.",
            "أنا بوحدي لي عندي هاد المشكل.",
        ),
        "medium": (
            "l équipe dyali kamla 3andha nfs l mouchkil.",
            "الفريق ديالي كامل متأثر.",
        ),
        "high": (
            "kolchi w9ef, 7ta wa7d ma 9ader ykhdem.",
            "كاملين حابسين، ما كاين لي يقدر يخدم.",
        ),
    },
}

#: Urgency markers by band: 1-2 (can wait), 3 (normal), 4-5 (blocking now).
URGENCY_MARKERS: dict[Language, dict[str, tuple[str, ...]]] = {
    Language.FRENCH: {
        "low": (
            "Ce n'est pas urgent, quand vous aurez le temps.",
            "À traiter quand ce sera possible, rien ne presse.",
            "Pas de blocage, c'est juste gênant.",
        ),
        "medium": (
            "Merci de regarder dans la journée.",
            "J'aimerais une réponse avant demain.",
        ),
        "high": (
            "C'est bloquant, je ne peux plus travailler du tout.",
            "Urgent, nous avons une échéance ce soir.",
            "À traiter immédiatement s'il vous plaît.",
        ),
    },
    Language.ARABIC: {
        "low": (
            "الأمر غير مستعجل، عندما يتاح لكم الوقت.",
            "ليس هناك أي عائق، مجرد إزعاج بسيط.",
        ),
        "medium": (
            "أرجو النظر في الموضوع خلال اليوم.",
            "أتمنى الحصول على رد قبل الغد.",
        ),
        "high": (
            "الأمر عاجل، لم أستطع العمل إطلاقا.",
            "نرجو التدخل الفوري، لدينا موعد نهائي الليلة.",
        ),
    },
    Language.DARIJA: {
        "low": (
            "machi musta3jel, mnin tel9aw l wa9t.",
            "ماشي مستعجل، ملي تلقاو الوقت.",
        ),
        "medium": (
            "3afak chofo lia had chi lyoum.",
            "عافاك شوفو ليا هاد الشي اليوم.",
        ),
        "high": (
            "had chi bloquant, ma9dartch nkhdem 3la walo.",
            "هاد الشي حابسني، ما قدرتش نخدم على والو. عافاك دغيا.",
        ),
    },
}


def band(level: int) -> str:
    """Map a 1-5 level onto the three phrasing bands."""
    if level <= 2:
        return "low"
    if level == 3:
        return "medium"
    return "high"


def markers_for(
    language: Language, urgency: int, impact: int
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The candidate impact and urgency phrasings for these levels.

    Falls back to French when a language has no entry, so adding a language to
    the catalogue never silently drops the severity signal.
    """
    impact_pool = IMPACT_MARKERS.get(language, IMPACT_MARKERS[Language.FRENCH])
    urgency_pool = URGENCY_MARKERS.get(language, URGENCY_MARKERS[Language.FRENCH])
    return impact_pool[band(impact)], urgency_pool[band(urgency)]
