"""Service catalogue and multilingual phrasings.

Three languages, because that is how a Moroccan service desk actually receives
tickets: French from head office, Modern Standard Arabic from formal
correspondence, and Darija — often typed in Latin letters — from users
describing a problem in their own words.

Every template carries slots (``{app}``, ``{floor}``) filled at generation time,
so a thousand tickets do not read like ten sentences repeated a hundred times.

**Slots carry their own article and preposition.** French agreement cannot be
patched in afterwards: substituting a bare noun into ``"un {device}"`` yields
*"un imprimante"*, and ``"au {place}"`` yields *"au agence Rabat"*. Grammatically
broken text would be worse than useless as training data, so the article is part
of the slot value and templates never supply one.

**All content here is invented.** No phrase, name or reference comes from a real
ticket — which is the entire point of the package.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Language, Level, TicketType


@dataclass(frozen=True, slots=True)
class Category:
    """One catalogue entry: how tickets of this kind look and behave."""

    key: str
    label_fr: str
    label_en: str
    type: TicketType
    #: Typical urgency/impact range, so a jammed printer never outranks an
    #: outage purely by chance.
    urgency_range: tuple[int, int]
    impact_range: tuple[int, int]
    #: Resolution target in hours, used to build the SLA deadline.
    sla_hours: int
    titles: dict[Language, tuple[str, ...]] = field(default_factory=dict)
    bodies: dict[Language, tuple[str, ...]] = field(default_factory=dict)


#: Slot values. French entries embed their article or preposition; see module
#: docstring for why.
SLOTS: dict[str, tuple[str, ...]] = {
    # Application names must stay article-free: templates supply their own
    # preposition, so a value like "le CRM" would yield "de le CRM".
    "app": (
        "SAP",
        "Sage",
        "Odoo",
        "Outlook",
        "Teams",
        "Jira",
        "SharePoint",
        "Salesforce",
    ),
    "app_ar": ("ساب", "أودو", "أوتلوك", "تيمز", "البوابة الداخلية"),
    "floor": ("1", "2", "3", "4"),
    # "at <place>" — preposition included.
    "at_place": (
        "au siège",
        "à l'agence de Casablanca",
        "à l'agence de Rabat",
        "sur le site de Tanger",
    ),
    # "of <place>" — the contraction is baked in, because "du" + "agence"
    # would produce "du agence".
    "of_place": (
        "du siège",
        "de l'agence de Casablanca",
        "de l'agence de Rabat",
        "du site de Tanger",
    ),
    # Four grammatical forms of the same equipment list: definite mid-sentence,
    # definite sentence-initial, indefinite, and bare for titles.
    "the_device": (
        "l'imprimante",
        "le scanner",
        "le poste fixe",
        "le portable",
        "l'écran",
    ),
    "The_device": (
        "L'imprimante",
        "Le scanner",
        "Le poste fixe",
        "Le portable",
        "L'écran",
    ),
    "a_device": (
        "une imprimante",
        "un scanner",
        "un poste fixe",
        "un portable",
        "un écran",
    ),
    "device_noun": ("Imprimante", "Scanner", "Poste fixe", "Portable", "Écran"),
    # Arabic splits by gender: a template carrying a feminine verb must only
    # ever receive a feminine noun, or the agreement breaks.
    "device_ar": ("الطابعة", "الماسح الضوئي", "الحاسوب", "الشاشة"),
    "device_ar_f": ("الطابعة", "الشاشة"),
    "device_ar_m": ("الماسح الضوئي", "الحاسوب"),
    "device_darija": ("l imprimante", "l scanner", "l pc", "l portable", "l écran"),
    "browser": ("Chrome", "Firefox", "Edge"),
    "error": ("0x0000007B", "ERR_CONNECTION_TIMED_OUT", "500", "AUTH_FAILED"),
}


CATEGORIES: tuple[Category, ...] = (
    Category(
        key="network.vpn",
        label_fr="Réseau > VPN",
        label_en="Network > VPN",
        type=TicketType.INCIDENT,
        urgency_range=(3, 5),
        impact_range=(3, 5),
        sla_hours=4,
        titles={
            Language.FRENCH: (
                "Impossible de se connecter au VPN",
                "VPN déconnecté en boucle",
                "Erreur {error} à la connexion VPN",
                "Accès VPN indisponible {at_place}",
            ),
            Language.ARABIC: (
                "تعذر الاتصال بالشبكة الافتراضية الخاصة",
                "انقطاع متكرر في اتصال VPN",
            ),
            Language.DARIJA: (
                "VPN ما خدامش عندي",
                "ma9darch ndkhol l VPN",
                "l VPN kata9ta3 bzaf",
            ),
        },
        bodies={
            Language.FRENCH: (
                "Depuis ce matin je n'arrive plus à me connecter au VPN "
                "{at_place}. Le client affiche {error} après quelques secondes.",
                "Le VPN se déconnecte toutes les dix minutes et je perds ma "
                "session sur {app} à chaque fois. Merci de regarder rapidement.",
                "Aucun collègue {at_place} n'arrive à ouvrir le VPN depuis la "
                "coupure de cette nuit.",
            ),
            Language.ARABIC: (
                "منذ صباح اليوم لا أستطيع الاتصال بالشبكة الافتراضية الخاصة. "
                "تظهر رسالة خطأ بعد بضع ثوان من المحاولة.",
                "ينقطع الاتصال بشكل متكرر مما يؤثر على عملي على {app_ar}.",
            ),
            Language.DARIJA: (
                "من الصباح و أنا كنحاول ندخل ل VPN و ما كيدخلش. "
                "كيطلع لي خطأ و من بعد كيتسد.",
                "l vpn kat9ta3 kol chi 10 d daqayq, tan7iyed men {app} kol mrra. "
                "3afak chofo lia had chi dghya.",
            ),
        },
    ),
    Category(
        key="hardware.printer",
        label_fr="Matériel > Imprimante",
        label_en="Hardware > Printer",
        type=TicketType.INCIDENT,
        urgency_range=(1, 3),
        impact_range=(1, 3),
        sla_hours=24,
        titles={
            Language.FRENCH: (
                "{device_noun} hors service étage {floor}",
                "Bourrage papier étage {floor}",
                "Impression impossible depuis {app}",
            ),
            Language.ARABIC: (
                "انحشار الورق في {device_ar_f}",
                "{device_ar_f} لا تعمل في الطابق {floor}",
            ),
            Language.DARIJA: (
                "{device_darija} dyal l etage {floor} ma khdamach",
                "الطابعة حشات الورقة",
            ),
        },
        bodies={
            Language.FRENCH: (
                "{The_device} de l'étage {floor} signale un bourrage papier "
                "alors que le bac est vide. Nous avons déjà redémarré l'appareil.",
                "Impossible d'imprimer depuis {app} : le travail reste en file "
                "d'attente sans message d'erreur.",
                "{The_device} {of_place} n'imprime plus qu'une page sur deux.",
            ),
            Language.ARABIC: (
                "تظهر {device_ar_f} رسالة انحشار الورق رغم أن الدرج فارغ. "
                "قمنا بإعادة تشغيل الجهاز دون جدوى.",
            ),
            Language.DARIJA: (
                "الطابعة ديال الطابق {floor} كتقول كاين الورق حاشر و لكن ما كاين والو. "
                "جربنا نطفيوها و نشعلوها و نفس المشكل.",
                "ma9darnach ntab3o men {app}, l document kaybqa f la file o safi.",
            ),
        },
    ),
    Category(
        key="account.password",
        label_fr="Compte > Mot de passe",
        label_en="Account > Password",
        type=TicketType.REQUEST,
        urgency_range=(2, 4),
        impact_range=(1, 3),
        sla_hours=2,
        titles={
            Language.FRENCH: (
                "Réinitialisation du mot de passe",
                "Compte bloqué après plusieurs tentatives",
                "Accès refusé sur {app}",
            ),
            Language.ARABIC: (
                "إعادة تعيين كلمة المرور",
                "الحساب مقفل بعد عدة محاولات",
            ),
            Language.DARIJA: (
                "nssit l mot de passe dyali",
                "الحساب ديالي تسد",
            ),
        },
        bodies={
            Language.FRENCH: (
                "J'ai oublié mon mot de passe et mon compte s'est bloqué après "
                "trois tentatives. Merci de le réinitialiser.",
                "Mon accès à {app} est refusé depuis le changement de mot de "
                "passe de la semaine dernière.",
            ),
            Language.ARABIC: (
                "نسيت كلمة المرور وتم قفل الحساب بعد ثلاث محاولات. أرجو إعادة تعيينها.",
            ),
            Language.DARIJA: (
                "نسيت كلمة السر ديالي و الحساب تسد من بعد تلت محاولات. "
                "عافاك عاودو ليا التعيين.",
                "ma9darch ndkhol l {app} men b3d ma bdlt l mot de passe.",
            ),
        },
    ),
    Category(
        key="software.crash",
        label_fr="Logiciel > Plantage",
        label_en="Software > Crash",
        type=TicketType.INCIDENT,
        urgency_range=(2, 4),
        impact_range=(2, 4),
        sla_hours=8,
        titles={
            Language.FRENCH: (
                "{app} se ferme tout seul",
                "Erreur {error} au lancement de {app}",
                "Plantage répété de {app}",
            ),
            Language.ARABIC: (
                "توقف {app_ar} عن العمل",
                "رسالة خطأ عند تشغيل التطبيق",
            ),
            Language.DARIJA: (
                "{app} kaytsed wa7do",
                "التطبيق كيوقف على المرة",
            ),
        },
        bodies={
            Language.FRENCH: (
                "{app} se ferme sans message dès que j'ouvre un dossier client. "
                "Le problème est apparu après la mise à jour de la semaine dernière.",
                "Au lancement de {app} j'obtiens l'erreur {error} puis "
                "l'application se ferme.",
                "Le même plantage touche plusieurs postes {at_place}.",
            ),
            Language.ARABIC: (
                "يتوقف {app_ar} عن العمل عند فتح ملف العميل، "
                "وقد بدأت المشكلة بعد التحديث الأخير.",
            ),
            Language.DARIJA: (
                "{app} kaytsed wa7do mnin kanfte7 chi dossier dyal client. "
                "had chi bda men b3d la mise a jour dyal simana lli fatet.",
                "منين كنشغل التطبيق كيطلع لي خطأ و من بعد كيتسد.",
            ),
        },
    ),
    Category(
        key="email.mailbox",
        label_fr="Messagerie > Boîte aux lettres",
        label_en="Email > Mailbox",
        type=TicketType.INCIDENT,
        urgency_range=(2, 4),
        impact_range=(2, 3),
        sla_hours=8,
        titles={
            Language.FRENCH: (
                "Boîte mail pleine",
                "Impossible d'envoyer des pièces jointes",
                "Messages sortants bloqués depuis {app}",
            ),
            Language.ARABIC: (
                "صندوق البريد ممتلئ",
                "تعذر إرسال المرفقات",
            ),
            Language.DARIJA: (
                "l boite mail 3amra",
                "ما قدرتش نصيفط لمرفقات",
            ),
        },
        bodies={
            Language.FRENCH: (
                "Ma boîte est pleine et je ne reçois plus rien depuis hier. "
                "Merci d'augmenter le quota.",
                "Les pièces jointes de plus de 5 Mo sont rejetées avec l'erreur "
                "{error} depuis {app}.",
            ),
            Language.ARABIC: (
                "صندوق البريد ممتلئ ولم أعد أستقبل أي رسالة منذ الأمس. "
                "أرجو الرفع من الحصة المخصصة.",
            ),
            Language.DARIJA: (
                "صندوق البريد ديالي عامر و ما بقيتش كنتوصل بوالو من البارح. "
                "عافاك زيدو لي الحجم.",
                "kolchi mail fih pièce jointe kbira kayrfd, kaytle3 lia {error}.",
            ),
        },
    ),
    Category(
        key="request.equipment",
        label_fr="Demande > Matériel",
        label_en="Request > Equipment",
        type=TicketType.REQUEST,
        urgency_range=(1, 3),
        impact_range=(1, 3),
        sla_hours=72,
        titles={
            Language.FRENCH: (
                "Demande de matériel pour un nouveau collaborateur",
                "Remplacement de matériel {at_place}",
                "{device_noun} à prévoir étage {floor}",
            ),
            Language.ARABIC: (
                "طلب {device_ar} لموظف جديد",
                "طلب تعويض {device_ar}",
            ),
            Language.DARIJA: (
                "kanteb {device_darija} l wa7d l collègue jdid",
                "بغيت نبدل الجهاز",
            ),
        },
        bodies={
            Language.FRENCH: (
                "Un nouveau collaborateur arrive lundi {at_place}, étage "
                "{floor}. Merci de prévoir {a_device} et les accès à {app}.",
                "{The_device} {of_place} est hors service depuis deux "
                "semaines, merci de prévoir son remplacement.",
            ),
            Language.ARABIC: (
                "سيلتحق موظف جديد يوم الاثنين، أرجو تجهيز {device_ar} "
                "وفتح الولوج إلى {app_ar}.",
            ),
            Language.DARIJA: (
                "غادي يجي واحد الزميل جديد نهار التنين، عافاك وجدو ليه الجهاز "
                "و الولوج للتطبيق.",
                "{device_darija} 7bes hadi jouj simanat, khassna wa7d jdid.",
            ),
        },
    ),
    Category(
        key="security.phishing",
        label_fr="Sécurité > Hameçonnage",
        label_en="Security > Phishing",
        type=TicketType.INCIDENT,
        urgency_range=(4, 5),
        impact_range=(3, 5),
        sla_hours=2,
        titles={
            Language.FRENCH: (
                "Signalement de mail suspect",
                "Tentative d'hameçonnage reçue",
                "Mail frauduleux diffusé {at_place}",
            ),
            Language.ARABIC: (
                "الإبلاغ عن رسالة مشبوهة",
                "محاولة تصيد احتيالي",
            ),
            Language.DARIJA: (
                "توصلت بمايل مشبوه",
                "wsselni chi mail mchbouh",
            ),
        },
        bodies={
            Language.FRENCH: (
                "J'ai reçu un message demandant mes identifiants {app} avec un "
                "lien externe. Je n'ai pas cliqué. Merci de vérifier.",
                "Plusieurs collègues {at_place} ont reçu le même mail suspect "
                "ce matin.",
            ),
            Language.ARABIC: (
                "توصلت برسالة تطلب مني بيانات الدخول مع رابط خارجي. "
                "لم أقم بالضغط عليه. أرجو التحقق.",
            ),
            Language.DARIJA: (
                "توصلت بواحد المايل كيطلب مني كلمة السر ديالي و فيه رابط غريب. "
                "ما ضغطتش عليه. عافاك شوفو هاد الشي.",
                "bzaf d zmala wsselhom nfs l mail lyoum sba7.",
            ),
        },
    ),
)


#: Invented staff, used as requesters and assignees.
REQUESTER_NAMES: tuple[str, ...] = (
    "Yassine Amrani",
    "Salma Bennani",
    "Karim Idrissi",
    "Nadia Lahlou",
    "Omar Tazi",
    "Imane Chraibi",
    "Rachid Benjelloun",
    "Hind Alaoui",
    "Mehdi Fassi",
    "Soukaina Berrada",
    "Anas Kettani",
    "Leila Naciri",
)

TECHNICIAN_NAMES: tuple[str, ...] = (
    "Support N1 - Hamza",
    "Support N1 - Ghita",
    "Support N2 - Youssef",
    "Support N2 - Meryem",
    "Expert Réseau - Adil",
    "Expert Sécurité - Sanaa",
)

GROUPS: tuple[str, ...] = (
    "Support N1",
    "Support N2",
    "Réseau",
    "Sécurité",
    "Applications",
)


def category_by_key(key: str) -> Category:
    for category in CATEGORIES:
        if category.key == key:
            return category
    raise KeyError(f"unknown category: {key}")


def clamp(value: int) -> Level:
    """Keep a level inside GLPI's 1-5 scale."""
    return Level(max(1, min(5, value)))
