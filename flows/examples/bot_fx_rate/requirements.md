# BOT FX Transfer Rate Collector

The requirements this example was built from. `flow.md` was written from this file by an AI assistant, following `AGENTS.md` in a new project (`kinenix init`); compare the two to see how each section became steps, settings, and error handling.

## Goal

Every month, the finance team needs the Bank of Thailand's buying transfer rates for the currencies we trade, for the whole of the previous month, in one file grouped by currency, sent to them by e-mail.

## Steps

1. Open https://www.bot.or.th/en/statistics/exchange-rate.html.
2. In "Historical Foreign Exchange Rates", select the currencies USD, GBP, SGD, JPY, and EUR.
3. Choose the period: from the first to the last day of the report month. (The first version of this request named 01-12-2024 to 31-12-2024; the month must now be a setting, the previous month by default.)
4. Search, then read the result table of each currency: the date and the Buying Rates Transfer.
5. Write all rates to one file, grouped by currency in the order of the currency list, with the columns Currency, Date, and Buying Transfer Rate. The rate must be a number, not text.
6. Save a screenshot of the result page as evidence.
7. E-mail the file to the recipient list.

## Settings that must change without editing the flow

- The page URL
- The list of currencies and their order
- The report month (default: the previous month; also a fixed month such as December 2024)
- Where the file and the screenshots are saved
- The e-mail recipients, subject, and message
- Whether the e-mail is really sent (to test without sending)
- Whether the browser window is shown

## Secrets

- The Gmail account and its app password used to send the e-mail

## Personal or confidential data

- none (exchange rates are public)

## Output

`output/Exchage_Rate.csv`, one row per currency and day:

| Currency | Date | Buying Transfer Rate |
| :--- | :--- | :--- |
| USD | 30 Dec 2024 | 33.8296 |

CSV instead of Excel, because Excel is not installed on the machine that runs it; the file opens in Excel or Google Sheets.

## Errors and exceptions

- If the site is slow or does not answer, retry twice, 5 seconds apart, then stop.
- If a cookie banner appears, accept it; if it does not, go on.
- If a currency is not offered by the site, stop and say which one.
- If a table is empty, or the site renamed a column, stop and show the columns the site has, instead of writing an empty or wrong file.
- If the file is open in another program, retry, then stop.
- If the e-mail cannot be sent, retry twice, 10 seconds apart.
- On any failure, keep a screenshot of the page, and report the failed step to the Hub.

## Schedule

On the 1st of every month at 08:00, on the worker, so the report covers the month that just ended.
