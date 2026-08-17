# Data Dictionary

**Source files:** `data/source/Financial_Sample.xlsx` (original), `data/raw/FinancialSample_raw.csv` (flattened)
**Rows:** 700 · **Columns:** 16
**Grain:** one row per Segment × Country × Product × Discount Band × Month

## Fields

| # | Field | Type | Description |
|---|---|---|---|
| 1 | `Segment` | Text | Customer segment. 5 values: Government, Small Business, Enterprise, Midmarket, Channel Partners. |
| 2 | `Country` | Text | Country of sale. 5 values: United States of America, Canada, France, Germany, Mexico. |
| 3 | `Product` | Text | Product sold. 6 values: Carretera, Montana, Paseo, Velo, VTT, Amarilla. |
| 4 | `Discount Band` | Text | Discount tier applied: None, Low, Medium, High. **Blank in 53 rows** — see Data quality below. |
| 5 | `Units Sold` | Decimal | Quantity sold. Fractional values occur (e.g. 1618.5) — the source treats units as a continuous measure, not an integer count. |
| 6 | `Manufacturing Price` | Currency | Unit cost to manufacture. |
| 7 | `Sale Price` | Currency | List price per unit before discount. |
| 8 | `Gross Sales` | Currency | `Units Sold × Sale Price`. Revenue before discount. |
| 9 | `Discounts` | Currency | Total discount value granted on the row. |
| 10 | `Sales` | Currency | `Gross Sales − Discounts`. **Net** revenue. Note the leading space in the Excel header (`" Sales"`) — trimmed during load. |
| 11 | `COGS` | Currency | Cost of goods sold. |
| 12 | `Profit` | Currency | `Sales − COGS`. Gross profit. |
| 13 | `Date` | Date | First day of the month the sale falls in. Range 2013-09-01 → 2014-12-01. |
| 14 | `Month Number` | Whole number | 1–12. Used for chronological sorting of `Month Name`. |
| 15 | `Month Name` | Text | Full month name. |
| 16 | `Year` | Whole number | 2013 or 2014. |

## Derived relationships

```
Gross Sales = Units Sold × Sale Price
Sales       = Gross Sales − Discounts
Profit      = Sales − COGS
```

Both identities hold on every row in this dataset; they were verified before modelling
rather than assumed. Any future extract should be re-checked, because a break in these
identities silently corrupts every downstream margin measure.

## Data quality notes

**1. Blank `Discount Band` (53 rows).**
Every blank row has `Discounts = 0`, so the blank means "no discount applied" rather than
"unknown". Replaced with the literal `"None"` during load. Leaving it blank would drop
these rows out of any discount-band visual and quietly understate the zero-discount margin
— which happens to be the highest margin group in the dataset, so the distortion would run
in the worst possible direction.

**2. Date format differs between the two source files.**
The `.xlsx` stores `Date` as a true Excel date serial; the `.csv` stores it as an
ISO-8601 string (`2014-01-01`). If you swap sources, re-check the column type in Power
Query — Power BI will sometimes infer text and break the date hierarchy.

**3. `2013` is a partial year.**
Only September–December 2013 are present, against all 12 months of 2014. Raw
year-over-year comparisons are therefore invalid. All growth figures in this project use a
like-for-like September–December window, and the report carries a visible note to stop
readers drawing the wrong conclusion.

**4. Fractional `Units Sold`.**
Do not cast to integer. Rounding changes `Gross Sales` and breaks the identities above.

**5. Header whitespace.**
The Excel `Sales` column header has a leading space. Trimmed on load; worth knowing if you
query the workbook directly.

**6. No nulls elsewhere.**
All other 15 columns are complete across all 700 rows.

## Scope limitations

- Gross-margin only. There is no operating expense, headcount or overhead data, so this is
  not a full P&L and the "Profit" figures are gross, not net.
- No budget or forecast column — variance analysis (actual vs plan) is out of scope until a
  plan table is added.
- No customer, order or salesperson identifiers, so no cohort or rep-level analysis.
