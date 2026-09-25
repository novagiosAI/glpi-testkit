"""ITIL priority derivation, matching GLPI's own behaviour.

GLPI does not compute priority arithmetically: it looks it up in a configurable
5x5 matrix stored as ``priority_matrix`` in ``glpi_configs``, indexed
``[urgency][impact]``. The default below was read from a stock GLPI 11 install,
and `CommonITILObject::computePriority` falls back to
``round((urgency + impact) / 2)`` when a cell is missing — reproduced here so
generated data lines up with what a real GLPI would have stored.
"""

from __future__ import annotations

from .models import Level

#: GLPI's out-of-the-box matrix, indexed [urgency][impact].
GLPI_DEFAULT_PRIORITY_MATRIX: dict[int, dict[int, int]] = {
    1: {1: 1, 2: 1, 3: 2, 4: 2, 5: 2},
    2: {1: 1, 2: 2, 3: 2, 4: 3, 5: 3},
    3: {1: 2, 2: 2, 3: 3, 4: 4, 5: 4},
    4: {1: 2, 2: 3, 3: 4, 4: 4, 5: 5},
    5: {1: 2, 2: 3, 3: 4, 4: 5, 5: 5},
}

PriorityMatrix = dict[int, dict[int, int]]


def compute_priority(
    urgency: Level | int,
    impact: Level | int,
    matrix: PriorityMatrix | None = None,
) -> Level:
    """Derive an ITIL priority from urgency and impact.

    Mirrors ``CommonITILObject::computePriority``, including its arithmetic
    fallback, so a custom matrix with gaps behaves the same way GLPI would.
    """
    table = matrix if matrix is not None else GLPI_DEFAULT_PRIORITY_MATRIX
    urgency_value, impact_value = int(urgency), int(impact)
    try:
        return Level(table[urgency_value][impact_value])
    except KeyError:
        return Level(round((urgency_value + impact_value) / 2))
