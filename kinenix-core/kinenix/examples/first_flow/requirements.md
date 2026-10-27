# Office Supply Prices

The task of the Kinenix tutorial (https://www.kinenix.com/tutorial/). `flow.md` is still empty: ask your AI assistant to build it from this file, then validate and run it.

## Goal

The office manager buys supplies every month from an online shop and has a budget per item. Each month she wants every product of the shop's catalog in a file, and a short list of the products that cost more than the budget, so she can look for cheaper ones before ordering.

## Steps

1. Open the shop's catalog page. While we build and test the flow, the catalog is a copy saved in this project: `tests/pages/catalog.html`.
2. Read every product on the page: its name, category, and price. The catalog has more than one page; follow "Next page" until the last page, so no product is left out.
3. Keep the price as a number, so the budget can be compared: the page shows "1,290.00 THB", the file needs 1290 without the comma and the currency.
4. If the catalog shows no products at all, stop and say so, instead of writing empty files.
5. Save all products to a CSV file.
6. Save the products that cost more than the budget to a second CSV file. If none is over the budget, do not write this file, and do not leave last month's file there either.
7. Write one line of summary: how many products were read, and how many are over the budget.
8. Close the browser at the end, also when something went wrong.

## Settings that must change without editing the flow

- The address of the catalog page (the saved copy now; the real shop later)
- The budget per item, in THB (500 for now)
- Whether the browser window is shown while the flow runs

## Secrets

- none

## Personal or confidential data

- none (the catalog is public; the shop and its products are made up)

## Output

All in `output/`:

- `products.csv`: one row per product, with the columns name, category, and price
- `over_budget.csv`: the same columns, only the products over the budget
- `summary.txt`: for example "10 products read, 5 over the budget of 500 THB."

## Errors and exceptions

- If the catalog page shows no products, stop with a message that names the page.
- If a product has no name or no price, stop and say which product, instead of saving a wrong row.
- If the page cannot be opened, stop; Kinenix keeps a screenshot of what was on screen.

## Schedule

By hand while learning. Later: on the 1st of every month, on a worker.
