variable "region" {
    description = "where the resources will be created"
    type        = string
}

variable "environment" {
    description = "What is the environment"
    type        = string
    default     = "development"
}

variable "project" {
    description = "What is the project name"
    type        = string
}

variable "airflow_name" {
    description = "The name of the Composer environment"
    type        = string
}

variable "project_id" {
    description = "What is the project name"
    type        = string
}

variable "secret_id" {
    description = "What is the project name"
    type        = string
}

variable "image_version" {
    description = "The version of the Composer image"
    type        = string
}

variable "sa_airflow" {
    description = "The service account to grant the roles"
    type        = string
}

variable "sa_role_composer_worker" {
    description = "The service account to grant the roles"
    type        = string
}

variable "sa_role_storage_object_admin" {
    description = "The service account to grant the roles"
    type        = string
}

variable "sa_role_cloudfunctions_invoker" {
    description = "The service account to grant the roles"
    type        = string
}

variable "cloud_function_url" {
    description = "The URL of the cloud function"
    type        = string
}