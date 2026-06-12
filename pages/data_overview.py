import streamlit as st
import pandas as pd
import sqlite3

import utils.display as display


if __name__ == "__main__":
    connection = sqlite3.connect("cell-count.db")
    cursor = connection.cursor()

    get_population_data_query = "SELECT * FROM populations_summary ORDER BY sample;"
    dfPopulation = display.get_data(get_population_data_query, connection)

    st.title("Data Overview")

    display.display_paginated_dataframe(dfPopulation)


    


