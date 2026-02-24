import pandas as pd
import streamlit as st

# Very small helper to return a sample DataFrame representing routes


def show_map_sample():
    data = [
        {"route_id": 1, "from": "A", "to": "B", "distance_km": 12.3},
        {"route_id": 2, "from": "B", "to": "C", "distance_km": 7.8},
    ]
    df = pd.DataFrame(data)
    st.map(df.assign(lat=[37.77, 37.78], lon=[-122.41, -122.42]))
    return df
