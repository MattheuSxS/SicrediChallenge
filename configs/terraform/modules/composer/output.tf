output "bkt_composer" {
  description = "Nome do bucket do Google Cloud Storage criado para o Cloud Composer"
  value       = replace(replace(google_composer_environment.sicredi-composer.config[0].dag_gcs_prefix, "gs://", ""), "/dags", "")
}