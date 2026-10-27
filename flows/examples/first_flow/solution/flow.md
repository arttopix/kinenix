# Office Supply Prices
> Description: Tutorial solution: read every product of the shop's catalog pages, save them to CSV, list the ones over the budget, and write a summary.
> Version: 1.0.0
> Requires: kinenix>=0.5.0b1

## Variables
- `over_budget`: []

## Steps

### 1. Remove Last Run's Over-Budget File (`file.delete`)
- **description:** over_budget.csv is written only when a product is over the budget; an old one must not pass for this month's.
- **path:** ./output/over_budget.csv
- **missing_ok:** true

### 2. Open The Catalog (`web.open`)
- **url:** ${config.catalog_url}
- **headless:** ${config.headless}

### 3. Read Every Product (`web.get_list`)
- **selector:** `article.product`
- **fields:** {"name": "h3", "category": ".category", "price": ".price"}
- **numeric_fields:** ["price"]
- **required_fields:** ["name", "price"]
- **next_selector:** `a.next`
- **timeout:** 5000
- **output_var:** `products`

### 4. Stop When The Catalog Is Empty (`flow.fail`)
- **condition:** `${len(products)} == 0`
- **message:** No products were found at ${config.catalog_url}. Check that catalog_url in config/config.json points to the catalog page.

### 5. Find Products Over Budget (`logic.loop`)
- **items:** ${products}
- **item_var:** `product`
- **item_label:** ${product.name}
- **Sub-steps:**
  - Keep If Over Budget (`logic.append`):
    - **condition:** `${product.price} > ${config.budget}`
    - **target:** `over_budget`
    - **item:** ${product}

### 6. Save All Products (`csv.write`)
- **file_path:** ./output/products.csv
- **data:** ${products}
- **columns:** ["name", "category", "price"]

### 7. Save Products Over Budget (`csv.write`)
- **condition:** `${len(over_budget)} > 0`
- **file_path:** ./output/over_budget.csv
- **data:** ${over_budget}
- **columns:** ["name", "category", "price"]

### 8. Write The Summary (`file.write_text`)
- **path:** ./output/summary.txt
- **content:** ${len(products)} products read, ${len(over_budget)} over the budget of ${config.budget} THB.

## Finally

### 1. Close The Browser (`web.close`)
- **on_error:** continue
