output "postgres_uri" {
  description = "value of the public ip"
  value       = google_sql_database_instance.sicredi-instance-postgres.public_ip_address
}

output "sa_database" {
  description = "value of the service account"
  value       = google_sql_database_instance.sicredi-instance-postgres.service_account_email_address
}