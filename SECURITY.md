# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

- GitHub → **Security** tab → *Report a vulnerability*, or
- email **security@novagios.com**

We aim to acknowledge within 5 business days and to ship a fix or give a timeline
within 30 days.

## Scope

This package generates text. It opens no network connections, reads no input files,
and has no runtime dependencies. The optional `glpi` extra pulls in
[`glpi-rest`](https://github.com/novagiosAI/glpi-rest) only if you choose to push tickets
into a server yourself.

## The privacy guarantee, and its limit

**There is no source dataset.** Every name, phrase, category and reference in this
package was invented and committed to the repository in plain sight. Nothing is
derived from a real ticket, so there is nothing to leak.

A test asserts the generated corpus contains nothing shaped like a Moroccan phone
number, RIB or ICE.

What this does **not** cover:

- If you add catalogue entries, **do not paste real ticket text into them.** Rephrase
  it. A template committed here is published forever.
- Generated tickets are safe to publish; a *real* export cleaned with a tool is a
  different matter. For that, see
  [`glpi-anonymizer`](https://github.com/novagiosAI/glpi-anonymizer), and note that
  pseudonymized data is still personal data under GDPR and Moroccan law 09-08.

## Do not point this at production

The integration tests create and purge tickets. Run them only against a disposable
instance — never against a live service desk.
