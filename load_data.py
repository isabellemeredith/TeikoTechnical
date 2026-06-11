import sqlite3
import pandas as pd

import time
from pathlib import Path
import subprocess
import pdb

if __name__ == "__main__":
    csv_filepath = "./Data/cell-count.csv"
    db_filepath = "cell-count.db"

    try:
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        project_creation_query = """
            CREATE TABLE PROJECT (
                ProjectID VARCHAR(255) NOT NULL,
                Desc VARCHAR(255)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS PROJECT")
        cursor.execute(project_creation_query)


        # crossover trials change treatment partway through, put it in sample?
        # exists to cheaply locate subjects that fulfill a condition
        subject_creation_query = """
            CREATE TABLE SUBJECT (
                SubjectID VARCHAR(255) NOT NULL,
                Condition CHAR(25) NOT NULL,
                Age INT,
                Sex CHAR(1),
                Treatment VARCHAR(255),
                Response CHAR(1),
                Project VARCHAR(255),
                FOREIGN KEY(Project) REFERENCES PROJECT(ProjectID)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS SUBJECT")
        cursor.execute(subject_creation_query)

        sample_creation_query = """
            CREATE TABLE SAMPLE (
                SampleID VARCHAR(255) NOT NULL,
                SampleType VARCHAR(255) NOT NULL,
                Time_Since_Treatment CHAR(25) NOT NULL,
                b_Cell INT,
                cd8_T_Cell INT,
                cd4_T_Cell INT,
                nk_cell INT,
                monocyte INT,
                Subject VARCHAR(255) NOT NULL,
                Project VARCHAR(255),
                FOREIGN KEY(Subject) REFERENCES SUBJECT(SubjectID),
                FOREIGN KEY(Project) REFERENCES PROJECT(ProjectID)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS SAMPLE")
        cursor.execute(sample_creation_query)

        bulk_creation_query = """
            CREATE TABLE BULK (
                ProjectID VARCHAR(255) NOT NULL,
                SubjectID VARCHAR(255) NOT NULL,
                Condition CHAR(25) NOT NULL,
                Age INT,
                Sex CHAR(1),
                Treatment VARCHAR(255),
                Response CHAR(1),
                SampleID VARCHAR(255) NOT NULL,
                SampleType VARCHAR(255) NOT NULL,
                Time_Since_Treatment CHAR(25) NOT NULL,
                b_Cell INT,
                cd8_T_Cell INT,
                cd4_T_Cell INT,
                nk_cell INT,
                monocyte INT
            );
        """
        cursor.execute("DROP TABLE IF EXISTS BULK")
        cursor.execute(bulk_creation_query)
        
        try:
            # Attempting the sqlite CLI first as it is faster for large files
            start_import = time.time()
            db_name = Path(db_filepath).resolve()
            csv_file = Path(csv_filepath).resolve()
            if not csv_file.exists():
                raise Exception("No such file or directory: {}".format(csv_file))
            result = subprocess.run(['sqlite3',
                                    str(db_name),
                                    '-cmd',
                                    '.mode csv',
                                    '.import --skip 1 ' + str(csv_file)
                                            +' BULK'],
                                    capture_output=True)
            end_import = time.time()
            cursor.execute("SELECT COUNT(*) FROM BULK")
            result = cursor.fetchall()
            print(result[0][0])
            print("Time for import load: {}".format(end_import - start_import))
        except:
            # If this fails then attempt the Pandas to_sql instead
            # May remove this later but there seems to be a potential issue with windows filepaths using the CLI import
            # that I haven't been able to test
            # but wouldn't affect the pandas method
            start_pandas = time.time()
            table_name = "BULK"
            pd.read_csv(csv_filepath).to_sql(table_name, conn, if_exists='delete_rows', index=False)
            end_pandas = time.time()
            cursor.execute("SELECT * FROM BULK")
            result = cursor.fetchall()
            print(result)
            print("Time for Pandas load: {}".format(end_pandas - start_pandas))

        print("Database setup complete")

        # project_insertion_query = """
        #     INSERT INTO PROJECT (ProjectID) SELECT DISTINCT ProjectID FROM BULK;
        # """
        # cursor.execute(project_insertion_query)

        # subject_insertion_query = """
        #     INSERT INTO SUBJECT () VALUES ();
        # """

        # sample_insertion_query = """
        #     INSERT INTO SAMPLE () VALUES ();
        # """

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
