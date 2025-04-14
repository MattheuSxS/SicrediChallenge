CREATE SCHEMA IF NOT EXISTS poc;


CREATE TABLE IF NOT EXISTS poc.associado (
    id INTEGER CONSTRAINT pk_id_associado PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    sobrenome VARCHAR(100) NOT NULL,
    idade INT NOT NULL,
    email VARCHAR(100) NOT NULL
);


CREATE TABLE IF NOT EXISTS poc.conta (
    id INTEGER CONSTRAINT pk_id_conta PRIMARY KEY,
    tipo VARCHAR(100) NOT NULL,
    data_criacao DATE NOT NULL,
    id_associado INT NOT NULL,
    CONSTRAINT fk_id_associado FOREIGN KEY(id_associado) REFERENCES poc.associado(id)
);


CREATE TABLE IF NOT EXISTS poc.cartao (
    id INTEGER CONSTRAINT pk_id_cartao PRIMARY KEY,
    num_cartao VARCHAR(20) NOT NULL,
    nom_impresso VARCHAR(100) NOT NULL,
    -- data_criacao DATE NOT NULL DEFAULT CURRENT_DATE,
    id_conta INT NOT NULL,
    id_associado INT NOT NULL,
    CONSTRAINT fk_id_conta FOREIGN KEY(id_conta) REFERENCES poc.conta(id),
    CONSTRAINT fk_id_associado FOREIGN KEY(id_associado) REFERENCES poc.associado(id)
);


CREATE TABLE IF NOT EXISTS poc.movimento (
    id INTEGER CONSTRAINT pk_id_movimento PRIMARY KEY,
    vlr_transacao DECIMAL(10,2) NOT NULL,
    des_transacao VARCHAR(100) NOT NULL,
    data_movimento DATE NOT NULL,
    id_cartao INT NOT NULL,
    CONSTRAINT fk_id_cartao FOREIGN KEY(id_cartao) REFERENCES poc.cartao(id)
);