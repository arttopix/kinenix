# Security & Data Privacy Standards

This document defines credential management, data privacy constraints, and local execution boundaries for **Kinenix**.

---

## 1. Zero Credential Leakage

- **No Hardcoded Secrets:** Never hardcode passwords, API tokens, webhook URLs (e.g., LINE Channel Access Token, Teams Webhooks), or database connection strings directly in source code or `flow.md` files.
- **Environment Variables & Secret Providers:**
  - Retrieve sensitive parameters via environment variables `${env:SECRET_KEY}` or designated configuration files.
  - Configuration files containing sensitive information must be explicitly listed in `.gitignore`.
- **Security checks in CI:** `pip-audit`, `bandit`, and `zizmor` run on every pull request and weekly (`.github/workflows/ci.yml`, job Security checks); CodeQL scans Python and JavaScript (`.github/workflows/codeql.yml`). Pin every action to a commit with its version in a comment (Dependabot keeps them current), set `persist-credentials: false` on checkouts, and pass `${{ }}` values to scripts through `env:`. Fix a bandit finding; when the code is safe as it is, explain it on the flagged line with `# nosec <test id>: <reason>`, never a bare `# nosec`. A dependency with a known vulnerability is upgraded or pinned to a fixed version before the merge.
- **Log Masking:** Redact secrets and personal data from execution logs, console errors, and Hub telemetry on the worker, through `kinenix/engine/redaction.py` only. What is hidden and how: `docs/logging.md` (Redaction). Never log or send a value before it passes through the Redactor.

---

## 2. Local Data Privacy & Enterprise Compliance

- **On-Device Data Processing:** Corporate data, business spreadsheets (`.xlsx`), customer records, and extracted web data must be processed locally within the worker environment.
- **No Unsolicited Data Egress:** Do not send business data to third-party cloud APIs unless explicitly configured by the user in an action designed specifically for that purpose.
- **Local AI Ingestion:** When passing runtime context to SLMs for diagnosis or self-healing selectors, utilize locally hosted models to ensure zero telemetry leakage outside the host network.
