variable "project" {
    description = "The project ID to deploy the IAM resources"
    type        = string
}

variable "db_service_account" {
    description = "The service account to grant the roles"
    type        = string
}

variable "sa_cloud_function" {
    description = "The service account to grant the roles"
    type        = string
}