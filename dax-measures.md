# DAX Measures

All measures live in a dedicated `_Measures` table so they group together in the field list
instead of scattering across the fact table.

## Core aggregations

```dax
Gross Sales = SUM ( financials[Gross Sales] )

Total Discounts = SUM ( financials[Discounts] )

Net Sales = SUM ( financials[Sales] )

Total COGS = SUM ( financials[COGS] )

Total Profit = SUM ( financials[Profit] )

Units Sold = SUM ( financials[Units Sold] )

Order Count = COUNTROWS ( financials )
```

## Ratios

`DIVIDE` is used throughout rather than the `/` operator — it returns blank on a zero
denominator instead of an error, which matters the moment a slicer produces an empty
selection.

```dax
Profit Margin % =
DIVIDE ( [Total Profit], [Net Sales] )

Gross Margin % =
DIVIDE ( [Net Sales] - [Total COGS], [Net Sales] )

Discount Rate % =
DIVIDE ( [Total Discounts], [Gross Sales] )

COGS Ratio % =
DIVIDE ( [Total COGS], [Net Sales] )

Avg Sale Price =
DIVIDE ( [Net Sales], [Units Sold] )

Profit per Unit =
DIVIDE ( [Total Profit], [Units Sold] )
```

`COGS Ratio %` is the measure that exposed the Enterprise problem: it sits at 103.1% for
that segment against 85.8% company-wide.

## Time intelligence

These require a marked date table. See `methodology.md` for the `Date` table definition.

```dax
Net Sales PY =
CALCULATE ( [Net Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )

Net Sales YoY % =
VAR Current = [Net Sales]
VAR Prior   = [Net Sales PY]
RETURN
    IF ( NOT ISBLANK ( Prior ), DIVIDE ( Current - Prior, Prior ) )

Net Sales YTD =
TOTALYTD ( [Net Sales], 'Date'[Date] )

Profit YTD =
TOTALYTD ( [Total Profit], 'Date'[Date] )

Net Sales MoM % =
VAR Prior = CALCULATE ( [Net Sales], DATEADD ( 'Date'[Date], -1, MONTH ) )
RETURN
    DIVIDE ( [Net Sales] - Prior, Prior )

Net Sales 3M Avg =
AVERAGEX (
    DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -3, MONTH ),
    [Net Sales]
)
```

The `IF ( NOT ISBLANK ( Prior ) ... )` guard on `Net Sales YoY %` is deliberate. Without it
every month from September 2013 to August 2014 reports a meaningless growth figure computed
against a nonexistent prior period, and the line chart shows a spike that isn't real.

## Contribution and ranking

```dax
% of Total Sales =
DIVIDE (
    [Net Sales],
    CALCULATE ( [Net Sales], REMOVEFILTERS () )
)

Segment Rank by Sales =
RANKX ( ALL ( financials[Segment] ), [Net Sales], , DESC, DENSE )

Running Total Sales =
CALCULATE (
    [Net Sales],
    FILTER ( ALLSELECTED ( 'Date'[Date] ), 'Date'[Date] <= MAX ( 'Date'[Date] ) )
)
```

## Variance scaffolding

There is no budget table in this dataset. These measures are included so a plan can be
dropped in without reworking the model — point them at a `Budget` table with a `Budget
Sales` column and they work immediately.

```dax
Budget Variance =
[Net Sales] - SUM ( Budget[Budget Sales] )

Budget Variance % =
DIVIDE ( [Budget Variance], SUM ( Budget[Budget Sales] ) )

Budget Attainment % =
DIVIDE ( [Net Sales], SUM ( Budget[Budget Sales] ) )
```

## Conditional formatting helper

Drives the KPI card colour so a negative-margin segment is visible without reading the
number:

```dax
Margin Status Colour =
SWITCH (
    TRUE (),
    [Profit Margin %] < 0,    "#C0392B",
    [Profit Margin %] < 0.10, "#E8A33D",
    "#00A896"
)
```

## Formatting applied

| Measure type | Format |
|---|---|
| Currency measures | `$#,0.0,,"M"` — thousands separator, millions suffix |
| Percentage measures | `0.0%` |
| Counts | `#,0` |

Displaying currency in millions is not cosmetic. At $118.7 M, a card showing the full digit
string is genuinely harder to read at a glance, and executives comparing two cards will
misread magnitude before they misread a suffix.
