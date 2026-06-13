import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

import utils.display as display
import analysis


if __name__ == "__main__":
    database_name = "cell-count.db"
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    analysis.create_project_view(conn)
    get_project_data_query = "SELECT * FROM projects_summary ORDER BY project_id_text;"
    dfProjects = display.get_data(get_project_data_query, conn)

    readable_columns = {"project_id_text": "Project ID", "subject_id_text": "Subject ID", "sample_id_text": "Sample ID", "response": "Response", "sex": "Sex"}

    st.title("Data Subset")

    display.display_paginated_dataframe(dfProjects[["project_id_text", "subject_id_text", "sample_id_text", "response", "sex"]].rename(columns=readable_columns))

    project_counts = analysis.get_counts(dfProjects, "project_id_text")

    dfProjectsSubjectLevel = dfProjects.drop_duplicates(subset="subject_id_text")
    sex_counts = analysis.get_counts(dfProjectsSubjectLevel, "sex")
    response_counts = analysis.get_counts(dfProjectsSubjectLevel, "response")

    fig = px.bar(project_counts, x=project_counts.index, y='count', color=project_counts.index, title="Counts by Project", labels={'x':'Project', 'count': 'Number of Subjects'})
    st.plotly_chart(fig, theme="streamlit", width="stretch")
    st.dataframe(project_counts.reset_index().rename(columns={"project_id_text": "Project", "count": "Number of Samples"}), hide_index=True)
    fig = px.bar(sex_counts, x=sex_counts.index, y='count', color=sex_counts.index, title="Counts by Sex", labels={'x':'Sex', 'count': 'Number of Subjects'})
    st.plotly_chart(fig, theme="streamlit", width="stretch")
    st.dataframe(sex_counts.reset_index().rename(columns={"sex": "Sex", "count": "Number of Subjects"}), hide_index=True)
    fig = px.bar(response_counts, x=response_counts.index, y='count', color=response_counts.index, title="Counts by Response", labels={'x':'Response', 'count': 'Number of Subjects'})
    st.plotly_chart(fig, theme="streamlit", width="stretch")
    st.dataframe(response_counts.reset_index().rename(columns={"response": "Responded to Miraclib", "count": "Number of Subjects"}), hide_index=True)


