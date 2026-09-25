"""Command line entry point: ``glpi-testkit``."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Sequence
from typing import Any

from .catalog import CATEGORIES
from .generator import TicketGenerator
from .models import Language, Ticket


def _summary(tickets: Sequence[Ticket]) -> str:
    languages = Counter(ticket.language for ticket in tickets)
    categories = Counter(ticket.category for ticket in tickets)
    statuses = Counter(ticket.status.name for ticket in tickets)
    priorities = Counter(ticket.priority.name for ticket in tickets)
    breached = sum(1 for ticket in tickets if ticket.sla_breached)

    lines = [f"{len(tickets)} tickets generated", ""]
    for title, counter in (
        ("language", languages),
        ("status", statuses),
        ("priority", priorities),
        ("category", categories),
    ):
        lines.append(f"  by {title}:")
        for key, value in counter.most_common():
            lines.append(f"    {key:<22} {value:>6}")
        lines.append("")
    lines.append(f"  SLA breached: {breached} ({breached / max(1, len(tickets)):.0%})")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glpi-testkit",
        description=(
            "Generate synthetic ITIL tickets for GLPI. No client data involved."
        ),
    )
    parser.add_argument("-n", "--count", type=int, default=100, help="how many tickets")
    parser.add_argument("-o", "--output", help="write JSON here instead of stdout")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="seed for reproducible output (same seed, same dataset)",
    )
    parser.add_argument(
        "-l",
        "--languages",
        nargs="+",
        choices=[language.value for language in Language],
        help="restrict to these languages (default: all three)",
    )
    parser.add_argument(
        "-c",
        "--categories",
        nargs="+",
        choices=[category.key for category in CATEGORIES],
        help="restrict to these catalogue entries (default: all)",
    )
    parser.add_argument(
        "--glpi-input",
        action="store_true",
        help="emit only the fields the GLPI API accepts on creation",
    )
    parser.add_argument(
        "--stats", action="store_true", help="print a distribution summary to stderr"
    )
    parser.add_argument(
        "--list-categories", action="store_true", help="show the catalogue and exit"
    )
    return parser


def _force_utf8_output() -> None:
    """Windows consoles default to a legacy code page.

    Arabic and Darija content would raise UnicodeEncodeError on the way to
    stdout, which is not acceptable for a package whose whole point is
    non-Latin text.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):  # pragma: no cover - exotic streams
                pass


def main(argv: Sequence[str] | None = None) -> int:
    _force_utf8_output()
    args = build_parser().parse_args(argv)

    if args.list_categories:
        for category in CATEGORIES:
            print(
                f"{category.key:<22} {category.type.name:<8} "
                f"SLA {category.sla_hours:>3}h  {category.label_en}"
            )
        return 0

    if args.count < 0:
        raise SystemExit("--count must be zero or greater")

    languages = (
        [Language(value) for value in args.languages] if args.languages else None
    )
    categories = (
        [category for category in CATEGORIES if category.key in set(args.categories)]
        if args.categories
        else None
    )

    generator = TicketGenerator(
        seed=args.seed, languages=languages, categories=categories
    )
    tickets = generator.generate(args.count)

    payload: list[dict[str, Any]] = [
        ticket.to_glpi_input() if args.glpi_input else ticket.to_dict()
        for ticket in tickets
    ]
    text = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")

    if args.stats:
        print(_summary(tickets), file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
