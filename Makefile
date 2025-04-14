.PHONY: deploy-spark-dev destroy-spark-dev spark-job-dev _sleep exec-job-dev deploy-spark-prod destroy-spark-prod spark-job-prod test coverage

deploy-spark-dev:
	docker compose -f ./docker/docker-compose.yml up -d --scale spark-worker=2
	@echo "Spark Cluster is up!"

destroy-spark-dev:
	docker compose -f ./docker/docker-compose.yml down
	@echo "Spark Cluster is down!"

spark-job-dev:
	docker exec pyspark-master spark-submit \
		--deploy-mode client \
		--jars /opt/spark/drivers/postgresql-42.7.4.jar \
		/opt/spark/apps/app_spark.py \
		--output_path "/opt/spark/data" \
		--mode "overwrite"

	@echo "Spark-Submit done!"

_sleep:
	@echo "Waiting for a few seconds..."
	sleep 5

exec-job-dev: deploy-spark-dev _sleep spark-job-dev destroy-spark-dev
	@echo "whole process done!"


#TODO: Implement the prod version
deploy-spark-prod:
	(cd ./configs/terraform/ && terraform init && terraform apply -auto-approve)
	@echo "Spark Cluster is up!"

spark-job-prod:
	gcloud dataproc jobs submit pyspark ./docker/jobs/app_spark.py \
		--cluster=sicredi-cluster \
		--region=us-east1 \
		--jars=gs://bkt-si-dataproc/spark_drivers/postgresql-42.7.4.jar \
		--output_path=gs://bkt-si-output-path \
		--mode=overwrite \
		--data_secret='{"project_id": "mts-default-projetct", "secret_id": "secret_db_credentials"}'
	@echo "Spark-Submit done!"

destroy-spark-prod:
	(cd ./configs/terraform/ && terraform destroy -auto-approve)
	@echo "Spark Cluster is down!"


test:
	@echo "Running tests..."
	@pytest -v \
	--junitxml=tests-result.xml \
	--html=dist/reports/html/tests-result.html

coverage:
	@echo "Running tests with coverage..."
	@pytest -v \
	--junitxml=tests-result.xml \
	--html=dist/reports/html/tests-result.html \
	--cov-report term \
	--cov-branch \
	--cov=. \
	&& coverage xml -o coverage.xml \
	&& coverage html -d dist/reports/html/coverage_html
