import streamlit as st
import pandas as pd
import sqlite3


@st.cache_data()
def get_data(data_query, _connection):
    df = pd.read_sql_query(data_query, _connection)
    return df

@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

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
    dfPopulation = get_data(get_population_data_query, connection)

    print(dfPopulation.head())

    st.title("Data Overview")

    # st.dataframe(dfPopulation)

    top_menu = st.columns(3)
    with top_menu[0]:
        sort = st.radio("Sort Data", options=["Yes", "No"], horizontal=1, index=1)
    if sort == "Yes":
        with top_menu[1]:
            sort_field = st.selectbox("Sort By", options=dfPopulation.columns)
        with top_menu[2]:
            sort_direction = st.radio(
                "Direction", options=["Asc", "Desc"], horizontal=True
            )
        dfPopulation = dfPopulation.sort_values(
            by=sort_field, ascending=sort_direction == "Asc", ignore_index=True
        )
    pagination = st.container()

    bottom_menu = st.columns((4, 1, 1))
    with bottom_menu[2]:
        batch_size = st.selectbox("Page Size", options=[25, 50, 100, 500, "All"])
        if batch_size == "All":
            batch_size = len(dfPopulation)
            
    with bottom_menu[1]:
        total_pages = (
            int(len(dfPopulation) / batch_size) if int(len(dfPopulation) / batch_size) > 0 else 1
        )
        if ( batch_size * total_pages ) < len(dfPopulation):
            total_pages += 1
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1
        )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}** ")



    pages = split_frame(dfPopulation, batch_size)
    pagination.dataframe(data=pages[current_page - 1], width='stretch')


