output "cf_file_path" {
    description = "path of the cloud function file"
    value = data.archive_file.source_cf.output_path
}

output "cloud_function_url" {
    description = "URL of the cloud function"
    value = google_cloudfunctions2_function.function.url
}

output "bkt_cloud_function" {
    description = "Name of the cloud function bucket"
    value = google_cloudfunctions2_function.function.build_config.0.source.0.storage_source.0.bucket
}