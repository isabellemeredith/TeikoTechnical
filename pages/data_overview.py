import streamlit as st
import pandas as pd
import sqlite3

import utils.display as display
import analysis


if __name__ == "__main__":
    database_name = "cell-count.db"
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    analysis.create_summary_view(conn)
    get_population_data_query = "SELECT * FROM populations_summary ORDER BY sample;"
    dfPopulation = display.get_data(get_population_data_query, conn)

    st.title("Data Overview")

    st.header("Frequency of each cell type in each sample")

    display.display_paginated_dataframe(dfPopulation)
    