import streamlit as st
import pandas as pd
import sqlite3


@st.cache_data(scope="session")
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
        SELECT SampleIDName, 
               b_Cell + cd8_T_Cell + cd4_T_Cell + nk_cell + monocyte,
               CASE FROM SAMPLE;
    """

    summary_view_query = """
        SELECT *
        FROM 
        (
            SELECT SampleIDName, population,
            CASE population
            WHEN 'b_Cell' then b_Cell
            WHEN 'cd8_T_Cell' then cd8_T_Cell
            WHEN 'cd4_T_Cell' then cd4_T_Cell
            WHEN 'nk_cell' then nk_cell
            WHEN 'monocyte' then monocyte
            END AS count
        FROM SAMPLE
        CROSS JOIN (VALUES('b_Cell'),('cd8_T_Cell'),('cd4_T_Cell'),('nk_cell'),('monocyte')) AS Pop(Population)
        ) AS D
        WHERE count IS NOT NULL;
    """

    

    # summary_view_query = """
    #     SELECT SampleIDName AS sample, population,
    #         CASE t.column1 
    #             WHEN 'b_Cell' then b_Cell
    #             WHEN 'cd8_T_Cell' then cd8_T_Cell
    #             WHEN 'cd4_T_Cell' then cd4_T_Cell
    #             WHEN 'nk_cell' then nk_cell
    #             WHEN 'monocyte' then monocyte
    #         END AS population,
    #         CASE t.column1 WHEN 'b_Cell' then b_Cell.value1 WHEN 2 THEN  original_table.value2 WHEN 3 THEN  original_table.value3 ELSE  original_table.value4 END AS value

    #     from SAMPLE
    #     JOIN (VALUES('b_Cell'),('cd8_T_Cell'),('cd4_T_Cell'),('nk_cell'),('monocyte')) t
    #     )as D
    #     where marks is not null;
    # """

    summary_view_query = """
        SELECT original_table._id,
          CASE t.column1 WHEN 1 THEN 'value1' WHEN 2 THEN 'value2' WHEN 3 THEN 'value3' ELSE 'value4' END AS name, 
          CASE t.column1 WHEN 1 THEN  original_table.value1 WHEN 2 THEN  original_table.value2 WHEN 3 THEN  original_table.value3 ELSE  original_table.value4 END AS value
        FROM (
        select 1 _id, 10 value1 , 11 value2 , "string value" value3 , 13 value4
        union all 
        select 2, 14,  "string value",null,17
        ) original_table
        JOIN (VALUES(1),(2),(3),(4)) t
    """

    summary_view_query = """
        SELECT * FROM SAMPLE JOIN (VALUES('b_Cell'),('cd8_T_Cell'),('cd4_T_Cell'),('nk_cell'),('monocyte')) t
    """

    summary_view_query = """
        CREATE VIEW populations 
        AS
        SELECT sample, population, total_count, count, 1.0 * count / total_count AS percentage FROM (
        SELECT SampleIDName AS sample, b_Cell + cd8_T_Cell + cd4_T_Cell + nk_cell + monocyte AS total_count, 'b_Cell' AS population,  b_Cell AS count FROM SAMPLE
        UNION ALL
        SELECT SampleIDName AS sample, b_Cell + cd8_T_Cell + cd4_T_Cell + nk_cell + monocyte AS total_count, 'cd8_T_Cell' AS population, cd8_T_Cell AS count FROM SAMPLE
        UNION ALL
        SELECT SampleIDName AS sample, b_Cell + cd8_T_Cell + cd4_T_Cell + nk_cell + monocyte AS total_count, 'cd4_T_Cell' AS population, cd4_T_Cell AS count FROM SAMPLE
        UNION ALL
        SELECT SampleIDName AS sample, b_Cell + cd8_T_Cell + cd4_T_Cell + nk_cell + monocyte AS total_count, 'nk_cell' AS population, nk_cell AS count FROM SAMPLE
        UNION ALL
        SELECT SampleIDName AS sample, b_Cell + cd8_T_Cell + cd4_T_Cell + nk_cell + monocyte AS total_count, 'monocyte' AS population, monocyte AS count FROM SAMPLE);
    """
    
    # cursor.execute("SELECT * FROM populations ORDER BY sample")
    # result = cursor.fetchall()
    # print(result)
    get_population_data_query = "SELECT * FROM populations ORDER BY sample;"
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


