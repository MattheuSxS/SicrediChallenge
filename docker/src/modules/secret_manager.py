import json
import logging

logging.basicConfig(
    format=("%(asctime)s | %(levelname)s | File_name ~> %(module)s.py "
            "| Function ~> %(funcName)s | Line ~> %(lineno)d  ~~>  %(message)s"),
    level=logging.INFO
)


def get_secret(project_id: str, secret_id: str) -> dict:
    """
        Retrieve a secret from Google Cloud Secret Manager.

        Args:
            project_id (str): The ID of the Google Cloud project.
            secret_id (str): The ID of the secret to retrieve.

        Returns:
            dict: The secret data as a dictionary.

        Raises:
            google.api_core.exceptions.GoogleAPICallError: If the request to the Secret Manager API fails.
            google.api_core.exceptions.RetryError: If the request to the Secret Manager API fails due to a retryable error.
            ValueError: If the response payload cannot be decoded or parsed as JSON.
    """
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()

    logging.info(f"Accessing secret: {secret_id} from project: {project_id}")
    response = client.access_secret_version(request={"name": f"projects/{project_id}/secrets/{secret_id}/versions/latest"})

    payload = response.payload.data.decode("UTF-8")
    return json.loads(payload)


# if __name__ == "__main__":
#     payload = get_secret("316500968288", "secret_db_credentials")
#     print(payload)