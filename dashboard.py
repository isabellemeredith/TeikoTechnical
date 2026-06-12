import streamlit as st

if __name__ == "__main__":
    data_overview = st.Page("./pages/data_overview.py", title="Data Overview") # , icon="🎈"
    statistical_analysis = st.Page("./pages/statistical_analysis.py", title="Analysis") # , icon="❄️"
    subset_analysis = st.Page("./pages/subset_analysis.py", title="Subset Analysis") # , icon="🎉"

    # Set up navigation
    pg = st.navigation([data_overview, statistical_analysis, subset_analysis])

    # Run the selected page
    pg.run()