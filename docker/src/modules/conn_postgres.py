import io
import logging
import psycopg2
import polars as pl


logging.basicConfig(
    format=("%(asctime)s | %(levelname)s | File_name ~> %(module)s.py "
            "| Function ~> %(funcName)s | Line ~> %(lineno)d  ~~>  %(message)s"),
    level=logging.INFO
)


class Postgres:
    """
        A class used to represent a connection to a PostgreSQL database using a connection pool.

        Methods
        -------
        __init__() -> None
            Initializes the connection pool and gets a connection from the pool.

        insert_multiple(query: str, params: list = None) -> None
            Executes a given query with multiple parameters and commits the transaction.

        create_tables(sql_file: str = "/opt/spark/drivers/init.sql") -> None
            Executes SQL commands from a given file to create tables in the database.
    """

    def __init__(self, db_credentials:dict) -> None:

        self.CONFIG = db_credentials
        self.conn = psycopg2.connect(
            host        = self.CONFIG['POSTGRES_HOST'],
            port        = self.CONFIG['POSTGRES_PORT'],
            database    = self.CONFIG['POSTGRES_DB'],
            user        = self.CONFIG['POSTGRES_USER'],
            password    = self.CONFIG['POSTGRES_PASSWORD']
        )

        logging.info("Connection to the database has been established.")


    def insert_with_copy(self, table:str, df:pl.DataFrame) -> None:
        """
            Inserts data from a Polars DataFrame into a PostgreSQL table using the COPY command.

            Args:
                table (str): The name of the target table in the PostgreSQL database.
                df (pl.DataFrame): The Polars DataFrame containing the data to be inserted.

            Raises:
                Exception: If an error occurs during the execution of the COPY command, the exception is logged,
                        the transaction is rolled back, and the exception is re-raised.
        """
        try:
            with self.conn.cursor() as cursor:
                buffer = io.StringIO()
                df.write_csv(buffer, include_header=False)
                buffer.seek(0)

                cursor.copy_expert(f"COPY {self.CONFIG['POSTGRES_SCHEMA']}.{table} FROM STDIN WITH CSV", buffer)
                self.conn.commit()
                logging.info(f"Data inserted with success | Total {table} ~~> {len(df)} records")

        except Exception as e:
            logging.error(f"Error during execution: {e}", exc_info=True)
            self.conn.rollback()
            raise e


    def close_connection(self) -> None:
        """
            Closes the current database connection.

            This method closes the connection to the PostgreSQL database that was
            previously established. It ensures that all resources associated with
            the connection are properly released.
        """

        self.conn.close()
        logging.info("Connection to the database has been closed.")