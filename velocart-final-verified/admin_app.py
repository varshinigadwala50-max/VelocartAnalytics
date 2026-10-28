"""
VeloCart — Admin View UI (Business Manager / Founder)
------------------------------------------------------
High-level sales KPIs, geographical sales, inventory health.

Run:
    streamlit run admin_app.py
"""

from __future__ import annotations

import os

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

from data_loader import load_orders
from metrics import SalesMetrics

# ---------- Blueberry + Cream Soda palette ----------
BLUEBERRY = "#1e1b4b"
BLUEBERRY_MID = "#4338ca"
BLUEBERRY_LIGHT = "#6366f1"
CREAM = "#fef3c7"
CREAM_GOLD = "#fcd34d"
INK = "#e0e7ff"

st.set_page_config(
    page_title="VeloCart Admin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background: linear-gradient(160deg, {BLUEBERRY} 0%, #312e81 50%, {BLUEBERRY} 100%); color: {CREAM}; }}
      [data-testid="stSidebar"] {{ background: {BLUEBERRY}; border-right: 1px solid {BLUEBERRY_MID}; }}
      h1, h2, h3, h4 {{ color: {CREAM} !important; }}
      .stMetric label {{ color: {INK} !important; }}
      .stMetric [data-testid="stMetricValue"] {{ color: {CREAM_GOLD} !important; }}
      div[data-testid="stFileUploader"] {{ border: 1px dashed {BLUEBERRY_LIGHT}; border-radius: 12px; padding: 0.5rem; }}
      .block-container {{ padding-top: 1.5rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data(upload_bytes: bytes | None, default_path: str) -> pd.DataFrame:
    if upload_bytes:
        return load_orders(pd.read_csv(pd.io.common.BytesIO(upload_bytes)))
    return load_orders(default_path)


def main() -> None:
    st.sidebar.title("⚡ VeloCart Admin")
    st.sidebar.caption("Business Manager · Sales velocity")
    st.sidebar.markdown("---")

    default_csv = os.path.join(os.path.dirname(__file__), "data", "sample_orders.csv")
    uploaded = st.sidebar.file_uploader("Upload company orders CSV", type=["csv"])
    upload_bytes = uploaded.getvalue() if uploaded else None

    try:
        orders = get_data(upload_bytes, default_csv)
    except Exception as e:
        st.error(f"Data load failed: {e}")
        return

    metrics = SalesMetrics(orders)
    kpis = metrics.kpis()
    priority = metrics.product_priority()
    regions = metrics.sales_by_region()
    by_day = metrics.revenue_by_day()
    by_cat = metrics.sales_by_category()
    health = metrics.inventory_health()
    customers = metrics.customer_trends()

    st.title("Admin Analytics")
    st.caption("High-level sales KPIs · Geography · Inventory health")

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue", f"${kpis['total_revenue']:,.0f}")
    c2.metric("Orders", f"{kpis['order_count']:,}")
    c3.metric("Customers", f"{kpis['customer_count']:,}")
    c4.metric("Avg Order Value", f"${kpis['avg_order_value']:,.2f}")
    c5.metric("Cancel Rate", f"{kpis['cancel_rate_pct']}%")

    st.markdown("---")

    left, right = st.columns(2)
    with left:
        st.subheader("Revenue over time")
        if not by_day.empty:
            fig = px.line(
                by_day,
                x="Date",
                y="Revenue",
                markers=True,
                color_discrete_sequence=[CREAM_GOLD],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(30,27,75,0.4)",
                font_color=CREAM,
                margin=dict(l=20, r=20, t=30, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No time-series data")

    with right:
        st.subheader("Sales by category")
        if not by_cat.empty:
            fig = px.pie(
                by_cat,
                names="Category",
                values="Revenue",
                color_discrete_sequence=[CREAM_GOLD, BLUEBERRY_LIGHT, "#818cf8", "#c7d2fe", "#fde68a"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color=CREAM,
                margin=dict(l=20, r=20, t=30, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Matplotlib chart: a second plotting library used for category revenue analysis.
    st.subheader("Category revenue (Matplotlib)")
    if not by_cat.empty:
        mpl_fig, mpl_ax = plt.subplots(figsize=(9, 4))
        mpl_ax.bar(by_cat["Category"].astype(str), by_cat["Revenue"], color=BLUEBERRY_LIGHT)
        mpl_ax.set_title("Revenue by Product Category")
        mpl_ax.set_xlabel("Product category")
        mpl_ax.set_ylabel("Revenue ($)")
        mpl_ax.tick_params(axis="x", rotation=25)
        mpl_ax.grid(axis="y", alpha=0.25)
        mpl_fig.tight_layout()
        st.pyplot(mpl_fig, use_container_width=True)
        plt.close(mpl_fig)
    else:
        st.info("No category revenue data available for the Matplotlib chart.")

    st.subheader("Geographical sales")
    if not regions.empty:
        fig = px.bar(
            regions,
            x="Region",
            y="Revenue",
            color="Revenue",
            color_continuous_scale=["#312e81", BLUEBERRY_LIGHT, CREAM_GOLD],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,27,75,0.4)",
            font_color=CREAM,
            showlegend=False,
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("High-priority products")
        st.dataframe(priority["high"], use_container_width=True, hide_index=True)
    with col_b:
        st.subheader("Low-priority / clearance candidates")
        st.dataframe(priority["low"], use_container_width=True, hide_index=True)

    st.subheader("Inventory health")
    st.dataframe(health, use_container_width=True, hide_index=True)

    st.subheader("Top customers")
    st.dataframe(customers, use_container_width=True, hide_index=True)

    st.sidebar.markdown("---")
    st.sidebar.success(f"Loaded **{len(orders)}** order rows")
    st.sidebar.caption("Theme: Blueberry + Cream Soda")


if __name__ == "__main__":
    main()
