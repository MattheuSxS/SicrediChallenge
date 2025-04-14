
import json
import logging
import argparse
from re import sub
from os import getenv
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, lit, substring, length, when
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DateType, DecimalType


logging.basicConfig(
    format=("%(asctime)s | %(levelname)s | File_name ~> %(module)s.py "
            "| Function ~> %(funcName)s | Line ~> %(lineno)d  ~~>  %(message)s"),
    level=logging.INFO
)

APP_NAME = "Read Data from PostgreSQL and save in CSV."

spark = SparkSession.builder.appName(APP_NAME).getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


logging.info("✨ Spark job started!")
logging.info("🔧 Reading data from PostgreSQL and writing to CSV ...")


# ====================================================================================================================================
#                                                 ~~~~> Secret Manager <~~~~                                                         #
# ====================================================================================================================================
def _secret_manager(data_secret: dict) -> dict:
    """
        Retrieves and decodes a secret from Google Cloud Secret Manager.

        Args:
            data_secret (dict): A dictionary containing the following keys:
                - 'project_id' (str): The Google Cloud project ID.
                - 'secret_id' (str): The ID of the secret to retrieve.

        Returns:
            dict: The decoded secret data as a dictionary.

        Raises:
            google.api_core.exceptions.GoogleAPIError: If there is an error accessing the secret.
            json.JSONDecodeError: If the secret data cannot be decoded as JSON.
    """
    from google.cloud import secretmanager

    secret_client = secretmanager.SecretManagerServiceClient()
    response = secret_client.access_secret_version(
        request={"name": f"projects/{data_secret['project_id']}/secrets/{data_secret['secret_id']}/versions/latest"})

    return json.loads(response.payload.data.decode("UTF-8"))


def _get_credentials(data_secret=None) -> dict:
    """
        Retrieves PostgreSQL connection credentials based on the provided secret data.

        Args:
            data_secret (Optional[dict]):
                - If None, default environment variables are used to construct the credentials.
                - If a dictionary, it is used to fetch credentials from a secret manager.
                - Any other type will raise a ValueError.

        Returns:
            dict: A dictionary containing the PostgreSQL connection details:
                - url (str): JDBC URL for the PostgreSQL database.
                - user (str): Username for the database.
                - password (str): Password for the database.
                - driver (str): JDBC driver class name.
                - schema (str): Database schema name.

        Raises:
            ValueError: If `data_secret` is not None or a dictionary.
    """

    match data_secret:
        case None:
            logging.info("🔐 DEV ~~> Using default credentials to connect to PostgreSQL ...")
            return \
                {
                    "url": f"jdbc:postgresql://{getenv('POSTGRES_HOST')}:{getenv('POSTGRES_PORT')}/{getenv('POSTGRES_DB')}",
                    "user": getenv("POSTGRES_USER"),
                    "password": getenv("POSTGRES_PASSWORD"),
                    "driver": "org.postgresql.Driver",
                    "schema": getenv("POSTGRES_SCHEMA")
                }

        case dict():
            logging.info("🔐 PRD ~~> Using provided credentials to connect to PostgreSQL ...")

            payload = _secret_manager(data_secret)
            return \
                {
                    "url": f"jdbc:postgresql://{payload['POSTGRES_HOST']}:{payload['POSTGRES_PORT']}/{payload['POSTGRES_DB']}",
                    "user": payload["POSTGRES_USER"],
                    "password": payload["POSTGRES_PASSWORD"],
                    "driver": "org.postgresql.Driver",
                    "schema": payload["POSTGRES_SCHEMA"]
                }

        case _:
            raise ValueError("❌ Invalid data_secret argument....")


# ====================================================================================================================================
#                                                       ~~~~> PySpark <~~~~                                                          #
# ====================================================================================================================================
def mask_card_number(card_number: str) -> str:
    """
    Masks a card number by replacing all but the first three and last three characters with asterisks.

    Args:
        card_number (str): The card number to be masked.

    Returns:
        str: The masked card number. If the input is None or its length is 6 or less,
             the original card number is returned unmodified.
    """
    if card_number and len(card_number) > 6:
        return card_number[:3] + "*" * (len(card_number) - 6) + card_number[-3:]
    return card_number


def data_schema(name_table:str) -> StructType:
    """
    Define o schema dos dados.
    """

    data_schema = \
        {
            "associado": StructType([
                StructField("id", IntegerType(), True),
                StructField("nome", StringType(), True),
                StructField("sobrenome", StringType(), True),
                StructField("idade", IntegerType(), True)
            ]),
            "conta": StructType([
                StructField("id", IntegerType(), True),
                StructField("id_associado", IntegerType(), True),
                StructField("tipo", StringType(), True),
                StructField("data_criacao", DateType(), True)
            ]),
            "cartao": StructType([
                StructField("id", IntegerType(), True),
                StructField("id_conta", IntegerType(), True),
                StructField("id_associado", IntegerType(), True),
                StructField("num_cartao", StringType(), True),
                StructField("nom_impresso", StringType(), True)
            ]),
            "movimento": StructType([
                StructField("id", IntegerType(), True),
                StructField("id_cartao", IntegerType(), True),
                StructField("vlr_transacao", DecimalType(10, 2), True),
                StructField("des_transacao", StringType(), True),
                StructField("data_movimento", DateType(), True)
            ])
        }

    return data_schema[name_table]


def _read_from_postgres(data_secret: str = None):
    """
        Reads data from PostgreSQL tables and loads them into Spark DataFrames.

        This function connects to a PostgreSQL database using credentials retrieved
        from a secret or configuration, and reads data from predefined tables into
        a dictionary of Spark DataFrames. Each table's schema and columns are
        specified in the `table_list` dictionary.

        Args:
            data_secret (str, optional): The identifier for retrieving database
                credentials. If not provided, default credentials will be used.

        Returns:
            dict: A dictionary where keys are table names and values are Spark
            DataFrames containing the data from the respective tables.

        Raises:
            Exception: If there is an error during the database connection or data
            loading process.

        Logging:
            Logs a success message if data is successfully loaded, or an error
            message if an exception occurs.

        Notes:
            - The function uses the `spark.read.format("jdbc")` method to read data
            from the database.
            - The `table_list` dictionary defines the tables to be read and their
            respective columns.
            - Database connection details such as URL, user, password, schema, and
            driver are retrieved from the `DB_CONFIG` dictionary.
    """
    DB_CONFIG = _get_credentials(data_secret)

    try:
        dfs = {}
        table_list = \
            {
                "associado": ["id", "nome", "sobrenome", "idade"],
                "conta": ["id", "id_associado", "tipo", "data_criacao"],
                "cartao": ["id", "id_conta", "id_associado","num_cartao", "nom_impresso"],
                "movimento": ["id", "id_cartao", "vlr_transacao", "des_transacao","data_movimento"]
            }

        for table, columns in table_list.items():
            dfs[table] = spark.read.format("jdbc") \
                .option("schema", data_schema(table)) \
                .option("url", DB_CONFIG["url"]) \
                .option("user", DB_CONFIG["user"]) \
                .option("password", DB_CONFIG["password"]) \
                .option("dbtable", f"{DB_CONFIG['schema']}.{table}") \
                .option("columnname", columns) \
                .option("driver", DB_CONFIG["driver"]) \
                .load()

        logging.info("✅ Successfully loaded data from PostgreSQL tables")
        return dfs

    except Exception as e:
        logging.error(f"❌ Error reading from PostgreSQL: {e}")
        raise e


def _transform_data(dfs: dict):
    """
        Transforms and joins multiple Spark DataFrames to create a unified DataFrame.

        This function performs the following operations:
        1. Renames columns in the "associado", "conta", "cartao", and "movimento" DataFrames.
        2. Adds a new column "data_criacao_cartao" to the "conta" DataFrame with the current date.
        3. Joins the DataFrames in the following order:
        - "associado" is joined with "conta" on the "id" and "id_associado" columns.
        - The resulting DataFrame is joined with "cartao" on "id_conta" and "id_associado".
        - The resulting DataFrame is joined with "movimento" on "id_cartao".
        4. Selects specific columns from the joined DataFrame for the final output.

        Args:
            dfs (dict): A dictionary containing the input Spark DataFrames with the following keys:
                - "associado": DataFrame containing information about associates.
                - "conta": DataFrame containing account information.
                - "cartao": DataFrame containing card information.
                - "movimento": DataFrame containing transaction movement information.

        Returns:
            pyspark.sql.DataFrame: A unified DataFrame containing transformed and joined data with the following columns:
                - "nome_associado"
                - "sobrenome_associado"
                - "idade_associado"
                - "vlr_transacao_movimento"
                - "des_transacao_movimento"
                - "data_movimento"
                - "numero_cartao"
                - "nome_impresso_cartao"
                - "data_criacao_cartao"
                - "tipo_conta"
                - "data_criacao_conta"
    """

    dfs["associado"] = \
        dfs["associado"] \
            .withColumnRenamed("nome", "nome_associado") \
            .withColumnRenamed("sobrenome", "sobrenome_associado") \
            .withColumnRenamed("idade", "idade_associado")

    dfs["conta"] = \
        dfs["conta"] \
            .withColumnRenamed("tipo", "tipo_conta") \
            .withColumnRenamed("data_criacao", "data_criacao_conta")


    dfs["cartao"] = \
        dfs["cartao"] \
            .withColumnRenamed("num_cartao", "numero_cartao") \
            .withColumnRenamed("nom_impresso", "nome_impresso_cartao")

    dfs["movimento"] = \
        dfs["movimento"] \
            .withColumnRenamed("vlr_transacao", "vlr_transacao_movimento") \
            .withColumnRenamed("des_transacao", "des_transacao_movimento") \
            .withColumnRenamed("data_movimento", "data_movimento")

    df_joined = dfs["associado"].join(
            dfs["conta"],
            dfs["associado"]["id"] == dfs["conta"]["id_associado"],
            "inner"
        ).join(
            dfs["cartao"],
            (dfs["cartao"]["id_conta"] == dfs["conta"]["id"]) & (dfs["cartao"]["id_associado"] == dfs["associado"]["id"]),
            "inner"
        ).join(
            dfs["movimento"],
            dfs["movimento"]["id_cartao"] == dfs["cartao"]["id"],
            "inner"
        ).withColumn("data_criacao_cartao", lit(col('data_criacao_conta'))) \
        .select(
            "nome_associado",
            "sobrenome_associado",
            "idade_associado",
            "vlr_transacao_movimento",
            "des_transacao_movimento",
            "data_movimento",
            "numero_cartao",
            "nome_impresso_cartao",
            "data_criacao_cartao",
            "tipo_conta",
            "data_criacao_conta"
        )

    return df_joined


def _data_governance(df):
    """
    Data governance checks.
    """

    logging.info(f"🔍 Checking for null values ... { {col: df.where(col(column).isNull()).count() for column in df.columns}}")
    logging.info(f"🔍 Checking for duplicate values ... { df.count() - df.dropDuplicates().count()}")
    logging.info(f"🔍 Checking for data shape ... {df.count(), len(df.columns)}")
    logging.info(f"🔍 Checking for data types ... {df.dtypes}")
    logging.info(f"🔍 Checking for data distribution ... {df.groupBy('tipo_conta').count().show()}")

    logging.info("🔍 Masking sensitive data ...")
    df = df.withColumn(
        "numero_cartao",
        when(
            length(col("numero_cartao")) > 6,
            concat(
                substring(col("numero_cartao"), 1, 3),
                lit("*" * 6),
                substring(col("numero_cartao"), -3, 3)
            )
        ).otherwise(col("numero_cartao"))
    )
    return df


def _write_csv(output_path: str, mode: str, data_secret: str = None) -> None:
    """
        Writes a DataFrame to CSV files with specified options and partitioning.

        This function reads data from a PostgreSQL database, applies transformations,
        and writes the resulting DataFrame to CSV files in the specified output path.
        The output files are partitioned by specific columns and include a header.

        Args:
            output_path (str): The base directory where the CSV files will be written.
            mode (str): The write mode for the CSV files (e.g., "overwrite", "append").
            data_secret (str, optional): A secret key or connection string for accessing
                the PostgreSQL database. Defaults to None.

        Raises:
            Exception: If an error occurs during the writing process, it logs the error
                and re-raises the exception.

        Logging:
            Logs the output path and success or failure of the write operation.
    """

    df = _data_governance(
            _transform_data(
                _read_from_postgres(data_secret)))

    data_string = sub('[^0-9]', '', str(datetime.now()))

    output_path = f"{output_path}/movimento_flat-{data_string}"
    logging.info(f"Writting the files in path {output_path}")

    try:
        df_ = df.repartition(3)
        df_.write.option("header",True) \
                .partitionBy("tipo_conta", "des_transacao_movimento", "data_movimento", ) \
                .option("encoding", "UTF-8") \
                .mode(mode) \
                .csv(output_path)
        logging.info("✅ Successfully wrote data to CSV")
    except Exception as e:
        logging.error(f"❌ Error writing to CSV ....")
        raise e


def main(output_path:str, mode:str, data_secret:str = None) -> None:
   _write_csv(output_path, mode, data_secret)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spark job with arguments")

    parser.add_argument("--output_path", type=str, default="/opt/spark/data", help="Path to output directory (default: /opt/spark/data)")
    parser.add_argument("--mode", type=str, choices=["overwrite", "append"], default="overwrite", help="Write mode (default: overwrite)")
    parser.add_argument("--data_secret", type=str, default=None, help="Prd ~~> postgres database credentials")

    args = parser.parse_args()

    if args.data_secret:
        args.data_secret = json.loads(args.data_secret)

    main(args.output_path, args.mode, args.data_secret)

    spark.stop()
    logging.info("✨ Spark job finished!")
