# ================================================================================================================================= --
# Object................: Sicredi Challenge                                                                            .
# Creation Date.........: 2025/03/04                                                                                   |
# Version...............: 0.0.1                                                                                       < >
# Project...............: Technical challenge                                                                          |
# VS....................:                                                                  ______                    (^ ^)
# Department............: Arquitetura e Engenharia de Dados                      .-,__,-. |Eatons|                    `|`
# Owner.................: Gerencia: gd13 - Engenharia B2C                        | ]""[ | |""""""|       ,.,__         |
# Author................: Matheus Dos S. Silva | matheus.s@                      | |""| | |""""""|     /`.     ` ;     |
# maintainer............:                                                        | |""| | |""""""|   /`.  '.       ;   |
# Modification Date.....:                                                        | |""| | |""""""| /`.  '.  .       ; /^\
# Obs...................:                                    ---Toronto----------'-'--'-'-'------''---'---'--'-------'---'----ldb
# ================================================================================================================================= --

import json
import logging
import subprocess
from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from datetime import timedelta, datetime
from google.protobuf.duration_pb2 import Duration
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocSubmitJobOperator,
    DataprocDeleteClusterOperator,
)


# ====================================================================================================================================
#                                                  ~~~~> Loggin Globais <~~~~                                                        #
# ====================================================================================================================================
logging.basicConfig(
    format=("%(asctime)s | %(levelname)s | File_name ~> %(module)s.py "
            "| Function ~> %(funcName)s | Line ~~> %(lineno)d  ~~>  %(message)s"),
    level=logging.INFO
)


# ====================================================================================================================================
#                                              ~~~~> Variaveis Globais <~~~~                                                         #
# ====================================================================================================================================
__artefact__    = "pipeline_trigger_prd"
__start_job__   = datetime.now() - timedelta(days=1)
__description__ = "Pipeline to trigger a Spark job"


# ====================================================================================================================================
#                                           ~~~~> Variaveis Globais Airflow <~~~~                                                    #
# ====================================================================================================================================
__env_var__         = Variable.get(__artefact__, deserialize_json=True)

VAR_PRJ_NAME        = __env_var__['project_vars']
VAR_PRJ_REGION      = __env_var__['dataproc_config']['region']
VAR_CLUSTER_NAME    = __env_var__['dataproc_config']['cluster_name']


# ====================================================================================================================================
#                                           ~~~~> Propriedades da DAG <~~~~                                                          #
# ====================================================================================================================================
default_args = dict(
    owner           = "Matheus S. Silva",
    start_date      =  __start_job__,
    depends_on_past = False,
    retries         = 3,
    retry_delay     = timedelta(minutes=__env_var__['retry_delay']),
    dagrun_timeout  = timedelta(minutes=__env_var__['dagrun_timeout']),
)

dag_kwargs = dict(
    default_args        = default_args,
    description         = __description__,
    schedule_interval   = __env_var__['schedule_interval'],
    catchup             = False,
    concurrency         = 2,
    tags                = ["MTS - Pipeline"],
)


# ====================================================================================================================================
#                                                     ~~~~> Functions <~~~~                                                          #
# ====================================================================================================================================
def dummy(name:str) -> None:
    return EmptyOperator(
        task_id=name
    )

@task(task_id="call_gcf_function")
def call_gcf_function() -> str:
    """
    Calls a Google Cloud Function using a POST request with curl.

    This function constructs a curl command to call a Google Cloud Function.
    It includes an authorization token and sends a JSON payload. The response
    from the cloud function is then parsed and checked for success.

    Returns:
        str: A string indicating the status and message from the cloud function response.

    Raises:
        Exception: If the cloud function response status is not "success", an exception is raised with the response message.
    """
    cmd = \
        f"""
            curl -X POST {__env_var__['cloud_function_url']} \
                -H "Authorization: bearer $(gcloud auth print-identity-token)" \
                -H "Content-Type: application/json" \
                -d '{json.dumps(
                    {
                        "project_id": VAR_PRJ_NAME,
                        "secret_id": __env_var__['secret_id'],}
                )}'
        """

    stdout, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    response = stdout.decode('utf-8').strip()

    result = json.loads(response)
    if result["status"] != "success":
        raise Exception(result['message'])

    return f"Status: {result['status']} {result['message']}"


# ====================================================================================================================================
#                                                       ~~~~> Funções Utils <~~~~                                                    #
# ====================================================================================================================================
def get_pyspark_job_config(cfg, task_id):
    job_id = task_id[0:78] + "_" + datetime.now().strftime("%Y%m%d%H%M%S%f")
    cfg["reference"]["job_id"] = job_id
    # cfg["pyspark_job"]["args"].append(job_id)
    return cfg


# ====================================================================================================================================
#                                                    ~~~~> Variaveis DataProc <~~~~                                                  #
# ====================================================================================================================================
def cluster_config() -> dict:
    durationIdle = Duration()
    durationIdle.seconds = 3600

    durationAuto = Duration()
    durationAuto.seconds = 3600 * (12 * 2 + 1)

    CLUSTER_NAME = __env_var__['dataproc_config']['cluster_name']
    CLUSTER_CONFIG = __env_var__['dataproc_config']['cluster_config']
    # CLUSTER_CONFIG["gce_cluster_config"]["zone_uri"] = f"https://www.googleapis.com/compute/v1/projects/{VAR_PRJ_NAME}/zones/us-east1-b"
    # CLUSTER_CONFIG["gce_cluster_config"]["subnetwork_uri"] = f"projects/{VAR_PRJ_NAME}/regions/{VAR_PRJ_REGION}/subnetworks/dataproc-internal-workloads"
    # CLUSTER_CONFIG["gce_cluster_config"]["subnetwork_uri"] = "projects/shared-services-268518/regions/us-east1/subnetworks/shared" # In creating...
    # CLUSTER_CONFIG["gce_cluster_config"]["tags"] = CLUSTER_CONFIG["gce_cluster_config"]["tags"].extend('Test') # In creating...
    CLUSTER_CONFIG["software_config"]["image_version"] = "2.2-debian12"
    CLUSTER_CONFIG["lifecycle_config"]["idle_delete_ttl"] = durationIdle
    CLUSTER_CONFIG["lifecycle_config"]["auto_delete_ttl"] = durationAuto
    BKT_CLUSTER = __env_var__["dataproc_config"]["bkt_gcp_dataproc"]

    PYSPARK_JOB = {
        "reference": {"project_id": VAR_PRJ_NAME},
        "placement": {"cluster_name": CLUSTER_NAME},
        "pyspark_job": {
            "main_python_file_uri": f"gs://{BKT_CLUSTER}/spark_job/app_spark.py",
            "args": ["--output_path", "gs://bkt-si-output-path", "--mode", "overwrite", "--data_secret", json.dumps({"project_id": VAR_PRJ_NAME, "secret_id": __env_var__['secret_id']})],
            "jar_file_uris": [f"gs://{BKT_CLUSTER}/spark_drivers/postgresql-42.7.4.jar"],
        },
    }

    return \
        {
            "cluster_name": CLUSTER_NAME,
            "cluster_config": CLUSTER_CONFIG,
            "pyspark_job": PYSPARK_JOB
        }


# ====================================================================================================================================
#                                               ~~~~> Functions Cloud DataProc <~~~~                                                 #
# ====================================================================================================================================
def create_dataproc_cluster() -> DataprocCreateClusterOperator:

    data_dict = cluster_config()
    return \
        DataprocCreateClusterOperator(
            task_id             = f"create_dataproc_cluster",
            project_id          = VAR_PRJ_NAME,
            cluster_name        = data_dict["cluster_name"],
            labels              = {"projeto": "vd", "vsname": "vendadireta"},
            cluster_config      = data_dict["cluster_config"],
            region              = VAR_PRJ_REGION,
            delete_on_error     = True,
            use_if_exists       = True,
            retries             = 1,
            trigger_rule        = TriggerRule.ONE_SUCCESS
        )


def spark_submit_job() -> DataprocSubmitJobOperator:

    data_dict = cluster_config()
    return \
        DataprocSubmitJobOperator(
            task_id             = f"spark_submit_job",
            job                 = get_pyspark_job_config(data_dict["pyspark_job"], "get_data_cloud_sql"),
            region              = VAR_PRJ_REGION,
            project_id          = VAR_PRJ_NAME,
            retries             = 1,
            execution_timeout   = timedelta(minutes=30),
        )


def delete_dataproc_cluster() -> DataprocDeleteClusterOperator:

    data_dict = cluster_config()
    return \
        DataprocDeleteClusterOperator(
            task_id         = f"delete_dataproc_cluster",
            project_id      = VAR_PRJ_NAME,
            cluster_name    = data_dict["cluster_name"],
            region          = VAR_PRJ_REGION,
            trigger_rule    = TriggerRule.ALL_DONE,
            retries         = 2
        )


# ====================================================================================================================================
#                                                 ~~~~> Airflow Pipeline <~~~~                                                       #
# ====================================================================================================================================
with DAG(dag_id=__artefact__, start_date=default_args['start_date'], **dag_kwargs):

    dummy("Start") >> call_gcf_function() >> create_dataproc_cluster() >> spark_submit_job() >> delete_dataproc_cluster() >> dummy("End")