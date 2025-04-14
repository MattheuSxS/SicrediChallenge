variable "project" {
    description = " Project ID"
    type = string
}

variable "region" {
    description = "Region of bucket"
    type        = string
}

variable "environment" {
    description = "Environment Development"
    type        = string
}

variable "bkt_names" {
    description = "bucket names"
    type = list(string)
}

variable "bkt_class_standard" {
    description = " Value of storage class"
    type    = string
}

variable "bkt_class_nearline" {
    description = " Value of storage class"
    type    = string
}

variable "bkt_class_coldline" {
    description = " Value of storage class"
    type    = string
}

variable "bkt_class_archive" {
    description = " Value of storage class"
    type    = string
}

variable "members" {
    description = "list of members"
    type = list(string)
}

variable "cf_file_path" {
    description = "path of the cloud function file"
    type = string
}

variable "bkt_composer" {
    description = "bucket name"
    type = string
}

variable "bkt_cloud_function" {
    description = "Name of the cloud function bucket"
    type = string
}