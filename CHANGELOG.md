# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-09-19

First public release.

### Added

- `TicketGenerator`, producing seeded, reproducible ITIL tickets shaped like a GLPI
  export: incidents and service requests, seven catalogue categories, urgency,
  impact, derived priority, statuses, escalations, reassignments, delay statistics
  and SLA deadlines.
- **GLPI's real priority matrix**, read out of a stock GLPI 11 install and applied
  as `priority_matrix[urgency][impact]`, including the arithmetic fallback from
  `CommonITILObject::computePriority`. Verified cell by cell — all 25 combinations —
  against a live server.
- Three languages: French, Modern Standard Arabic, and Darija in both Arabic script
  and Latin letters (`ary`, ISO 639-3).
- Slot substitution that respects French articles, elision and gender, and Arabic
  gender agreement, with a dedicated test suite scanning thousands of generated
  sentences for each fault class.
- `sla_pressure` knob controlling the share of breached tickets; the default of 0.2
  yields a measured 13–14%.
- `to_glpi_input()` emitting exactly the fields the GLPI REST API accepts, and
  `to_dict()` emitting the full record for offline use.
- `glpi-testkit` command line tool with language and category filters, `--stats`,
  `--glpi-input` and `--list-categories`.
- UTF-8 output forced on Windows consoles, so Arabic and Darija do not raise
  `UnicodeEncodeError`.
- 53 offline tests plus 7 integration tests that push generated tickets into a live
  GLPI 11 and read them back.
- CI across Python 3.10–3.13 with `pytest`, `ruff` and `mypy --strict`.

[Unreleased]: https://github.com/novagiosAI/glpi-testkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/novagiosAI/glpi-testkit/releases/tag/v0.1.0
