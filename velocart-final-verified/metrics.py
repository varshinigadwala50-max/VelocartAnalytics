"""
VeloCart — Analytics Engine
---------------------------
Financial performance, high/low priority product sorting,
customer trends, inventory health signals.

Usage:
    from data_loader import load_orders
    from metrics import SalesMetrics
    m = SalesMetrics(load_orders())
    print(m.kpis())
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from data_loader import load_products_summary


class SalesMetrics:
    def __init__(self, orders: pd.DataFrame):
        self.orders = orders.copy()
        if "Status" not in self.orders.columns:
            self.orders["Status"] = "completed"
        self.valid = self.orders[self.orders["Status"] != "cancelled"].copy()

    # ---------- High-level KPIs ----------
    def kpis(self) -> Dict[str, Any]:
        rev = float(self.valid["Revenue"].sum())
        orders = int(self.valid["Order_ID"].nunique()) if "Order_ID" in self.valid.columns else len(self.valid)
        customers = (
            int(self.valid["Customer_ID"].nunique())
            if "Customer_ID" in self.valid.columns
            else int(self.valid["Customer_Name"].nunique())
            if "Customer_Name" in self.valid.columns
            else 0
        )
        aov = rev / orders if orders else 0.0
        cancelled = self.orders[self.orders["Status"] == "cancelled"]
        cancel_rate = len(cancelled) / len(self.orders) * 100 if len(self.orders) else 0.0
        return {
            "total_revenue": round(rev, 2),
            "order_count": orders,
            "customer_count": customers,
            "avg_order_value": round(aov, 2),
            "cancel_rate_pct": round(cancel_rate, 1),
        }

    # ---------- Product priority ----------
    def product_priority(
        self,
        high_pct: float = 0.3,
        low_pct: float = 0.3,
    ) -> Dict[str, pd.DataFrame]:
        """
        Split products into high-priority (top sellers) and low-priority
        (slow movers / overstock clearance candidates) by revenue share.
        """
        summary = load_products_summary(self.orders)
        if summary.empty:
            return {"high": summary, "low": summary, "all": summary}

        summary = summary.sort_values("Revenue", ascending=False).reset_index(drop=True)
        n = len(summary)
        high_n = max(1, int(np.ceil(n * high_pct)))
        low_n = max(1, int(np.ceil(n * low_pct)))

        high = summary.head(high_n).copy()
        high["Priority"] = "High"
        low = summary.tail(low_n).sort_values("Units_Sold", ascending=True).copy()
        low["Priority"] = "Low / Clearance"
        summary["Priority"] = "Medium"
        summary.loc[summary["Product_ID"].isin(high["Product_ID"]), "Priority"] = "High"
        summary.loc[summary["Product_ID"].isin(low["Product_ID"]), "Priority"] = "Low / Clearance"

        return {"high": high, "low": low, "all": summary}

    # ---------- Customer trends ----------
    def customer_trends(self, top_n: int = 10) -> pd.DataFrame:
        if "Customer_Name" not in self.valid.columns and "Customer_ID" not in self.valid.columns:
            return pd.DataFrame()
        key = "Customer_ID" if "Customer_ID" in self.valid.columns else "Customer_Name"
        name_col = "Customer_Name" if "Customer_Name" in self.valid.columns else key
        g = (
            self.valid.groupby([key] + ([name_col] if name_col != key else []))
            .agg(
                Orders=("Order_ID", "nunique") if "Order_ID" in self.valid.columns else ("Revenue", "count"),
                Revenue=("Revenue", "sum"),
                Last_Order=("Order_Date", "max"),
            )
            .reset_index()
            .sort_values("Revenue", ascending=False)
            .head(top_n)
        )
        g["Revenue"] = g["Revenue"].round(2)
        return g

    # ---------- Geographic sales ----------
    def sales_by_region(self) -> pd.DataFrame:
        if "Region" not in self.valid.columns:
            return pd.DataFrame({"Region": [], "Revenue": []})
        g = (
            self.valid.groupby("Region", dropna=False)["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )
        g["Revenue"] = g["Revenue"].round(2)
        return g

    # ---------- Time series ----------
    def revenue_by_day(self) -> pd.DataFrame:
        g = (
            self.valid.groupby(self.valid["Order_Date"].dt.date)["Revenue"]
            .sum()
            .reset_index()
            .rename(columns={"Order_Date": "Date"})
        )
        g["Revenue"] = g["Revenue"].round(2)
        return g

    def sales_by_category(self) -> pd.DataFrame:
        if "Category" not in self.valid.columns:
            return pd.DataFrame()
        g = (
            self.valid.groupby("Category")["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )
        g["Revenue"] = g["Revenue"].round(2)
        return g

    # ---------- Inventory health (proxy from sales velocity) ----------
    def inventory_health(self) -> pd.DataFrame:
        """
        Proxy health score from units sold:
        - Fast movers → Healthy
        - Mid → Watch
        - Slow → Overstock risk
        """
        summary = load_products_summary(self.orders)
        if summary.empty:
            return summary
        q33, q66 = summary["Units_Sold"].quantile([0.33, 0.66])
        def label(u: int) -> str:
            if u >= q66:
                return "Healthy"
            if u >= q33:
                return "Watch"
            return "Overstock risk"
        summary["Health"] = summary["Units_Sold"].apply(label)
        return summary.sort_values("Units_Sold")


if __name__ == "__main__":
    from data_loader import load_orders

    m = SalesMetrics(load_orders())
    print("KPIs:", m.kpis())
    print("\nHigh priority:\n", m.product_priority()["high"])
    print("\nLow priority:\n", m.product_priority()["low"])
