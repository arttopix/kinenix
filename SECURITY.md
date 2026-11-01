# Security Policy

## Supported versions

Security fixes go into the latest 1.x release of `kinenix`, `kinenix-hub`, and `kinenix-worker`. Versions before 1.0.0 do not get fixes; upgrade to 1.x ([docs/releasing.md](docs/releasing.md#3-upgrading-an-installation)). `kinenix-studio` is not published and is not supported.

## Reporting a vulnerability

Do not open a public issue. Report it privately on GitHub: open the repository's **Security** tab and choose **Report a vulnerability**.

Include the Kinenix version (`kinenix version`), what an attacker can do, and the steps or a small `flow.md` that shows it. Leave out real passwords and business data.

You get a first reply within 7 days. Once the problem is confirmed, we agree on a fix and a date to publish it, and credit you in the advisory unless you prefer not to be named.

## Scope

What Kinenix protects and what it trusts are written in the threat model, [docs/design/threat-model.md](docs/design/threat-model.md). A flow is code: it runs with the rights of the user who starts it, so a flow that does harm because someone wrote it to is not a vulnerability in Kinenix. A way to run code or read data that the flow did not ask for is.
