import pandas as pd
import sqlite3
import statsmodels.formula.api as smf
import plotly.express as px


def get_data(data_query, _connection):
    df = pd.read_sql_query(data_query, _connection)
    return df

def create_summary_view(conn):
    cursor = conn.cursor()
    summary_view_query = """
        CREATE VIEW populations_summary 
        AS
        SELECT sample_id_text AS sample, population_name AS population, SUM(count) OVER (PARTITION BY sample_id) AS total_count, count, 100.0 * count / SUM(count) OVER (PARTITION BY sample_id) AS percentage FROM POPULATION;
    """
    cursor.execute("DROP VIEW IF EXISTS populations_summary;")
    cursor.execute(summary_view_query)

def create_analysis_view(conn):
    cursor = conn.cursor()
    analysis_view_query = """
        CREATE VIEW analysis 
        AS
        SELECT population_id, POPULATION.sample_id, POPULATION.sample_id_text, population_name, SUM(count) OVER (PARTITION BY POPULATION.sample_id) AS total_count, count, 100.0 * count / SUM(count) OVER (PARTITION BY POPULATION.sample_id) AS percentage, condition, response, sample_type, treatment, time_from_treatment_start, age, sex
        FROM (POPULATION JOIN SAMPLE 
        ON POPULATION.sample_id = SAMPLE.sample_id
        JOIN SUBJECT
        ON SAMPLE.subject_id = SUBJECT.subject_id) 
        WHERE sample_type = "PBMC"
        AND condition = "melanoma"
        AND treatment = "miraclib"
        AND response IS NOT NULL;
    """

    cursor.execute("DROP VIEW IF EXISTS analysis;")
    cursor.execute(analysis_view_query)

def get_population_fig(dfAnalysis, selected_rows, 
                       population_dict = {"b_cell" : "B Cell", "cd4_t_cell": "CD4 T Cell", "cd8_t_cell": "CD8 T Cell", "nk_cell": "NK Cell", "monocyte": "Monocyte"}):
    fig = px.box(dfAnalysis.loc[selected_rows].replace(population_dict), x="population_name", y="percentage", color="response", 
                 title="Relative Cell Population Percentages by Response to Miraclib in Melanoma Patients", 
                 labels={"population_name": "Cell Population Name", "percentage": "Percentage", "response": "Responded to Miraclib"})
    return fig

def create_project_view(conn):
    cursor = conn.cursor()
    project_view_query = """
        CREATE VIEW projects_summary 
        AS
        SELECT sample_id, sample_id_text, SUBJECT.subject_id, SUBJECT.subject_id_text, SUBJECT.project_id_text, response, sex, sample_type, condition, treatment, time_from_treatment_start
        FROM SUBJECT
        JOIN SAMPLE ON SAMPLE.subject_id = SUBJECT.subject_id
        WHERE sample_type = "PBMC"
        AND condition = "melanoma"
        AND treatment = "miraclib"
        AND response IS NOT NULL
        AND time_from_treatment_start = 0;
    """
    cursor.execute("DROP VIEW IF EXISTS projects_summary;")
    cursor.execute(project_view_query)

def get_responder_diff(dfAnalysis, multiple_comparisons = 1.0):
    dfAnalysis["binary_response"] = dfAnalysis['response'].map({'yes':1, 'no':0})
    dfAnalysis["binary_sex"] = dfAnalysis['sex'].map({'M':1, 'F':0})

    populations = dfAnalysis["population_name"].unique()
    print(populations)
    n_populations = len(populations)
    dfResults = pd.DataFrame({"population_name": populations, "coef": 0.0, "p_value": 0.0, "significant": False})
    dfResults.set_index("population_name", inplace=True)
    for population in populations:
        data = dfAnalysis.loc[dfAnalysis["population_name"] == population]

        model = smf.mixedlm("percentage ~ binary_response", data, groups=data["sample_id"])
        model_fit = model.fit(method=["lbfgs", "Nelder-Mead", "Newton-CG"])

        coef = model_fit.fe_params["binary_response"]
        dfResults.at[population, "coef"] = coef
        p_value = model_fit.pvalues["binary_response"]
        dfResults.at[population, "p_value"] = p_value
        significant = (multiple_comparisons * p_value) < 0.05
        dfResults.at[population, "significant"] = significant 
    return dfResults


if __name__ == "__main__":
    conn = sqlite3.connect("cell-count.db")
    cursor = conn.cursor()

    create_summary_view(conn)
    get_summary_data_query = "SELECT * FROM populations_summary;"
    dfSummary = get_data(get_summary_data_query, conn)
    dfSummary.to_csv("./output/summary.csv")

    create_analysis_view(conn)
    get_analysis_data_query = "SELECT * FROM analysis;"
    dfAnalysis = get_data(get_analysis_data_query, conn)
    dfAnalysis.to_csv("./output/miraclib_melanoma_subset.csv")

    fig = get_population_fig(dfAnalysis, selected_rows = slice(None))
    fig.write_image("./output/population-percentages.png", width=1200, height=700)

    dfResults = get_responder_diff(dfAnalysis)
    dfResults.to_csv("./output/miraclib_response_analysis_results.csv")

    create_project_view(conn)
    get_project_data_query = "SELECT * FROM projects_summary ORDER BY project_id_text;"
    dfProjects = get_data(get_project_data_query, conn)
    dfProjects.to_csv("./output/miraclib_melanoma_baseline_subset.csv")

    get_part_five_average_query = """
        SELECT AVG(count)
        FROM POPULATION 
        JOIN SAMPLE ON POPULATION.sample_id = SAMPLE.sample_id
        JOIN SUBJECT ON SAMPLE.subject_id = SUBJECT.subject_id
        WHERE population_name = "b_cell"
        AND treatment = "miraclib"
        AND condition = "melanoma"
        AND response = "yes"
        AND sex = "M"
        AND time_from_treatment_start = 0;
    """
    cursor.execute(get_part_five_average_query)
    result = cursor.fetchall()
    print("Average number of B cells for melanoma males who were responders at time=0", result)