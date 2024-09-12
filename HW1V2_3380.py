import psycopg2 
from psycopg2 import OperationalError
import pandas as pd

def connect_to_db():
    db_parameters = {
        "host": "localhost",
        "dbname": "Test-database",
        "user": "postgres",
        "port": "5432",
        "password" : "1234"
    }

    try:
        # Attempt to establish a connection
        print("Connecting to database...")
        conn = psycopg2.connect(**db_params)
        
        # Create a cursor
        cursor = conn.cursor()
        
        print("Connected successfully!")
        return conn, cursor
    
    except OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None, None



def ReferentialIntegrityCheck(t1, t2,cur):
    cur.execute("""
                 FROM {t1} Table1   
                    LEFT JOIN {t2} Table2
                    ON Table2.k1    
                    """)











""" conn = psycopg2.connect(host="localhost", dbname = "Test-database", 
                        user = "postgres", password = "1234", 
                        port = 5432)






cur = conn.cursor()

file1 = open("HW1-testcase1.txt", "a")
file1.read([])


quer1 =  cur.execute("

SELECT k1, k2, a, b FROM t1 WHERE k1 = 1
            ")


for row in cur.fetchall():
    print(row)

print(cur)

conn.commit()

cur.close()
conn.close()

"""