#   ********************************************************************************************************    #
#                                             Google Cloud Storage                                              #
#   ********************************************************************************************************    #
module "buckets" {
    source              = "./modules/gcs"
    region              = var.region
    environment         = var.environment
    project             = var.project
    bkt_class_standard  = var.bkt_class_standard
    bkt_class_nearline  = var.bkt_class_nearline
    bkt_class_coldline  = var.bkt_class_coldline
    bkt_class_archive   = var.bkt_class_archive
    bkt_names           = var.bkt_names
    members             = var.members
    cf_file_path        = module.cloud_function.cf_file_path
    bkt_composer        = module.composer.bkt_composer
    bkt_cloud_function  = module.cloud_function.bkt_cloud_function
}

#   ********************************************************************************************************    #
#                                               Google Cloud Sql                                                #
#   ********************************************************************************************************    #
module "cloud_sql" {
    source                  = "./modules/cloud_sql"
    project                 = var.project
    region                  = var.region
    environment             = var.environment
    postgres_instance_name  = var.postgres_instance_name
    postgres_db_name        = var.postgres_db_name
    postgres_username       = var.postgres_username
    postgres_password       = var.postgres_password
    bkt_config_bucket       = module.buckets.bkt_config_bucket
    list_file_db_config     = module.buckets.list_file_db_config
    access_allowed          = module.iam.access_allowed
}

#   ********************************************************************************************************    #
#                                             Google Cloud Function                                             #
#   ********************************************************************************************************    #
module "cloud_function" {
    source              = "./modules/cloud_function"
    project             = var.project
    region              = var.region
    environment         = var.environment
    function_name       = var.function_name
    bkt_cf_file_path    = module.buckets.bkt_cf_file_path
    bkt_cf_file_name    = module.buckets.bkt_cf_file_name
    ready_cf_file       = module.buckets.ready_cf_file
}

#   ********************************************************************************************************    #
#                                          IAM Members Permissions                                              #
#   ********************************************************************************************************    #
module "iam" {
    source              = "./modules/iam"
    project             = var.project
    db_service_account  = module.cloud_sql.sa_database
    sa_cloud_function   = var.sa_cloud_function
}

#   ********************************************************************************************************    #
#                                                   Secret Manager                                              #
#   ********************************************************************************************************    #
module "secret_manager" {
    source                  = "./modules/secret_manager"
    secret_db_credentials   = var.secret_db_credentials
    postgres_username       = var.postgres_username
    postgres_password       = var.postgres_password
    postgres_uri            = module.cloud_sql.postgres_uri
    postgres_db_name        = var.postgres_db_name
    postgres_schema         = var.postgres_schema
    environment             = var.environment
}

#   ********************************************************************************************************    #
#                                               Cloud Composer                                                  #
#   ********************************************************************************************************    #
module "composer" {
    source                          = "./modules/composer"
    project                         = var.project
    region                          = var.region
    environment                     = var.environment
    airflow_name                    = var.airflow_name
    project_id                      = var.project_id
    secret_id                       = module.secret_manager.secret_id
    image_version                   = var.image_version
    sa_airflow                      = module.iam.sa_airflow
    sa_role_composer_worker         = module.iam.sa_role_composer_worker
    sa_role_storage_object_admin    = module.iam.sa_role_storage_object_admin
    sa_role_cloudfunctions_invoker  = module.iam.sa_role_cloudfunctions_invoker
    cloud_function_url              = module.cloud_function.cloud_function_url
}