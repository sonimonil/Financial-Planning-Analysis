# Financial Planning & Analysis (FP&A) Dashboard

An end-to-end FP&A reporting project built in **Power BI**, covering revenue, discounting,
cost of goods sold and profitability across five market segments, five countries and six
products.

![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?style=flat&logo=powerbi&logoColor=black)
![Excel](https://img.shields.io/badge/Excel-217346?style=flat&logo=microsoftexcel&logoColor=white)
![DAX](https://img.shields.io/badge/DAX-01A6F0?style=flat)
![Format](https://img.shields.io/badge/format-PBIP-yellow?style=flat)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

---

## Overview

Finance teams rarely need more data — they need the *narrative* inside it. This project
takes a flat transactional sales extract and turns it into a decision-support model that
answers four questions a CFO actually asks:

1. **Where is the money coming from?** Revenue mix by segment, country and product.
2. **Where is it leaking?** Discount exposure and its measurable cost to margin.
3. **What are we selling at a loss?** Segment-level profitability, not just revenue.
4. **Which way is the trend pointing?** Monthly performance on a like-for-like basis.

The report is saved in **PBIP (Power BI Project)** format rather than a binary `.pbix`,
so the report definition is plain JSON — reviewable in a pull request and diffable in Git.

## Dataset at a glance

| Attribute | Value |
|---|---|
| Records | 700 |
| Fields | 16 |
| Period covered | September 2013 – December 2014 (16 months) |
| Segments | Government, Small Business, Enterprise, Midmarket, Channel Partners |
| Countries | USA, Canada, France, Germany, Mexico |
| Products | Carretera, Montana, Paseo, Velo, VTT, Amarilla |
| Discount bands | None, Low, Medium, High |
| Grain | One row per Segment × Country × Product × Discount Band × Month |

Source: Microsoft's public **Financial Sample** dataset, provided here as both the original
workbook and a flattened CSV. See [`docs/data-dictionary.md`](docs/data-dictionary.md) for
field-level definitions.

## Headline results

| KPI | Value |
|---|---|
| Gross Sales | $127.93 M |
| Discounts | $9.21 M (7.2% of gross) |
| **Net Sales** | **$118.73 M** |
| COGS | $101.83 M (85.8% of net sales) |
| **Profit** | **$16.89 M** |
| **Profit Margin** | **14.23%** |
| Units Sold | 1,125,806 |

## Key findings

**1. Government is the engine — and it is also the most profitable at scale.**
The segment delivers $52.5 M of net sales (44% of total) at a 21.7% margin. Most
businesses have to choose between volume and margin; here the largest customer group is
also the second-highest margin group.

**2. Enterprise sells below cost.**
$19.6 M of net sales producing a **loss of $0.61 M**. COGS runs at **103.1%** of net sales
against a company average of 85.8% — every Enterprise order destroys value before a single
overhead cost is applied. This is the single most actionable finding in the dataset.

**3. Discounting costs roughly 13 margin points.**
Margin falls in a straight line as discounting deepens:

| Discount Band | Orders | Discount Rate | Profit Margin |
|---|---|---|---|
| None | 53 | 0.0% | 21.9% |
| Low | 160 | 2.5% | 17.9% |
| Medium | 242 | 7.2% | 14.4% |
| High | 245 | 12.5% | 9.1% |

The *High* band alone gave away $5.32 M. It carries the most orders and the worst margin —
discounting is being used as a default, not as a lever.

**4. Growth is real, once the periods are made comparable.**
2013 only covers September–December, so a raw year-over-year comparison overstates growth.
On a like-for-like **Sep–Dec** basis: net sales **+36.9%**, profit **+40.1%**.

**5. Revenue is lumpy and back-loaded.**
October 2014 ($12.38 M) and December 2014 ($12.00 M) alone account for 21% of all revenue,
while November 2014 collapses to $5.38 M. Quarter-end concentration of this severity
usually signals discount-driven pull-forward rather than underlying demand.

**6. Channel Partners is an under-exploited channel.**
73.1% margin — by far the highest — on just $1.8 M of sales (1.5% of revenue). Small
absolute numbers, but the best unit economics in the business.

## Recommendations

- **Reprice or exit Enterprise.** A 103% COGS ratio is a pricing failure, not a volume
  problem. Model a price floor at COGS + 12% before renewing contracts.
- **Cap the High discount band.** Moving even a third of High-band orders to Medium is
  worth an estimated $1.5–1.8 M in recovered profit at constant volume.
- **Fund Channel Partners growth.** Highest margin, smallest base — the clearest
  risk-adjusted place to invest incremental spend.
- **Investigate month-end spikes.** Confirm whether Oct/Dec volume is demand or
  pull-forward before building it into next year's forecast.

## Repository structure

```
finance-fpa-dashboard/
├── data/
│   ├── raw/       FinancialSample_raw.csv    Flattened extract, 700 rows
│   └── source/    Financial_Sample.xlsx      Original workbook
├── powerbi/
│   ├── Finance_FPA_Dashboard.pbip            Project pointer file
│   └── Finance FPA Dashboard.Report/         Report definition (JSON)
├── docs/
│   ├── data-dictionary.md                    Field definitions & data quality notes
│   ├── dax-measures.md                       Every measure, with commentary
│   ├── methodology.md                        Model design & modelling decisions
│   └── images/                               Dashboard screenshots
├── presentation/
│   └── Finance_FPA_Dashboard.pptx            Stakeholder deck
├── scripts/
│   └── profile_data.py                       Reproduces the KPIs above from the CSV
├── .gitattributes
├── .gitignore
└── LICENSE
```

## Getting started

**Open the report**

1. Install [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (June 2024 or later —
   earlier builds cannot open PBIP projects).
2. Enable the project format: *File → Options and settings → Options → Preview features →
   **Power BI Project (.pbip) save option***, then restart.
3. Open `powerbi/Finance_FPA_Dashboard.pbip`.

**Repoint the data source**

The model references an absolute local path. After cloning, update it:

*Transform data → Data source settings → Change Source* → select
`data/source/Financial_Sample.xlsx` from your clone, then **Refresh**.

**Verify the numbers**

```bash
pip install pandas openpyxl
python scripts/profile_data.py
```

Prints the KPI table, segment/country/product breakdowns and discount-band analysis above,
so any figure in this README can be checked against the source data.

## Tech stack

| Layer | Tool |
|---|---|
| Data source | Excel (`.xlsx`), CSV |
| Transformation | Power Query (M) |
| Modelling | Star schema, DAX |
| Visualisation | Power BI Desktop |
| Version control | PBIP format + Git |
| Validation | Python (pandas) |

## License

Released under the [MIT License](LICENSE). The underlying Financial Sample dataset is
published by Microsoft as sample data for learning and demonstration purposes.
