from components.map_helper import show_map_sample
import pandas as pd
import streamlit as st
import os
import sys

# Add parent directory to path so we can import ml and components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


st.set_page_config(page_title="ASCM Dashboard", layout="wide")

st.sidebar.title("ASCM-app")
page = st.sidebar.radio("Go to", ["Home", "Upload", "Forecast", "Routing"])

if page == "Home":
    st.title("ASCM — Supply Chain Orchestration Demo")
    st.markdown(
        "Upload sample data, run quick training, and try routing/forecasting.")
    st.info("This is a minimal scaffold. Connect a Supabase project and real models to productionize.")

if page == "Upload":
    st.header("Upload CSV")
    uploaded = st.file_uploader("Upload orders CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.write(df.head())
        st.success("File loaded into memory. In production, persist to Supabase.")

if page == "Forecast":
    st.header("Demand Forecast")
    st.markdown("Run the demo forecasting model (quick mode)")
    if st.button("Run Forecast (demo)"):
        from ml.train import quick_forecast
        df_forecast = quick_forecast()
        st.line_chart(df_forecast.set_index('ds')['yhat'])

if page == "Routing":
    st.header("Route Optimization")
    st.markdown("Run the demo route optimizer (GNN stub + heuristic)")
    if st.button("Run Route Opt (demo)"):
        df_routes = show_map_sample()
        st.write(df_routes)
        st.success("Displayed sample routes on map.")
