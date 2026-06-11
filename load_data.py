import sqlite3
import pandas as pd

from pathlib import Path
import subprocess

if __name__ == "__main__":
    csv_filepath = "./Data/cell-count.csv"
    db_filepath = "cell-count.db"

    try:
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        # Include a project description column despite it missing from the data for scalability
        project_creation_query = """
            CREATE TABLE PROJECT (
                ProjectID INTEGER PRIMARY KEY NOT NULL,
                ProjectIDName VARCHAR(255) NOT NULL,
                Desc VARCHAR(255)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS PROJECT")
        cursor.execute(project_creation_query)


        # crossover trials change treatment partway through, put it in sample?
        # exists to cheaply locate subjects that fulfill a condition
        subject_creation_query = """
            CREATE TABLE SUBJECT (
                SubjectID INTEGER PRIMARY KEY NOT NULL,
                SubjectIDName VARCHAR(255) NOT NULL,
                Condition CHAR(25) NOT NULL,
                Age INT,
                Sex CHAR(1),
                Treatment VARCHAR(255),
                Response CHAR(1),
                ProjectIDName VARCHAR(255),
                ProjectID INTEGER,
                FOREIGN KEY(ProjectID) REFERENCES PROJECT(ProjectID)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS SUBJECT")
        cursor.execute(subject_creation_query)

        sample_creation_query = """
            CREATE TABLE SAMPLE (
                SampleID INTEGER PRIMARY KEY NOT NULL,
                SampleIDName VARCHAR(255) NOT NULL,
                SampleType VARCHAR(255) NOT NULL,
                Time_Since_Treatment CHAR(25) NOT NULL,
                b_Cell INT,
                cd8_T_Cell INT,
                cd4_T_Cell INT,
                nk_cell INT,
                monocyte INT,
                SubjectIDName VARCHAR(255) NOT NULL,
                ProjectIDName VARCHAR(255),
                SubjectID INTEGER,
                ProjectID INTEGER,
                FOREIGN KEY(SubjectID) REFERENCES SUBJECT(SubjectID),
                FOREIGN KEY(ProjectID) REFERENCES PROJECT(ProjectID)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS SAMPLE")
        cursor.execute(sample_creation_query)

        bulk_creation_query = """
            CREATE TABLE BULK (
                ProjectIDName VARCHAR(255) NOT NULL,
                SubjectIDName VARCHAR(255) NOT NULL,
                Condition CHAR(25) NOT NULL,
                Age INT,
                Sex CHAR(1),
                Treatment VARCHAR(255),
                Response CHAR(1),
                SampleIDName VARCHAR(255) NOT NULL,
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
        except:
            # If this fails then attempt the Pandas to_sql instead
            # May remove this later but there seems to be a potential issue with windows filepaths using the CLI import
            # that I haven't been able to test
            # but wouldn't affect the pandas method
            table_name = "BULK"
            pd.read_csv(csv_filepath).to_sql(table_name, conn, if_exists='delete_rows', index=False)


        project_insertion_query = """
            INSERT INTO PROJECT (ProjectIDName) SELECT DISTINCT ProjectIDName FROM BULK;
        """
        cursor.execute(project_insertion_query)

        subject_insertion_query = """
            INSERT INTO SUBJECT (SubjectIDName, Condition, Age, Sex, Treatment, Response, ProjectIDName, ProjectID) 
            SELECT SubjectIDName, Condition, Age, Sex, Treatment, Response, BULK.ProjectIDName, ProjectID
            FROM BULK INNER JOIN PROJECT 
            ON PROJECT.ProjectIDName = BULK.ProjectIDName
            GROUP BY SubjectIDName, BULK.ProjectIDName;
        """

        cursor.execute(subject_insertion_query)

        sample_insertion_query = """
            INSERT INTO SAMPLE (SampleIDName, SampleType, Time_Since_Treatment, b_Cell, cd8_T_Cell, cd4_T_Cell, nk_cell, monocyte, SubjectIDName, ProjectIDName, SubjectID, ProjectID) 
            SELECT SampleIDName, SampleType, Time_Since_Treatment, b_Cell, cd8_T_Cell, cd4_T_Cell, nk_cell, monocyte, BULK.SubjectIDName, BULK.ProjectIDName, SubjectID, ProjectID
            FROM BULK INNER JOIN SUBJECT 
            ON SUBJECT.SubjectIDName = BULK.SubjectIDName
            AND SUBJECT.ProjectIDName = BULK.ProjectIDName;
        """

        cursor.execute(sample_insertion_query)

        cursor.execute("DROP TABLE IF EXISTS BULK")

        conn.commit()

        print("Database setup complete")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
