#   ********************************************************************************************************    #
#                                               Create Service Account                                          #
#   ********************************************************************************************************    #
resource "google_service_account" "sa_airflow" {
    project = var.project
    account_id = "sa-airflow"
    display_name = "Service Account for Airflow"
}


#   ********************************************************************************************************    #
#                                               Grant Roles to Service Account                                  #
#   ********************************************************************************************************    #
resource "google_project_iam_member" "storage_admin" {
    depends_on = [var.db_service_account]

    project = var.project
    role    = "roles/storage.admin"
    member  = "serviceAccount:${var.db_service_account}"
}

resource "google_project_iam_member" "secret_manager_v0" {
    depends_on = [var.sa_cloud_function]

    project = var.project
    role    = "roles/secretmanager.secretAccessor"
    member  = "serviceAccount:${var.sa_cloud_function}"
}

resource "google_project_iam_member" "secret_manager_v1" {
    depends_on = [var.sa_cloud_function]

    project = var.project
    role    = "roles/secretmanager.secretAccessor"
    member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "composer_worker" {
  project = var.project
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "storage_object_admin" {
  project = var.project
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "cloudfunctions_invoker" {
  project = var.project
  role    = "roles/cloudfunctions.invoker"
  member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "cloudfunctions_2g_invoker" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "airflow_token_creator" {
  project = var.project
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "dataproc_editor_v0" {
  project = var.project
  role    = "roles/dataproc.editor"
  member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "dataproc_editor_v2" {
  project = var.project
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.sa_airflow.email}"
}

resource "google_project_iam_member" "dataproc_editor_v3" {
  project = var.project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.sa_cloud_function}"
}
