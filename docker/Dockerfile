# Imagem do SO usada como base
FROM python:3.12-bullseye as spark-base

# Atualiza o SO e instala pacotes
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      sudo \
      curl \
      vim \
      nano \
      unzip \
      rsync \
      openjdk-11-jdk \
      build-essential \
      software-properties-common \
      ssh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Variáveis de ambiente
ENV SPARK_HOME=${SPARK_HOME:-"/opt/spark"}
ENV HADOOP_HOME=${HADOOP_HOME:-"/opt/hadoop"}
ENV SPARK_VERSION=3.5.4
ENV HADOOP_VERSION=3

# Cria as pastas
RUN mkdir -p ${HADOOP_HOME} && mkdir -p ${SPARK_HOME}
WORKDIR ${SPARK_HOME}

# Download do arquivo de binários do Spark
RUN curl "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" -o spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
 && tar xvzf spark-${SPARK_VERSION}-bin-hadoop3.tgz --directory /opt/spark --strip-components 1 \
 && rm -rf spark-${SPARK_VERSION}-bin-hadoop3.tgz

# Prepara o ambiente com PySpark
FROM spark-base as pyspark

# Instala as dependências Python
COPY ./requirements.txt .

# Cria a pasta do driver
RUN mkdir driver

# Instala as dependências Python
RUN pip3 install -r requirements.txt

# Mais variáveis de ambiente
ENV PATH="/opt/spark/sbin:/opt/spark/bin:${PATH}"
ENV SPARK_HOME="/opt/spark"
ENV SPARK_MASTER="spark://spark-master:7077"
ENV SPARK_MASTER_HOST spark-master
ENV SPARK_MASTER_PORT 7077
ENV PYSPARK_PYTHON python3
ENV SPARK_NO_DAEMONIZE=true

# Copia o arquivo de configuração do Spark para a imagem
COPY conf/spark-defaults.conf "$SPARK_HOME/conf"

# Permissões
RUN chmod u+x /opt/spark/sbin/* && \
    chmod u+x /opt/spark/bin/*

# Variável PYTHONPATH
ENV PYTHONPATH=$SPARK_HOME/python/:$PYTHONPATH

# Copia o script de inicialização dos serviços para a imagem
COPY entrypoint.sh .

# Ajusta o privilégio
RUN chmod +x entrypoint.sh

# Executa o script quando inicializar um container
ENTRYPOINT ["./entrypoint.sh"]

