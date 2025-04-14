import os
import unittest
from flask.wrappers import Request
from unittest.mock import patch, MagicMock
from src.main import main, get_db_credentials


class TestGetDBCredentials(unittest.TestCase):
    def setUp(self):
        self.valid_credentials = {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test_db",
            "POSTGRES_SCHEMA": "public",
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "password",
        }

    def test_success_with_request(self):
        """
        Testa o caso de sucesso onde as credenciais são obtidas de um objeto Request.
        """
        mock_request = MagicMock(spec=Request)
        mock_request.get_json.return_value = {
            "project_id": "test_project",
            "secret_id": "test_secret",
        }

        with patch("src.main.get_secret", return_value=self.valid_credentials):
            credentials = get_db_credentials(mock_request)

        self.assertEqual(credentials, self.valid_credentials)
        mock_request.get_json.assert_called_once_with(silent=True)

    def test_failure_with_invalid_request_json(self):
        """
        Testa o caso de falha onde o JSON do Request é inválido ou ausente.
        """
        mock_request = MagicMock(spec=Request)
        mock_request.get_json.return_value = None

        # Verifica se uma exceção é levantada
        with self.assertRaises(ValueError) as context:
            get_db_credentials(mock_request)
        self.assertEqual(str(context.exception), "Invalid or missing JSON payload in request.")

    def test_success_with_environment_variables(self):
        """
        Testa o caso de sucesso onde as credenciais são obtidas de variáveis de ambiente.
        """

        with patch.dict(os.environ, self.valid_credentials):
            credentials = get_db_credentials()

        self.assertEqual(credentials, self.valid_credentials)

    def test_failure_with_missing_environment_variables(self):
        """
        Testa o caso de falha onde as variáveis de ambiente estão ausentes ou inválidas.
        """
        with patch.dict(os.environ, {}):
            with self.assertRaises(ValueError) as context:
                get_db_credentials()
            self.assertIn("Missing or invalid credentials for:", str(context.exception))

    def test_failure_with_invalid_request_object(self):
        """
        Testa o caso de falha onde o objeto Request é inválido.
        """
        invalid_request = "invalid_request"

        # Verifica se uma exceção é levantada
        with self.assertRaises(ValueError) as context:
            get_db_credentials(invalid_request)
        self.assertEqual(str(context.exception), "Invalid request object. Expected Flask Request or None.")