# Use a imagem oficial do Ubuntu como base
FROM google/cloud-sdk:515.0.0-slim

# Mantenedor da imagem (opcional)
LABEL maintainer="Matheus Fidelis <"


# Atualizar os pacotes do sistema e instalar dependências necessárias
RUN apt-get update && \
    apt-get install -y wget unzip curl

# Definir a versão do Terraform (ajuste conforme necessário)
ENV TERRAFORM_VERSION=1.11.2

# Baixar e instalar Terraform
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Definir o comando padrão para execução quando o container for iniciado
CMD ["/bin/bash"]
