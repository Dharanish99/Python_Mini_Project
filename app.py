import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap

# Page configuration
st.set_page_config(layout="wide", page_title="US Traffic Accident Dashboard", page_icon="🚦")
st.title("🚦 US Traffic Accident Dashboard")
st.markdown("Explore and analyze traffic accident patterns across the United States.")

# Cache data loading
@st.cache_data
def load_data(nrows=100000):
    try:
        df = pd.read_csv("US_Accidents_Dataset.csv", nrows=nrows)
        df['Start_Time'] = pd.to_datetime(df['Start_Time'], errors='coerce')
        df = df.dropna(subset=['Start_Time', 'Start_Lat', 'Start_Lng', 'Weather_Condition'])
        return df
    except FileNotFoundError:
        st.error("Error: 'US_Accidents_Dataset.csv' not found. Please ensure the file is in the correct directory.")
        return pd.DataFrame()

# Load data
df = load_data()

# Sidebar for filters
st.sidebar.header("Filter Options")
date_range = st.sidebar.date_input(
    "Select Date Range",
    [df['Start_Time'].min().date(), df['Start_Time'].max().date()],
    min_value=df['Start_Time'].min().date(),
    max_value=df['Start_Time'].max().date()
)
weather_options = st.sidebar.multiselect(
    "Select Weather Conditions",
    options=df['Weather_Condition'].unique(),
    default=df['Weather_Condition'].unique()
)

# Filter data
filtered_df = df[
    (df['Start_Time'].dt.date >= date_range[0]) &
    (df['Start_Time'].dt.date <= date_range[1]) &
    (df['Weather_Condition'].isin(weather_options))
]

# Data summary
st.subheader("📊 Data Summary")
if not filtered_df.empty:
    st.write(f"Total Accidents: {len(filtered_df)}")
    st.write(f"Date Range: {filtered_df['Start_Time'].min().date()} to {filtered_df['Start_Time'].max().date()}")
    st.write(f"Unique Weather Conditions: {filtered_df['Weather_Condition'].nunique()}")
else:
    st.warning("No data available for the selected filters.")

# --- HEATMAP ---
st.subheader("📍 Accident Location Heatmap")
map_type = st.selectbox("Select Map Type", ["Markers", "Heatmap"])
m = folium.Map(location=[37.0902, -95.7129], zoom_start=4, tiles="CartoDB positron")

if map_type == "Markers":
    for _, row in filtered_df.sample(min(100, len(filtered_df))).iterrows():
        folium.CircleMarker(
            location=[row['Start_Lat'], row['Start_Lng']],
            radius=3,
            color='red',
            fill=True,
            fill_opacity=0.6,
            popup=f"Time: {row['Start_Time']}<br>Weather: {row['Weather_Condition']}"
        ).add_to(m)
else:
    heat_data = [[row['Start_Lat'], row['Start_Lng']] for _, row in filtered_df.iterrows()]
    HeatMap(heat_data, radius=15, blur=20).add_to(m)

st_data = st_folium(m, width=1000, height=500)

# --- LINE PLOT: Accidents Over Time ---
st.subheader("📈 Accidents Over Time")
if not filtered_df.empty:
    accidents_over_time = filtered_df['Start_Time'].dt.date.value_counts().sort_index()
    fig_time = px.line(
        x=accidents_over_time.index,
        y=accidents_over_time.values,
        labels={'x': 'Date', 'y': 'Number of Accidents'},
        title="Accidents Over Time",
        color_discrete_sequence=['#1f77b4']
    )
    fig_time.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Accidents",
        template="plotly_white"
    )
    st.plotly_chart(fig_time, use_container_width=True)
else:
    st.write("No data to display for the line plot.")

# --- BAR PLOT: Accidents by Weather ---
st.subheader("☁️ Accidents by Weather Condition")
if not filtered_df.empty:
    weather_counts = filtered_df['Weather_Condition'].value_counts().nlargest(10)
    fig_weather = px.bar(
        x=weather_counts.index,
        y=weather_counts.values,
        labels={'x': 'Weather Condition', 'y': 'Accident Count'},
        title="Top Weather Conditions for Accidents",
        color=weather_counts.index,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_weather.update_layout(
        xaxis_title="Weather Condition",
        yaxis_title="Accident Count",
        template="plotly_white"
    )
    st.plotly_chart(fig_weather, use_container_width=True)
else:
    st.write("No data to display for the bar plot.")

# --- PIE CHART: Weather Distribution ---
st.subheader("🥧 Weather Condition Distribution")
if not filtered_df.empty:
    weather_dist = filtered_df['Weather_Condition'].value_counts()
    fig_pie = px.pie(
        names=weather_dist.index,
        values=weather_dist.values,
        title="Distribution of Accidents by Weather Condition",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(template="plotly_white")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.write("No data to display for the pie chart.")

# Display raw data (optional)
if st.checkbox("Show Raw Data"):
    st.subheader("📋 Raw Data")
    st.dataframe(filtered_df)
