resource "google_composer_environment" "sicredi-composer" {
  depends_on = [var.sa_airflow,
    var.sa_role_composer_worker,
    var.sa_role_storage_object_admin,
    var.sa_role_cloudfunctions_invoker
    ]

  provider = google-beta
  project = var.project
  region = var.region
  name = var.airflow_name

  config {

    environment_size = "ENVIRONMENT_SIZE_MEDIUM"

    software_config {
      image_version = var.image_version
    }

    workloads_config {

      scheduler {
        cpu = 1
        memory_gb = 2.5
        storage_gb = 2
        count = 1
      }
      triggerer {
        count = 3
        cpu = 1
        memory_gb = 1
      }
      web_server {
        cpu = 1
        memory_gb = 2.5
        storage_gb = 2
      }
      worker {
        cpu = 1
        memory_gb = 2
        storage_gb = 2
        min_count = 2
        max_count = 4
      }
    }

    node_config {
      service_account = var.sa_airflow
    }
  }

  labels = {
    "created_by": "terraform",
    "env": var.environment
  }
}


resource "local_file" "create_airflow_variable_script" {
  filename = "./scripts/set_airflow_variables.py"
  content  = <<-EOT
    import json
    import logging
    from pathlib import Path
    from google.cloud import storage
    from airflow.models import Variable


    logging.basicConfig(
        format=("%(asctime)s | %(levelname)s | File_name ~> %(module)s.py "
                "| Function ~> %(funcName)s | Line ~~> %(lineno)d  ~~>  %(message)s"),
        level=logging.INFO
    )


    def read_json_files_from_gcs(bucket_name, prefix=""):
      """
      Read JSON files from a GCS bucket.

      Args:
          bucket_name (str): GCS bucket name.
          prefix (str): Prefix to filter files in the bucket.

      Returns:
          list: List of tuples with file name and JSON content.
      """
      json_data_list = list()

      try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)

        for blob in blobs:
          if blob.name.endswith(".json"):
            file_name = Path(blob.name).stem  # Nome do arquivo sem extensão
            logging.info(f"Reading file {blob.name}")

            json_data = blob.download_as_text()

            try:
              data = json.loads(json_data)
              json_data_list.append((file_name, data))  # Armazena o nome do arquivo e o conteúdo JSON
            except json.JSONDecodeError as e:
              logging.error(f"Error decoding JSON in file {blob.name} - {e}")
            except Exception as e:
              logging.error(f"Unexpected error processing file {blob.name} - {e}")

      except Exception as e:
        logging.error(f"Error accessing GCS bucket {bucket_name} - {e}")

      return json_data_list


    def set_airflow_variables(bucket_name, prefix):
      """
        Reads JSON files from a Google Cloud Storage (GCS) bucket and sets Airflow variables.

        This function reads JSON files from the specified GCS bucket and prefix, and sets Airflow
        variables based on the contents of these files. Each key-value pair in the JSON files is
        set as an Airflow variable.

        Args:
          bucket_name (str): The name of the GCS bucket.
          prefix (str): The prefix path within the GCS bucket where the JSON files are located.

        Returns:
          None

        Logs:
          - An error if no JSON files are found or an error occurs while reading files.
          - An error if a file does not contain a valid JSON dictionary.
          - An error if there is an issue setting the Airflow variables.
          - An info message for each variable successfully created.
      """

      json_data = read_json_files_from_gcs(bucket_name, prefix)

      if not json_data:
        logging.error("No JSON files found or an error occurred while reading files.")
        return

      for file_name, data in json_data:
        if not isinstance(data, dict):
          logging.error(f"File {file_name} does not contain a valid JSON dictionary.")
          continue

        try:
          for key, value in data.items():
            Variable.set(key, json.dumps(value, indent=4))
            logging.info(f"Variable '{file_name}_{key}' created with success")
        except Exception as e:
          logging.error(f"Error setting variables from file '{file_name}' - {e}")


    bucket_name = "${replace(replace(google_composer_environment.sicredi-composer.config[0].dag_gcs_prefix, "gs://", ""), "/dags", "")}"
    prefix = "variables/"

    set_airflow_variables(bucket_name, prefix)
  EOT
}

resource "null_resource" "create_airflow_variable" {

  depends_on = [
    google_composer_environment.sicredi-composer,
    local_file.create_airflow_variable_script
  ]

  provisioner "local-exec" {
    command = <<EOT
      echo "Waiting for Composer to be ready..."
      sleep 30
      gcloud composer environments storage plugins import \
        --environment ${var.airflow_name} \
        --location ${var.region} \
        --source ${local_file.create_airflow_variable_script.filename}
    EOT
  }
}
