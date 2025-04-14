#!/bin/bash

SPARK_WORKLOAD=$1

echo "SPARK_WORKLOAD: $SPARK_WORKLOAD"

# Tempo de espera para garantir que o PostgreSQL esteja pronto
# Execute o script Python
if [ "$SPARK_WORKLOAD" == "master" ];
then
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
    echo "Running Python job: /opt/spark/src/main.py"
    python /opt/spark/src/main.py
else
    echo "Python script /opt/spark/src/main.py not found!"
fi


if [ "$SPARK_WORKLOAD" == "master" ];
then
  start-master.sh -p 7077
elif [ "$SPARK_WORKLOAD" == "worker" ];
then
  start-worker.sh spark://spark-master:7077
elif [ "$SPARK_WORKLOAD" == "history" ]
then
  start-history-server.sh
fi

