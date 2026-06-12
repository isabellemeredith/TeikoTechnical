import streamlit as st
import pandas as pd
import sqlite3

import utils.display as display


if __name__ == "__main__":
    connection = sqlite3.connect("cell-count.db")
    cursor = connection.cursor()

    project_view_query = """
        CREATE VIEW projects_summary 
        AS
        SELECT sample_id, sample_id_text, SUBJECT.subject_id, SUBJECT.subject_id_text, SUBJECT.project_id_text, response, sex, sample_type, condition, treatment, time_from_treatment_start
        FROM SUBJECT
        JOIN PROJECT ON SUBJECT.project_id = PROJECT.project_id
        JOIN SAMPLE ON SAMPLE.subject_id = SUBJECT.subject_id
        WHERE sample_type = "PBMC"
        AND condition = "melanoma"
        AND treatment = "miraclib"
        AND response IS NOT NULL
        AND time_from_treatment_start = 0;
    """
    cursor.execute("DROP VIEW IF EXISTS projects_summary;")
    cursor.execute(project_view_query)

    # project_view_summary_query = """
    #     SELECT COUNT(sample_id) OVER (PARTITION BY project_id_text) AS n_project, COUNT(sample_id) OVER (PARTITION BY response) AS n_responders, COUNT(sample_id) OVER (PARTITION BY sex) AS n_sex FROM projects_summary;
    # """

    # cursor.execute(project_view_summary_query)
    # result = cursor.fetchall()
    # print(result)

    # cursor.execute("SELECT * FROM populations ORDER BY sample")
    # result = cursor.fetchall()
    # print(result)
    get_project_data_query = "SELECT * FROM projects_summary ORDER BY project_id_text;"
    dfProjects = display.get_data(get_project_data_query, connection)

    readable_columns = {"project_id_text": "Project ID", "subject_id_text": "Subject ID", "sample_id_text": "Sample ID", "response": "Response", "sex": "Sex"}

    st.title("Data Subset")

    display.display_paginated_dataframe(dfProjects[["project_id_text", "subject_id_text", "sample_id_text", "response", "sex"]].rename(columns=readable_columns))

    project_counts = dfProjects["project_id_text"].value_counts()
    sex_counts = dfProjects["sex"].value_counts()
    response_counts = dfProjects["response"].value_counts()

    st.dataframe(project_counts)
    st.dataframe(sex_counts)
    st.dataframe(response_counts)

    # result_set = c.execute('SELECT * FROM distro WHERE id IN (%s)' %
    #                        ','.join('?'*len(desired_ids)), desired_ids)

