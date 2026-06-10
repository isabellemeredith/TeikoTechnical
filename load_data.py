import sqlite3
import pdb

if __name__ == "__main__":
    try:
        conn = sqlite3.connect("cell-count.db")
        cursor = conn.cursor()

        project_creation_query = """
            CREATE TABLE PROJECT (
                ProjectID VARCHAR(255) NOT NULL,
                Desc VARCHAR(255)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS PROJECT")
        cursor.execute(project_creation_query)

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
                FOREIGN KEY(Subject) REFERENCES SUBJECT(SubjectID)
            );
        """

        cursor.execute("DROP TABLE IF EXISTS SAMPLE")
        cursor.execute(sample_creation_query)

        print("Database setup complete")

        # project_insertion_query = """
        #     INSERT INTO PROJECT () VALUES ();
        # """

        # subject_insertion_query = """
        #     INSERT INTO SUBJECT () VALUES ();
        # """

        # sample_insertion_query = """
        #     INSERT INTO SAMPLE () VALUES ();
        # """

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        if conn:
            conn.close()
