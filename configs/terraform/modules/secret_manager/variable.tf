variable "secret_db_credentials" {
  description   = "credentials of the database"
  type          = string
}

variable "environment" {
    description = "Environment Development"
    type        = string
}

variable "postgres_username" {
  description   = "username of the database"
  type          = string
}

variable "postgres_password" {
  description   = "password of the database"
  type          = string
}

variable "postgres_db_name" {
  description   = "name of the database"
  type          = string
}

variable "postgres_schema" {
  description   = "schema of the database"
  type          = string
}

variable "postgres_uri" {
  description   = "uri of the database"
  type          = string
}
