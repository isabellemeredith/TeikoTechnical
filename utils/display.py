import streamlit as st
import pandas as pd


@st.cache_data()
def get_data(data_query, _connection):
    """Take a SQLite query and database connection and return a Pandas dataframe of the results 

    Keyword arguments:
    conn -- SQLite database connection
    """
    df = pd.read_sql_query(data_query, _connection)
    return df

@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    """Return a list of subsets of a dataframe 

    Keyword arguments:
    input_df - Pandas dataframe to be subset
    rows - number of rows per subset
    """
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

def display_paginated_dataframe(data):
    """Display a paginated dataframe using Streamlit

    Keyword arguments:
    data - Pandas dataframe to be displayed
    """
    top_menu = st.columns(3)
    with top_menu[0]:
        sort = st.radio("Sort Data", options=["Yes", "No"], horizontal=1, index=1)
    if sort == "Yes":
        with top_menu[1]:
            sort_field = st.selectbox("Sort By", options=data.columns)
        with top_menu[2]:
            sort_direction = st.radio(
                "Direction", options=["Asc", "Desc"], horizontal=True
            )
        data = data.sort_values(
            by=sort_field, ascending=sort_direction == "Asc", ignore_index=True
        )
    pagination = st.container()

    bottom_menu = st.columns((4, 1, 1))
    with bottom_menu[2]:
        batch_size = st.selectbox("Page Size", options=[25, 50, 100, 500, "All"])
        if batch_size == "All":
            batch_size = len(data)
            
    with bottom_menu[1]:
        total_pages = (
            int(len(data) / batch_size) if int(len(data) / batch_size) > 0 else 1
        )
        if ( batch_size * total_pages ) < len(data):
            total_pages += 1
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1
        )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}** ")



    pages = split_frame(data, batch_size)
    pagination.dataframe(data=pages[current_page - 1], width='stretch')