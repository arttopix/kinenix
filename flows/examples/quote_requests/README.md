# Motor Insurance Quote Requests

Enters car insurance quote requests from a CSV file, one by one, into an insurer's quote form, reads every package offered, and e-mails the packages and the list of failed requests. The insurer, Kinenix Demo Insurance, is made up: its quote page is saved in `tests/pages/quote.html`, so the example runs without internet. The page behaves like modern quote sites: custom dropdowns with a search box, a cookie banner that appears late over the form, and the packages shown as cards.

```bash
kinenix init quotes --example quote_requests
kinenix run quotes
```

It takes about a minute for the five sample requests. Set `"headless": true` in `config/config.json` to hide the browser.

## Requirements

[`requirements.md`](requirements.md) is the task this flow implements, in the sections you fill in for your own task after `kinenix init "Task name"`.

## What happens to the five sample requests

| Request | What it shows |
| :--- | :--- |
| R001, R002 | Quoted: three Class 1 packages, two Class 2+ packages |
| R003 | The model is written `HRV`; the site says `HR-V`. `web.choose` with `match: loose` picks it |
| R004 | `CX-30` is not offered: the request fails, its reason lists what the site offers (`CX-3`), and the run goes on |
| R005 | No sub-model: skipped as a business error with `on_error: next_item`, with the reason saved |

The run ends with 3 of 5 requests done; on the Hub it shows as partial success, "2 จาก 5 รายการไม่สำเร็จ".

## Output

| File | Content |
| :--- | :--- |
| `output/packages.csv` | One row per package: request, car, package name, yearly premium (a number), sum insured, repair type |
| `output/failed_requests.csv` | The failed requests and why |
| `output/screenshots/` | One screenshot per quoted request |

The e-mail is checked but not sent while `email.dry_run` is `true`. To send it, put the account in `.env` (see `.env.example`) and set `dry_run` to `false`.

## How it is built

| Part | Pattern |
| :--- | :--- |
| `flow.md` step 3 | A loop with `item_label`, so each request is counted and named in logs and on the Hub |
| Missing details | `logic.append` with a condition notes the reason; `flow.fail` with `on_error: next_item` skips the rest of the request |
| `subflows/quote_one.md` | One request per subflow call, with `on_error: continue` on the call; the result is reset before each call, because a failed call does not set it |
| Dropdowns | `web.choose` with `search: true`, `search_text` (the start of the name), and `match: loose` |
| Packages | `web.get_list` with `numeric_fields`, `required_fields`, and `add_columns` |
| Failure reasons | `${error.root_cause}`, Kinenix's one-line cause of the failure |
| Personal data | `"redact": ["customer_name"]` in `config/config.json` |
| `## On Error`, `## Finally` | A screenshot and an e-mail when the run stops; the browser always closed |

## Files

| File | Purpose |
| :--- | :--- |
| `flow.md` | The main flow |
| `subflows/quote_one.md` | Quotes one request |
| `config/config.json` | Site address, requests file, e-mail, `redact` |
| `input/requests.csv` | Five made-up requests |
| `tests/pages/quote.html` | The made-up insurer's quote page |
| `.env.example` | The e-mail secrets, for when the e-mail is really sent |
