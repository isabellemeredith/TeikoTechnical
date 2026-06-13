import pandas as pd
import sqlite3
import statsmodels.formula.api as smf
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns


def create_summary_view(conn):
    """Get the frequency of each cell type for each sample and save it as a view for future analysis

    Keyword arguments:
    conn -- SQLite database connection
    """
    cursor = conn.cursor()
    summary_view_query = """
        CREATE VIEW populations_summary 
        AS
        SELECT sample_id_text AS sample, population_name AS population, SUM(count) OVER (PARTITION BY sample_id) AS total_count, count, 100.0 * count / SUM(count) OVER (PARTITION BY sample_id) AS percentage FROM POPULATION;
    """
    cursor.execute("DROP VIEW IF EXISTS populations_summary;")
    cursor.execute(summary_view_query)

def create_analysis_view(conn):
    """Get the melanoma miraclib data subset and save it as a view for future analysis

    Keyword arguments:
    conn -- SQLite database connection
    """
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

def create_project_view(conn):
    """Get the subject and sample level summary for subset analysis and save it as a view for future analysis

    Keyword arguments:
    conn -- SQLite database connection
    """
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

def get_responder_diff(df, multiple_comparisons = 1.0):
    """Fit linear mixed effects models for the relationship between Miraclib response and cell population type
    Keyword arguments:
    df -- Pandas dataframe
    multiple_comparisons - float to multiply the significance threshold by to adjust for multiple comparisons. Default 1.0 for no adjustment
    """
    df["binary_response"] = df['response'].map({'yes':1, 'no':0})
    df["binary_sex"] = df['sex'].map({'M':1, 'F':0})

    populations = df["population_name"].unique()
    n_populations = len(populations)
    dfResults = pd.DataFrame({"population_name": populations, "coef": 0.0, "p_value": 0.0, "significant": False})
    dfResults.set_index("population_name", inplace=True)
    for population in populations:
        data = df.loc[df["population_name"] == population]

        model = smf.mixedlm("percentage ~ binary_response", data, groups=data["sample_id"])
        model_fit = model.fit(method=["lbfgs", "Nelder-Mead", "Newton-CG"])

        coef = model_fit.fe_params["binary_response"]
        dfResults.at[population, "coef"] = coef
        p_value = model_fit.pvalues["binary_response"]
        dfResults.at[population, "p_value"] = p_value
        significant = (multiple_comparisons * p_value) < 0.05
        dfResults.at[population, "significant"] = significant 
    return dfResults

def get_responder_summary(conn):
    """Get the summary statistics for Miraclib responsers

    Keyword arguments:
    conn -- SQLite database connection
    """
    responder_query = """
        SELECT population_name, response, AVG(percentage), MIN(percentage), MAX(percentage), COUNT(percentage) 
        FROM analysis
        GROUP BY response, population_name
        ORDER BY population_name;
    """
    df = pd.read_sql_query(responder_query, conn)
    return df
    
def get_population_fig(df, selected_rows=slice(None), 
                       population_dict = {"b_cell" : "B Cell", "cd4_t_cell": "CD4 T Cell", "cd8_t_cell": "CD8 T Cell", "nk_cell": "NK Cell", "monocyte": "Monocyte"},
                       use_plotly=True):
    """Produce a figure of boxplots comparing responders and nonresponders by cell population count. 
    Returns a plotly plot by default or a seaborn plot if plotly disabed

    Keyword arguments:
    df -- Pandas dataframe to be summarized
    selected_rows - Pandas slice to subset data. Default selects the entire dataframe
    population_dict - dictionary for nice population name formatting
    use_plotly - whether to return a plotly or seaborn plot
    """
    if use_plotly:
        fig = px.box(df.loc[selected_rows].replace(population_dict), x="population_name", y="percentage", color="response", 
                 title="Relative Cell Population Percentage of Sample by Response to Miraclib in Melanoma Patients", 
                 labels={"population_name": "Cell Population Name", "percentage": "Percentage", "response": "Responded to Miraclib"})
    else:
        boxplot = sns.boxplot(x="population_name",y="percentage",data=df.loc[selected_rows].replace(population_dict).replace({"yes": "responder", "no": "nonresponder"}),hue="response")
        boxplot.set(title="Relative Cell Population Percentage of Sample by\nResponse to Miraclib in Melanoma Patients", xlabel="Cell Population Name", ylabel="Percentage")
        fig = boxplot.get_figure()

    return fig

def get_counts(df, selection):
    """Get value counts for a dataframe

    Keyword arguments:
    df - Pandas dataframe
    selection - Columns to get value counts from
    """
    dfCounts = df[selection].value_counts()
    return dfCounts

def get_melanoma_male_avg(conn):
    """Get the average number of B cells for melanoma males who were responders at time=0

    Keyword arguments:
    conn -- SQLite database connection
    """
    cursor = conn.cursor()
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
    result = round(cursor.fetchone()[0], 2)
    return result

if __name__ == "__main__":
    database_name = "cell-count.db"
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # part 2 analysis
    create_summary_view(conn)
    get_summary_data_query = "SELECT * FROM populations_summary;"
    dfSummary = pd.read_sql_query(get_summary_data_query, conn)
    dfSummary.to_csv("./output/summary.csv")

    # part 3 analysis
    create_analysis_view(conn)
    get_analysis_data_query = "SELECT * FROM analysis;"
    dfAnalysis = pd.read_sql_query(get_analysis_data_query, conn)
    dfAnalysis.to_csv("./output/miraclib_melanoma_subset.csv")

    dfResponderSummary = get_responder_summary(conn)
    dfResponderSummary.to_csv("./output/miraclib_response_summary.csv")

    fig = get_population_fig(dfAnalysis, use_plotly=False)
    fig.savefig("./output/population-percentages.png")

    dfResults = get_responder_diff(dfAnalysis)
    dfResults.to_csv("./output/miraclib_response_analysis_results.csv")

    # part 4 analysis
    create_project_view(conn)
    get_project_data_query = "SELECT * FROM projects_summary ORDER BY project_id_text;"
    dfProjects = pd.read_sql_query(get_project_data_query, conn)
    dfProjects.to_csv("./output/miraclib_melanoma_baseline_subset.csv")

    project_counts = get_counts(dfProjects, "project_id_text")
    project_counts.to_csv("./output/miraclib_melanoma_baseline_project_counts.csv")

    dfProjectsSubjectLevel = dfProjects.drop_duplicates(subset="subject_id_text")
    sex_counts = get_counts(dfProjectsSubjectLevel, "sex")
    sex_counts.to_csv("./output/miraclib_melanoma_baseline_sex_counts.csv")
    response_counts = get_counts(dfProjectsSubjectLevel, "response")
    response_counts.to_csv("./output/miraclib_melanoma_baseline_response_counts.csv")

    
    print("Average number of B cells for melanoma males who were responders at time=0:", get_melanoma_male_avg(conn))