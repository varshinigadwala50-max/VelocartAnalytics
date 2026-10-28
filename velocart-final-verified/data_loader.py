"""
VeloCart — Data Ingestion Layer
--------------------------------
Accepts a company CSV (or in-memory DataFrame), cleans missing values,
and standardizes columns: Order_Date, Revenue, Product_ID, etc.

Usage:
    from data_loader import load_orders
    df = load_orders("data/sample_orders.csv")
"""

from __future__ import annotations

import os
from typing import Optional, Union

import pandas as pd
import numpy as np

# Canonical column names expected by the analytics engine
STANDARD_COLUMNS = {
    "order_id": "Order_ID",
    "orderdate": "Order_Date",
    "order_date": "Order_Date",
    "date": "Order_Date",
    "product_id": "Product_ID",
    "productid": "Product_ID",
    "sku": "Product_ID",
    "product_name": "Product_Name",
    "product": "Product_Name",
    "category": "Category",
    "qty": "Quantity",
    "quantity": "Quantity",
    "unit_price": "Unit_Price",
    "price": "Unit_Price",
    "revenue": "Revenue",
    "amount": "Revenue",
    "total": "Revenue",
    "customer_id": "Customer_ID",
    "customerid": "Customer_ID",
    "customer_name": "Customer_Name",
    "customer": "Customer_Name",
    "region": "Region",
    "country": "Region",
    "status": "Status",
}

REQUIRED = ["Order_Date", "Revenue", "Product_ID"]


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Map arbitrary headers to standard names."""
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        if key in STANDARD_COLUMNS:
            rename[col] = STANDARD_COLUMNS[key]
    return df.rename(columns=rename)


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    if "Order_Date" in df.columns:
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    if "Revenue" in df.columns:
        df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")
    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0).astype(int)
    if "Unit_Price" in df.columns:
        df["Unit_Price"] = pd.to_numeric(df["Unit_Price"], errors="coerce")
    if "Status" in df.columns:
        df["Status"] = df["Status"].astype(str).str.strip().str.lower()
    return df


def _fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Clean missing values with safe defaults."""
    if "Status" in df.columns:
        df["Status"] = df["Status"].fillna("completed")
    if "Region" in df.columns:
        df["Region"] = df["Region"].fillna("Unknown")
    if "Category" in df.columns:
        df["Category"] = df["Category"].fillna("Uncategorized")
    if "Product_Name" in df.columns:
        df["Product_Name"] = df["Product_Name"].fillna(df.get("Product_ID", "Unknown"))
    if "Customer_Name" in df.columns:
        df["Customer_Name"] = df["Customer_Name"].fillna("Guest")
    # Drop rows with no date or revenue
    df = df.dropna(subset=[c for c in REQUIRED if c in df.columns])
    return df.reset_index(drop=True)


def load_orders(
    source: Union[str, pd.DataFrame] = "data/sample_orders.csv",
    base_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load and clean order data from CSV path or DataFrame.

    Parameters
    ----------
    source : str or DataFrame
        Path to CSV relative to project root, or a pandas DataFrame.
    base_dir : str, optional
        Project root. Defaults to this file's parent directory.
    """
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        root = base_dir or os.path.dirname(os.path.abspath(__file__))
        path = source if os.path.isabs(source) else os.path.join(root, source)
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV not found: {path}")
        df = pd.read_csv(path)

    df = _normalize_headers(df)
    df = _coerce_types(df)
    df = _fill_missing(df)

    # Derive Revenue if missing but qty * price exist
    if "Revenue" not in df.columns and {"Quantity", "Unit_Price"}.issubset(df.columns):
        df["Revenue"] = df["Quantity"] * df["Unit_Price"]

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"After cleaning, required columns still missing: {missing}")

    return df


def load_products_summary(orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate product-level stats from cleaned orders."""
    completed = orders[orders.get("Status", "completed") != "cancelled"].copy()
    agg = (
        completed.groupby(["Product_ID", "Product_Name", "Category"], dropna=False)
        .agg(
            Units_Sold=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Orders=("Order_ID", "nunique") if "Order_ID" in completed.columns else ("Revenue", "count"),
        )
        .reset_index()
    )
    agg["Units_Sold"] = agg["Units_Sold"].fillna(0).astype(int)
    agg["Revenue"] = agg["Revenue"].round(2)
    return agg.sort_values("Revenue", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    # Quick self-test
    df = load_orders()
    print(f"Loaded {len(df)} orders")
    print(df.head())
    print(load_products_summary(df).head())
