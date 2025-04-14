output "bkt_config_bucket" {
    description = "The name of the bucket to store the configuration files"
    value       = google_storage_bucket.bucket[1].name
}

output "list_file_db_config" {
  description = "The name of the files in the bucket"
  value       = { for k, v in google_storage_bucket_object.files-db-config : k => v.name }
}

output "bkt_cf_file_path" {
  description = "name of the bucket of the cloud function"
  value       = google_storage_bucket.bucket[2].name
}

output "bkt_cf_file_name" {
  description = "name of the file of the cloud function"
  value = google_storage_bucket_object.cf-file.name
}

output "ready_cf_file" {
  description = "ready the cloud function file"
  value       = google_storage_bucket_object.cf-file.name
}