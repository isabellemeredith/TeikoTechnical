import streamlit as st
import pandas as pd
import sqlite3

import utils.display as display
import analysis


if __name__ == "__main__":
    conn = sqlite3.connect("cell-count.db")
    cursor = conn.cursor()

    analysis.create_project_view(conn)
    get_project_data_query = "SELECT * FROM projects_summary ORDER BY project_id_text;"
    dfProjects = display.get_data(get_project_data_query, conn)

    readable_columns = {"project_id_text": "Project ID", "subject_id_text": "Subject ID", "sample_id_text": "Sample ID", "response": "Response", "sex": "Sex"}

    st.title("Data Subset")

    display.display_paginated_dataframe(dfProjects[["project_id_text", "subject_id_text", "sample_id_text", "response", "sex"]].rename(columns=readable_columns))

    project_counts = dfProjects["project_id_text"].value_counts()
    sex_counts = dfProjects["sex"].value_counts()
    response_counts = dfProjects["response"].value_counts()

    st.dataframe(project_counts)
    st.dataframe(sex_counts)
    st.dataframe(response_counts)


