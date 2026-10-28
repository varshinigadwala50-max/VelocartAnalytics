"""
VeloCart — Customer View UI
---------------------------
Search, product detail trends, and "Less Priority / Overstock Clearance"
bargain section.

Run:
    streamlit run customer_app.py
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import load_orders, load_products_summary
from metrics import SalesMetrics

# ---------- Blueberry + Cream Soda ----------
BLUEBERRY = "#1e1b4b"
BLUEBERRY_MID = "#4338ca"
BLUEBERRY_LIGHT = "#6366f1"
CREAM = "#fef3c7"
CREAM_GOLD = "#fcd34d"
INK = "#e0e7ff"

st.set_page_config(
    page_title="VeloCart Shopper",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background: linear-gradient(160deg, {BLUEBERRY} 0%, #312e81 55%, {BLUEBERRY} 100%); color: {CREAM}; }}
      [data-testid="stSidebar"] {{ background: {BLUEBERRY}; border-right: 1px solid {BLUEBERRY_MID}; }}
      h1, h2, h3 {{ color: {CREAM} !important; }}
      .stMetric [data-testid="stMetricValue"] {{ color: {CREAM_GOLD} !important; }}
      .bargain-card {{
        background: rgba(49, 46, 129, 0.85);
        border: 1px solid {CREAM_GOLD};
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 0.75rem;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_all(path: str):
    orders = load_orders(path)
    metrics = SalesMetrics(orders)
    products = load_products_summary(orders)
    priority = metrics.product_priority()
    return orders, metrics, products, priority


def main() -> None:
    st.sidebar.title("🛍️ VeloCart Customer")
    st.sidebar.caption("Browse · Trends · Clearance bargains")

    csv_path = os.path.join(os.path.dirname(__file__), "data", "sample_orders.csv")
    try:
        orders, metrics, products, priority = load_all(csv_path)
    except Exception as e:
        st.error(f"Could not load catalog: {e}")
        return

    # ---------- Search ----------
    st.title("Product Explorer")
    q = st.sidebar.text_input("Search products", placeholder="e.g. earbuds, yoga…")
    cat_options = ["All"] + sorted(products["Category"].dropna().unique().tolist()) if not products.empty else ["All"]
    cat = st.sidebar.selectbox("Category", cat_options)

    filtered = products.copy()
    if q:
        mask = (
            filtered["Product_Name"].str.contains(q, case=False, na=False)
            | filtered["Product_ID"].str.contains(q, case=False, na=False)
        )
        filtered = filtered[mask]
    if cat != "All":
        filtered = filtered[filtered["Category"] == cat]

    st.subheader("Catalog")
    st.dataframe(
        filtered.rename(columns={"Units_Sold": "Sold", "Revenue": "Sales $"}),
        use_container_width=True,
        hide_index=True,
    )

    # ---------- Product detail ----------
    st.subheader("Product detail & trend")
    names = filtered["Product_Name"].tolist() if not filtered.empty else []
    if names:
        pick = st.selectbox("Select a product", names)
        row = filtered[filtered["Product_Name"] == pick].iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Units sold", int(row["Units_Sold"]))
        c2.metric("Sales revenue", f"${row['Revenue']:,.2f}")
        c3.metric("Orders", int(row["Orders"]) if "Orders" in row else "—")

        # Mini trend from orders
        pid = row["Product_ID"]
        hist = orders[
            (orders["Product_ID"] == pid) & (orders["Status"] != "cancelled")
        ].copy()
        if not hist.empty:
            daily = (
                hist.groupby(hist["Order_Date"].dt.date)["Quantity"]
                .sum()
                .reset_index()
                .rename(columns={"Order_Date": "Date", "Quantity": "Units"})
            )
            fig = px.bar(
                daily,
                x="Date",
                y="Units",
                color_discrete_sequence=[CREAM_GOLD],
                title=f"Sales velocity — {pick}",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(30,27,75,0.4)",
                font_color=CREAM,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No completed sales history for this product.")
    else:
        st.warning("No products match your search.")

    st.markdown("---")

    # ---------- Clearance / low priority ----------
    st.subheader("Less Priority / Overstock Clearance")
    st.caption("Slow movers — great place to grab a bargain or request a discount from the company.")

    low = priority["low"]
    if low.empty:
        st.info("No low-priority products right now.")
    else:
        for _, p in low.iterrows():
            st.markdown(
                f"""
                <div class="bargain-card">
                  <strong style="color:{CREAM_GOLD}">{p['Product_Name']}</strong>
                  <span style="color:{INK}"> · {p['Category']}</span><br/>
                  <span style="color:{CREAM}">Sold: {int(p['Units_Sold'])} units · Revenue: ${p['Revenue']:,.2f}</span><br/>
                  <span style="color:{BLUEBERRY_LIGHT}">Priority: {p.get('Priority', 'Low / Clearance')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Request discount — {p['Product_ID']}", key=f"disc_{p['Product_ID']}"):
                st.success(
                    f"Discount request noted for **{p['Product_Name']}**. "
                    "A company representative will follow up (demo)."
                )

    st.sidebar.markdown("---")
    st.sidebar.caption("Theme: Blueberry + Cream Soda")


if __name__ == "__main__":
    main()
