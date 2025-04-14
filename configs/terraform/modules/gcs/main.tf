#   ********************************************************************************************************    #
#                                                 Create GCS Buckets                                            #
#   ********************************************************************************************************    #
resource "google_storage_bucket" "bucket" {
    count                           = length(var.bkt_names)
    name                            = "bkt-${var.bkt_names[count.index]}"
    project                         = var.project
    location                        = var.region
    storage_class                   = var.bkt_class_standard
    force_destroy                   = true
    uniform_bucket_level_access     = true

    versioning {
        enabled = true
    }

    lifecycle_rule {
        condition {
            age = 90
        }
        action {
            type = "SetStorageClass"
            storage_class = var.bkt_class_nearline
        }
    }

    lifecycle_rule {
        condition {
            age = 150
        }
        action {
            type = "SetStorageClass"
            storage_class = var.bkt_class_coldline
        }
    }

    lifecycle_rule {
        condition {
            age = 180
        }
        action {
            type = "SetStorageClass"
            storage_class = var.bkt_class_archive
        }
    }

    lifecycle_rule {
        condition {
            num_newer_versions = 3
        }
        action {
            type = "Delete"
        }
    }

    labels = {
        "created_by": "terraform",
        "env": var.environment
    }
}

#   ********************************************************************************************************    #
#                                                Sendig files to GCS                                            #
#   ********************************************************************************************************    #
resource "google_storage_bucket_object" "files-db-config" {
    depends_on = [google_storage_bucket.bucket]

    for_each    = fileset("../../docker/drivers/", "**.sql")
    name        = each.value
    bucket      = google_storage_bucket.bucket[1].name
    source      = "../../docker/drivers/${each.value}"
}

resource "google_storage_bucket_object" "cf-file" {
    depends_on = [
        google_storage_bucket.bucket,
        var.cf_file_path
    ]

    name            = "index.zip"
    bucket          = google_storage_bucket.bucket[2].name
    source          = var.cf_file_path
    content_type    = "application/zip"

  lifecycle {
    ignore_changes = [detect_md5hash]
  }
}

resource "google_storage_bucket_object" "my_dags" {

    for_each    = fileset("../pipe/", "**_prd.py")
    name        = "dags/${each.value}"
    bucket      = var.bkt_composer
    source      = "../pipe/${each.value}"
}

resource "google_storage_bucket_object" "variables" {

    for_each    = fileset("../pipe/variables/", "**_prd.json")
    name        = "variables/${each.value}"
    bucket      = var.bkt_composer
    source      = "../pipe/variables/${each.value}"
}

resource "google_storage_bucket_object" "spark_job" {

    for_each    = fileset("../../docker/jobs/", "**.py")
    name        = "spark_job/${each.value}"
    bucket      = google_storage_bucket.bucket[3].name
    source      = "../../docker/jobs/${each.value}"
}

resource "google_storage_bucket_object" "spark_drivers" {

    for_each    = fileset("../../docker/drivers/", "**.jar")
    name        = "spark_drivers/${each.value}"
    bucket      = google_storage_bucket.bucket[3].name
    source      = "../../docker/drivers/${each.value}"
}

resource "google_storage_bucket_object" "spark_drivers_v1" {

    for_each    = fileset("../../docker/drivers/dataproc/", "**.sh")
    name        = "spark_drivers/${each.value}"
    bucket      = google_storage_bucket.bucket[3].name
    source      = "../../docker/drivers/dataproc/${each.value}"
}


resource "null_resource" "dataproc_files" {

  depends_on = [google_storage_bucket.bucket]

  provisioner "local-exec" {
    command = <<-EOT
        gcloud storage cp gs://goog-dataproc-initialization-actions-${var.region}/cloud-sql-proxy/cloud-sql-proxy.sh \
            gs://${google_storage_bucket.bucket[3].name}/cloud-sql-proxy/cloud-sql-proxy.sh
    EOT
  }
}


#   ********************************************************************************************************    #
#                                               Delete GCS Buckets                                              #
#   ********************************************************************************************************    #
resource "null_resource" "bkt_compose_delete" {

  depends_on = [
    var.bkt_composer,
    google_storage_bucket_object.my_dags
    ]

  triggers = {
    bucket_name = var.bkt_composer
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      gcloud storage rm -r --recursive gs://${self.triggers.bucket_name}
    EOT
  }
}

#   ********************************************************************************************************    #
#                                                 Security Policies                                             #
#   ********************************************************************************************************    #
data "google_iam_policy" "admin" {
    binding {
        role = "roles/storage.admin"
        members = var.members
    }
}

resource "google_storage_bucket_iam_policy" "policy" {
    count = length(var.bkt_names)
    bucket = google_storage_bucket.bucket[count.index].name
    policy_data = data.google_iam_policy.admin.policy_data
}