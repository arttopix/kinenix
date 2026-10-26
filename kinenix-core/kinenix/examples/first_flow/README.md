# Your First Flow: Office Supply Prices

The starting point of the Kinenix tutorial: https://www.kinenix.com/tutorial/ (in the repository: `docs/tutorial.md`).

This project is not finished on purpose. [`requirements.md`](requirements.md) describes the task in full; `flow.md` is empty. You ask your AI assistant to build `flow.md` from the requirements, then validate it, run it, and break it on purpose to see how Kinenix reports a problem. Everything runs on your machine without internet: the shop's catalog is saved in `tests/pages/`.

```bash
kinenix init my-first-flow --example first_flow
```

## Files

| File | Purpose |
| :--- | :--- |
| `requirements.md` | The task: goal, steps, settings, output, and what to do when something goes wrong |
| `AGENTS.md`, `CLAUDE.md` | Instructions your AI assistant reads before it writes `flow.md` |
| `flow.md` | Empty at the start; your assistant writes it |
| `config/config.json` | The catalog address, the budget, and whether the browser window is shown |
| `config/empty.json` | Settings for the "break it on purpose" step: an empty catalog |
| `tests/pages/` | The made-up shop's catalog: two pages of products and an empty page |
| `solution/flow.md` | One possible solution; open it after you have tried |

To run the solution: copy `solution/flow.md` over `flow.md`, then `kinenix run my-first-flow`.
