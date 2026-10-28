
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="E-commerce Analytics",
    page_icon="📊",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

st.title("E-commerce Analytics Dashboard")
st.caption("Data Engineering Portfolio | Python • SQL • Analytics")

@st.cache_data
def load_data():
    customers = pd.read_csv(DATA / "customers.csv")
    products = pd.read_csv(DATA / "products.csv")
    orders = pd.read_csv(DATA / "orders.csv")

    # Keep one record per order
    orders = orders.drop_duplicates("order_id").copy()

    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )
    orders["quantity"] = pd.to_numeric(
        orders["quantity"], errors="coerce"
    )

    orders = orders.dropna(
        subset=[
            "order_id", "customer_id", "product_id",
            "order_date", "quantity", "status",
        ]
    )
    orders = orders[orders["quantity"] > 0]

    df = orders.merge(
        customers, on="customer_id", how="inner"
    )
    df = df.merge(
        products, on="product_id", how="inner"
    )

    df["revenue"] = df["quantity"] * df["price"]
    return df, customers, products

try:
    df, customers, products = load_data()
except Exception as exc:
    st.error(f"Could not load project data: {exc}")
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

dates = df["order_date"].dt.date
min_date = dates.min()
max_date = dates.max()

date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

statuses = sorted(df["status"].dropna().unique())
selected_statuses = st.sidebar.multiselect(
    "Order status",
    options=statuses,
    default=statuses,
)

filtered = df[df["status"].isin(selected_statuses)].copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["order_date"].dt.date.between(start_date, end_date)
    ]

# Cancelled orders are excluded from sales KPIs
sales = filtered[filtered["status"] != "cancelled"].copy()

total_revenue = sales["revenue"].sum()
total_orders = sales["order_id"].nunique()
units_sold = sales["quantity"].sum()
average_order_value = (
    total_revenue / total_orders if total_orders else 0
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Sales Revenue", f"₹{total_revenue:,.0f}")
c2.metric("Non-cancelled Orders", f"{total_orders:,}")
c3.metric("Units Sold", f"{units_sold:,.0f}")
c4.metric("Average Order Value", f"₹{average_order_value:,.0f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Revenue by Product")
    product_sales = (
        sales.groupby("product_name", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    fig = px.bar(
        product_sales,
        x="product_name",
        y="revenue",
        labels={
            "product_name": "Product",
            "revenue": "Revenue (₹)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Daily Revenue")
    daily = (
        sales.groupby(sales["order_date"].dt.date)["revenue"]
        .sum()
        .reset_index()
    )
    daily.columns = ["date", "revenue"]
    fig = px.line(
        daily,
        x="date",
        y="revenue",
        markers=True,
        labels={"date": "Date", "revenue": "Revenue (₹)"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Order Status Breakdown")
status_counts = (
    filtered.groupby("status", as_index=False)["order_id"]
    .nunique()
    .rename(columns={"order_id": "orders"})
)
fig = px.pie(
    status_counts,
    names="status",
    values="orders",
    hole=0.4,
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Order Details")
display_columns = [
    "order_id", "order_date", "name", "city",
    "product_name", "quantity", "status", "revenue",
]
st.dataframe(
    filtered[display_columns].sort_values(
        "order_date", ascending=False
    ),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Demo dataset for portfolio purposes. "
    "Revenue is calculated from quantity × listed product price."
)
