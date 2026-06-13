import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
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

    population_dict = {"b_cell" : "B Cell", "cd4_t_cell": "CD4 T Cell", "cd8_t_cell": "CD8 T Cell", "nk_cell": "NK Cell", "monocyte": "Monocyte"}

    fig = analysis.get_population_fig(dfAnalysis, selected_rows)
    st.plotly_chart(fig, theme="streamlit", width="stretch")

    st.header("Association Between Cell Type and Responder Status")

    st.text("The relationship between cell population frequency and miraclib response was evaluated using a linear mixed effects model with subject id as a random effect and response as a main effect to account for the repeated measures at different study time points. Note that statistically significant is not equivalent to clinically relevant.")

    dfResults = analysis.get_responder_diff(dfAnalysis)
    
    for population in dfAnalysis["population_name"].unique():
        st.subheader(population_dict[population])

        if dfResults.at[population, "significant"]:
            coef=dfResults.at[population, "coef"]
            difference = "higher" if coef > 0 else "lower"
            st.text("There was a significant association between response to miraclib and frequency of {type} (p = {pvalue:10.3f}). Responders had {coef:3.2f} {difference} percentage points of {type}s".format(type=population_dict[population], pvalue=dfResults.at[population, "p_value"], coef=coef, difference=difference))
        else:
            st.text("There was not a significant association between response to miraclib and frequency of {type} (p = {pvalue:10.3f}).".format(type=population_dict[population], pvalue=dfResults.at[population, "p_value"]))
        
        
