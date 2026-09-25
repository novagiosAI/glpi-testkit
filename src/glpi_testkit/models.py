"""Ticket model and the GLPI enumerations it uses.

Values match GLPI's own integers, so a generated ticket can be posted to the
API unchanged.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any

GLPI_DATETIME = "%Y-%m-%d %H:%M:%S"


class TicketType(IntEnum):
    """GLPI ``Ticket.type``. ITIL separates the two: something broken versus
    something asked for."""

    INCIDENT = 1
    REQUEST = 2


class Status(IntEnum):
    """GLPI ``Ticket.status``."""

    NEW = 1
    ASSIGNED = 2
    PLANNED = 3
    WAITING = 4
    SOLVED = 5
    CLOSED = 6


class Level(IntEnum):
    """Shared scale for urgency, impact and priority (GLPI uses 1-5)."""

    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class Language(str, Enum):
    """Languages the generator writes tickets in.

    ``ary`` is the ISO 639-3 code for Moroccan Arabic; it is a distinct
    language tag from ``ar``, which matters when the output feeds a model.
    """

    FRENCH = "fr"
    ARABIC = "ar"
    DARIJA = "ary"


@dataclass(frozen=True, slots=True)
class Actor:
    """A synthetic person. Never a real one."""

    id: int
    name: str
    group: str


@dataclass(frozen=True, slots=True)
class Event:
    """One step in a ticket's life: assignment, escalation, reassignment..."""

    at: datetime
    kind: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "at": self.at.strftime(GLPI_DATETIME),
            "kind": self.kind,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class Ticket:
    """A synthetic ITIL ticket, shaped like a GLPI ``Ticket``."""

    id: int
    name: str
    content: str
    type: TicketType
    status: Status
    urgency: Level
    impact: Level
    priority: Level
    category: str
    language: str
    date: datetime
    date_mod: datetime
    requester: Actor
    assignee: Actor | None = None
    takeintoaccount_delay_stat: int = 0
    solve_delay_stat: int = 0
    close_delay_stat: int = 0
    solvedate: datetime | None = None
    closedate: datetime | None = None
    time_to_resolve: datetime | None = None
    sla_breached: bool = False
    events: list[Event] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """A JSON-ready dict with GLPI's field names and formats."""
        data = asdict(self)
        for key in ("date", "date_mod", "solvedate", "closedate", "time_to_resolve"):
            value = getattr(self, key)
            data[key] = value.strftime(GLPI_DATETIME) if value else None
        data["type"] = int(self.type)
        data["status"] = int(self.status)
        data["urgency"] = int(self.urgency)
        data["impact"] = int(self.impact)
        data["priority"] = int(self.priority)
        data["events"] = [event.to_dict() for event in self.events]
        return data

    def to_glpi_input(self) -> dict[str, Any]:
        """Only the fields GLPI accepts when creating a ticket via the API."""
        payload: dict[str, Any] = {
            "name": self.name,
            "content": self.content,
            "type": int(self.type),
            "status": int(self.status),
            "urgency": int(self.urgency),
            "impact": int(self.impact),
            "priority": int(self.priority),
            "date": self.date.strftime(GLPI_DATETIME),
        }
        if self.solvedate:
            payload["solvedate"] = self.solvedate.strftime(GLPI_DATETIME)
        if self.closedate:
            payload["closedate"] = self.closedate.strftime(GLPI_DATETIME)
        if self.time_to_resolve:
            payload["time_to_resolve"] = self.time_to_resolve.strftime(GLPI_DATETIME)
        return payload
