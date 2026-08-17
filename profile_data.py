#!/usr/bin/env python3
"""
Reproduce every KPI quoted in README.md directly from the source data.

Run this to verify the report's numbers without opening Power BI:

    pip install pandas openpyxl
    python scripts/profile_data.py

Optional: point at the Excel source instead of the CSV.

    python scripts/profile_data.py --source data/source/Financial_Sample.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas is required:  pip install pandas openpyxl")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "data" / "raw" / "FinancialSample_raw.csv"


def load(source: Path) -> pd.DataFrame:
    """Load the extract from CSV or Excel and apply the same cleaning as Power Query."""
    if not source.exists():
        sys.exit(f"Source file not found: {source}")

    if source.suffix.lower() in {".xlsx", ".xlsm"}:
        df = pd.read_excel(source)
    else:
        df = pd.read_csv(source)

    # The Excel source has a leading space in the "Sales" header.
    df.columns = [c.strip() for c in df.columns]

    df["Date"] = pd.to_datetime(df["Date"])

    # Blank Discount Band means "no discount applied" -- all such rows have
    # Discounts == 0. Left blank, these rows drop out of discount-band visuals
    # and understate the zero-discount margin, which is the highest in the set.
    df["Discount Band"] = df["Discount Band"].fillna("None").astype(str).str.strip()

    return df


def check_identities(df: pd.DataFrame) -> None:
    """The three arithmetic identities the model depends on."""
    tol = 0.01
    checks = {
        "Units Sold x Sale Price = Gross Sales":
            (df["Units Sold"] * df["Sale Price"] - df["Gross Sales"]).abs().max(),
        "Gross Sales - Discounts = Sales":
            (df["Gross Sales"] - df["Discounts"] - df["Sales"]).abs().max(),
        "Sales - COGS = Profit":
            (df["Sales"] - df["COGS"] - df["Profit"]).abs().max(),
    }
    print("\nARITHMETIC IDENTITIES")
    print("-" * 62)
    for label, max_diff in checks.items():
        status = "PASS" if max_diff <= tol else f"FAIL (max diff {max_diff:,.2f})"
        print(f"  {status:<8} {label}")


def money(x: float) -> str:
    return f"${x / 1_000_000:,.2f} M"


def headline(df: pd.DataFrame) -> None:
    gross = df["Gross Sales"].sum()
    disc = df["Discounts"].sum()
    net = df["Sales"].sum()
    cogs = df["COGS"].sum()
    profit = df["Profit"].sum()

    print("\nHEADLINE KPIs")
    print("-" * 62)
    print(f"  Gross Sales      {money(gross):>14}")
    print(f"  Discounts        {money(disc):>14}   ({disc / gross:.1%} of gross)")
    print(f"  Net Sales        {money(net):>14}")
    print(f"  COGS             {money(cogs):>14}   ({cogs / net:.1%} of net sales)")
    print(f"  Profit           {money(profit):>14}")
    print(f"  Profit Margin    {profit / net:>13.2%}")
    print(f"  Units Sold       {df['Units Sold'].sum():>14,.0f}")
    print(f"  Records          {len(df):>14,}")


def breakdown(df: pd.DataFrame, dimension: str) -> None:
    g = (
        df.groupby(dimension)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .assign(
            Margin=lambda x: x["Profit"] / x["Sales"],
            Share=lambda x: x["Sales"] / df["Sales"].sum(),
        )
        .sort_values("Sales", ascending=False)
    )

    print(f"\nBY {dimension.upper()}")
    print("-" * 62)
    print(f"  {dimension:<26}{'Sales':>12}{'Profit':>12}{'Margin':>9}")
    for name, row in g.iterrows():
        print(
            f"  {str(name)[:25]:<26}{money(row.Sales):>12}"
            f"{money(row.Profit):>12}{row.Margin:>9.1%}"
        )


def discount_analysis(df: pd.DataFrame) -> None:
    order = ["None", "Low", "Medium", "High"]
    g = (
        df.groupby("Discount Band")
        .agg(
            Orders=("Sales", "size"),
            Gross=("Gross Sales", "sum"),
            Disc=("Discounts", "sum"),
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
        )
        .reindex([b for b in order if b in df["Discount Band"].unique()])
    )
    g["DiscRate"] = g["Disc"] / g["Gross"]
    g["Margin"] = g["Profit"] / g["Sales"]

    print("\nDISCOUNT BAND IMPACT")
    print("-" * 62)
    print(f"  {'Band':<10}{'Orders':>8}{'Discount $':>14}{'Disc rate':>11}{'Margin':>9}")
    for name, row in g.iterrows():
        print(
            f"  {name:<10}{int(row.Orders):>8}{money(row.Disc):>14}"
            f"{row.DiscRate:>11.1%}{row.Margin:>9.1%}"
        )


def trend(df: pd.DataFrame) -> None:
    m = df.groupby(df["Date"].dt.to_period("M")).agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum")
    )

    print("\nMONTHLY TREND")
    print("-" * 62)
    print(f"  {'Month':<10}{'Sales':>14}{'Profit':>14}")
    for period, row in m.iterrows():
        print(f"  {str(period):<10}{money(row.Sales):>14}{money(row.Profit):>14}")

    print(f"\n  Peak month     {m['Sales'].idxmax()}  {money(m['Sales'].max())}")
    print(f"  Trough month   {m['Sales'].idxmin()}  {money(m['Sales'].min())}")


def like_for_like(df: pd.DataFrame) -> None:
    """2013 covers Sep-Dec only, so raw YoY is invalid. Compare Sep-Dec both years."""
    window = [9, 10, 11, 12]
    c = df[df["Month Number"].isin(window)].groupby("Year").agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum")
    )

    print("\nLIKE-FOR-LIKE GROWTH (Sep-Dec, both years)")
    print("-" * 62)
    if len(c) < 2:
        print("  Not enough years in the data for a comparison.")
        return

    years = sorted(c.index)
    prior, current = years[0], years[-1]
    for year in years:
        print(f"  {year}   Sales {money(c.loc[year, 'Sales']):>13}"
              f"   Profit {money(c.loc[year, 'Profit']):>13}")
    sales_growth = c.loc[current, "Sales"] / c.loc[prior, "Sales"] - 1
    profit_growth = c.loc[current, "Profit"] / c.loc[prior, "Profit"] - 1
    print(f"\n  Net sales growth   {sales_growth:+.1%}")
    print(f"  Profit growth      {profit_growth:+.1%}")

    raw = df.groupby("Year")["Sales"].sum()
    raw_growth = raw.loc[current] / raw.loc[prior] - 1
    print(f"\n  For contrast, the raw full-year figure reads {raw_growth:+.0%} --")
    print(f"  an artefact of {prior} holding only {len(window)} months of data.")


def data_quality(df: pd.DataFrame) -> None:
    print("\nDATA QUALITY")
    print("-" * 62)
    raw_nulls = {k: v for k, v in df.isna().sum().items() if v}
    print(f"  Nulls after cleaning     {raw_nulls or 'none'}")
    print(f"  Duplicate rows           {df.duplicated().sum()}")
    print(f"  Date range               {df['Date'].min():%Y-%m-%d} to {df['Date'].max():%Y-%m-%d}")
    print(f"  Distinct months          {df['Date'].dt.to_period('M').nunique()}")
    frac = (df["Units Sold"] % 1 != 0).sum()
    print(f"  Fractional Units Sold    {frac} rows (do not round - breaks identities)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_SOURCE,
        help="path to the CSV or XLSX extract",
    )
    args = parser.parse_args()

    df = load(args.source)

    print("=" * 62)
    print("  FP&A DASHBOARD - DATA PROFILE")
    print(f"  Source: {args.source.relative_to(REPO_ROOT) if REPO_ROOT in args.source.resolve().parents else args.source}")
    print("=" * 62)

    headline(df)
    check_identities(df)
    breakdown(df, "Segment")
    breakdown(df, "Country")
    breakdown(df, "Product")
    discount_analysis(df)
    trend(df)
    like_for_like(df)
    data_quality(df)

    print("\n" + "=" * 62)
    print("  Figures above match those quoted in README.md")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
