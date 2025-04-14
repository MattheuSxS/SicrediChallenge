import os
import logging
from flask.wrappers import Request
from typing import Optional, Dict, Any
from modules.conn_postgres import Postgres
from modules.fake_data import FakeDataTransf
from modules.secret_manager import get_secret


logging.basicConfig(
    format=("%(asctime)s | %(levelname)s | File_name ~> %(module)s.py "
            "| Function ~> %(funcName)s | Line ~> %(lineno)d  ~~>  %(message)s"),
    level=logging.INFO
)


def get_db_credentials(request_obj: Optional[Request] = None) -> Dict[str, Any]:
    """
    Retrieves database credentials either from a Flask request or environment variables.

    Args:
        request_obj (Optional[Request]): The Flask request object. If None, credentials
                                         are fetched from environment variables.

    Returns:
        Dict[str, Any]: A dictionary containing the database credentials.

    Raises:
        ValueError: If the request object is invalid or credentials are missing.
    """
    if isinstance(request_obj, Request):
        request_json = request_obj.get_json(silent=True)
        if not request_json:
            raise ValueError("Invalid or missing JSON payload in request.")

        payload = get_secret(
            request_json.get("project_id"),
            request_json.get("secret_id")
        )

        credentials = {
            "POSTGRES_HOST": payload.get("POSTGRES_HOST"),
            "POSTGRES_PORT": payload.get("POSTGRES_PORT"),
            "POSTGRES_DB": payload.get("POSTGRES_DB"),
            "POSTGRES_SCHEMA": payload.get("POSTGRES_SCHEMA"),
            "POSTGRES_USER": payload.get("POSTGRES_USER"),
            "POSTGRES_PASSWORD": payload.get("POSTGRES_PASSWORD"),
        }
    elif request_obj is None:
        credentials = {
            "POSTGRES_HOST": os.environ.get("POSTGRES_HOST"),
            "POSTGRES_PORT": os.environ.get("POSTGRES_PORT"),
            "POSTGRES_DB": os.environ.get("POSTGRES_DB"),
            "POSTGRES_SCHEMA": os.environ.get("POSTGRES_SCHEMA"),
            "POSTGRES_USER": os.environ.get("POSTGRES_USER"),
            "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        }
    else:
        raise ValueError("Invalid request object. Expected Flask Request or None.")


    if not all(credentials.values()):
        missing = [key for key, value in credentials.items() if not value]
        raise ValueError(f"Missing or invalid credentials for: {', '.join(missing)}")

    return credentials


def main(request = None) -> dict:
    """
        Main function to initiate the process of creating tables and inserting fake data into a PostgreSQL database.
        Args:
            sql_file (str, optional): Path to the SQL file containing table creation statements. Defaults to None.
        Returns:
            None
        Logs:
            - Logs the start of the process.
            - Logs the creation of tables if `sql_file` is provided.
            - Logs the generation of fake data.
            - Logs the insertion of data into each table.
            - Logs the successful completion of the process.
            - Logs any errors encountered during execution.
    """

    logging.info("Starting the process...")
    postgres = Postgres(get_db_credentials(request))
    fake_data = FakeDataTransf()

    try:
        logging.info("Generating fake data...")
        data_dict = fake_data.data_dict()

        logging.info("Inserting data into tables...")
        for table, df in data_dict.items():
            postgres.insert_with_copy(table, df)

        logging.info("all data inserted successfully!")

        if request:
            return {"status": "success", "message": "Data processing completed!"}, 200

    except Exception as e:
        logging.error(f"Error during execution: {e}", exc_info=True)

        if request:
            return {"status": "error", "message": str(e)}, 500
    finally:
        postgres.conn.close()

if __name__ == "__main__":
    main()