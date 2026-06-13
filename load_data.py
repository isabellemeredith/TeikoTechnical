import sqlite3
import pandas as pd
import os

from pathlib import Path
import subprocess
import csv


def setup_tables(conn):
    cursor = conn.cursor()

    # Include a project description column despite it missing from the data for scalability
    project_creation_query = """
        CREATE TABLE PROJECT (
            project_id INTEGER PRIMARY KEY NOT NULL,
            project_id_text VARCHAR(255) NOT NULL,
            principal_investigator VARCHAR(255),
            company VARCHAR(255),
            description VARCHAR(255)
        );
    """

    cursor.execute("DROP TABLE IF EXISTS PROJECT")
    cursor.execute(project_creation_query)


    # crossover trials change treatment partway through, put it in sample?
    # exists to cheaply locate subjects that fulfill a condition
    subject_creation_query = """
        CREATE TABLE SUBJECT (
            subject_id INTEGER PRIMARY KEY NOT NULL,
            subject_id_text VARCHAR(255) NOT NULL,
            condition CHAR(25) NOT NULL,
            age INT,
            sex CHAR(1),
            treatment VARCHAR(255),
            response CHAR(1),
            project_id_text VARCHAR(255),
            project_id INTEGER,
            FOREIGN KEY(project_id) REFERENCES PROJECT(project_id)
        );
    """

    cursor.execute("DROP TABLE IF EXISTS SUBJECT")
    cursor.execute(subject_creation_query)

    sample_creation_query = """
        CREATE TABLE SAMPLE (
            sample_id INTEGER PRIMARY KEY NOT NULL,
            sample_id_text VARCHAR(255) NOT NULL,
            sample_type VARCHAR(255) NOT NULL,
            time_from_treatment_start CHAR(25) NOT NULL,
            subject_id_text VARCHAR(255) NOT NULL,
            project_id_text VARCHAR(255),
            subject_id INTEGER,
            project_id INTEGER,
            FOREIGN KEY(subject_id) REFERENCES SUBJECT(subject_id),
            FOREIGN KEY(project_id) REFERENCES PROJECT(project_id)
        );
    """

    cursor.execute("DROP TABLE IF EXISTS SAMPLE")
    cursor.execute(sample_creation_query)

    population_creation_query = """
        CREATE TABLE POPULATION (
            population_id INTEGER PRIMARY KEY NOT NULL,
            population_name VARCHAR(255) NOT NULL,
            count INT,
            sample_id_text VARCHAR(255),
            subject_id_text VARCHAR(255) NOT NULL,
            project_id_text VARCHAR(255),
            sample_id INTEGER,
            subject_id INTEGER,
            project_id INTEGER,
            FOREIGN KEY(sample_id) REFERENCES SAMPLE(sample_id),
            FOREIGN KEY(subject_id) REFERENCES SUBJECT(subject_id),
            FOREIGN KEY(project_id) REFERENCES PROJECT(project_id)
        );
    """

    cursor.execute("DROP TABLE IF EXISTS POPULATION")
    cursor.execute(population_creation_query)

    conn.commit()

if __name__ == "__main__":
    csv_filepath = "./data/cell-count.csv"
    db_filepath = "cell-count.db"

    if os.path.exists(db_filepath):
        os.remove(db_filepath)

    try:
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        setup_tables(conn)

        dfBulk = pd.read_csv(csv_filepath).rename(columns={"project": "project_id_text", "subject": "subject_id_text", "sample": "sample_id_text"})
        print(dfBulk.head())

        dfProject = pd.DataFrame({"project_id_text": dfBulk["project_id_text"].unique(), "principal_investigator": "Bob Loblaw", "company": "Loblaw Bio"})
        dfProject.to_sql("PROJECT", conn, if_exists='append', index=False, method="multi")

        dfBulk[["subject_id_text", "condition", "age", "sex", "treatment", "response", "project_id_text"]].to_sql("SUBJECT", conn, if_exists='append', index=False, method="multi")

        dfBulk[["sample_id_text", "sample_type", "time_from_treatment_start", "subject_id_text", "project_id_text"]].to_sql("SAMPLE", conn, if_exists='append', index=False, method="multi")

        dfBulk[["sample_id_text", "subject_id_text", "project_id_text", "b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]].melt(id_vars=["sample_id_text", "subject_id_text", "project_id_text"], value_vars=["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"], var_name="population_name", value_name="count").to_sql("POPULATION", conn, if_exists='append', index=False)
        
        print("Linking new primary keys. This may take a while.")

        link_project_keys_subject_query = """
            UPDATE SUBJECT 
            SET project_id = (SELECT project_id FROM PROJECT
                                                WHERE SUBJECT.project_id_text = PROJECT.project_id_text);
        """
        cursor.execute(link_project_keys_subject_query)

        link_project_keys_sample_query = """
            UPDATE SAMPLE 
            SET project_id = (SELECT project_id FROM PROJECT
                                                WHERE SAMPLE.project_id_text = PROJECT.project_id_text);
        """
        cursor.execute(link_project_keys_sample_query)

        link_subject_keys_sample_query = """
            UPDATE SAMPLE 
            SET subject_id = (SELECT subject_id FROM SUBJECT
                                                WHERE SAMPLE.subject_id_text = SUBJECT.subject_id_text
                                                AND SAMPLE.project_id = SUBJECT.project_id);
        """
        cursor.execute(link_subject_keys_sample_query)

        link_project_keys_population_query = """
            UPDATE POPULATION 
            SET project_id = (SELECT project_id FROM PROJECT
                                                WHERE POPULATION.project_id_text = PROJECT.project_id_text);
        """
        cursor.execute(link_project_keys_population_query)

        link_subject_keys_population_query = """
            UPDATE POPULATION 
            SET subject_id = (SELECT subject_id FROM SUBJECT
                                                WHERE POPULATION.subject_id_text = SUBJECT.subject_id_text
                                                AND POPULATION.project_id = SUBJECT.project_id);
        """
        cursor.execute(link_subject_keys_population_query)

        link_sample_keys_population_query = """
            UPDATE POPULATION 
            SET sample_id = (SELECT sample_id FROM SAMPLE
                                                WHERE POPULATION.sample_id_text = SAMPLE.sample_id_text
                                                AND POPULATION.subject_id = SAMPLE.subject_id
                                                AND POPULATION.project_id = SAMPLE.project_id);
        """
        cursor.execute(link_sample_keys_population_query)


        conn.commit()

        print("Database setup complete")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
