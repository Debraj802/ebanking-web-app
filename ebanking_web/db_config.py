import mysql.connector
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="**************",
        database="2f!78%^@#"
    )