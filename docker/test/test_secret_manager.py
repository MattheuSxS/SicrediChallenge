import json
import pytest
from unittest import mock
from google.api_core.exceptions import GoogleAPICallError, RetryError
from src.modules.secret_manager import get_secret

@mock.patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_secret_success(mock_secret_manager_client):
    # Mock the response from Secret Manager
    mock_client_instance = mock_secret_manager_client.return_value
    mock_response = mock.Mock()
    mock_response.payload.data.decode.return_value = json.dumps({"key": "value"})
    mock_client_instance.access_secret_version.return_value = mock_response

    # Call the function
    project_id = "fake_project_id"
    secret_id = "fake_secret_id"
    result = get_secret(project_id, secret_id)

    # Assertions
    mock_secret_manager_client.assert_called_once()
    mock_client_instance.access_secret_version.assert_called_once_with(
        request={"name": f"projects/{project_id}/secrets/{secret_id}/versions/latest"}
    )
    assert result == {"key": "value"}


@mock.patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_secret_google_api_call_error(mock_secret_manager_client):
    # Mock the client to raise GoogleAPICallError
    mock_client_instance = mock_secret_manager_client.return_value
    mock_client_instance.access_secret_version.side_effect = GoogleAPICallError("API call failed")

    # Call the function and assert it raises the exception
    with pytest.raises(GoogleAPICallError):
        get_secret("test_project", "test_secret")


@mock.patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_secret_retry_error(mock_secret_manager_client):
    # Mock the client to raise RetryError
    mock_client_instance = mock_secret_manager_client.return_value
    mock_client_instance.access_secret_version.side_effect = RetryError("Retryable error", cause=Exception("Test cause"))

    # Patch the SecretManagerServiceClient to return the mock instance
    with mock.patch("google.cloud.secretmanager.SecretManagerServiceClient", return_value=mock_client_instance):
        # Call the function and assert it raises the exception
        with pytest.raises(RetryError) as exc_info:
            get_secret("test_project", "test_secret")

        # Verify the exception message and cause
        assert str(exc_info.value) == 'Retryable error, last exception: Test cause'
        assert isinstance(exc_info.value.cause, Exception)
        assert str(exc_info.value.cause) == "Test cause"

        # Verify the method was called with the correct arguments
        mock_client_instance.access_secret_version.assert_called_once_with(
            request={"name": "projects/test_project/secrets/test_secret/versions/latest"}
        )

@mock.patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_secret_value_error(mock_secret_manager_client):
    # Mock the response with invalid JSON
    mock_client_instance = mock_secret_manager_client.return_value
    mock_response = mock.Mock()
    mock_response.payload.data.decode.return_value = "invalid_json"
    mock_client_instance.access_secret_version.return_value = mock_response

    # Call the function and assert it raises ValueError
    with pytest.raises(ValueError):
        get_secret("test_project", "test_secret")