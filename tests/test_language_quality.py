"""Guards on the linguistic quality of the generated text.

Slot substitution is the obvious way to get variety and the obvious way to
produce broken grammar: ``"un {device}"`` yields *"un imprimante"*, ``"du
{place}"`` yields *"du agence"*. Training data with those faults in it is worse
than no data, so each fault class found during development is pinned here.
"""

from __future__ import annotations

import re

import pytest

from glpi_testkit import Language, TicketGenerator

SAMPLE = 2000


@pytest.fixture(scope="module")
def french_text() -> list[str]:
    tickets = TicketGenerator(seed=11, languages=[Language.FRENCH]).generate(SAMPLE)
    return [field for t in tickets for field in (t.name, t.content)]


@pytest.fixture(scope="module")
def arabic_text() -> list[str]:
    tickets = TicketGenerator(seed=11, languages=[Language.ARABIC]).generate(SAMPLE)
    return [field for t in tickets for field in (t.name, t.content)]


class TestFrenchGrammar:
    def test_no_unelided_contraction(self, french_text):
        """'du agence' / 'de le CRM' must never appear.

        "de le" is only wrong before a noun: in "merci de le
        réinitialiser" the "le" is a pronoun and the sentence is correct,
        so the pattern targets the substitution signature - an article
        followed by a capitalised product name.
        """
        bad = re.compile(r"du [aeiouéèêh]|de le [A-Z]|de les [A-Z]|à le [A-Z]")
        offenders = [text for text in french_text if bad.search(text)]
        assert not offenders, offenders[:3]

    def test_no_unelided_preposition(self, french_text):
        bad = re.compile(r"\bau [aeiouéèê]")
        offenders = [text for text in french_text if bad.search(text)]
        assert not offenders, offenders[:3]

    def test_articles_agree_in_gender(self, french_text):
        """'un imprimante' and 'une scanner' are the classic failures."""
        bad = re.compile(
            r"\bun (?:imprimante)\b|\bune (?:scanner|portable|écran|poste)\b|"
            r"\bLa (?:écran|scanner|portable|poste)\b"
        )
        offenders = [text for text in french_text if bad.search(text)]
        assert not offenders, offenders[:3]

    def test_sentences_start_with_a_capital(self, french_text):
        """A template may begin with a slot whose value is lowercase."""
        bad = re.compile(r"^[a-zàâéèêîôùûç]")
        offenders = [text for text in french_text if bad.search(text)]
        assert not offenders, offenders[:3]

    def test_no_double_spaces_or_stray_punctuation(self, french_text):
        for text in french_text:
            assert "  " not in text, text
            assert not text.startswith(" "), text
            assert not text.endswith(" "), text


class TestArabicAgreement:
    def test_feminine_verb_takes_a_feminine_noun(self, arabic_text):
        """'الماسح الضوئي لا تعمل' mixes a masculine noun with a feminine verb."""
        masculine = ("الماسح الضوئي", "الحاسوب")
        feminine_verbs = ("لا تعمل", "تظهر")
        for text in arabic_text:
            for noun in masculine:
                if noun in text:
                    for verb in feminine_verbs:
                        assert verb not in text, f"{noun} + {verb}: {text}"

    def test_arabic_is_not_mangled(self, arabic_text):
        """Arabic script must survive generation intact."""
        assert any("؀" <= char <= "ۿ" for text in arabic_text for char in text)


class TestAllLanguages:
    @pytest.mark.parametrize("language", list(Language))
    def test_no_slot_survives_substitution(self, language):
        tickets = TicketGenerator(seed=5, languages=[language]).generate(500)
        for ticket in tickets:
            assert "{" not in ticket.name and "}" not in ticket.name
            assert "{" not in ticket.content and "}" not in ticket.content

    @pytest.mark.parametrize("language", list(Language))
    def test_text_is_never_empty(self, language):
        tickets = TicketGenerator(seed=5, languages=[language]).generate(200)
        for ticket in tickets:
            assert ticket.name.strip()
            assert ticket.content.strip()

    def test_darija_keeps_its_lowercase_latin_style(self):
        """Users really do type arabizi lowercase; forcing capitals would
        make the data less like production, not more."""
        tickets = TicketGenerator(seed=5, languages=[Language.DARIJA]).generate(300)
        latin = [t.name for t in tickets if re.match(r"^[a-zA-Z]", t.name)]
        assert latin, "expected some Latin-script Darija titles"
        assert any(re.match(r"^[a-z]", title) for title in latin)

    def test_every_language_is_encodable_as_utf8(self):
        """Output has to survive a file write on any platform."""
        tickets = TicketGenerator(seed=5).generate(300)
        for ticket in tickets:
            ticket.name.encode("utf-8")
            ticket.content.encode("utf-8")


class TestSeverityMarkers:
    """Urgency and impact must be visible in the text.

    Without this the generator sampled urgency and impact but wrote a body
    chosen only by category, so priority was unlearnable from the text — a
    classifier trained on that output scored below the majority baseline.
    """

    @pytest.mark.parametrize("language", list(Language))
    def test_high_and_low_impact_read_differently(self, language):
        generator = TicketGenerator(seed=5, languages=[language])
        tickets = generator.generate(600)

        low = {t.content for t in tickets if int(t.impact) <= 2}
        high = {t.content for t in tickets if int(t.impact) >= 4}
        assert low and high
        assert not (low & high), "impact bands must not share wording"

    @pytest.mark.parametrize("language", list(Language))
    def test_high_and_low_urgency_read_differently(self, language):
        tickets = TicketGenerator(seed=5, languages=[language]).generate(600)
        low = {t.content for t in tickets if int(t.urgency) <= 2}
        high = {t.content for t in tickets if int(t.urgency) >= 4}
        assert low and high
        assert not (low & high)

    def test_markers_do_not_name_the_level(self):
        """The text must imply severity, not state it, or the task is a lookup."""
        tickets = TicketGenerator(seed=5).generate(400)
        for ticket in tickets:
            lowered = ticket.content.lower()
            for forbidden in ("urgency=", "impact=", "priority=", "p1", "p5"):
                assert forbidden not in lowered

    def test_body_still_carries_the_category_wording(self):
        """Severity text is appended, it must not replace the problem."""
        tickets = TicketGenerator(seed=5, languages=[Language.FRENCH]).generate(200)
        vpn = [t for t in tickets if t.category == "network.vpn"]
        assert vpn
        assert all("VPN" in t.content or "vpn" in t.content.lower() for t in vpn)
