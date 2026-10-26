# Quote One Request
> Description: Fill the insurer's quote form for one request and return the offered packages. The main flow calls it once per request; a failure here fails only that request.
> Version: 1.0.0
> Requires: kinenix>=0.5.0b1

## Variables
- `req`: {}
- `website_url`: ""
- `headless`: true

## Steps

### 1. Start A Fresh Quote Form (`web.goto`)
- **url:** ${website_url}
- **headless:** ${headless}
- **max_retries:** 2
- **retry_interval:** 3

### 2. Accept Cookies When Shown (`web.click`)
- **description:** The banner appears a moment after the page loads and covers the form.
- **selector:** `#accept-cookies`
- **optional:** true
- **timeout:** 5000

### 3. Choose Insurance Class (`web.click`)
- **selector:** `[data-testid=class-option]:text-is('${req.insurance_class}')`
- **timeout:** 10000

### 4. Choose Registration Year (`web.choose`)
- **selector:** `[data-testid=year] > button`
- **option:** ${req.year}

### 5. Choose Brand (`web.choose`)
- **selector:** `[data-testid=brand] > button`
- **option:** ${req.brand}
- **search:** true
- **match:** loose

### 6. Choose Model (`web.choose`)
- **description:** People write models differently (HRV for HR-V); match loose ignores spaces, hyphens, and case. The site's search filters by what is typed, so type only the start of the name.
- **selector:** `[data-testid=model] > button`
- **option:** ${req.model}
- **search:** true
- **search_text:** ${substring(req.model, 0, 2)}
- **match:** loose

### 7. Choose Sub-Model (`web.choose`)
- **selector:** `[data-testid=submodel] > button`
- **option:** ${req.sub_model}
- **search:** true
- **match:** loose

### 8. Choose Repair Type For Class 1 (`web.click`)
- **condition:** `${req.insurance_class} == Class 1`
- **selector:** `[data-testid=repair] input[value='${default(req.repair, 'Garage')}']`

### 9. Get The Quote (`web.click`)
- **selector:** `[data-testid=get-quote]`

### 10. Read The Offered Packages (`web.get_list`)
- **selector:** `article.package-card`
- **fields:** {"package_name": "h3", "premium_thb_per_year": ".premium", "sum_insured": ".sum-insured", "repair_type": ".repair-type"}
- **numeric_fields:** ["premium_thb_per_year"]
- **required_fields:** ["package_name", "premium_thb_per_year"]
- **add_columns:** {"request_id": "${req.request_id}", "insurance_class": "${req.insurance_class}", "year": "${req.year}", "brand": "${req.brand}", "model": "${req.model}", "sub_model": "${req.sub_model}"}
- **min_rows:** 1
- **timeout:** 10000
- **output_var:** `packages`

### 11. Save Evidence (`web.screenshot`)
- **path:** ./output/screenshots/${req.request_id}.png
- **full_page:** true
- **on_error:** continue

### 12. Return The Packages (`flow.return`)
- **value:** {"status": "ok", "packages": "${packages}"}
