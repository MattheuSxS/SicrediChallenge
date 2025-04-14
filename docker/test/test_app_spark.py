import json
import logging
import unittest
from decimal import *
from datetime import datetime, date
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from unittest.mock import patch, MagicMock
from google.api_core.exceptions import GoogleAPIError

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DateType, DecimalType
from jobs.app_spark import \
    (
        _secret_manager, _get_credentials, mask_card_number, data_schema, _read_from_postgres,
        _transform_data, _write_csv
    )

class TestSecretManager(unittest.TestCase):

    @patch("google.cloud.secretmanager.SecretManagerServiceClient")
    def test_secret_manager_success(self, mock_secret_manager_client):
        # Mock the response from SecretManagerServiceClient
        mock_client_instance = MagicMock()
        mock_secret_manager_client.return_value = mock_client_instance
        mock_response = MagicMock()
        mock_response.payload.data.decode.return_value = json.dumps({
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test_db",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
            "POSTGRES_SCHEMA": "public"
        })
        mock_client_instance.access_secret_version.return_value = mock_response

        # Input data
        data_secret = {
            "project_id": "test_project",
            "secret_id": "test_secret"
        }

        # Call the function
        result = _secret_manager(data_secret)

        # Assertions
        mock_client_instance.access_secret_version.assert_called_once_with(
            request={"name": "projects/test_project/secrets/test_secret/versions/latest"}
        )
        self.assertEqual(result["POSTGRES_HOST"], "localhost")
        self.assertEqual(result["POSTGRES_PORT"], "5432")
        self.assertEqual(result["POSTGRES_DB"], "test_db")
        self.assertEqual(result["POSTGRES_USER"], "test_user")
        self.assertEqual(result["POSTGRES_PASSWORD"], "test_password")
        self.assertEqual(result["POSTGRES_SCHEMA"], "public")

    @patch("google.cloud.secretmanager.SecretManagerServiceClient")
    def test_secret_manager_google_api_error(self, mock_secret_manager_client):
        # Mock the SecretManagerServiceClient to raise an exception
        mock_client_instance = MagicMock()
        mock_secret_manager_client.return_value = mock_client_instance
        mock_client_instance.access_secret_version.side_effect = GoogleAPIError("Google API Error")

        # Input data
        data_secret = {
            "project_id": "test_project",
            "secret_id": "test_secret"
        }

        # Call the function and assert it raises an exception
        with self.assertRaises(GoogleAPIError):
            _secret_manager(data_secret)

    @patch("google.cloud.secretmanager.SecretManagerServiceClient")
    def test_secret_manager_json_decode_error(self, mock_secret_manager_client):
        # Mock the response from SecretManagerServiceClient with invalid JSON
        mock_client_instance = MagicMock()
        mock_secret_manager_client.return_value = mock_client_instance
        mock_response = MagicMock()
        mock_response.payload.data.decode.return_value = "invalid_json"
        mock_client_instance.access_secret_version.return_value = mock_response

        # Input data
        data_secret = {
            "project_id": "test_project",
            "secret_id": "test_secret"
        }

        # Call the function and assert it raises a JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            _secret_manager(data_secret)


class TestGetCredentials(unittest.TestCase):

    @patch("jobs.app_spark.getenv")
    def test_get_credentials_default(self, mock_getenv):
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test_db",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
            "POSTGRES_SCHEMA": "public"
        }.get(key)

        # Call the function with None
        result = _get_credentials()

        # Assertions
        self.assertEqual(result["url"], "jdbc:postgresql://localhost:5432/test_db")
        self.assertEqual(result["user"], "test_user")
        self.assertEqual(result["password"], "test_password")
        self.assertEqual(result["driver"], "org.postgresql.Driver")
        self.assertEqual(result["schema"], "public")

    @patch("jobs.app_spark._secret_manager")
    def test_get_credentials_with_secret(self, mock_secret_manager):
        # Mock the secret manager response
        mock_secret_manager.return_value = {
            "POSTGRES_HOST": "remote_host",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "prod_db",
            "POSTGRES_USER": "prod_user",
            "POSTGRES_PASSWORD": "prod_password",
            "POSTGRES_SCHEMA": "prod_schema"
        }

        # Input data
        data_secret = {
            "project_id": "test_project",
            "secret_id": "test_secret"
        }

        # Call the function with a secret
        result = _get_credentials(data_secret)

        # Assertions
        mock_secret_manager.assert_called_once_with(data_secret)
        self.assertEqual(result["url"], "jdbc:postgresql://remote_host:5432/prod_db")
        self.assertEqual(result["user"], "prod_user")
        self.assertEqual(result["password"], "prod_password")
        self.assertEqual(result["driver"], "org.postgresql.Driver")
        self.assertEqual(result["schema"], "prod_schema")

    def test_get_credentials_invalid_argument(self):
        # Call the function with an invalid argument and assert it raises a ValueError
        with self.assertRaises(ValueError):
            _get_credentials(data_secret="invalid_argument")

class TestMaskCardNumber(unittest.TestCase):

    def test_mask_card_number_valid(self):
        # Test with a valid card number
        card_number = "123456789012"
        expected_result = "123******012"
        self.assertEqual(mask_card_number(card_number), expected_result)

    def test_mask_card_number_short(self):
        # Test with a card number of length 6 or less
        card_number = "123456"
        expected_result = "123456"
        self.assertEqual(mask_card_number(card_number), expected_result)

    def test_mask_card_number_none(self):
        # Test with None as input
        card_number = None
        expected_result = None
        self.assertEqual(mask_card_number(card_number), expected_result)

    def test_mask_card_number_empty(self):
        # Test with an empty string
        card_number = ""
        expected_result = ""
        self.assertEqual(mask_card_number(card_number), expected_result)

    def test_mask_card_number_exact_length(self):
        # Test with a card number of exactly 7 characters
        card_number = "1234567"
        expected_result = "123*567"
        self.assertEqual(mask_card_number(card_number), expected_result)

class TestDataSchema(unittest.TestCase):

    def test_data_schema_associado(self):
        expected_schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("nome", StringType(), True),
            StructField("sobrenome", StringType(), True),
            StructField("idade", IntegerType(), True)
        ])
        self.assertEqual(data_schema("associado"), expected_schema)

    def test_data_schema_conta(self):
        expected_schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("id_associado", IntegerType(), True),
            StructField("tipo", StringType(), True),
            StructField("data_criacao", DateType(), True)
        ])
        self.assertEqual(data_schema("conta"), expected_schema)

    def test_data_schema_cartao(self):
        expected_schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("id_conta", IntegerType(), True),
            StructField("id_associado", IntegerType(), True),
            StructField("num_cartao", StringType(), True),
            StructField("nom_impresso", StringType(), True)
        ])
        self.assertEqual(data_schema("cartao"), expected_schema)

    def test_data_schema_movimento(self):
        expected_schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("id_cartao", IntegerType(), True),
            StructField("vlr_transacao", DecimalType(10, 2), True),
            StructField("des_transacao", StringType(), True),
            StructField("data_movimento", DateType(), True)
        ])
        self.assertEqual(data_schema("movimento"), expected_schema)

    def test_data_schema_invalid_table(self):
        with self.assertRaises(KeyError):
            data_schema("invalid_table")


class TestReadFromPostgres(unittest.TestCase):
    def setUp(self):
        # Set up a Spark session for testing
        self.spark = SparkSession.builder.master("local[1]").appName("TestReadFromPostgres").getOrCreate()

        # Mock the logger
        logging.basicConfig(level=logging.INFO)

        # Mock the _get_credentials function
        self.mock_db_config = {
            "url": "jdbc:postgresql://localhost:5432/test_db",
            "user": "user",
            "password": "password",
            "schema": "public",
            "driver": "org.postgresql.Driver",
        }

        # Mock the data_schema function
        self.mock_data_schema = MagicMock(return_value="public")

        # Mock the table list
        self.table_list = {
            "associado": ["id", "nome", "sobrenome", "idade"],
            "conta": ["id", "id_associado", "tipo", "data_criacao"],
            "cartao": ["id", "id_conta", "id_associado", "num_cartao", "nom_impresso"],
            "movimento": ["id", "id_cartao", "vlr_transacao", "des_transacao", "data_movimento"],
        }

    def tearDown(self):
        # Stop the Spark session after each test
        self.spark.stop()

class TestReadFromPostgres(unittest.TestCase):
    def setUp(self):
        # Set up a Spark session for testing
        self.spark = SparkSession.builder.master("local[1]").appName("TestReadFromPostgres").getOrCreate()

        # Mock the logger
        logging.basicConfig(level=logging.INFO)

        # Mock the _get_credentials function
        self.mock_db_config = {
            "url": "jdbc:postgresql://localhost:5432/test_db",
            "user": "user",
            "password": "password",
            "schema": "public",
            "driver": "org.postgresql.Driver",
        }

        # Mock the data_schema function
        self.mock_data_schema = MagicMock(return_value="public")

        # Mock the table list
        self.table_list = {
            "associado": ["id", "nome", "sobrenome", "idade"],
            "conta": ["id", "id_associado", "tipo", "data_criacao"],
            "cartao": ["id", "id_conta", "id_associado", "num_cartao", "nom_impresso"],
            "movimento": ["id", "id_cartao", "vlr_transacao", "des_transacao", "data_movimento"],
        }

    def tearDown(self):
        # Stop the Spark session after each test
        self.spark.stop()

    @patch("jobs.app_spark._get_credentials")
    @patch("jobs.app_spark.data_schema")
    @patch("pyspark.sql.SparkSession.read")
    def test_read_from_postgres_success(self, mock_spark_read, mock_data_schema, mock_get_credentials):
        # Mock the _get_credentials function
        mock_get_credentials.return_value = self.mock_db_config

        # Mock the data_schema function
        mock_data_schema.return_value = "public"

        # Mock the Spark DataFrame
        mock_df = MagicMock()
        mock_spark_read.format.return_value = mock_spark_read
        mock_spark_read.option.return_value = mock_spark_read
        mock_spark_read.load.return_value = mock_df

        # Call the function
        result = _read_from_postgres(data_secret="test-secret")

        # Assertions
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), len(self.table_list))
        for table in self.table_list:
            self.assertIn(table, result)
            self.assertEqual(result[table], mock_df)

        # Verify logging
        with self.assertLogs(level=logging.INFO) as log:
            _read_from_postgres(data_secret="test-secret")
            self.assertIn("✅ Successfully loaded data from PostgreSQL tables", log.output[0])


    @patch("jobs.app_spark._get_credentials")
    @patch("jobs.app_spark.data_schema")
    @patch("pyspark.sql.SparkSession.read")
    def test_read_from_postgres_error(self, mock_spark_read, mock_data_schema, mock_get_credentials):
        # Mock the _get_credentials function
        mock_get_credentials.return_value = self.mock_db_config

        # Mock the data_schema function
        mock_data_schema.return_value = "public"

        # Simulate an error during data loading
        mock_spark_read.format.return_value = mock_spark_read
        mock_spark_read.option.return_value = mock_spark_read
        mock_spark_read.load.side_effect = Exception("Test error")

        # Call the function and assert that it raises an exception
        with self.assertRaises(Exception) as context:
            # Verify logging within the same context
            with self.assertLogs(level=logging.ERROR) as log:
                _read_from_postgres(data_secret="test-secret")
            self.assertIn("❌ Error reading from PostgreSQL: Test error", log.output[0])
        self.assertIn("Test error", str(context.exception))


class TestTransformData(unittest.TestCase):
    def setUp(self):
        # Set up a Spark session for testing
        self.spark = SparkSession.builder.master("local[1]").appName("TestTransformData").getOrCreate()

        # Create sample data for testing
        self.dfs = {
            "associado": self.spark.createDataFrame(
                [
                    (1, "John", "Doe", 30),
                    (2, "Jane", "Smith", 25)
                ],
                ["id", "nome", "sobrenome", "idade"]
            ),
            "conta": self.spark.createDataFrame(
                [
                    (1, 1, "corrente", date(2023, 1, 1)),
                    (2, 2, "poupanca", date(2023, 2, 1))
                ],
                ["id", "id_associado", "tipo", "data_criacao"]
            ),
            "cartao": self.spark.createDataFrame(
                [
                    (1, 1, 1, "123456789012", "John Doe"),
                    (2, 2, 2, "987654321098", "Jane Smith")
                ],
                ["id", "id_conta", "id_associado", "num_cartao", "nom_impresso"]
            ),
            "movimento": self.spark.createDataFrame(
                [
                    (1, 1, Decimal(100.0), "compra", date(2023, 3, 1)),
                    (2, 2, Decimal(200.0), "saque", date(2023, 3, 2))
                ],
                ["id", "id_cartao", "vlr_transacao", "des_transacao", "data_movimento"]
            )
        }

    def tearDown(self):
        # Stop the Spark session after each test
        self.spark.stop()

    #TODO: Fix the test_transform_data_success test
    # def test_transform_data_success(self):
    #     # Call the function
    #     result_df = _transform_data(self.dfs)

    #     # Expected data
    #     expected_data = [
    #         (
    #             "John", "Doe", 30, Decimal(100.0), "compra", date(2023, 3, 1), "123456789012", "John Doe",
    #             date(2023, 1, 1), "corrente", date(2023, 1, 1)  # Use date objects instead of strings
    #         ),
    #         (
    #             "Jane", "Smith", 25, Decimal(200.0), "saque", date(2023, 3, 2), "987654321098", "Jane Smith",
    #             date(2023, 2, 1), "poupanca", date(2023, 2, 1)  # Use date objects instead of strings
    #         )
    #     ]

    #     # Define the expected schema
    #     expected_schema = StructType([
    #         StructField("nome_associado", StringType(), True),
    #         StructField("sobrenome_associado", StringType(), True),
    #         StructField("idade_associado", IntegerType(), True),
    #         StructField("vlr_transacao_movimento", DecimalType(10, 2), True),
    #         StructField("des_transacao_movimento", StringType(), True),
    #         StructField("data_movimento", DateType(), True),
    #         StructField("numero_cartao", StringType(), True),
    #         StructField("nome_impresso_cartao", StringType(), True),
    #         StructField("data_criacao_cartao", DateType(), True),
    #         StructField("tipo_conta", StringType(), True),
    #         StructField("data_criacao_conta", DateType(), True)
    #     ])


    #     # Create the expected DataFrame with the defined schema
    #     expected_df = self.spark.createDataFrame(expected_data, schema=expected_schema)

    #     # result_df = result_df.withColumn("idade_associado", col("idade_associado").cast(IntegerType()))
    #     # result_df = result_df.withColumn("vlr_transacao_movimento", col("vlr_transacao_movimento").cast(DecimalType()))
    
    #     # Assert schema equality
    #     self.assertEqual(result_df.schema, expected_df.schema)

    #     # Assert data equality
    #     self.assertEqual(result_df.collect(), expected_df.collect())

    def test_transform_data_empty_input(self):
        # Create empty DataFrames for input
        empty_dfs = {
            "associado": self.spark.createDataFrame([], self.dfs["associado"].schema),
            "conta": self.spark.createDataFrame([], self.dfs["conta"].schema),
            "cartao": self.spark.createDataFrame([], self.dfs["cartao"].schema),
            "movimento": self.spark.createDataFrame([], self.dfs["movimento"].schema)
        }

        # Call the function
        result_df = _transform_data(empty_dfs)

        # Assert that the result is an empty DataFrame
        self.assertEqual(result_df.count(), 0)

    def test_transform_data_missing_column(self):
        # Remove a column from one of the input DataFrames
        invalid_dfs = self.dfs.copy()
        invalid_dfs["associado"] = invalid_dfs["associado"].drop("nome")

        # Call the function and assert it raises an exception
        with self.assertRaises(Exception):
            _transform_data(invalid_dfs)


class TestWriteCSV(unittest.TestCase):
    def setUp(self):
        # Set up a Spark session for testing
        self.spark = SparkSession.builder.master("local[1]").appName("TestWriteCSV").getOrCreate()

        # Create sample data for testing
        self.dfs = {
            "associado": self.spark.createDataFrame(
                [
                    (1, "John", "Doe", 30),
                    (2, "Jane", "Smith", 25)
                ],
                ["id", "nome", "sobrenome", "idade"]
            ),
            "conta": self.spark.createDataFrame(
                [
                    (1, 1, "corrente", date(2023, 1, 1)),
                    (2, 2, "poupanca", date(2023, 2, 1))
                ],
                ["id", "id_associado", "tipo", "data_criacao"]
            ),
            "cartao": self.spark.createDataFrame(
                [
                    (1, 1, 1, "123456789012", "John Doe"),
                    (2, 2, 2, "987654321098", "Jane Smith")
                ],
                ["id", "id_conta", "id_associado", "num_cartao", "nom_impresso"]
            ),
            "movimento": self.spark.createDataFrame(
                [
                    (1, 1, Decimal(100.0), "compra", date(2023, 3, 1)),
                    (2, 2, Decimal(200.0), "saque", date(2023, 3, 2))
                ],
                ["id", "id_cartao", "vlr_transacao", "des_transacao", "data_movimento"]
            )
        }

    def tearDown(self):
        # Stop the Spark session after each test
        self.spark.stop()

    # @patch("jobs.app_spark._read_from_postgres")
    # @patch("jobs.app_spark._transform_data")
    # @patch("jobs.app_spark._data_governance")
    # @patch("pyspark.sql.DataFrame.write")
    # def test_write_csv_success(self, mock_write, mock_data_governance, mock_transform_data, mock_read_from_postgres):
    #     # Mock the data pipeline
    #     mock_read_from_postgres.return_value = self.dfs
    #     mock_transform_data.return_value = self.dfs["movimento"]
    #     mock_data_governance.return_value = self.dfs["movimento"]

    #     # Mock the write operation
    #     mock_write.option.return_value = mock_write
    #     mock_write.partitionBy.return_value = mock_write
    #     mock_write.mode.return_value = mock_write
    #     mock_write.csv.return_value = None

    #     # Call the function
    #     output_path = "/tmp/test_output"
    #     mode = "overwrite"
    #     _write_csv(output_path, mode)

    #     # Assertions
    #     mock_read_from_postgres.assert_called_once()
    #     mock_transform_data.assert_called_once()
    #     mock_data_governance.assert_called_once()
    #     mock_write.csv.assert_called_once_with(f"{output_path}/movimento_flat-*")

    @patch("jobs.app_spark._read_from_postgres")
    @patch("jobs.app_spark._transform_data")
    @patch("jobs.app_spark._data_governance")
    @patch("pyspark.sql.DataFrame.write")
    def test_write_csv_error(self, mock_write, mock_data_governance, mock_transform_data, mock_read_from_postgres):
        # Mock the data pipeline
        mock_read_from_postgres.return_value = self.dfs
        mock_transform_data.return_value = self.dfs["movimento"]
        mock_data_governance.return_value = self.dfs["movimento"]

        # Simulate an error during the write operation
        mock_write.option.return_value = mock_write
        mock_write.partitionBy.return_value = mock_write
        mock_write.mode.return_value = mock_write
        mock_write.csv.side_effect = Exception("Test write error")

        # Call the function and assert it raises an exception
        output_path = "/tmp/test_output"
        mode = "overwrite"
        with self.assertRaises(Exception) as context:
            _write_csv(output_path, mode)

        # Assertions
        self.assertIn("Test write error", str(context.exception))
        mock_read_from_postgres.assert_called_once()
        mock_transform_data.assert_called_once()
        mock_data_governance.assert_called_once()
        mock_write.csv.assert_called_once()

#TODO: Fix the test_write_csv_empty_dataframe test
#     @patch("jobs.app_spark._read_from_postgres")
#     @patch("jobs.app_spark._transform_data")
#     @patch("jobs.app_spark._data_governance")
#     def test_write_csv_empty_dataframe(self, mock_data_governance, mock_transform_data, mock_read_from_postgres):
#         # Mock the data pipeline to return an empty DataFrame with the correct schema
#         empty_schema = StructType([
#             StructField("id", IntegerType(), True),
#             StructField("id_cartao", IntegerType(), True),
#             StructField("vlr_transacao", DecimalType(10, 2), True),
#             StructField("des_transacao", StringType(), True),
#             StructField("data_movimento", DateType(), True),
#             StructField("tipo_conta", StringType(), True)  # Include the partition column
#         ])
#         empty_df = self.spark.createDataFrame([], empty_schema)
#         mock_read_from_postgres.return_value = self.dfs
#         mock_transform_data.return_value = empty_df
#         mock_data_governance.return_value = empty_df

#         # Call the function
#         output_path = "/tmp/test_output"
#         mode = "overwrite"
#         _write_csv(output_path, mode)

#         # Assertions
#         mock_read_from_postgres.assert_called_once()
#         mock_transform_data.assert_called_once()
#         mock_data_governance.assert_called_once()
#         self.assertEqual(empty_df.count(), 0)


# if __name__ == "__main__":
#     unittest.main()


# # Struc[140 chars]do', LongType(), True), StructField('vlr_trans[408 chars]ue)])
# # Struc[140 chars]do', IntegerType(), True), StructField('vlr_tr[408 chars]ue)])