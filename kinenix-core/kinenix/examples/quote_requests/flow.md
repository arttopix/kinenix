# Motor Insurance Quote Requests
> Description: Enter each quote request from a CSV file into the insurer's quote form, collect the offered packages, list the requests that failed and why, and e-mail both files.
> Version: 1.0.0
> Requires: kinenix>=0.5.0b1

## Variables
- `packages`: []
- `failed`: []

## Steps

### 1. Read The Requests (`csv.read`)
- **file_path:** ${config.input_csv}
- **clean_headers:** true
- **output_var:** `requests`

### 2. Stop When There Are No Requests (`flow.fail`)
- **condition:** `${len(requests)} == 0`
- **message:** ${config.input_csv} has no requests.

### 3. Quote Each Request (`logic.loop`)
- **items:** ${requests}
- **item_var:** `req`
- **item_label:** ${req.request_id} ${req.brand} ${req.model}
- **Sub-steps:**
  - Note Missing Car Details (`logic.append`):
    - **condition:** `${req.brand} is empty or ${req.model} is empty or ${req.sub_model} is empty`
    - **target:** `failed`
    - **item:** {"request_id": "${req.request_id}", "reason": "brand, model, and sub_model are required"}
  - Skip A Request With Missing Car Details (`flow.fail`):
    - **condition:** `${req.brand} is empty or ${req.model} is empty or ${req.sub_model} is empty`
    - **message:** ${req.request_id}: brand, model, and sub_model are required.
    - **on_error:** next_item
  - Reset The Result (`logic.set_variable`):
    - **description:** A failed subflow call does not set quote_result; without this, the previous request's result would be used.
    - **name:** quote_result
    - **value:** {"status": "failed", "packages": []}
  - Quote One Request (`flow.call`):
    - **flow:** ./subflows/quote_one.md
    - **inputs:** {"req": "${req}", "website_url": "${config.website_url}", "headless": "${config.headless}"}
    - **output_var:** `quote_result`
    - **on_error:** continue
  - Keep The Packages (`logic.append`):
    - **condition:** `${quote_result.status} == ok`
    - **target:** `packages`
    - **item:** ${quote_result.packages}
    - **extend:** true
  - Note The Failure (`logic.append`):
    - **condition:** `${quote_result.status} != ok`
    - **target:** `failed`
    - **item:** {"request_id": "${req.request_id}", "reason": "${default(error.root_cause, error.message)}"}

### 4. Save The Packages (`csv.write`)
- **condition:** `${len(packages)} > 0`
- **file_path:** ./output/packages.csv
- **data:** ${packages}
- **columns:** ["request_id", "insurance_class", "year", "brand", "model", "sub_model", "package_name", "premium_thb_per_year", "sum_insured", "repair_type"]

### 5. Save The Failed Requests (`csv.write`)
- **condition:** `${len(failed)} > 0`
- **file_path:** ./output/failed_requests.csv
- **data:** ${failed}
- **columns:** ["request_id", "reason"]

### 6. Send The Results (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject} (${len(requests)} requests, ${len(failed)} failed)
- **body:** |
    Quotes for ${len(requests)} requests: ${len(packages)} packages found, ${len(failed)} requests failed.
    The packages and the failed requests with their reasons are attached.
- **attachments:** ["./output/packages.csv", "./output/failed_requests.csv"]
- **dry_run:** ${config.email.dry_run}
- **max_retries:** 2
- **retry_interval:** 10

## On Error

### 1. Capture The Screen (`web.screenshot`)
- **path:** ./output/errors/run_failure.png
- **on_error:** continue

### 2. Tell The Team (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject} stopped at ${error.step_name}
- **body:** The quote run stopped: ${error.message}
- **dry_run:** ${config.email.dry_run}
- **on_error:** continue

## Finally

### 1. Close The Browser (`web.close`)
- **on_error:** continue
