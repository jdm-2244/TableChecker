"""
Rayan Josan    rajosan@cougarnet.uh.edu 2409702
Joaquin Moreno jdmoren6@cougarnet.uh.edu 1991139
"""

import argparse
import psycopg2
import os
from psycopg2 import OperationalError

# Function to connect to the PostgreSQL database
def connect_db():
    try:
        return psycopg2.connect(
            host="127.0.0.1",
            dbname="cosc3380",
            user="dbs10",
            password="test1234",
            port="5432"
        )
    except OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to execute and log queries
def execute_and_log_query(connection, query, params=None, sql_file=None):
    with connection.cursor() as cur:
        cur.execute(query, params)
        if params:
            executed_query = cur.mogrify(query, params).decode('utf-8')
        else:
            executed_query = query
        if sql_file:
            with open(sql_file, "a") as f:
                f.write(executed_query + ";\n\n")

# Function to check 2NF (Partial Dependency) for the given table
def check_2nf(connection, table, primary_key, column_w_no_key, base_case, sql_file):
    for col in column_w_no_key:
        request = f"""
        SELECT 1
        FROM HW1.{base_case}_{table}
        GROUP BY {primary_key}
        HAVING COUNT(DISTINCT {col}) > 1;
        """
        execute_and_log_query(connection, "SET search_path TO HW1;", sql_file=sql_file)
        execute_and_log_query(connection, request, sql_file=sql_file)
        with connection.cursor() as cur:
            cur.execute("SET search_path TO HW1;")
            cur.execute(request)
            result = cur.fetchone()
            if result:
                return "N"
    return "Y"

# Function to check 3NF (Transitive Dependency) for the given table
def check_3nf(connection, table, column_w_no_key, foreign_keys, base_case, sql_file):
    all_columns = column_w_no_key + [foreign_key[0] for foreign_key in foreign_keys]
    for i in range(len(all_columns)):
        for j in range(i + 1, len(all_columns)):
            col1 = all_columns[i]
            col2 = all_columns[j]
            request = f"""
            SELECT {col1}, {col2}
            FROM HW1.{base_case}_{table}
            GROUP BY {col1}, {col2}
            HAVING COUNT(*) > 1;
            """
            execute_and_log_query(connection, request, sql_file=sql_file)
            with connection.cursor() as cur:
                cur.execute(request)
                result = cur.fetchone()
                if result:
                    return "N"
    return "Y"

# Function to check both 2NF and 3NF for the given table
def check_normalization(connection, table, primary_key, column_w_no_key, foreign_keys, base_case, sql_file):
    if check_2nf(connection, table, primary_key, column_w_no_key, base_case, sql_file) == "N":
        return "N"
    if check_3nf(connection, table, column_w_no_key, foreign_keys, base_case, sql_file) == "N":
        return "N"
    return "Y"

# Function to check referential integrity between tables
def referential_integrity(connection, table, foreign_key, ref_table, ref_key, base_case, sql_file):
    query = f"""
    SELECT 1
    FROM HW1.{base_case}_{table}
    LEFT JOIN HW1.{base_case}_{ref_table} ON HW1.{base_case}_{table}.{foreign_key} = HW1.{base_case}_{ref_table}.{ref_key}
    WHERE HW1.{base_case}_{ref_table}.{ref_key} IS NULL
    LIMIT 1;
    """
    execute_and_log_query(connection, "SET search_path TO HW1;", sql_file=sql_file)
    execute_and_log_query(connection, query, sql_file=sql_file)
    with connection.cursor() as cur:
        cur.execute("SET search_path TO HW1;")
        cur.execute(query)
        return "N" if cur.fetchone() else "Y"

# Function to parse table definitions from the input file
def parsing_table(line, base_case):
    table_name, cols = line.split('(', 1)
    table_name = table_name.strip()
    cols = cols.rstrip(')').strip()
    primary_key, foreign_keys, column_w_no_key = None, [], []
    for col in cols.split(','):
        col = col.strip()
        if '(pk)' in col:
            primary_key = col.split('(pk)')[0].strip()
        elif '(fk:' in col:
            fk_col, ref = col.split('(fk:', 1)
            fk_col = fk_col.strip()
            ref_table, ref_key = ref.rstrip(')').split('.')
            foreign_keys.append((fk_col, ref_table, ref_key))
        else:
            column_w_no_key.append(col.split(' ')[0])
    return table_name, primary_key, foreign_keys, column_w_no_key

# Function to handle command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Check database referential integrity and normalization.')
    parser.add_argument('database', type=str, help='Database file in the format key=filename')
    return parser.parse_args()

def format_output(findings, overall_ref_integrity, overall_normalization):
    header = "-----------------------------------------\n"
    header += " Referential integrity     Normalized\n"
    header += "-----------------------------------------\n"
    table_lines = "\n".join([f"{r.split()[0]:<16} {r.split()[1]:<18} {r.split()[2]:<10}" for r in findings])
    footer = f"\nDB referential integrity: {overall_ref_integrity}\n"
    footer += f"DB normalized: {overall_normalization}\n"
    print(header+table_lines+footer)
    return header + table_lines + footer

# Beginning of main
def main(database_file):
    connection = connect_db()
    if not connection:
        return

    findings = []
    base_case = os.path.splitext(os.path.basename(database_file))[0]
    output_file_name = f"{base_case}_output.txt"
    sql_filename = f"{base_case}_output.sql"
    print(output_file_name)
    with open(database_file) as file:
        for line in file:
            table = line.strip()
            if not table:
                continue

            table_name, primary_key, foreign_keys, column_w_no_key = parsing_table(table, base_case)
            if not primary_key:
                print(f"{table_name} has missing primary key.")
                continue

            # Check referential integrity for the table
            ref_integrity = "Y"
            for fk_col, ref_table, ref_key in foreign_keys:
                if referential_integrity(connection, table_name, fk_col, ref_table, ref_key, base_case, sql_filename) == "N":
                    ref_integrity = "N"
                    break

            # Check normalization (2NF and 3NF) for the table
            normalization = check_normalization(connection, table_name, primary_key, column_w_no_key, foreign_keys, base_case, sql_filename)
            findings.append(f"{table_name} {ref_integrity} {normalization}")

    # Determine result of Referential Integrity and Normalization
    RI_Result = "Y" if all(r.split()[1] == "Y" for r in findings) else "N"
    N_Result = "Y" if all(r.split()[2] == "Y" for r in findings) else "N"
    formatted_output = format_output(findings, RI_Result, N_Result)

    with open(output_file_name, "w") as output_file:
        output_file.write(formatted_output)
        output_file.write(f"\nDB referential integrity: {RI_Result}\n")
        output_file.write(f"DB normalized: {N_Result}\n")

    connection.close()
    print("Database connection closed.")

# Entry point for the script
if __name__ == "__main__":
    args = parse_arguments()

    if '=' in args.database:
        key, filename = args.database.split('=', 1)
        if key == 'database':
            main(filename)
        else:
            print(f"Unknown key: {key}")
    else:
        print("Usage: python checkdb.py database=filename")
