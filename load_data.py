import sqlite3
import pandas as pd
import os

from pathlib import Path
import subprocess
import csv


if __name__ == "__main__":
    csv_filepath = "./Data/cell-count.csv"
    db_filepath = "cell-count.db"

    if os.path.exists(db_filepath):
        os.remove(db_filepath)

    try:
        conn = sqlite3.connect(db_filepath)
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

        cursor.execute("DROP TABLE IF EXISTS POPULATIon")
        cursor.execute(population_creation_query)

        # bulk_creation_query = """
        #     CREATE TABLE BULK (
        #         project_id_text VARCHAR(255) NOT NULL,
        #         subject_id_text VARCHAR(255) NOT NULL,
        #         condition CHAR(25) NOT NULL,
        #         age INT,
        #         sex CHAR(1),
        #         treatment VARCHAR(255),
        #         response CHAR(1),
        #         sample_id_text VARCHAR(255) NOT NULL,
        #         sample_type VARCHAR(255) NOT NULL,
        #         time_from_treatment_start CHAR(25) NOT NULL,
        #         b_Cell INT,
        #         cd8_T_Cell INT,
        #         cd4_T_Cell INT,
        #         nk_cell INT,
        #         monocyte INT
        #     );
        # """
        # cursor.execute("DROP TABLE IF EXISTS BULK")
        # cursor.execute(bulk_creation_query)
        
        # try:
        #     # Attempting the sqlite CLI first as it is faster for large files
        #     db_name = Path(db_filepath).resolve()
        #     csv_file = Path(csv_filepath).resolve()
        #     if not csv_file.exists():
        #         raise Exception("No such file or directory: {}".format(csv_file))
        #     result = subprocess.run(['sqlite3',
        #                             str(db_name),
        #                             '-cmd',
        #                             '.mode csv',
        #                             '.import --skip 1 ' + str(csv_file)
        #                                     +' BULK'],
        #                             capture_output=True)
        # except:
        #     # If this fails then attempt the Pandas to_sql instead
        #     # May remove this later but there seems to be a potential issue with windows filepaths using the CLI import
        #     # that I haven't been able to test
        #     # but wouldn't affect the pandas method
        #     table_name = "BULK"
        #     pd.read_csv(csv_filepath).to_sql(table_name, conn, if_exists='delete_rows', index=False)

        dfBulk = pd.read_csv(csv_filepath).rename(columns={"project": "project_id_text", "subject": "subject_id_text", "sample": "sample_id_text"})
        print(dfBulk.head())

        dfProject = pd.DataFrame({"project_id_text": dfBulk["project_id_text"].unique(), "principal_investigator": "Bob Loblaw", "company": "Loblaw Bio"})
        dfProject.to_sql("PROJECT", conn, if_exists='append', index=False, method="multi")

        dfBulk[["subject_id_text", "condition", "age", "sex", "treatment", "response", "project_id_text"]].to_sql("SUBJECT", conn, if_exists='append', index=False, method="multi")

        dfBulk[["sample_id_text", "sample_type", "time_from_treatment_start", "subject_id_text", "project_id_text"]].to_sql("SAMPLE", conn, if_exists='append', index=False, method="multi")

        dfBulk[["sample_id_text", "subject_id_text", "project_id_text", "b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]].melt(id_vars=["sample_id_text", "subject_id_text", "project_id_text"], value_vars=["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"], var_name="population_name", value_name="count").to_sql("POPULATION", conn, if_exists='append', index=False)
        


        # use csv reader
        # with open(csv_filepath, 'r') as csv_file:
        #     csv_reader = csv.reader(csv_file)
        #     for row in csv_reader:

        #         cursor.execute('INSERT INTO my_table VALUES (?, ?)', row)

        # project_insertion_query = """
        #     INSERT INTO PROJECT (project_id_text, principal_investigator, company) SELECT DISTINCT project_id_text, "Bob Loblaw", "Loblaw Bio" FROM BULK;
        # """
        # cursor.execute(project_insertion_query)

        # subject_insertion_query = """
        #     INSERT INTO SUBJECT (subject_id_text, condition, age, sex, treatment, response, project_id_text, project_id) 
        #     SELECT subject_id_text, condition, age, sex, treatment, response, BULK.project_id_text, project_id
        #     FROM BULK INNER JOIN PROJECT 
        #     ON PROJECT.project_id_text = BULK.project_id_text
        #     GROUP BY subject_id_text, BULK.project_id_text;
        # """

        # cursor.execute(subject_insertion_query)

        # sample_insertion_query = """
        #     INSERT INTO SAMPLE (sample_id_text, sample_type, time_from_treatment_start, b_Cell, cd8_T_Cell, cd4_T_Cell, nk_cell, monocyte, subject_id_text, project_id_text, subject_id, project_id) 
        #     SELECT sample_id_text, sample_type, time_from_treatment_start, b_Cell, cd8_T_Cell, cd4_T_Cell, nk_cell, monocyte, BULK.subject_id_text, BULK.project_id_text, subject_id, project_id
        #     FROM BULK INNER JOIN SUBJECT 
        #     ON SUBJECT.subject_id_text = BULK.subject_id_text
        #     AND SUBJECT.project_id_text = BULK.project_id_text;
        # """

        # cursor.execute(sample_insertion_query)

        # population_insertion_query = """
        #     INSERT INTO POPULATION (population_name, count, sample_id_text, subject_id_text, project_id_text, sample_id, subject_id, project_id) 
        #     SELECT population_name, population, total_count, count, 1.0 * count / total_count AS percentage FROM (
        #     SELECT population_name, sample_id_text, subject_id_text, sample_id, subject_id, project_id, 'b_Cell' AS population, b_Cell AS count FROM BULK
        #     UNION ALL
        #     SELECT population_name, sample_id_text, subject_id_text, sample_id, subject_id, project_id, 'cd8_T_Cell' AS population, cd8_T_Cell AS count FROM BULK
        #     UNION ALL
        #     SELECT population_name, sample_id_text, subject_id_text, sample_id, subject_id, project_id, 'cd4_T_Cell' AS population, cd4_T_Cell AS count FROM BULK
        #     UNION ALL
        #     SELECT population_name, sample_id_text, subject_id_text, sample_id, subject_id, project_id, 'nk_cell' AS population, nk_cell AS count FROM BULK
        #     UNION ALL
        #     SELECT population_name, sample_id_text, subject_id_text, sample_id, subject_id, project_id, 'monocyte' AS population, monocyte AS count FROM BULK);
        # """

        

        # cursor.execute("DROP TABLE IF EXISTS BULK")

        conn.commit()

        print("Database setup complete")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
