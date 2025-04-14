locals {
  onprem = ["80.233.56.217"]
}

resource "google_sql_database_instance" "sicredi-instance-postgres" {
  name                            = var.postgres_instance_name
  project                         = var.project
  region                          = var.region
  root_password                   = var.postgres_password
  database_version                = "POSTGRES_17"
  deletion_protection             = "false"

  settings {
    edition = "ENTERPRISE"
    tier = "db-custom-8-30720"

    user_labels = {
      created_by = "terraform"
      env = var.environment
    }
    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
          name  = "allow-all"
          value = "0.0.0.0/0"
        }
      }
    }

    lifecycle {
        prevent_destroy = false
    }
}


resource "google_sql_database" "sicredi-database" {
  depends_on  = [
    google_sql_database_instance.sicredi-instance-postgres
  ]

  name        = var.postgres_db_name
  project     = var.project
  instance    = google_sql_database_instance.sicredi-instance-postgres.name
  charset     = "UTF8"

  lifecycle {
    prevent_destroy = false
  }
}


resource "google_sql_user" "users" {
  depends_on  = [
    google_sql_database_instance.sicredi-instance-postgres,
    google_sql_database.sicredi-database
  ]

  project         = var.project
  instance        = google_sql_database_instance.sicredi-instance-postgres.name
  name            = var.postgres_username
  password        = var.postgres_password

  type            = "BUILT_IN"
  deletion_policy = "ABANDON"
}


resource "null_resource" "import-sql" {
  depends_on = [
    var.bkt_config_bucket,
    var.access_allowed
  ]

  for_each = var.list_file_db_config
  provisioner "local-exec" {
    command = <<EOT
    echo "Waiting for the database to be ready"
    sleep 30
    gcloud sql import sql ${google_sql_database_instance.sicredi-instance-postgres.name} \
        gs://${var.bkt_config_bucket}/${each.value} \
        --project=${var.project} \
        --user=${var.postgres_username} \
        --database=${google_sql_database.sicredi-database.name} \
        --quiet
  EOT
  }
}