from __future__ import annotations

import json
from datetime import datetime

import pytest

from glpi_testkit import (
    CATEGORIES,
    GLPI_DEFAULT_PRIORITY_MATRIX,
    Language,
    Level,
    Status,
    TicketGenerator,
    TicketType,
    compute_priority,
    generate_tickets,
)


class TestPriorityMatrix:
    def test_matches_glpi_defaults(self):
        """Read from a stock GLPI 11 install: priority_matrix[urgency][impact]."""
        assert compute_priority(5, 5) == Level.VERY_HIGH
        assert compute_priority(1, 1) == Level.VERY_LOW
        assert compute_priority(3, 3) == Level.MEDIUM
        assert compute_priority(4, 5) == Level.VERY_HIGH
        assert compute_priority(1, 5) == Level.LOW

    def test_default_matrix_is_symmetric(self):
        """GLPI's stock table happens to treat urgency and impact alike.

        Worth pinning: if a future GLPI release changes it, the generated data
        would silently stop matching a real install.
        """
        for urgency in range(1, 6):
            for impact in range(1, 6):
                assert compute_priority(urgency, impact) == compute_priority(
                    impact, urgency
                )

    def test_asymmetric_custom_matrices_are_supported(self):
        """The lookup must not assume symmetry, since the matrix is editable."""
        skewed = {u: {i: min(5, u) for i in range(1, 6)} for u in range(1, 6)}
        assert compute_priority(2, 4, skewed) != compute_priority(4, 2, skewed)

    def test_every_cell_is_covered(self):
        for urgency in range(1, 6):
            for impact in range(1, 6):
                assert 1 <= int(compute_priority(urgency, impact)) <= 5

    def test_custom_matrix_is_used(self):
        always_high = {u: {i: 5 for i in range(1, 6)} for u in range(1, 6)}
        assert compute_priority(1, 1, always_high) == Level.VERY_HIGH

    def test_missing_cell_falls_back_like_glpi(self):
        """GLPI falls back to round((urgency + impact) / 2)."""
        assert compute_priority(4, 4, {1: {1: 1}}) == Level(4)

    def test_default_matrix_shape(self):
        assert set(GLPI_DEFAULT_PRIORITY_MATRIX) == set(range(1, 6))
        for row in GLPI_DEFAULT_PRIORITY_MATRIX.values():
            assert set(row) == set(range(1, 6))


class TestDeterminism:
    def test_same_seed_gives_the_same_dataset(self):
        """A benchmark that cannot be reproduced is not a benchmark."""
        first = [t.to_dict() for t in generate_tickets(50, seed=42)]
        second = [t.to_dict() for t in generate_tickets(50, seed=42)]
        assert first == second

    def test_different_seeds_differ(self):
        first = [t.to_dict() for t in generate_tickets(50, seed=1)]
        second = [t.to_dict() for t in generate_tickets(50, seed=2)]
        assert first != second

    def test_output_is_json_serializable(self):
        payload = [t.to_dict() for t in generate_tickets(20, seed=7)]
        assert json.loads(json.dumps(payload, ensure_ascii=False)) == payload


class TestShape:
    @pytest.fixture(scope="class")
    @staticmethod
    def tickets():
        return generate_tickets(400, seed=2026)

    def test_count(self, tickets):
        assert len(tickets) == 400

    def test_ids_are_unique_and_sequential(self, tickets):
        assert [t.id for t in tickets] == list(range(1, 401))

    def test_priority_always_matches_the_matrix(self, tickets):
        for ticket in tickets:
            assert ticket.priority == compute_priority(ticket.urgency, ticket.impact)

    def test_levels_stay_in_range(self, tickets):
        for ticket in tickets:
            for level in (ticket.urgency, ticket.impact, ticket.priority):
                assert 1 <= int(level) <= 5

    def test_both_itil_types_appear(self, tickets):
        types = {ticket.type for ticket in tickets}
        assert types == {TicketType.INCIDENT, TicketType.REQUEST}

    def test_all_three_languages_appear(self, tickets):
        assert {t.language for t in tickets} == {"fr", "ar", "ary"}

    def test_no_placeholder_survives(self, tickets):
        """Every {slot} must have been filled."""
        for ticket in tickets:
            assert "{" not in ticket.name, ticket.name
            assert "{" not in ticket.content, ticket.content

    def test_titles_and_bodies_vary(self, tickets):
        """A thousand tickets must not read like ten repeated sentences."""
        assert len({t.name for t in tickets}) > 40
        assert len({t.content for t in tickets}) > 30


class TestLifecycleConsistency:
    """Timestamps must tell a story a real ITSM tool could have produced."""

    @pytest.fixture(scope="class")
    @staticmethod
    def tickets():
        return generate_tickets(400, seed=99)

    def test_dates_are_ordered(self, tickets):
        for t in tickets:
            assert t.date <= t.date_mod
            if t.solvedate:
                assert t.date <= t.solvedate
            if t.closedate and t.solvedate:
                assert t.solvedate <= t.closedate

    def test_new_tickets_have_no_assignee(self, tickets):
        for t in tickets:
            if t.status is Status.NEW:
                assert t.assignee is None
                assert t.takeintoaccount_delay_stat == 0

    def test_non_new_tickets_are_assigned(self, tickets):
        for t in tickets:
            if t.status is not Status.NEW:
                assert t.assignee is not None

    def test_only_finished_tickets_have_a_solve_date(self, tickets):
        for t in tickets:
            if t.status in (Status.SOLVED, Status.CLOSED):
                assert t.solvedate is not None
            else:
                assert t.solvedate is None

    def test_only_closed_tickets_have_a_close_date(self, tickets):
        for t in tickets:
            assert (t.closedate is not None) == (t.status is Status.CLOSED)

    def test_delays_are_positive(self, tickets):
        for t in tickets:
            assert t.takeintoaccount_delay_stat >= 0
            assert t.solve_delay_stat >= 0
            assert t.close_delay_stat >= 0

    def test_solve_delay_matches_the_dates(self, tickets):
        for t in tickets:
            if t.solvedate:
                expected = int((t.solvedate - t.date).total_seconds())
                assert t.solve_delay_stat == expected

    def test_sla_breach_matches_the_deadline(self, tickets):
        for t in tickets:
            if t.solvedate and t.time_to_resolve:
                assert t.sla_breached == (t.solvedate > t.time_to_resolve)
            else:
                assert not t.sla_breached

    def test_events_are_chronological(self, tickets):
        for t in tickets:
            times = [event.at for event in t.events]
            assert times == sorted(times), t.id

    def test_escalations_happen_on_high_priority(self, tickets):
        escalated = [t for t in tickets if any(e.kind == "escalate" for e in t.events)]
        assert escalated, "expected some escalations"
        for t in escalated:
            assert t.priority >= Level.HIGH


class TestFiltering:
    def test_language_filter(self):
        tickets = TicketGenerator(seed=5, languages=[Language.DARIJA]).generate(50)
        assert {t.language for t in tickets} == {"ary"}

    def test_category_filter(self):
        only = [c for c in CATEGORIES if c.key == "network.vpn"]
        tickets = TicketGenerator(seed=5, categories=only).generate(30)
        assert {t.category for t in tickets} == {"network.vpn"}

    def test_date_window_is_respected(self):
        start = datetime(2025, 6, 1)
        end = datetime(2025, 6, 30)
        tickets = TicketGenerator(seed=5, start=start, end=end).generate(60)
        for t in tickets:
            assert start <= t.date <= end

    def test_start_after_end_is_refused(self):
        with pytest.raises(ValueError):
            TicketGenerator(start=datetime(2026, 1, 2), end=datetime(2026, 1, 1))

    def test_negative_count_is_refused(self):
        with pytest.raises(ValueError):
            TicketGenerator(seed=1).generate(-1)

    def test_zero_count_is_allowed(self):
        assert TicketGenerator(seed=1).generate(0) == []


class TestGlpiCompatibility:
    def test_glpi_input_holds_only_accepted_fields(self):
        payload = generate_tickets(1, seed=3)[0].to_glpi_input()
        allowed = {
            "name",
            "content",
            "type",
            "status",
            "urgency",
            "impact",
            "priority",
            "date",
            "solvedate",
            "closedate",
            "time_to_resolve",
        }
        assert set(payload) <= allowed

    def test_glpi_input_uses_integers_for_enums(self):
        payload = generate_tickets(1, seed=3)[0].to_glpi_input()
        for key in ("type", "status", "urgency", "impact", "priority"):
            assert isinstance(payload[key], int)

    def test_dates_use_glpi_format(self):
        payload = generate_tickets(1, seed=3)[0].to_glpi_input()
        datetime.strptime(payload["date"], "%Y-%m-%d %H:%M:%S")


class TestPrivacy:
    """The whole point: nothing here may come from a real person."""

    def test_no_real_looking_identifiers(self):
        import re

        tickets = generate_tickets(300, seed=11)
        blob = " ".join(f"{t.name} {t.content}" for t in tickets)
        assert not re.search(r"\b\d{24}\b", blob), "no RIB-shaped strings"
        assert not re.search(r"\b\d{15}\b", blob), "no ICE-shaped strings"
        assert not re.search(r"\b0[5-7]\d{8}\b", blob), "no Moroccan phone numbers"
        assert "@" not in blob or "example" in blob, "no stray email addresses"
