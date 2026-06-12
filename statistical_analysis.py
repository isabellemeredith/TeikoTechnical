import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import statsmodels.api as sm
import statsmodels.formula.api as smf
# import gpboost as gpb
# import numpy as np
# import scipy.stats

import utils.display as display


if __name__ == "__main__":
    conn = sqlite3.connect("cell-count.db")
    cursor = conn.cursor()
    
    analysis_view_query = """
        CREATE VIEW analysis 
        AS
        SELECT population_id, POPULATION.sample_id, POPULATION.sample_id_text, population_name, SUM(count) OVER (PARTITION BY POPULATION.sample_id) AS total_count, count, 1.0 * count / SUM(count) OVER (PARTITION BY POPULATION.sample_id) AS percentage, condition, response, sample_type, treatment, time_from_treatment_start, age, sex
        FROM (POPULATION JOIN SAMPLE 
        ON POPULATION.sample_id = SAMPLE.sample_id
        JOIN SUBJECT
        ON SAMPLE.subject_id = SUBJECT.subject_id) 
        WHERE sample_type = "PBMC"
        AND condition = "melanoma"
        AND treatment = "miraclib"
        AND response IS NOT NULL;
    """


    cursor.execute("DROP VIEW IF EXISTS analysis;")
    cursor.execute(analysis_view_query)

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

    dfAnalysis["binary_response"] = dfAnalysis['response'].map({'yes':1, 'no':0})
    dfAnalysis["binary_sex"] = dfAnalysis['sex'].map({'M':1, 'F':0})
    
    population_dict = {"b_cell" : "B Cell", "cd4_t_cell": "CD4 T Cell", "cd8_t_cell": "CD8 T Cell", "nk_cell": "NK Cell", "monocyte": "Monocyte"}
    
    multiple_comparisons = 1.0
    for population in dfAnalysis["population_name"].unique():
        st.subheader(population_dict[population])
        print(population_dict[population])
        data = dfAnalysis.loc[dfAnalysis["population_name"] == population]

        # gp_model = gpb.GPModel(group_data=data["sample_id"], likelihood="binary")
        # x = sm.tools.tools.add_constant(data["binary_response"])

        # result = gp_model.fit(y=data["percentage"], X=x)
        # print(result.summary())

        # gp_model = gpb.GPModel(group_data=data["sample_id"], likelihood="binary")
        # x = sm.tools.tools.add_constant(data[["percentage", "age", "binary_sex"]])

        # result = gp_model.fit(y=data["binary_response"], X=x)
        # print(result.summary())
        # coefs = result.get_coef(std_err=True)
        # z_values = np.array(coefs.iloc[0] / coefs.iloc[1])
        # p_values = 2 * scipy.stats.norm.cdf(-np.abs(z_values))

        model = smf.mixedlm("percentage ~ binary_response", data, groups=data["sample_id"])
        model_fit = model.fit()
        print(model_fit.summary())

        print(model_fit.fe_params["binary_response"])

        coef = model_fit.fe_params["binary_response"]
        p_value = model_fit.pvalues["binary_response"]
        significant = (multiple_comparisons * p_value) < 0.05

        if significant:
            st.text("There was a significant association between response to miraclib and frequency of {type} (p = {pvalue:10.3f}). Responders had a {coef:3.2f} higher frequency of {type}s".format(type=population_dict[population], pvalue=p_value, coef=coef))
        else:
            st.text("There was not a significant association between response to miraclib and frequency of {type} (p = {pvalue:10.4f}).".format(type=population_dict[population], pvalue=p_value))
        
        
