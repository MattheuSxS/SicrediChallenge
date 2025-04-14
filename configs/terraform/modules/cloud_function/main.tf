data "archive_file" "source_cf" {
    type        = "zip"
    source_dir  = "../../docker/src/"
    output_path = "../../docker/src/index.zip"
}

resource "google_cloudfunctions2_function" "function" {
  depends_on    = [var.ready_cf_file]
  project       = var.project
  location      = var.region
  name          = var.function_name
  description   = "Insert the datas into Postgres"

  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = var.bkt_cf_file_path
        object = var.bkt_cf_file_name
      }
    }
  }

  labels = {
    "created_by": "terraform",
    "layer": var.environment
  }

  service_config {
    min_instance_count  = 1
    max_instance_count  = 2
    available_memory    = "512M"
    timeout_seconds     = 1000

  }

  lifecycle {
    ignore_changes = [
      build_config,
      service_config,
    ]
  }

}