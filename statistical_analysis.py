import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
import gpboost as gpb
import scipy.stats as stats
import numpy as np


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

    dfAnalysis["binary_response"] = dfAnalysis['response'].map({'yes':1, 'no':0})
    
    
    for population in dfAnalysis["population_name"].unique():
        print(population)
        data = dfAnalysis.loc[dfAnalysis["population_name"] == population]
        fam = sm.families.Binomial()
        ind = sm.cov_struct.Exchangeable()
        model = smf.gee("binary_response ~ percentage + time_from_treatment_start".format(population), "sample_id", data, 
                      cov_struct=ind, family=fam)
        
        result = model.fit()
        print(result.summary())

        model = smf.gee("binary_response ~ percentage + age + sex".format(population), "sample_id", data, 
                      cov_struct=ind, family=fam)
        
        result = model.fit()
        print(result.summary())


        gp_model = gpb.GPModel(group_data=data["sample_id"], likelihood="binary")
        x = sm.tools.tools.add_constant(data["percentage"])

        result = gp_model.fit(y=data["binary_response"], X=x)
        print(result.summary())
        
        


# use t tests to start but this might need linear mixed models
