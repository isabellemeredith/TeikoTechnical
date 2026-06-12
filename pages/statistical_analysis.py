import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os

import utils.display as display
import analysis


if __name__ == "__main__":
    conn = sqlite3.connect("cell-count.db")
    cursor = conn.cursor()

    analysis.create_analysis_view(conn)

    get_analysis_data_query = "SELECT * FROM analysis;"
    dfAnalysis = display.get_data(get_analysis_data_query, conn)

    st.title("Miraclib Responder Analysis")
    
    time_point = st.selectbox("Time Point", options=["All", 0, 7, 14]) 
    if time_point == "All":
        selected_rows = slice(None)
    else:
        selected_rows = dfAnalysis["time_from_treatment_start"] == str(time_point)

    fig = px.box(dfAnalysis.loc[selected_rows], x="population_name", y="percentage", color="response")
    st.plotly_chart(fig, theme="streamlit", width="stretch")

    st.header("Association Between Cell Type and Responder Status")

    st.text("The relationship between cell population frequency and miraclib response was evaluated using a linear mixed effects model to account for the repeated measures at different study time points. Note that statistically significant is not equivalent to clinically relevant.")

    if os.path.exists("./output/analysis_results.csv"):
        dfResults = pd.read_csv("./output/analysis_results.csv")
    else:
        dfResults = analysis.get_responder_diff(dfAnalysis)
    
    # dfResults.set_index("population_name", inplace=True)
    population_dict = {"b_cell" : "B Cell", "cd4_t_cell": "CD4 T Cell", "cd8_t_cell": "CD8 T Cell", "nk_cell": "NK Cell", "monocyte": "Monocyte"}
    
    multiple_comparisons = 1.0
    for population in dfAnalysis["population_name"].unique():
        st.subheader(population_dict[population])

        if dfResults.at[population, "significant"]:
            st.text("There was a significant association between response to miraclib and frequency of {type} (p = {pvalue:10.3f}). Responders had a {coef:3.2f} higher frequency of {type}s".format(type=population_dict[population], pvalue=dfResults.at[population, "p_value"], coef=dfResults.at[population, "coef"]))
        else:
            st.text("There was not a significant association between response to miraclib and frequency of {type} (p = {pvalue:10.4f}).".format(type=population_dict[population], pvalue=dfResults.at[population, "p_value"]))
        
        
