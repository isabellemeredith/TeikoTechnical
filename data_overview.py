import streamlit as st
import sqlite3

if __name__ == "__main__":
    connection = sqlite3.connect("cell-count.db")
    cursor = connection.cursor()

    st.title("Data Overview")

    
