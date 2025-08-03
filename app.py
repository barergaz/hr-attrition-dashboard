import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="HR Attrition Dashboard", layout="wide", page_icon="📊")

# --- Custom CSS for clean background and compact layout ---
st.markdown("""
    <style>
        .main {background-color: #f7f7fa !important;}
        .block-container {padding-top: 2rem;}
        .stPlotlyChart {background: #f7f7fa !important;}
        .st-bb {background: #f7f7fa !important;}
        .st-cq {background: #f7f7fa !important;}
        .st-cx {background: #f7f7fa !important;}
        .css-1v0mbdj, .css-1d391kg {background: #f7f7fa; border-radius: 12px;}
    </style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
df = pd.read_csv('united.csv')
# Map the Attrition column from Yes/No to 1/0 for easier calculations
df["Attrition"] = df["Attrition"].map({'Yes': 1, 'No': 0})
df["OverTime"] = df["OverTime"].map({'Yes': True, 'No': False})

# Pre‑calculate tenure groupings used throughout the dashboard.  The "YearsAtCompanyGroup"
# column divides employees into meaningful tenure bins (0–2, 2–5, 5–10, 10+ years).
tenure_bins = [0, 2, 5, 10, float('inf')]
tenure_labels = ["0–2 years", "2–5 years", "5–10 years", "10+ years"]
df["YearsAtCompanyGroup"] = pd.cut(
    df["YearsAtCompany"],
    bins=tenure_bins,
    labels=tenure_labels,
    right=False,
    include_lowest=True
)

# --- KPI SECTION ---
st.title("HR Attrition Analysis Dashboard")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
# KPI 1: Overall Attrition Rate
overall_attrition_rate = df["Attrition"].mean() * 100
kpi1.metric("Overall Attrition Rate", f"{overall_attrition_rate:.1f}%")
# KPI 2: Entry-Level Attrition
level1 = df[df["JobLevel"] == 1]
level1_rate = level1["Attrition"].mean() * 100 if not level1.empty else 0
kpi2.metric("Entry-Level Attrition", f"{level1_rate:.1f}%")
# KPI 3: Early Tenure Attrition
early_tenure = df[df["YearsAtCompany"] <= 2]
early_tenure_rate = early_tenure["Attrition"].mean() * 100 if not early_tenure.empty else 0
kpi3.metric("0–2yr Attrition", f"{early_tenure_rate:.1f}%")
# KPI 4: Highest Risk Role
jobrole_attr = (
    df.groupby("JobRole")
    .agg(count_JobRole=("JobRole", "count"),
         attrition_left=("Attrition", lambda x: 100 * (x == 1).sum() / len(x)),
         attrition_stay=("Attrition", lambda x: 100 * (x == 0).sum() / len(x)))
    .sort_values(["attrition_left"], ascending=False)
)
if not jobrole_attr.empty:
    top_role = jobrole_attr.index[0]
    top_role_val = jobrole_attr.iloc[0]["attrition_left"]
    kpi4.metric("Highest Risk Role", f"{top_role}", f"{top_role_val:.1f}%")
else:
    kpi4.metric("Highest Risk Role", "N/A", "0.0%")

# --- TABLE: Attrition by Job Role ---
st.subheader("Attrition by Job Role (Table)")
st.dataframe(jobrole_attr, use_container_width=False)

# --- CHART: Attrition Rate by Job Role ---
st.subheader("Attrition Rate by Job Role")
col1, col2 = st.columns([2,1])
with col1:
    # Filters
    departments = ['All'] + sorted(df['Department'].dropna().unique())
    selected_dept = st.selectbox("Filter by Department", departments, key='dept_chart_1')
    filtered_df = df.copy()
    if selected_dept != 'All':
        filtered_df = filtered_df[filtered_df['Department'] == selected_dept]
    # Recreate jobrole_attr for filtered data
    jobrole_attr_filtered = (
        filtered_df.groupby("JobRole")
        .agg(count_JobRole=("JobRole", "count"),
             attrition_left=("Attrition", lambda x: 100 * (x == 1).sum() / len(x)),
             attrition_stay=("Attrition", lambda x: 100 * (x == 0).sum() / len(x)))
        .sort_values(["attrition_left"], ascending=False)
    )
    if not jobrole_attr_filtered.empty:
        fig = px.bar(jobrole_attr_filtered.reset_index(),
                     x="JobRole", y="attrition_left",
                     color_discrete_sequence=["#1976D2"]*len(jobrole_attr_filtered),  # United color
                     )
        fig.update_traces(marker_line_color='black', marker_line_width=1)
        fig.update_layout(width=500, height=350, margin=dict(l=20, r=20, t=40, b=20),
                          xaxis_title="Job Role", yaxis_title="Attrition Rate (%)",
                          title="Attrition Rate by Job Role")
        fig.update_xaxes(tickangle=30)
        st.plotly_chart(fig)
    else:
        st.info("No data for selected filter.")
with col2:
    st.markdown("**Insight:** Sales Representatives have the highest attrition rate (~40%), suggesting potential issues in role satisfaction or workload. Roles with lower attrition may have better retention practices or job satisfaction.")

# --- NEW KPI GRAPH: Attrition by Gender ---
st.subheader("Attrition Rate by Gender")
gender_attrition = (
    df.groupby("Gender")["Attrition"].mean() * 100
)
fig = px.bar(gender_attrition.reset_index(), x="Gender", y="Attrition", color_discrete_sequence=["#BA68C8"],
             labels={"Attrition": "Attrition Rate (%)"}, title="Attrition Rate by Gender")
fig.update_traces(marker_line_color='black', marker_line_width=1)
fig.update_layout(width=500, height=350, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='#f7f7fa', paper_bgcolor='#f7f7fa')
st.plotly_chart(fig)

# 2. Attrition by Distance From Home & Job Role
st.subheader("Attrition % by Distance From Home Range and JobRole")
col1, col2 = st.columns([2,1])
with col1:
    # Filters
    departments = ['All'] + sorted(df['Department'].dropna().unique())
    selected_dept2 = st.selectbox("Filter by Department", departments, key='dept_chart_2')
    filtered_df = df.copy()
    if selected_dept2 != 'All':
        filtered_df = filtered_df[filtered_df['Department'] == selected_dept2]
    min_dist = filtered_df["DistanceFromHome"].min() if not filtered_df.empty else 0
    max_dist = filtered_df["DistanceFromHome"].max() if not filtered_df.empty else 0
    bin_edges = list(range(int(min_dist), int(max_dist) + 7, 7)) if max_dist > 0 else [0,1]
    if bin_edges[-1] < max_dist:
        bin_edges.append(int(max_dist) + 1)
    range_labels = [f"{bin_edges[i]}–{bin_edges[i+1]-1}" for i in range(len(bin_edges)-1)] if len(bin_edges) > 1 else ["0-1"]
    filtered_df["DistanceFromHomeRange"] = pd.cut(filtered_df["DistanceFromHome"], bins=bin_edges, labels=range_labels, include_lowest=True, ordered=True) if len(bin_edges) > 1 else "0-1"
    summary = (
        filtered_df.groupby(["DistanceFromHomeRange", "JobRole"])
        .agg(count=("Attrition", "count"), attrition_left=("Attrition", lambda x: 100 * (x == 1).sum() / len(x)))
        .reset_index()
    )
    summary = summary[summary["count"] > 7]
    if not summary.empty:
        fig = px.bar(summary, x="DistanceFromHomeRange", y="attrition_left", color="JobRole", barmode="group", color_discrete_sequence=px.colors.sequential.Purples)
        fig.update_traces(marker_line_color='black', marker_line_width=1)
        fig.update_layout(width=500, height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig)
    else:
        st.info("No data for selected filter.")
with col2:
    st.markdown("**Insight:** Attrition increases with commute distance for some roles.")

# 3. Attrition Rate by Overtime
st.subheader("Attrition Rate by Overtime Participation")
col1, col2 = st.columns([2,1])
with col1:
    overtime_opts = ['All', 'Yes', 'No']
    selected_overtime = st.selectbox("Filter by Overtime", overtime_opts, key='overtime_chart_1')
    filtered_df = df.copy()
    if selected_overtime != 'All':
        filtered_df = filtered_df[filtered_df['OverTime'] == (selected_overtime == 'Yes')]
    overtime_labels = {True: "Did Overtime", False: "Did Not Do Overtime"}
    filtered_df["OverTimeLabel"] = filtered_df["OverTime"].map(overtime_labels)
    overtime_attrition = pd.crosstab(filtered_df["OverTimeLabel"], filtered_df["Attrition"], normalize='index') * 100
    overtime_attrition = overtime_attrition.rename(columns={1: "Left", 0: "Stayed"})
    fig = go.Figure(data=[
        go.Bar(name='Left', x=overtime_attrition.index, y=overtime_attrition["Left"], marker_color="#6EC6FF", marker_line_color='black', marker_line_width=1),
        go.Bar(name='Stayed', x=overtime_attrition.index, y=overtime_attrition["Stayed"], marker_color="#A5D6A7", marker_line_color='black', marker_line_width=1)
    ])
    fig.update_layout(barmode='stack', title="Attrition Rate by Overtime Participation", yaxis_title="% Employees", width=500, height=350, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='#f7f7fa', paper_bgcolor='#f7f7fa')
    st.plotly_chart(fig)
with col2:
    st.markdown("**Insight:** Employees who work overtime are nearly 3x more likely to leave.")

# 4. Attrition by Job Level
st.subheader("Attrition Rate by Job Level")
col1, col2 = st.columns([2,1])
with col1:
    joblevels = sorted(df['JobLevel'].dropna().unique())
    selected_level = st.selectbox("Filter by Job Level", ['All'] + [str(jl) for jl in joblevels], key='level_chart_1')
    filtered_df = df.copy()
    if selected_level != 'All':
        filtered_df = filtered_df[filtered_df['JobLevel'] == int(selected_level)]
    joblevel_attrition = (
        filtered_df.groupby("JobLevel")["Attrition"]
        .value_counts(normalize=True)
        .unstack()
        .rename(columns={0: "Stayed", 1: "Left"})
        * 100
    )
    fig = go.Figure(data=[
        go.Bar(name='Stayed', x=joblevel_attrition.index, y=joblevel_attrition["Stayed"], marker_color="#7986CB", marker_line_color='black', marker_line_width=1),
        go.Bar(name='Left', x=joblevel_attrition.index, y=joblevel_attrition["Left"], marker_color="#BA68C8", marker_line_color='black', marker_line_width=1)
    ])
    fig.update_layout(barmode='stack', title="Attrition Rate by Job Level", yaxis_title="% Employees", width=500, height=350, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='#f7f7fa', paper_bgcolor='#f7f7fa')
    st.plotly_chart(fig)
with col2:
    st.markdown("**Insight:** Entry-level employees have the highest attrition rate.")

# 5. Attrition by Years at Company
st.subheader("Attrition Distribution by Years at Company")
col1, col2 = st.columns([2,1])
with col1:
    bins = [0, 2, 5, 10, float('inf')]
    tenure_labels = ["0–2 years", "2–5 years", "5–10 years", "10+ years"]
    df["YearsAtCompanyGroup"] = pd.cut(df["YearsAtCompany"], bins=bins, labels=tenure_labels, right=False, include_lowest=True)
    selected_tenure = st.selectbox("Filter by Tenure Group", ['All'] + tenure_labels, key='tenure_chart_1')
    filtered_df = df.copy()
    if selected_tenure != 'All':
        filtered_df = filtered_df[filtered_df['YearsAtCompanyGroup'] == selected_tenure]
    experience_attrition = (
        filtered_df.groupby("YearsAtCompanyGroup")["Attrition"]
        .value_counts(normalize=True)
        .unstack()
        .rename(columns={0: "Stayed", 1: "Left"})
        * 100
    )
    fig = go.Figure(data=[
        go.Bar(name='Stayed', x=experience_attrition.index, y=experience_attrition["Stayed"], marker_color="#4FC3F7", marker_line_color='black', marker_line_width=1),
        go.Bar(name='Left', x=experience_attrition.index, y=experience_attrition["Left"], marker_color="#9575CD", marker_line_color='black', marker_line_width=1)
    ])
    fig.update_layout(barmode='stack', title="Attrition Distribution by Years at Company", yaxis_title="% Employees", width=500, height=350, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='#f7f7fa', paper_bgcolor='#f7f7fa')
    st.plotly_chart(fig)
with col2:
    st.markdown("**Insight:** Employees with 0–2 years tenure show the highest attrition rates.")

# --- SUMMARY BAR CHART: Attrition Rate by Years at Company ---
st.subheader("Attrition Rate by Years at Company (Summary)")

# Compute attrition rate dynamically per tenure group.  Since the "Attrition" column is
# numeric (1 for Yes, 0 for No), the mean multiplied by 100 yields the rate as a
# percentage.  Missing groups (e.g. if a filter above removed them) are handled by
# reindexing against the full list of tenure labels.
summary_rate = (
    df.groupby("YearsAtCompanyGroup")["Attrition"].mean() * 100
).reindex(tenure_labels)
summary_df = summary_rate.reset_index().rename(columns={"Attrition": "AttritionRate"})

fig = px.bar(
    summary_df,
    x="YearsAtCompanyGroup",
    y="AttritionRate",
    color_discrete_sequence=["orange"] * len(summary_df),
    labels={"AttritionRate": "Attrition Rate (%)", "YearsAtCompanyGroup": "Years at Company"},
    title="Attrition Rate by Years at Company"
)
fig.update_traces(
    marker_line_color='black',
    marker_line_width=1,
    text=summary_df["AttritionRate"].apply(lambda x: f"{x:.1f}%"),
    textposition='outside'
)
fig.update_layout(
    width=None,
    height=350,
    margin=dict(l=20, r=20, t=40, b=20),
    plot_bgcolor='white',
    paper_bgcolor='white',
    xaxis_title="Years at Company",
    yaxis_title="Attrition Rate (%)",
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# 6. Cross Analysis: Job Level × Tenure (heatmap)
st.subheader("Attrition Rate by Job Level and Years at Company (Heatmap)")
col1, col2 = st.columns([2,1])
with col1:
    # Use the pre‑computed tenure grouping.  Group by JobLevel and YearsAtCompanyGroup and
    # calculate attrition rate on the fly.  "Attrition" is already numeric.
    joblevel_tenure_attrition = (
        df.groupby(["JobLevel", "YearsAtCompanyGroup"])
        .agg(
            Total_Employees=("EmployeeNumber", "count"),
            Left=("Attrition", "sum")
        )
        .reset_index()
    )
    joblevel_tenure_attrition["Attrition Rate (%)"] = (
        joblevel_tenure_attrition["Left"] / joblevel_tenure_attrition["Total_Employees"] * 100
    )
    pivot_table = joblevel_tenure_attrition.pivot(
        index="JobLevel", columns="YearsAtCompanyGroup", values="Attrition Rate (%)"
    )
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(
        pivot_table,
        annot=True,
        cmap="BuGn",
        fmt=".1f",
        linewidths=0.5,
        linecolor='gray',
        cbar=True,
        ax=ax
    )
    ax.set_title("Attrition Rate by Job Level and Years at Company")
    ax.set_xlabel("Years at Company")
    ax.set_ylabel("Job Level")
    st.pyplot(fig)
with col2:
    st.markdown("**Insight:** Highest attrition is among entry-level employees with 0–2 years at the company.")

# --- Recommendations ---
st.header("Recommendations")
st.markdown("""
- **Improve onboarding and support for new employees (0–2 years) to reduce early attrition.**
- **Reassess work-life balance and overtime policies, especially for high-risk roles.**
- **Consider flexible work options for employees living farther from the office.**
- **Target retention efforts at job roles and levels with the highest attrition rates.**
""") 