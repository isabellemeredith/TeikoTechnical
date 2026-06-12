import streamlit as st
import pandas as pd
import sqlite3
import utils.display as display


if __name__ == "__main__":
    connection = sqlite3.connect("cell-count.db")
    cursor = connection.cursor()

    summary_view_query = """
        CREATE VIEW populations_summary 
        AS
        SELECT sample_id_text AS sample, population_name AS population, SUM(count) OVER (PARTITION BY sample_id) AS total_count, count, 1.0 * count / SUM(count) OVER (PARTITION BY sample_id) AS percentage FROM POPULATION;
    """
    cursor.execute("DROP VIEW IF EXISTS populations_summary;")
    cursor.execute(summary_view_query)

    # cursor.execute("SELECT * FROM populations ORDER BY sample")
    # result = cursor.fetchall()
    # print(result)
    get_population_data_query = "SELECT * FROM populations_summary ORDER BY sample;"
    dfPopulation = display.get_data(get_population_data_query, connection)

    st.title("Data Overview")

    display.display_paginated_dataframe(dfPopulation)

    # st.dataframe(dfPopulation)

    


