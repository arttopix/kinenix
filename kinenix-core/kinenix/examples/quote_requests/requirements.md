# Motor Insurance Quote Requests

The requirements of this example, written the way you fill in `requirements.md` in a new project (`kinenix init`). `flow.md` and `subflows/quote_one.md` do what they ask; compare them to see how each section becomes steps, settings in `config/config.json`, and error handling. The insurer is made up; its quote page is saved in `tests/pages/quote.html`.

## Goal

The sales team receives car insurance quote requests from customers every day. For each request, they need every package the insurer offers and its yearly premium, to send the customer a comparison. Typing the requests into the insurer's quote form by hand takes most of a morning; the flow should do it and tell the team which requests could not be quoted and why.

## Steps

1. Read the requests from `input/requests.csv`: request id, customer name, insurance class, registration year, brand, model, sub-model, and repair type (garage or dealer, for Class 1 only).
2. For each request:
   1. If the brand, model, or sub-model is missing, note the request as failed with the reason, and go on with the next request.
   2. Open a fresh quote form on the insurer's site.
   3. Accept the cookie banner if it appears.
   4. Choose the insurance class, then the registration year, brand, model, and sub-model in the dropdowns. Customers write model names in different ways (HRV for HR-V): accept those.
   5. For Class 1, choose the repair type.
   6. Get the quote and read every package offered: its name, yearly premium (as a number), sum insured, and repair type.
   7. Keep a screenshot of the result as evidence.
   8. If anything on the site fails for this request, note it as failed with the reason, and go on with the next request.
3. Save all packages to one file, and the failed requests with their reasons to another.
4. E-mail both files to the sales team, with the number of requests and failures in the subject.

## Settings that must change without editing the flow

- The address of the insurer's quote page (the saved copy now; the real site later)
- The requests file
- The e-mail recipients and subject, and whether the e-mail is really sent (to test without sending)
- Whether the browser window is shown

## Secrets

- The e-mail account and its app password used to send the results

## Personal or confidential data

- The customer's name must not appear in logs or on the Hub. It is not typed into the insurer's form either.

## Output

In `output/`:

- `packages.csv`: one row per package, with the request id, class, year, brand, model, sub-model, package name, yearly premium, sum insured, and repair type
- `failed_requests.csv`: the request id and the reason, one row per failed request
- `screenshots/`: one screenshot per quoted request

## Errors and exceptions

- A request without brand, model, or sub-model is a business error: skip it, with the reason, and go on.
- A model or option the site does not offer: fail that request, say which options the site has, and go on.
- The site slow to open: try again twice, then fail that request.
- The requests file missing or empty: stop the run and say so.
- If the whole run stops, keep a screenshot and e-mail the team where it stopped.
- Close the browser at the end, also after a failure.

## Schedule

Every weekday at 09:00 on a worker, reporting to the Hub, where a run with some failed requests shows as partial success.
