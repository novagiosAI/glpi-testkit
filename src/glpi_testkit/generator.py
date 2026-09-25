"""Deterministic generator of synthetic ITIL tickets."""

from __future__ import annotations

import random
import re
from collections.abc import Iterator, Sequence
from datetime import datetime, timedelta

from .catalog import (
    CATEGORIES,
    GROUPS,
    REQUESTER_NAMES,
    SLOTS,
    TECHNICIAN_NAMES,
    Category,
    clamp,
)
from .models import Actor, Event, Language, Level, Status, Ticket, TicketType
from .priority import PriorityMatrix, compute_priority
from .severity import markers_for

_SLOT = re.compile(r"\{(\w+)\}")

#: Distribution of final statuses. Most tickets in a real export are closed;
#: a generator that returns mostly "new" produces useless training data.
STATUS_WEIGHTS: tuple[tuple[Status, float], ...] = (
    (Status.CLOSED, 0.55),
    (Status.SOLVED, 0.15),
    (Status.ASSIGNED, 0.14),
    (Status.WAITING, 0.08),
    (Status.PLANNED, 0.04),
    (Status.NEW, 0.04),
)


class TicketGenerator:
    """Produce synthetic tickets that look like a real GLPI export.

    Seeded, so the same seed always yields the same dataset — a benchmark that
    cannot be reproduced is not a benchmark.

    ``sla_pressure`` scales how long resolution takes relative to each
    category's SLA target, and so drives the share of breached tickets.
    Measured over 3000 tickets across five seeds:

    ===============  ==================
    sla_pressure     tickets breaching
    ===============  ==================
    0.2 (default)    13-14%
    0.35             23%
    0.5              32%
    1.0              49%
    ===============  ==================

    The default models a service desk that is meeting its targets. Raise it to
    generate data for a team under strain.

    Example:
        >>> tickets = TicketGenerator(seed=42).generate(100)
        >>> len(tickets)
        100
    """

    __slots__ = (
        "_random",
        "_categories",
        "_languages",
        "_start",
        "_end",
        "_matrix",
        "_sla_pressure",
    )

    def __init__(
        self,
        seed: int | None = None,
        categories: Sequence[Category] | None = None,
        languages: Sequence[Language] | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        priority_matrix: PriorityMatrix | None = None,
        sla_pressure: float = 0.2,
    ) -> None:
        self._random = random.Random(seed)
        self._categories = list(categories) if categories else list(CATEGORIES)
        self._languages = list(languages) if languages else list(Language)
        self._end = end or datetime(2026, 1, 1, 9, 0, 0)
        self._start = start or (self._end - timedelta(days=365))
        if self._start >= self._end:
            raise ValueError("start must be before end")
        self._matrix = priority_matrix
        if not 0 < sla_pressure <= 2:
            raise ValueError("sla_pressure must be within (0, 2]")
        self._sla_pressure = sla_pressure

    def generate(self, count: int) -> list[Ticket]:
        if count < 0:
            raise ValueError("count must be zero or greater")
        return list(self.iter_tickets(count))

    def iter_tickets(self, count: int) -> Iterator[Ticket]:
        for index in range(1, count + 1):
            yield self._one(index)

    # -- internals -------------------------------------------------------

    def _fill(self, template: str) -> str:
        """Replace ``{slot}`` placeholders with catalogue values."""
        return _SLOT.sub(
            lambda match: self._random.choice(
                SLOTS.get(match.group(1), (match.group(0),))
            ),
            template,
        )

    @staticmethod
    def _sentence_case(text: str, language: Language) -> str:
        """Capitalise the first letter of French sentences.

        A template can begin with a slot (``"{app} se ferme tout seul"``), and
        some slot values start lowercase, so the capital has to be applied
        after substitution.

        Darija typed in Latin letters is deliberately left as-is: users really
        do write it lowercase, and that is what a classifier will meet in
        production. Arabic has no letter case, so this is a no-op there.
        """
        if language is not Language.FRENCH or not text:
            return text
        return text[0].upper() + text[1:]

    def _body(
        self,
        category: Category,
        language: Language,
        urgency: Level,
        impact: Level,
    ) -> str:
        """The ticket body, plus phrasing that carries urgency and impact.

        Without the severity markers the text says nothing about how many people
        are affected or how soon it matters, which makes priority unlearnable
        from the text. See :mod:`glpi_testkit.severity`.
        """
        base = self._sentence_case(
            self._fill(self._random.choice(category.bodies[language])), language
        )
        impact_pool, urgency_pool = markers_for(language, int(urgency), int(impact))
        return " ".join(
            [
                base,
                self._random.choice(impact_pool),
                self._random.choice(urgency_pool),
            ]
        )

    def _pick_language(self, category: Category) -> Language:
        available = [
            language
            for language in self._languages
            if category.titles.get(language) and category.bodies.get(language)
        ]
        if not available:
            raise ValueError(
                f"category {category.key!r} has no phrasing for the requested languages"
            )
        return self._random.choice(available)

    def _pick_status(self) -> Status:
        statuses = [status for status, _ in STATUS_WEIGHTS]
        weights = [weight for _, weight in STATUS_WEIGHTS]
        return self._random.choices(statuses, weights=weights, k=1)[0]

    def _business_delay(self, hours: float) -> timedelta:
        """A response delay skewed towards fast answers, with a long tail."""
        return timedelta(hours=max(0.05, self._random.lognormvariate(0, 0.9) * hours))

    def _one(self, ticket_id: int) -> Ticket:
        category = self._random.choice(self._categories)
        language = self._pick_language(category)

        urgency = clamp(self._random.randint(*category.urgency_range))
        impact = clamp(self._random.randint(*category.impact_range))
        priority = compute_priority(urgency, impact, self._matrix)

        created = self._start + timedelta(
            seconds=self._random.randint(
                0, int((self._end - self._start).total_seconds())
            )
        )
        status = self._pick_status()

        requester = Actor(
            id=1000 + self._random.randrange(len(REQUESTER_NAMES)),
            name=self._random.choice(REQUESTER_NAMES),
            group="Utilisateurs",
        )

        events: list[Event] = []
        assignee: Actor | None = None
        take_into_account = 0
        solve_delay = 0
        close_delay = 0
        solvedate: datetime | None = None
        closedate: datetime | None = None
        last_change = created

        # A ticket is only picked up once it leaves NEW.
        if status is not Status.NEW:
            assignee = Actor(
                id=2000 + self._random.randrange(len(TECHNICIAN_NAMES)),
                name=self._random.choice(TECHNICIAN_NAMES),
                group=self._random.choice(GROUPS),
            )
            accepted_at = created + self._business_delay(category.sla_hours / 6)
            take_into_account = int((accepted_at - created).total_seconds())
            events.append(Event(accepted_at, "assign", f"assigned to {assignee.name}"))
            last_change = accepted_at

            # High-priority tickets get escalated and bounce between groups,
            # which is what makes assignment prediction a non-trivial task.
            if priority >= Level.HIGH and self._random.random() < 0.55:
                escalated_at = last_change + self._business_delay(
                    category.sla_hours / 4
                )
                new_group = self._random.choice(GROUPS)
                events.append(
                    Event(escalated_at, "escalate", f"escalated to {new_group}")
                )
                assignee = Actor(
                    id=2000 + self._random.randrange(len(TECHNICIAN_NAMES)),
                    name=self._random.choice(TECHNICIAN_NAMES),
                    group=new_group,
                )
                last_change = escalated_at
            elif self._random.random() < 0.2:
                moved_at = last_change + self._business_delay(category.sla_hours / 3)
                new_group = self._random.choice(GROUPS)
                events.append(Event(moved_at, "reassign", f"reassigned to {new_group}"))
                last_change = moved_at

            if status is Status.WAITING:
                waited_at = last_change + self._business_delay(category.sla_hours / 5)
                events.append(
                    Event(waited_at, "wait", "waiting for requester feedback")
                )
                last_change = waited_at

        if status in (Status.SOLVED, Status.CLOSED):
            solvedate = last_change + self._business_delay(
                category.sla_hours * self._sla_pressure
            )
            solve_delay = int((solvedate - created).total_seconds())
            events.append(Event(solvedate, "solve", "solution provided"))
            last_change = solvedate

        if status is Status.CLOSED and solvedate is not None:
            closedate = solvedate + self._business_delay(category.sla_hours / 2)
            close_delay = int((closedate - created).total_seconds())
            events.append(Event(closedate, "close", "closed after validation"))
            last_change = closedate

        time_to_resolve = created + timedelta(hours=category.sla_hours)
        breached = solvedate is not None and solvedate > time_to_resolve

        return Ticket(
            id=ticket_id,
            name=self._sentence_case(
                self._fill(self._random.choice(category.titles[language])), language
            ),
            content=self._body(category, language, urgency, impact),
            type=category.type,
            status=status,
            urgency=urgency,
            impact=impact,
            priority=priority,
            category=category.key,
            language=language.value,
            date=created,
            date_mod=last_change,
            requester=requester,
            assignee=assignee,
            takeintoaccount_delay_stat=take_into_account,
            solve_delay_stat=solve_delay,
            close_delay_stat=close_delay,
            solvedate=solvedate,
            closedate=closedate,
            time_to_resolve=time_to_resolve,
            sla_breached=breached,
            events=events,
        )


def generate_tickets(
    count: int,
    seed: int | None = None,
    languages: Sequence[Language] | None = None,
) -> list[Ticket]:
    """Shorthand for the common case."""
    return TicketGenerator(seed=seed, languages=languages).generate(count)


__all__ = ["TicketGenerator", "generate_tickets", "STATUS_WEIGHTS", "TicketType"]
