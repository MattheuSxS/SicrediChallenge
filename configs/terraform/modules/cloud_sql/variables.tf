variable "project" {
    description = "The project ID to deploy the Cloud SQL instance"
    type        = string
}

variable "region" {
    description = "The region to deploy the Cloud SQL instance"
    type        = string
}

variable "postgres_instance_name" {
    description = "The name of the Cloud SQL instance"
    type        = string
}

variable "postgres_db_name" {
    description = "The name of the database to create"
    type        = string
}

variable "postgres_username" {
    description = "the username for the user"
    type        = string
}

variable "postgres_password" {
    description = "The password for the user"
    type        = string
}

variable "environment" {
    description = "Environment Development"
    type        = string
}

variable "bkt_config_bucket" {
    description = "The name of the bucket to store the configuration files"
    type        = string
}

variable "list_file_db_config" {
    description = "The name of the init.sql file"
    type        = map(string)
}

variable "access_allowed"{
    description = "commit of the access allowed"
    type        = string
}