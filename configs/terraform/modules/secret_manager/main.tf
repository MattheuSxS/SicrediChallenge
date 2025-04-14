resource "google_secret_manager_secret" "db_credentials" {
  secret_id = var.secret_db_credentials

  labels = {
    created_by = "terraform"
    env = var.environment
  }

  replication {
    auto {}
  }
}


resource "google_secret_manager_secret_version" "si-db-credentials" {
  secret = google_secret_manager_secret.db_credentials.id
  secret_data = jsonencode({
    POSTGRES_HOST     = var.postgres_uri
    POSTGRES_PORT     = 5432
    POSTGRES_DB       = var.postgres_db_name
    POSTGRES_SCHEMA   = var.postgres_schema
    POSTGRES_USER     = var.postgres_username
    POSTGRES_PASSWORD = var.postgres_password
  })
}
