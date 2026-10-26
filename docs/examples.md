# Examples

Complete flow projects that ship with Kinenix. Each one has the `requirements.md` it implements, in the sections `kinenix init` gives you for your own task, so you can see how a description in plain language becomes `flow.md`, settings, and error handling. Copy one with:

```bash
kinenix init --list                       # the examples, and which need a browser
kinenix init my-copy --example hello      # copy one into your flows folder
kinenix run my-copy
```

The examples that run offline use pages saved in their folder (`tests/pages/`) and made-up data, so they work without internet, on any machine, and in CI, which runs them end to end on every change.

| Example | What it does | Offline | Patterns it shows |
| :--- | :--- | :--- | :--- |
| `hello` | Builds a greeting per name from `config.json` and writes a CSV; the quickest installation check | Yes, no browser | A loop, a subflow per item with `flow.call`, `flow.fail` on empty input, `csv.write` |
| `first_flow` | The [tutorial](tutorial.md): finished requirements and an empty `flow.md` for your AI assistant to build; reads a made-up shop's catalog and lists the products over a budget | Yes | Requirements to a flow with an assistant; `web.get_list` over two pages (`next_selector`), `numeric_fields`, a condition in a loop, `## Finally`; reading a failure on purpose |
| `quote_requests` | Enters car insurance quote requests from a CSV into a made-up insurer's form, reads the packages offered, and e-mails the packages and the failed requests with their reasons | Yes | A subflow per request; `web.goto`, `web.choose` with search and `match: loose`, `web.get_list`; `on_error: next_item` and `continue` in a loop; `${error.root_cause}`; `redact`; On Error and Finally; partial success on the Hub |
| `bot_fx_rate` | Bank of Thailand transfer rates for chosen currencies over the previous month, to CSV, e-mailed | No (bot.or.th) | `date.calc`, date pickers, `web.get_table` with `numeric_columns` and `add_columns`, retries, e-mail |
| `rpachallenge` | Fills the RPA Challenge form ten times from an Excel file while its fields move | No (rpachallenge.com) | `excel.read`, `web.type` by label, `logic.if` in a loop, an optional e-mail through a shared subflow |
| `rpachallenge_ocr` | Reads an invoice image with a local AI model (Ollama) into a CSV row | No, and needs Ollama (repository only) | `web.download`, `ai.extract` with a schema |

`rpachallenge_ocr` is in the repository (`flows/examples/`) but not in the package, because it needs a local AI model.

## Reading an example

1. Start with `requirements.md`: the goal, the steps, which values are settings, the secrets, the output, and what to do when something fails.
2. Open `flow.md` next to it. Each requirement step becomes one or more steps; the settings are `${config...}`; the errors section becomes `max_retries`, `on_error`, `flow.fail`, and `## On Error`.
3. Run it, open `output/`, and read the run's log under `logs/`. With a Hub connected, the run appears on the dashboard.
4. Change `config/config.json` and run again; then change the flow.
