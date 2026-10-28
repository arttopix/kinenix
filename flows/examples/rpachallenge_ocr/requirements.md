# RPA Challenge OCR Invoice Extractor

The requirements of this example, written the way you fill in `requirements.md` in a new project (`kinenix init`). `flow.md` does what they ask; compare the two to see how each section becomes steps, settings in `config/config.json`, and error handling.

## Goal

Read the key fields of an invoice image with an AI model that runs on our own machine, so the invoice never leaves it, and save them as a table row in the format of the Automation Challenge - OCR.

## Steps

1. Open https://rpachallengeocr.azurewebsites.net.
2. Download "sample invoice 1" into the project's `assets` folder.
3. Ask the local AI model (Ollama) to read the invoice and return InvoiceNo, InvoiceDate, CompanyName, and TotalDue.
4. Make one row with the challenge's ID and due date and the four fields.
5. Save the row as a CSV file with the columns ID, DueDate, InvoiceNo, InvoiceDate, CompanyName, and TotalDue.
6. Close the browser.

## Settings that must change without editing the flow

- The challenge URL
- Where the invoice image is saved
- The address of the Ollama server and the model name
- Whether the browser window is shown
- Where the CSV file is saved

## Secrets

- none (Ollama runs locally without a key)

## Personal or confidential data

- none for the sample; with real invoices, the company names and amounts stay on this machine because the model is local

## Output

`output/result.csv`, one row:

| ID | DueDate | InvoiceNo | InvoiceDate | CompanyName | TotalDue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| sample1 | 25-02-2019 | ... | ... | ... | ... |

## Errors and exceptions

- If the download link is missing, stop and keep a screenshot.
- If Ollama is not running or the model is not installed, stop and say how to start it.

## Schedule

By hand, as a demonstration of local AI extraction. It needs Ollama with the model installed on the machine that runs it.
