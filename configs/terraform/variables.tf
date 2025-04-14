
#   ********************************************************************************************************    #
#                                                    Cloud Project                                              #
#   ********************************************************************************************************    #
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

variable "project_id" {
    description = "What is the project name"
    type        = string
}

#   ********************************************************************************************************    #
#                                             Google Cloud Storage                                              #
#   ********************************************************************************************************    #
variable "bkt_names" {
    description = "The name of the buckets"
    type        = list(string)
}

variable "bkt_class_standard" {
    description = "The class of the bucket"
    type        = string
}

variable "bkt_class_nearline" {
    description = "The class of the bucket"
    type        = string
}

variable "bkt_class_coldline" {
    description = "The class of the bucket"
    type        = string
}


variable "bkt_class_archive" {
    description = "The class of the bucket"
    type        = string
}

#   ********************************************************************************************************    #
#                                                Google Cloud Sql                                               #
#   ********************************************************************************************************    #
variable "postgres_instance_name" {
    description = "The name of the Cloud SQL instance"
    type        = string
}

variable "postgres_db_name" {
    description = "The name of the database to create"
    type        = string
}

variable "postgres_schema" {
    description = "The name of the schema to create"
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

#   ********************************************************************************************************    #
#                                          IAM Members Permissions                                              #
#   ********************************************************************************************************    #

variable "members" {
    description = "The members that will have access to the buckets"
    type        = list(string)
}

#   ********************************************************************************************************    #
#                                              Google Cloud Function                                            #
#   ********************************************************************************************************    #
variable "function_name" {
    description = "name of the function"
    type        = string
}

variable "sa_cloud_function" {
    description = "The service account to grant the roles"
    type        = string
}

#   ********************************************************************************************************    #
#                                                   Secret Manager                                              #
#   ********************************************************************************************************    #
variable "secret_db_credentials" {
    description = "secret name of the db credentials"
    type        = string
}

#   ********************************************************************************************************    #
#                                               Cloud Composer                                                  #
#   ********************************************************************************************************    #
variable "airflow_name" {
    description = "The name of the Composer environment"
    type        = string
}

variable "image_version" {
    description = "The version of the Composer environment"
    type        = string
}