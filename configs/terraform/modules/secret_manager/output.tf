output "secret_id" {
  value = google_secret_manager_secret.db_credentials.secret_id
}
