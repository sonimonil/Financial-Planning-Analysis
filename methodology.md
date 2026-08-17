# Methodology

## Pipeline

```
Financial_Sample.xlsx  ──▶  Power Query (M)  ──▶  Star schema  ──▶  DAX measures  ──▶  Report
     (source)                (clean & shape)      (model)          (_Measures)       (4 pages)
```

## 1. Transformation (Power Query)

Applied steps, in order:

1. **Promote headers** and set explicit column types. Explicit beats inferred — a silent
   type change on refresh is one of the most common ways a Power BI report breaks.
2. **Trim column names.** The source `" Sales"` header carries a leading space.
3. **Replace blank `Discount Band` with `"None"`.** Justified in
   [`data-dictionary.md`](data-dictionary.md#data-quality-notes) — the blanks are genuine
   zero-discount rows, not missing data.
4. **Remove redundant columns.** `Month Number`, `Month Name` and `Year` are all derivable
   from `Date` and belong in the date dimension, not the fact table. Keeping them creates
   two competing sources of truth for "which month is this".
5. **Verify arithmetic identities** (`Gross Sales − Discounts = Sales`,
   `Sales − COGS = Profit`) before loading. Checked, not assumed.

## 2. Model design

A flat 700-row table would technically work. It was still split into a star schema, because
a single flat table makes time intelligence unreliable (no contiguous date axis), forces
every slicer to scan the fact table, and leaves no clean place to hang a future budget table.

```
                    ┌──────────────┐
                    │     Date     │
                    │  (marked as  │
                    │  date table) │
                    └───────┬──────┘
                            │ 1
                            │
                            ▼ *
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│   Segment    │1──*│   financials  │*──1│   Product    │
└──────────────┘    │    (fact)     │    └──────────────┘
                    └───────┬───────┘
                            │ *
                   ┌────────┴────────┐
                   ▼ 1               ▼ 1
            ┌──────────────┐  ┌──────────────┐
            │   Country    │  │Discount Band │
            └──────────────┘  └──────────────┘
```

- All relationships **one-to-many, single direction** (dimension → fact). Bidirectional
  filtering is avoided; it introduces ambiguity that surfaces later as measures that
  return different numbers in different visuals.
- Dimension tables generated with `DISTINCT()` over the source columns.
- `_Measures` is a disconnected table holding measures only.

### Date table

```dax
Date =
VAR MinDate = MIN ( financials[Date] )
VAR MaxDate = MAX ( financials[Date] )
RETURN
ADDCOLUMNS (
    CALENDAR ( DATE ( YEAR ( MinDate ), 1, 1 ), DATE ( YEAR ( MaxDate ), 12, 31 ) ),
    "Year",         YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Month Name",   FORMAT ( [Date], "mmmm" ),
    "Month Short",  FORMAT ( [Date], "mmm" ),
    "Quarter",      "Q" & QUARTER ( [Date] ),
    "Year-Month",   FORMAT ( [Date], "yyyy-mm" )
)
```

Two settings that are easy to skip and cause visible bugs:

- **Mark as date table** (Table tools → Mark as date table → `Date`). Without it,
  `SAMEPERIODLASTYEAR` and `TOTALYTD` return wrong results rather than errors.
- **Sort `Month Name` by `Month Number`.** Otherwise every month axis sorts alphabetically
  — April, August, December.

The calendar is built to full year boundaries, not to the data range, so YTD calculations
have complete years to work against.

## 3. Report pages

| Page | Purpose | Key visuals |
|---|---|---|
| **1 · Executive Summary** | One screen, five seconds | KPI cards (Net Sales, Profit, Margin %, Discount Rate), monthly trend line, segment contribution bar |
| **2 · Profitability** | Where value is created and destroyed | Margin % by segment, COGS ratio by segment, profit waterfall (Gross → Discounts → COGS → Profit), scatter of sales vs margin |
| **3 · Discount Analysis** | Quantify the cost of discounting | Margin by discount band, discount rate by segment, order-count distribution across bands |
| **4 · Geography & Product** | Mix detail | Sales by country map, product matrix (sales / profit / margin), country × segment heat map |

Slicers for Year, Segment, Country and Product are synced across all pages so filter state
survives navigation.

## 4. Design decisions worth stating

**Net Sales, not Gross Sales, is the headline revenue figure.** Gross Sales is $127.9 M and
looks better. It is also money that was never collected — $9.2 M of it was discounted away.
Leading with gross would flatter the numbers and hide the discount problem that turns out
to be one of the report's main findings.

**Margin is shown alongside every revenue figure.** Revenue-only views are how a
loss-making segment like Enterprise stays invisible: it is the third-largest segment by
sales and would look healthy on any revenue chart.

**Year-over-year comparisons are labelled.** 2013 is a four-month stub. A raw YoY figure
reads as +249% growth, which is an artefact of the date range, not performance. The report
uses a like-for-like Sep–Dec window and says so on the page.

**Currency displayed in millions.** Consistent scale across all cards so magnitudes are
comparable at a glance.

## 5. Reproducing the analysis

Every figure quoted in the README and the deck comes from `scripts/profile_data.py`:

```bash
pip install pandas openpyxl
python scripts/profile_data.py
```

Independent of Power BI, so the numbers can be verified without opening the report.

## 6. Possible extensions

- Add a budget/plan table to activate the variance measures already scaffolded in
  [`dax-measures.md`](dax-measures.md#variance-scaffolding).
- Rolling 3-month forecast, once more than 16 months of history exists.
- Row-level security by `Country` for a multi-region rollout.
- Deploy via Fabric deployment pipelines (dev → test → prod), which the PBIP format
  supports directly.
