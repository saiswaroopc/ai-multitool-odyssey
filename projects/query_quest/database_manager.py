import pandas as pd
import psycopg2
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages database connections and queries. It ensures connections are properly opened and closed,
    and it handles the execution of queries.
    """

    def __init__(self, db_name, user, password, host, port, schema):
        """
        Initializes database configuration.
        """
        self.connection_params = {
            "dbname": db_name,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }
        self.schema = schema

    @contextmanager
    def connect(self):
        """
        Context manager for database connections.
        """
        conn = psycopg2.connect(**self.connection_params)
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SET search_path TO {self.schema};")
            yield conn
        finally:
            conn.close()

    def execute_query(self, query):
        """
        Executes a SQL query using the managed connection.
        """
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                try:
                    results = cursor.fetchall()
                    result = [
                        dict(
                            zip([desc[0] for desc in cursor.description], row)
                        ) for row in results
                    ]
                    return result
                except psycopg2.ProgrammingError:
                    return []  # Handling cases where there are no results to fetch

    def verify_connection(self):
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    if cursor.fetchone():
                        return True
        except psycopg2.Error:
            return False

    def list_tables(self):
        """
        Returns a list of all tables in the current database schema.
        """
        query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{self.schema}'"
        tables = self.execute_query(query)

        tables_formatted = []
        for table in tables:
            tables_formatted.append(f"{self.schema}.{table['table_name']}")
        return tables_formatted

    def get_table_definition(self, table_name):
        """
        Returns the column names and data types for a given table.
        """
        query_columns = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = '{self.schema}' AND table_name = '{table_name}'
        """
        columns = self.execute_query(query_columns)

        query_constraints = f"""
        SELECT tc.constraint_type, kcu.column_name, 
           CASE WHEN tc.constraint_type = 'FOREIGN KEY' THEN rc.update_rule ELSE NULL END as update_rule,
           CASE WHEN tc.constraint_type = 'FOREIGN KEY' THEN rc.delete_rule ELSE NULL END as delete_rule,
           ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu 
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.referential_constraints AS rc 
          ON tc.constraint_name = rc.constraint_name AND tc.table_schema = rc.constraint_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu 
          ON rc.unique_constraint_name = ccu.constraint_name AND rc.unique_constraint_schema = ccu.constraint_schema
        WHERE tc.table_schema = '{self.schema}' AND tc.table_name = '{table_name}';
        """
        constraints = self.execute_query(query_constraints)

        result = {
            'columns': pd.DataFrame(columns).to_string(index=False),
            'constraints': pd.DataFrame(constraints).to_string(index=False),
        }
        return result

    def get_top_rows(self, table_name, row_count=3):
        """
        Returns the top N rows from a specified table.
        """
        query = f"SELECT * FROM {table_name} LIMIT {row_count}"
        top_rows = self.execute_query(query)
        return pd.DataFrame(top_rows).to_string(index=False)
