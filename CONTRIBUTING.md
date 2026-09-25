# Contributing to glpi-testkit

Thanks for taking the time to contribute. Two kinds of contribution are especially
valuable here:

- **Corrections to the Arabic and Darija phrasings** by native speakers. The
  wording is written to be idiomatic, but a native reviewer will always improve it.
  This is the single most useful pull request this project can receive.
- **New catalogue entries.** Seven categories is a start; real service desks have
  dozens.

## Getting set up

```bash
git clone https://github.com/novagiosAI/glpi-testkit.git
cd glpi-testkit
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Before opening a pull request

```bash
pytest
ruff check .
ruff format .
mypy
```

To also run the integration suite against a live GLPI, see
`tests/test_integration_glpi.py`. Use a disposable instance.

## The absolute rule

**Never paste text from a real ticket into this repository.** Not anonymized, not
"just as an example". The entire value of this package is that it has no source
dataset. Invent the phrasing, or rewrite a real one until nothing of the original
survives.

## Adding a catalogue entry

1. Add a `Category` to `catalog.py` with its ITIL type, urgency/impact ranges and
   SLA target. Ranges matter: a jammed printer must not be able to outrank a
   security incident.
2. Write titles and bodies for **all three languages**. A category missing a
   language is silently skipped for that language, which quietly skews the mix.
3. **Slots carry their own article, preposition and gender.** This is the trap:
   `"un {device}"` produces *"un imprimante"*, `"du {place}"` produces *"du
   agence"*, `"de {app}"` with `app="le CRM"` produces *"de le CRM"*, and an Arabic
   feminine verb against a masculine noun is wrong the same way. Use the existing
   `the_device` / `The_device` / `a_device` / `device_ar_f` / `at_place` /
   `of_place` slots, and add new ones in the same style rather than bare nouns.
4. Run `pytest tests/test_language_quality.py`. It scans thousands of generated
   sentences for every fault class found so far. If you introduce a new one, add a
   guard for it.

## Design principles

1. **No source dataset, ever.** See above.
2. **Match GLPI's real behaviour.** The priority matrix was read out of a running
   GLPI 11 and is verified cell by cell against a live server in the integration
   suite. Guessing would defeat the purpose.
3. **Seeded and reproducible.** The same seed must always yield the same dataset.
   A benchmark that cannot be reproduced is not a benchmark.
4. **Coherent lifecycles.** Timestamps, statuses and delay statistics must tell a
   story a real ITSM tool could have produced.

## Security issues

Do not open a public issue for a vulnerability. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE).
