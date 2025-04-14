variable "project" {
    description = " Project ID"
    type = string
}

variable "region" {
    description = "Region of bucket"
    type        = string
}

variable "function_name" {
    description = "name of cloud function"
    type        = string
}

variable "environment" {
    description = "Environment Development"
    type        = string
}

variable "bkt_cf_file_path" {
    description = "path of the cloud function file"
    type        = string
}

variable "bkt_cf_file_name" {
    description = "name of the cloud function file"
    type        = string
}

variable "ready_cf_file" {
    description = "ready the cloud function file"
    type        = string
}