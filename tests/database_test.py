import pytest
import sqlite3

class TestDatabaseSize:
    # Testing that we get the table sizes we expect to see given the input data
    def test_n_projects(self):
        database_name = "cell-count.db"
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM PROJECT;")
        n_projects = cursor.fetchone()[0]
        assert n_projects == 3

    def test_n_subjects(self):
        database_name = "cell-count.db"
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM SUBJECT;")
        n_subjects = cursor.fetchone()[0]
        assert n_subjects == 3500

    def test_n_samples(self):
        database_name = "cell-count.db"
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM SAMPLE;")
        n_samples = cursor.fetchone()[0]
        assert n_samples == 10500

    def test_n_populations(self):
        database_name = "cell-count.db"
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM POPULATION;")
        n_populations = cursor.fetchone()[0]
        assert n_populations == 52500
