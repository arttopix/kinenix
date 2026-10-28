# Tutorial: Your First Flow

In this tutorial you build a working automation the way Kinenix is meant to be used: you describe the task in `requirements.md`, an AI assistant writes `flow.md`, and Kinenix checks and runs it. It takes about 20 minutes and needs no internet: the shop the flow reads from is a set of pages saved in the project.

The task: an office manager wants every product of a supplier's online catalog in a file, and a list of the products that cost more than her budget. You will end with three files in `output/`, and you will have seen what Kinenix tells you when the shop's page is not what the flow expects.

## What you need

- Kinenix installed, and its browser installed once: `pip install kinenix`, then `kinenix install-browsers` ([quickstart.md](quickstart.md)).
- An AI assistant that can read and write files in a folder, for example Claude Code, OpenAI Codex, GitHub Copilot, or Cursor. Most of them read `AGENTS.md`, the instructions Kinenix puts in every project, by themselves; otherwise ask the assistant to read it first.

## 1. Create the project

```bash
kinenix init my-first-flow --example first_flow
kinenix list
```

`kinenix init` creates the project in your flows folder (`kinenix flows-dir` shows where), so `kinenix run my-first-flow` works from any folder. Open the folder in your editor:

| File | What it is |
| :--- | :--- |
| `requirements.md` | The task, written for people. This is the file you would write for your own tasks |
| `AGENTS.md` | Instructions for the AI assistant: where things go, which commands to run, mistakes to avoid |
| `flow.md` | The flow. It has one placeholder step; the assistant replaces it |
| `config/config.json` | Values that change without editing the flow: the catalog address, the budget |
| `tests/pages/` | The shop's catalog pages, saved so the tutorial works offline |

Open `tests/pages/catalog.html` in your browser: ten products on two pages, with a "Next page" link.

## 2. Read the requirements

Open `requirements.md`. Each section tells the assistant something different:

| Section | What the assistant does with it |
| :--- | :--- |
| Goal | Understands why, so it can make sensible small decisions |
| Steps | Writes one or more steps of `flow.md` for each |
| Settings that must change without editing the flow | Puts the catalog address and the budget in `config/config.json` and reads them as `${config.catalog_url}` and `${config.budget}` |
| Secrets | Would put passwords in `.env`, never in the flow (there are none here) |
| Personal or confidential data | Would hide those fields in logs and on the Hub (none here) |
| Output | Writes exactly these files and columns |
| Errors and exceptions | Adds the checks that stop the flow with a clear message |
| Schedule | Tells you how to run it unattended later |

For your own tasks, `kinenix init "Task name"` creates the same sections, empty, with hints.

## 3. Ask the assistant to build the flow

Open the `my-first-flow` folder in your AI assistant and ask:

> Build the flow described in requirements.md. Follow AGENTS.md. When `kinenix validate` and `kinenix run` both pass, tell me what you checked.

A good assistant will:

- read `requirements.md` and `AGENTS.md`;
- run `kinenix actions web` to see the exact parameters of the web actions, instead of guessing;
- open `tests/pages/catalog.html` to choose the selectors (`article.product`, `h3`, `.price`, and the `a.next` link);
- write `flow.md` and update `config/config.json`;
- run `kinenix validate .` and `kinenix run .`, and fix what they report.

If your assistant cannot run commands, run them yourself (steps 4 and 5) and paste the output back to it.

## 4. Validate

```bash
kinenix validate my-first-flow
```

`OK` means every step uses a known action, every parameter is one the action accepts, and every expression is valid. Otherwise each warning names the line and what to change, for example:

```text
Warning: Step 'step_2' (Read Every Product): web.get_list does not use parameter 'field'; it would be ignored. Did you mean 'fields'?
```

Give the warnings to the assistant, or fix them yourself; `validate` catches most mistakes before anything runs.

## 5. Run

```bash
kinenix run my-first-flow
```

A browser window opens (set `"headless": true` in `config/config.json` to hide it), the flow reads both catalog pages, and the run ends with a summary in the terminal. Look in `my-first-flow/output/`:

- `products.csv`: ten products with their name, category, and price as a number
- `over_budget.csv`: the five products above 500 THB
- `summary.txt`: `10 products read, 5 over the budget of 500 THB.`

Every run also writes a log, with each step, its result, and how long it took ([logging.md](logging.md)), under `logs/<flow name>/<date>/` of the git repository you run the command in (your flows folder when it is one), otherwise of the current folder; `kinenix run --log-dir PATH` puts it elsewhere. The run's last lines in the terminal show the path.

## 6. Break it on purpose

Real pages change. The project has a second settings file that points the flow at an empty catalog page:

```bash
kinenix run my-first-flow --config config/empty.json
```

`--config` replaces the settings of `config/config.json` that the file names, for this run only ([cli_guide.md](cli_guide.md)). If your flow follows the requirements, it stops with a message that says what is wrong and what to check, and `kinenix run` exits with code 3, so a scheduler or a CI job knows the run stopped on a problem with the data (a technical failure, such as a page that cannot be opened, is 1; all codes: [cli_guide.md, Exit Codes](cli_guide.md#28-exit-codes)). Kinenix also saved a screenshot of the page in `output/errors/`.

Try two more changes and read what Kinenix reports:

- In `tests/pages/catalog-2.html`, delete the price of one product. If the flow requires a price for every product (`required_fields`), the run stops and says which product has none.
- In `flow.md`, change the selector of the price to one the page does not have, for example `.cost`. The run stops at the first product and names the field, its selector, and what the product reads, so you know which selector to fix.

Put the pages back as they were afterwards (or copy them again with `kinenix init` into a new folder).

## 7. Compare with the solution

The solution is not in your project, so the assistant could not copy it: [solution/flow.md](https://github.com/arttopix/kinenix/blob/main/flows/examples/first_flow/solution/flow.md) in the Kinenix repository. Your assistant's flow does not need to be the same; check that it does the same things:

- reads both pages (`web.get_list` with `next_selector: a.next`);
- keeps the price as a number (`numeric_fields`);
- stops on an empty catalog with a message (`flow.fail` with a condition);
- finds the products over the budget in a loop with a condition, and writes the second file only when there are any, after removing last month's (`file.delete` with `missing_ok`);
- closes the browser in `## Finally`, so it is closed also after a failure.

To run the solution itself, save it over your `flow.md` and run again.

## 8. Next steps

- **Your own task:** `kinenix init "Get stock data"` creates a project with an empty `requirements.md`. Fill it in, then repeat steps 3 to 6.
- **A real website:** once the flow works on saved pages, point `catalog_url` at the real site. To try with a site made for practice, ask your assistant to adapt the flow to https://books.toscrape.com/ (it needs internet, and the selectors differ: each book is an `article.product_pod`).
- **Test before every change:** keep the saved pages and a `config/test.json`, and run with `--config` before you deploy a change ([project_bundles.md, Testing Against Saved Pages](project_bundles.md#4-testing-against-saved-pages)).
- **Run it unattended and see it on the Hub:** connect the machine to a Hub with `kinenix connect` and schedule the flow on a worker ([quickstart.md](quickstart.md), [hub.md](hub.md)).
