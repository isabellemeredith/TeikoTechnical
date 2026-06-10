import sqlite3

if __name__ == "__main__":
    connection = sqlite3.connect("cell-count.db")
    cursor = connection.cursor()

    print("Database setup complete")