import streamlit as st
import pandas as pd
from datetime import date
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ------------------ PAGE CONFIG (FIRST LINE) ------------------
st.set_page_config(page_title="Expense Tracker", layout="wide")

# ------------------ CUSTOM CSS ------------------
st.markdown("""
<style>
.main {
    background-color: #f4f6f9;
}

.block-container {
    padding-top: 2rem;
}

.card {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 6px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div style="
    background: linear-gradient(90deg, #4f46e5, #3b82f6);
    padding: 20px;
    border-radius: 12px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
">
    <h2>💰 Expense Tracker</h2>
    <p>Track, analyze and optimize your spending</p>
</div>
""", unsafe_allow_html=True)

# ------------------ MONGODB SETUP ------------------
load_dotenv()

client = MongoClient(st.secrets["MONGO_URI"])
db = client["finance_db"]
collection = db["expenses"]

# ------------------ LOAD DATA ------------------
def load_data():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])

    return df

df = load_data()

# ------------------ ADD INCOME ------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("💰 Add Income")

inc_col1, inc_col2 = st.columns(2)

with st.form("income_form"):
    with inc_col1:
        inc_amount = st.number_input("Income Amount (₹)", min_value=0.0, step=100.0)
        
        
    with inc_col2:
        inc_description = st.text_input("Source")
        inc_date = st.date_input("Income Date", value=date.today(), key="inc_date")

    inc_submitted = st.form_submit_button("Add Income")

if inc_submitted:
    
    collection.insert_one({
        "amount": inc_amount,
        "category": "Income", 
        "description": inc_description,
        "date": str(inc_date)
    })

    st.toast("💸 Income added successfully!")
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ------------------ ADD EXPENSE ------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("➕ Add New Expense")

col1, col2 = st.columns(2)

with st.form("expense_form"):
    with col1:
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        category = st.selectbox(
            "Category",
            ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Health", "Education", "Other"]
        )

    with col2:
        description = st.text_input("Description")
        expense_date = st.date_input("Date", value=date.today())

    submitted = st.form_submit_button("Add Expense")

if submitted:
    collection.insert_one({
        "amount": amount,
        "category": category,
        "description": description,
        "date": str(expense_date)
    })

    st.toast("💸 Expense added successfully!")
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ------------------ FILTERS ------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    selected_category = st.selectbox(
        "Category",
        ["All"] + list(df["category"].unique()) if not df.empty else ["All"]
    )

with col2:
    use_date_filter = st.checkbox("Enable Date Filter")

filtered_df = df.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]

if use_date_filter and not df.empty:
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    filtered_df = filtered_df[
        (pd.to_datetime(filtered_df["date"]) >= pd.to_datetime(start_date)) &
        (pd.to_datetime(filtered_df["date"]) <= pd.to_datetime(end_date))
    ]

st.markdown('</div>', unsafe_allow_html=True)

# ------------------ EXPENSE TABLE ------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📋 All Expenses")

if not filtered_df.empty:
    st.dataframe(
        filtered_df.sort_values(by="date", ascending=False),
        use_container_width=True
    )
else:
    st.info("No expenses found")

st.markdown('</div>', unsafe_allow_html=True)

# ------------------ INSIGHTS (Only for Expenses) ------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 📊 Expense Insights")

if not df.empty:
    expense_only_df = df[df["category"] != "Income"]
    
    if not expense_only_df.empty:
        total_expense = expense_only_df["amount"].sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💰 Total Spending", f"₹ {total_expense}")

        with col2:
            top_category = expense_only_df.groupby("category")["amount"].sum().idxmax()
            st.metric("🔥 Top Category", top_category)

        with col3:
            st.metric("📊 Expense Entries", len(expense_only_df))

        st.divider()

        st.markdown("### 📊 Category Breakdown")
        category_summary = expense_only_df.groupby("category")["amount"].sum()
        st.bar_chart(category_summary)

        # Highest expense
        highest = expense_only_df.loc[expense_only_df["amount"].idxmax()]
        st.error(
            f"⚠️ Highest expense: ₹{highest['amount']} on {highest['category']} ({highest['description']})"
        )

        st.markdown("### 📉 Weekly Spending Trend")
        weekly = expense_only_df.groupby(expense_only_df["date"].dt.to_period("W"))["amount"].sum()
        weekly.index = weekly.index.astype(str)
        st.line_chart(weekly)

        st.markdown("### 📆 Monthly Spending Trend")
        monthly = expense_only_df.groupby(expense_only_df["date"].dt.to_period("M"))["amount"].sum()
        monthly.index = monthly.index.astype(str)
        st.line_chart(monthly)
    else:
        st.info("No expense data available (Only income records found).")

else:
    st.info("Add expenses to see insights")

st.markdown('</div>', unsafe_allow_html=True)
