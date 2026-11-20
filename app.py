
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import time
import os

st.set_page_config(
    page_title="Database Sharding Simulator",
    page_icon="🗄️",
    layout="wide"
)

st.title("🗄️ Distributed Database Sharding Simulator")
st.caption("Customer Data Distribution and Intelligent Query Routing")

DB_FOLDER = "database"

# Load original dataset
@st.cache_data
def load_data():
    return pd.read_csv("customers_sample_300.csv")

df = load_data()

# Automatically create database files
# if they do not exist

@st.cache_resource
def initialize_databases():

    os.makedirs("database", exist_ok=True)

    # Create single database
    conn = sqlite3.connect(
        "database/single_database.db"
    )

    df.to_sql(
        "customers",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    # Create three shards
    for shard_no in range(1, 4):

        shard_df = df[
            df["customer_id"] % 3 == shard_no - 1
        ]

        conn = sqlite3.connect(
            f"database/shard_{shard_no}.db"
        )

        shard_df.to_sql(
            "customers",
            conn,
            if_exists="replace",
            index=False
        )

        conn.close()

    return True


initialize_databases()


# Read shard data
def get_shard_data(shard_no):

    conn = sqlite3.connect(
        f"{DB_FOLDER}/shard_{shard_no}.db"
    )

    data = pd.read_sql_query(
        "SELECT * FROM customers",
        conn
    )

    conn.close()

    return data


# Query routing
def route_query(customer_id):

    shard_no = (int(customer_id) % 3) + 1

    conn = sqlite3.connect(
        f"{DB_FOLDER}/shard_{shard_no}.db"
    )

    start = time.perf_counter()

    result = pd.read_sql_query(
        "SELECT * FROM customers WHERE customer_id = ?",
        conn,
        params=(int(customer_id),)
    )

    execution_time = (
        time.perf_counter() - start
    ) * 1000

    conn.close()

    return result, shard_no, execution_time


# Sidebar navigation
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Section",
    [
        "Dashboard",
        "Shard Explorer",
        "Query Router",
        "Performance Analysis"
    ]
)


# Dashboard
if page == "Dashboard":

    st.header("Project Dashboard")

    counts = [
        len(get_shard_data(i))
        for i in range(1, 4)
    ]

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Customers", len(df))
    c2.metric("Total Shards", 3)
    c3.metric("Records per Shard", 100)

    st.subheader("Customer Distribution")

    distribution = pd.DataFrame({
        "Shard": ["Shard 1", "Shard 2", "Shard 3"],
        "Records": counts
    })

    fig = px.pie(
        distribution,
        names="Shard",
        values="Records",
        title="Records Stored in Each Shard"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Customer Dataset")
    st.dataframe(df, use_container_width=True)


# Shard Explorer
elif page == "Shard Explorer":

    st.header("Shard Explorer")

    selected_shard = st.selectbox(
        "Choose a Shard",
        [1, 2, 3]
    )

    shard_data = get_shard_data(selected_shard)

    st.metric("Total Records", len(shard_data))

    st.dataframe(
        shard_data,
        use_container_width=True
    )


# Query Router
elif page == "Query Router":

    st.header("Intelligent Query Routing")

    customer_id = st.number_input(
        "Enter Customer ID",
        min_value=1001,
        max_value=1300,
        step=1
    )

    if st.button("Search Customer"):

        result, shard, execution_time = route_query(
            customer_id
        )

        st.success(
            f"Query automatically routed to Shard {shard}"
        )

        st.metric(
            "Execution Time",
            f"{execution_time:.4f} ms"
        )

        if not result.empty:
            st.subheader("Customer Details")
            st.dataframe(result, use_container_width=True)
        else:
            st.warning("Customer not found!")


# Performance Analysis
elif page == "Performance Analysis":

    st.header("Performance Comparison")

    customer_id = st.number_input(
        "Enter Customer ID for comparison",
        min_value=1001,
        max_value=1300,
        value=1001,
        step=1
    )

    if st.button("Compare Performance"):

        # Single database query
        conn = sqlite3.connect(
            f"{DB_FOLDER}/single_database.db"
        )

        start = time.perf_counter()

        single_result = pd.read_sql_query(
            "SELECT * FROM customers WHERE customer_id = ?",
            conn,
            params=(customer_id,)
        )

        single_time = (
            time.perf_counter() - start
        ) * 1000

        conn.close()

        # Sharded database query
        shard_result, shard, shard_time = route_query(
            customer_id
        )

        performance_df = pd.DataFrame({
            "Database": [
                "Single Database",
                "Sharded Database"
            ],
            "Execution Time (ms)": [
                single_time,
                shard_time
            ]
        })

        st.write("Performance Results")
        st.dataframe(performance_df)

        fig = px.bar(
            performance_df,
            x="Database",
            y="Execution Time (ms)",
            title="Query Execution Time Comparison"
        )

        st.plotly_chart(fig, use_container_width=True)


st.sidebar.markdown("---")
st.sidebar.caption("Distributed Computing Mini Project")
