import pytest
from unittest.mock import patch, MagicMock
import polars as pl
from io import StringIO
from src.modules.conn_postgres import Postgres

@pytest.fixture
def db_credentials():
    return {
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'test_db',
        'POSTGRES_USER': 'test_user',
        'POSTGRES_PASSWORD': 'test_password',
        'POSTGRES_SCHEMA': 'public'
    }


@pytest.fixture
def postgres_instance(db_credentials):
    with patch('psycopg2.connect') as mock_connect:
        mock_connect.return_value = MagicMock()
        return Postgres(db_credentials)


def test_init_connection(db_credentials):
    with patch('psycopg2.connect') as mock_connect:
        Postgres(db_credentials)
        mock_connect.assert_called_once_with(
            host=db_credentials['POSTGRES_HOST'],
            port=db_credentials['POSTGRES_PORT'],
            database=db_credentials['POSTGRES_DB'],
            user=db_credentials['POSTGRES_USER'],
            password=db_credentials['POSTGRES_PASSWORD']
        )


def test_insert_with_copy(postgres_instance, db_credentials):
    mock_cursor = MagicMock()
    postgres_instance.conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Cria um DataFrame de exemplo
    df = pl.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"]
    })

    # Usa um StringIO real para simular o buffer
    with patch('io.StringIO') as mock_stringio:
        mock_buffer = StringIO()  # Buffer real
        mock_stringio.return_value = mock_buffer

        # Mock o método write_csv do DataFrame para escrever no buffer
        def mock_write_csv(buffer, **kwargs):
            buffer.write("1,Alice\n2,Bob\n3,Charlie\n")  # Simula a escrita do DataFrame

        with patch.object(df, 'write_csv', side_effect=mock_write_csv):
            postgres_instance.insert_with_copy("test_table", df)

            # Verifica se o buffer contém os dados esperados
            mock_buffer.seek(0)  # Rebobina o buffer para leitura
            assert mock_buffer.read() == "1,Alice\n2,Bob\n3,Charlie\n"

            # Verifica se o COPY foi executado
            mock_cursor.copy_expert.assert_called_once_with(
                f"COPY {db_credentials['POSTGRES_SCHEMA']}.test_table FROM STDIN WITH CSV",
                mock_buffer
            )

            # Verifica se a transação foi commitada
            postgres_instance.conn.commit.assert_called_once()


def test_insert_with_copy_exception(postgres_instance):
    mock_cursor = MagicMock()
    postgres_instance.conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Simulate an exception during the COPY command
    mock_cursor.copy_expert.side_effect = Exception("COPY command failed")

    df = pl.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"]
    })

    with pytest.raises(Exception, match="COPY command failed"):
        postgres_instance.insert_with_copy("test_table", df)

    # Assert that the transaction was rolled back
    postgres_instance.conn.rollback.assert_called_once()


def test_close_connection(postgres_instance):
    postgres_instance.close_connection()
    postgres_instance.conn.close.assert_called_once()