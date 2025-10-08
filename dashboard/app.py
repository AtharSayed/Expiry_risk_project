# app.py
import sys
import os

# --- Add project root to Python path so 'src' can be imported ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import joblib
import plotly.express as px

from src import forecasting, risk_scoring
from src.recommendations.recommend import run_recommendation_pipeline
from src.modelling import predict_expiry_class
from src.data_preprocessing import main as data_preprocessing_main
from src.forecasting import main as forecast_main
from src.risk_scoring import main as risk_main

# --- Streamlit page configuration ---
st.set_page_config(page_title="Inventory Insights Dashboard", layout="wide")

# --- Enhanced Styling for Professional Look ---
# Apply custom CSS styles
st.markdown(
    """
    <style>
    .css-18e3th9 {
        padding: 2rem;
        background-color: #f9f9f9;
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .css-1d391kg {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 1rem;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-size: 16px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .stDownloadButton > button {
        background-color: #007BFF;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-size: 16px;
        cursor: pointer;
    }
    .stDownloadButton > button:hover {
        background-color: #0056b3;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Update page title and header styling
st.markdown(
    """
    <h1 style="text-align: center; color: #333333;">
        📊 Inventory Insights Dashboard
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown("""
Upload your inventory CSV to get actionable insights including expiry predictions, risk levels, and recommendations.
""")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload Inventory CSV", type=["csv"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")
    uploaded_df = pd.read_csv(uploaded_file)

    # --- Run Backend Pipeline ---
    uploaded_file_path = "data/raw/uploaded_inventory.csv"
    os.makedirs("data/raw", exist_ok=True)
    uploaded_df.to_csv(uploaded_file_path, index=False)

    # Run the pipeline silently
    data_preprocessing_main(uploaded_file_path)
    forecast_main()
    risk_main()
    run_recommendation_pipeline()

    # --- Display Results ---
    st.subheader("⚖️ Risk Levels")
    risk_df = pd.read_csv("data/external/risk_scores.csv")
    st.bar_chart(risk_df["Risk_Level"].value_counts())

    st.subheader("🎯 Recommendations")
    rec_file = "data/external/recommendations.csv"
    if os.path.exists(rec_file):
        rec_df = pd.read_csv(rec_file)
        st.dataframe(rec_df.head(10))

        # --- Download Recommendations ---
        st.download_button(
            label="Download Recommendations CSV",
            data=rec_df.to_csv(index=False).encode('utf-8'),
            file_name="recommendations.csv",
            mime="text/csv"
        )

        # --- Additional Insights ---
        st.subheader("📊 Insights from Recommendations")

        # Filterable plot: Top 10 highest demand products
        st.subheader("Top 10 Products with Highest Stock Quantity")
        top_demand_products = rec_df.groupby("Product_Name")["Stock_Quantity"].sum().nlargest(10).reset_index()
        st.bar_chart(top_demand_products.set_index("Product_Name"))

        # Additional analysis: Action distribution by risk level
        st.subheader("Action Distribution by Risk Level")
        action_risk_distribution = rec_df.groupby(["Risk_Level", "Predicted_Action"]).size().unstack(fill_value=0)
        st.dataframe(action_risk_distribution)

        # Additional analysis: Average discount by product category
        if "Predicted_Discount_Percent" in rec_df.columns and "Category" in rec_df.columns:
            st.subheader("Average Discount by Product Category")
            avg_discount_category = rec_df.groupby("Category")["Predicted_Discount_Percent"].mean().sort_values(ascending=False)
            st.bar_chart(avg_discount_category)
    else:
        st.warning("⚠️ Recommendations file not found.")

    # --- Enhanced Insights and Filters ---
    st.subheader("📊 Enhanced Insights and Filters")

    if os.path.exists(rec_file):
        rec_df = pd.read_csv(rec_file)

        # Filter by Risk Level
        st.sidebar.header("Filter Options")
        risk_levels = rec_df["Risk_Level"].unique()
        selected_risk_levels = st.sidebar.multiselect("Select Risk Levels", options=risk_levels, default=risk_levels)
        filtered_df = rec_df[rec_df["Risk_Level"].isin(selected_risk_levels)]

        # Filter by Predicted Action
        actions = rec_df["Predicted_Action"].unique()
        selected_actions = st.sidebar.multiselect("Select Actions", options=actions, default=actions)
        filtered_df = filtered_df[filtered_df["Predicted_Action"].isin(selected_actions)]

        # Display Filtered Data
        st.dataframe(filtered_df.head(20))

        # Plot: Stock Quantity by Risk Level
        st.subheader("Stock Quantity by Risk Level")
        stock_by_risk = filtered_df.groupby("Risk_Level")["Stock_Quantity"].sum()
        st.bar_chart(stock_by_risk)

        # Plot: Average Discount by Risk Level
        if "Predicted_Discount_Percent" in filtered_df.columns:
            st.subheader("Average Discount by Risk Level")
            avg_discount_risk = filtered_df.groupby("Risk_Level")["Predicted_Discount_Percent"].mean()
            st.bar_chart(avg_discount_risk)

        # Interactive Table: Top Products by Stock Quantity
        st.subheader("Top Products by Stock Quantity")
        top_products = filtered_df.groupby("Product_Name")["Stock_Quantity"].sum().nlargest(10).reset_index()
        st.dataframe(top_products)

        # --- Enhanced Visualizations ---
        st.subheader("📊 Enhanced Visualizations")

        # Pie Chart: Risk Level Distribution
        st.subheader("Risk Level Distribution")
        risk_level_counts = rec_df["Risk_Level"].value_counts()
        st.plotly_chart(
            px.pie(
                names=risk_level_counts.index,
                values=risk_level_counts.values,
                title="Risk Level Distribution",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
        )

        # Line Chart: Stock Quantity Over Risk Levels
        st.subheader("Stock Quantity Over Risk Levels")
        stock_by_risk = rec_df.groupby("Risk_Level")["Stock_Quantity"].sum().reset_index()
        st.plotly_chart(
            px.line(
                stock_by_risk,
                x="Risk_Level",
                y="Stock_Quantity",
                title="Stock Quantity by Risk Level",
                markers=True,
                color_discrete_sequence=["#636EFA"]
            )
        )

    # --- Add KPI Cards ---
    st.markdown("""<h2 style='text-align: center;'>Key Metrics</h2>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Products", "1,000")
    with col2:
        st.metric("Expired Items", "50")
    with col3:
        st.metric("Near-Expiry Items", "200")

    # --- Add Predictive Insights Section ---
    st.markdown("""<h2 style='text-align: center;'>Predictive Insights</h2>""", unsafe_allow_html=True)
    if uploaded_file:
        st.subheader("Expiry Prediction Table")
        if "Risk_Level" in uploaded_df.columns:
            uploaded_df["Risk_Level"] = uploaded_df["Risk_Level"].map({"High": "🟥", "Medium": "🟧", "Low": "🟩"})
        st.dataframe(uploaded_df.head(10))

    # --- Add Forecasting Section ---
    st.markdown("""<h2 style='text-align: center;'>Forecasting & Trend Analysis</h2>""", unsafe_allow_html=True)
    forecast_df = pd.read_csv("forecasts/product_level/all_products_forecast.csv")

    # Debugging: Print column names to identify the issue
    st.write("Forecast DataFrame Columns:", forecast_df.columns.tolist())

    # Check if 'Date' column exists before setting it as index
    if 'Date' in forecast_df.columns:
        st.line_chart(forecast_df.set_index("Date"))
    else:
        st.error("The 'Date' column is missing in the forecast data. Please check the CSV file.")

    # --- Add Risk Scoring Section ---
    st.markdown("""<h2 style='text-align: center;'>Risk Scoring Insights</h2>""", unsafe_allow_html=True)
    # Debugging: Print column names to identify the issue
    st.write("Uploaded DataFrame Columns:", uploaded_df.columns.tolist())

    # Check if 'Risk_Score' column exists before plotting
    if 'Risk_Score' in uploaded_df.columns:
        st.plotly_chart(px.box(uploaded_df, x="Category", y="Risk_Score", color="Risk_Level"))
    else:
        st.error("The 'Risk_Score' column is missing in the uploaded data. Please check the data or preprocessing pipeline.")

    # --- Add Optimization Section ---
    st.markdown("""<h2 style='text-align: center;'>Optimization & Recommendations</h2>""", unsafe_allow_html=True)
    if "Predicted_Discount_Percent" in rec_df.columns:
        st.dataframe(rec_df[["Product_Name", "Predicted_Action", "Predicted_Discount_Percent"]].head(10))
    else:
        st.dataframe(rec_df[["Product_Name", "Predicted_Action"]].head(10))

    # --- Add Footer ---
    st.markdown("""<footer style='text-align: center;'>Version 1.0 | Last Updated: October 8, 2025</footer>""", unsafe_allow_html=True)
else:
    st.info("Please upload a CSV file to get started.")
