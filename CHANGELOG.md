# Changelog

`kinenix`, `kinenix-hub`, and `kinenix-worker` are released together with one version. How to release: [docs/releasing.md](docs/releasing.md).

## Unreleased

### Deprecated

These still work in 1.x and warn when used; Kinenix 2.0 removes them.

- `on_error: retry`: it already works like `fail`. Delete the line; `max_retries` does the retrying.
- `fallback_step_id`: use `on_error: continue` and a next step with a `condition`, or `## On Error`.
- `kinenix export-md`: convert any `flow.json` from 0.2.0b3 or older with Kinenix 1.x.
- The Orchestrator names: `kinenix orchestrator`, `kinenix run --orchestrator`, the `ORCHESTRATOR_*` and `KINENIX_ORCHESTRATOR_*` variables, and `~/.kinenix/orchestrator.env` ([docs/hub.md](docs/hub.md), section 5).

`kinenix validate` prints the deprecated parts of a flow without failing, and every run logs them.

## 0.5.0b1 (2026-10-28)

Learn and test: a tutorial from requirements to a running flow, a business example, testing a flow against saved pages, and documentation for AI assistants.

Nothing changes for existing flows. A flow that uses `match: loose` on `web.choose`, or a page saved in its folder as the `url` of `web.open` or `web.goto`, should say `> Requires: kinenix>=0.5.0b1`: older versions do not know them.

### Learn

- A tutorial, `docs/tutorial.md` (https://www.kinenix.com/tutorial/): `kinenix init my-first-flow --example first_flow` gives a finished `requirements.md`, an empty `flow.md` for your AI assistant to build, a made-up shop's catalog saved in the project, and a solution; it goes through validate, run, and breaking the flow on purpose (#117).
- `quote_requests`, a business example: quote requests from a CSV entered into a made-up insurer's form, the packages collected, and the failed requests listed with their reasons, offline.
- `docs/examples.md`: every example and the patterns it shows. Every example has the `requirements.md` it implements.
- `llms.txt` for AI assistants, served as https://www.kinenix.com/llms.txt (#119).

### Flows

- Test a flow against saved pages: `kinenix run FLOW --config config/test.json` replaces settings for one run, and `web.open` and `web.goto` open a page saved in the flow's folder, such as `tests/pages/form.html` (#106).
- `web.choose` with `match: loose` ignores spaces, hyphens, and case (`HRV` picks `HR-V`); several loose matches fail instead of guessing. `match: contains` replaces `exact: false`, which still works. `search_text` sets what is typed into the search box (#107).
- `kinenix validate` reports a `flow.json` or a subflow `.json` next to its `.md`; `kinenix init --update-agents` refreshes `AGENTS.md` and `CLAUDE.md` of an older project from the current template (#105).
- The `AGENTS.md` given to new projects teaches `on_error: next_item` in loops, the web actions of 0.4.0b1, cookie banners and menus, resetting a subflow's result before each call, and testing against saved pages.

### Also

- `kinenix init --example` also copies `.env.example`, input files, saved test pages, and a tutorial's solution; `kinenix list` no longer lists a `solution` folder as a flow.
- CI runs the offline examples end to end in Chromium, with their outputs checked.

## 0.4.0b1 (2026-10-23)

Web actions: modern pages (cards instead of tables, custom dropdowns, paged tables, single-page apps) in one step each.

**A parent flow now continues on the page its subflow left** (a page the subflow went to, switched to, or opened). Before, it kept its own page. Set `propagate_sessions: false` on the `flow.call` to keep the old behavior. **Add `> Requires: kinenix>=0.4.0b1` to a flow that uses `on_error: next_item`** (`kinenix validate` says when): Kinenix 0.3.0b1 and older stop the flow at that step.

### Web

- `web.goto` goes to a URL in the current tab, and opens a browser when none is open (#58).
- `web.choose` picks an option by name in custom dropdowns (Radix and shadcn Select, cmdk combobox, Headless UI, MUI) or a native `<select>`, optionally typing into its search box. A missing option fails with the list of options that are there (#57).
- `web.get_list` reads repeated elements such as cards into rows, with `fields` (text, `@attribute`, or the element itself), `numeric_fields`, `required_fields`, `add_columns`, and `min_rows` (#55).
- `web.get_table` and `web.get_list` read every page of a paged table or list with `next_selector`; more pages than `max_pages` fails instead of leaving pages out.
- A browser a subflow opened is closed at the end of the run; a subflow with `propagate_sessions: false` uses its own browser, which is closed when it ends.
- A failed web step says in one line what went wrong and how to fix it, instead of only Playwright's call log: what covered the element (named as a cookie banner, popup, or menu when it looks like one), a selector that never appeared or matches several elements, a hidden or disabled element, a site that could not be reached. A failed subflow passes its step's cause up to the caller. No AI is involved; unknown messages keep the general wording (#111).

### Flows

- `on_error: next_item` for steps inside a `logic.loop`: the failure is recorded, the rest of the item is skipped, and the loop goes on with its next item. The item counts as failed (#102).
- A value with a leading zero, such as `0012`, stays text. `kinenix validate` reports a `{...}` or `[...]` value that is not valid JSON, which would be read as text (#103).
- A run that succeeds no longer carries `failure_details` from a failure handled by `on_error: continue` (#102).

### Hub

- A run that finished, but with failed work items or failures it went on after, is **partial** instead of success: an amber "สำเร็จบางส่วน · 1 จาก 2 รายการไม่สำเร็จ" on the dashboard, with a filter, and `partial` in `hub status`, `logs`, `report`, and `hub query`. Runs already stored are updated when the Hub starts (#110).
- The steps view and `kinenix hub logs` show a failed step's cause, how to fix it, and the work item it failed on; the full message is one click away.
- The startup banner shows the dashboard's LAN address when other machines may log in; `http://127.0.0.1:8080` opened over ssh is the viewer's own machine.

### Also

- `kinenix list` names a flow by its folder also when run inside it (it showed `.`), and no longer lists the old flat flows from `kinenix-core/examples`, which were removed (#108).
- `PWD` and `OLDPWD` are no longer hidden as secrets, so paths in logs stay readable on Linux and macOS (#101).
- Every action declares what it can do outside the run (`email`, `files`, `web`, `network`); `kinenix actions` shows it.
- CI runs the browser tests in Chromium on Linux and Windows.

## 0.3.0b1 (2026-10-16)

Expressions: count, join, clean, pick, and calculate values inside `${...}`, safely. Design: [docs/design/expressions.md](docs/design/expressions.md).

**Add `> Requires: kinenix>=0.3.0b1` to a flow that uses expressions or `and` / `or` / `not`** (`kinenix validate` says when). Kinenix 0.2.0b4 and older turn `${len(rows)}` into empty text and read `and` as part of a value, without an error. Upgrade every worker first.

### Flows

- Functions in `${...}`: `len`, `join`, `number`, `trim`, `lower`, `upper`, `replace`, `default`, `round`, `part`, `substring`; `+ - * / %` on numbers; indexing such as `${rows[0].id}` and `${row['Unit Price (THB)']}` (#56).
- Conditions join comparisons with `and`, `or`, and `not`; a value such as `Johnson and Johnson` is not split.
- Nothing written in a flow can run code: expressions are parsed and checked against a fixed list, without `eval`. `${x.__class__}`, which read Python internals before, now gives empty.
- A variable that exists is read as before, so keys such as `First Name` or `Role in Company` keep working. A missing key written with clear expression syntax (a function call, brackets, quotes, or `+ * / % < > = !`) now reports an error instead of giving empty.
- `kinenix validate` reports expression errors and unknown functions with their line.

### Also

- When a run cannot reach the Hub, the log says why in plain words (name not found, Hub not running, firewall), as `kinenix connect` does.
- The copyright owner is named in every LICENSE and NOTICE file.
- www.kinenix.com is rebuilt when the documentation on `main` changes.

## 0.2.0b4 (2026-10-16)

Phase 2: subflows, error handling, and run records that people and AI can query.

**Upgrade every worker before you deploy a flow that uses `## On Error` or `## Finally`.** Kinenix 0.2.0b3 and older read the steps under those headings as ordinary steps, so an older worker would, for example, send the error e-mail on every successful run. Add `> Requires: kinenix>=0.2.0b4` under a flow's title; 0.2.0b4 and newer refuse a flow that needs a newer version. Upgrading: [docs/releasing.md, section 3](docs/releasing.md#3-upgrading-an-installation).

### Flows

- `## On Error` and `## Finally` sections, `${error}` (message, step, path, subflow, line, loop item, retries, root cause, screenshot), and `${run}` (id, flow, started, status, log path) (#50, #51).
- `max_retries` always retries first; `on_error: continue` then records the failure and goes on; `max_retries`, `retry_interval`, and `config.error_dir` accept `${...}` (#52).
- `logic.loop` takes `item_label`, which names each item in logs and on the Hub and counts work items.
- Subflows are written as `.md`, share the bundle's config and folder (`@shared/` subflows keep their own unless `inherit_config: true`), and `kinenix validate` follows them (#49, #60).
- `> Requires: kinenix>=VERSION` under a flow's title.

### Run records

- One record per run: every step, including subflow steps, with its line, path, subflow, loop item, retries, and for failures how they were handled (`stopped`, `continued`, `fallback`). Subflows no longer write their own logs or send their own runs (#62).
- A live log (`.jsonl`) written while the flow runs, available as `${run.log_path}`; one screenshot per failure (#54).
- Secrets and personal data are redacted on the worker before logs, `${error}`, and the Hub.

### Hub

- Tables `step_results` and `failures`, `executions.details` with a Markdown run report, views `v_runs`, `v_failures`, and `v_steps`, and a data dictionary ([docs/hub_data.md](docs/hub_data.md)). An existing `hub.db` is upgraded in place, and its runs get their records at the first start.
- `kinenix hub query` (read-only questions, on the Hub machine or with `--url`), user views from `~/.kinenix/hub_views/`, `kinenix hub report --flow NAME`, and `kinenix hub logs --flow NAME`.
- `kinenix connect URL` saves the Hub a machine reports to, after checking the key; `kinenix hub setup` offers it for runs on the Hub machine.
- Failure summaries name a Business error as a business rule that was not met, and report an unrecognized error as unknown instead of guessing.

### Also

- License changed to Apache-2.0.
- The repository is now `arttopix/kinenix`.
