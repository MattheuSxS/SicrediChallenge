output "access_allowed" {
    description = "The service account to grant the roles"
    value       = google_project_iam_member.storage_admin.member
}

output "sa_airflow" {
    description = "The service account to grant the roles"
    value       = google_service_account.sa_airflow.email
}

output "sa_role_composer_worker" {
    description = "The service account to grant the roles"
    value       = google_project_iam_member.composer_worker.id
}

output "sa_role_storage_object_admin" {
    description = "The service account to grant the roles"
    value       = google_project_iam_member.storage_object_admin.id
}

output "sa_role_cloudfunctions_invoker" {
    description = "The service account to grant the roles"
    value       = google_project_iam_member.cloudfunctions_invoker.id
}