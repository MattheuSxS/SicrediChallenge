# ================================================================================================================================= --
# Object................: Sicredi Challenge                                                                            .
# Creation Date.........: 2025/03/04                                                                                   |
# Version...............: 1.2.0                                                                                       < >
# Project...............: Technical challenge                                                                          |
# VS....................:                                                                  ______                    (^ ^)
# Department............: Arquitetura e Engenharia de Dados                      .-,__,-. |Eatons|                    `|`
# Owner.................: Gerencia: gd13 - Engenharia B2C                        | ]""[ | |""""""|       ,.,__         |
# Author................: Matheus Dos S. Silva | matheus.s@                      | |""| | |""""""|     /`.     ` ;     |
# maintainer............:                                                        | |""| | |""""""|   /`.  '.       ;   |
# Modification Date.....: 2025/03/05                                             | |""| | |""""""| /`.  '.  .       ; /^\
# Obs...................:                                    ---Toronto----------'-'--'-'-'------''---'---'--'-------'---'----ldb
# ================================================================================================================================= --


import logging
import subprocess
from airflow import DAG
from datetime import timedelta, datetime
from airflow.operators.empty import EmptyOperator
from airflow.operators.python_operator import PythonOperator



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
__artefact__ = "pipeline-trigger-dev"
__data__ = datetime.now() - timedelta(days=1)

# ====================================================================================================================================
#                                                     ~~~~> Functions <~~~~                                                          #
# ====================================================================================================================================
def trigger_spark_job() -> None:
    cmd = [
        "docker", "exec", "pyspark-master", "spark-submit",
        "--deploy-mode", "client",
        "--jars", "/opt/spark/drivers/postgresql-42.7.4.jar",
        "/opt/spark/apps/app_spark.py",
        "--output_path", "/opt/spark/data",
        "--mode", "overwrite"
    ]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Decode output
        output = stdout.decode("utf-8").strip()
        error = stderr.decode("utf-8").strip()

        if process.returncode == 0:
            logging.info("Spark job executed successfully!")
            logging.info(output)
        else:
            logging.error(f"Spark job failed with error")
            raise Exception(f"Spark job failed with error:\n{error}")

    except Exception as e:
        logging.error(f"Failed to execute Spark job!")
        raise e


def Step(name:str) -> None:
    return EmptyOperator(
        task_id=name
    )

# ====================================================================================================================================
#                                           ~~~~> Propriedades da DAG <~~~~                                                          #
# ====================================================================================================================================
default_args = dict(
    owner                           = "Matheus S. Silva",
    start_date                      =  __data__,
    depends_on_past                 = False,
    retries                         = 3,
    retry_delay                     = timedelta(minutes=10),
    dagrun_timeout                  = timedelta(minutes=20),
)

dag_kwargs = dict(
    default_args        = default_args,
    description         = "Pipeline to trigger a Spark job",
    schedule_interval   = "30 6 * * *",
    catchup             = False,
    concurrency         = 2,
    tags                = ["MTS - Pipeline"],
)

with DAG(dag_id=__artefact__, start_date=default_args['start_date'], **dag_kwargs):

    spark_job = PythonOperator(
        task_id='park_job',
        python_callable=trigger_spark_job
    )

    Step("Start") >> spark_job >> Step("End")
