-- Garante que estamos usando o banco de dados nfe_agente
-- O MYSQL_DATABASE no docker-compose já deve ter criado, mas garantimos o uso.
USE nfe_agente;

-- Tabela para o Endereço do Emitente
CREATE TABLE IF NOT EXISTS endereco (
    id INT AUTO_INCREMENT PRIMARY KEY,
    logradouro VARCHAR(255) NOT NULL,
    numero VARCHAR(255),
    bairro VARCHAR(255),
    municipio VARCHAR(255) NOT NULL,
    uf CHAR(255) NOT NULL,
    cep VARCHAR(255)
);

-- Tabela para o Emitente
CREATE TABLE IF NOT EXISTS emitente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cnpj_emitente VARCHAR(255) NOT NULL UNIQUE,
    nome_emitente VARCHAR(255) NOT NULL,
    ie_emitente VARCHAR(255),
    id_endereco INT,
    FOREIGN KEY (id_endereco) REFERENCES endereco(id)
);

-- Tabela para os Detalhes dos Tributos
CREATE TABLE IF NOT EXISTS tributos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    total_tributos_incidentes DECIMAL(10, 2),
    tributos_federais DECIMAL(10, 2),
    percentual_federais DECIMAL(5, 2),
    tributos_estaduais DECIMAL(10, 2),
    percentual_estaduais DECIMAL(5, 2),
    fonte_tributos VARCHAR(255),
    lei_tributos VARCHAR(255)
);

-- Tabela para os Totais
CREATE TABLE IF NOT EXISTS totais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qtd_total_itens INT NOT NULL,
    valor_total_produtos DECIMAL(10, 2),
    descontos_gerais DECIMAL(10, 2) NOT NULL,
    acrescimos_gerais DECIMAL(10, 2) NOT NULL,
    valor_total_a_pagar DECIMAL(10, 2) NOT NULL,
    id_tributos INT,
    FOREIGN KEY (id_tributos) REFERENCES tributos(id)
);

-- Tabela para o Pagamento
CREATE TABLE IF NOT EXISTS pagamento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    forma_pagamento VARCHAR(255) NOT NULL,
    valor_pago DECIMAL(10, 2) NOT NULL,
    troco DECIMAL(10, 2),
    meio_pagamento_detalhe VARCHAR(255)
);

-- Tabela para os Dados Adicionais
CREATE TABLE IF NOT EXISTS dados_adicionais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    caixa VARCHAR(255),
    operador VARCHAR(255),
    vendedor VARCHAR(255)
);

-- Tabela Principal da Nota Fiscal (NFe)
CREATE TABLE IF NOT EXISTS nfe (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_emitente INT,
    chave_acesso VARCHAR(255),
    protocolo_autorizacao VARCHAR(255),
    data_autorizacao DATE,
    hora_autorizacao TIME,
    numero_nfce VARCHAR(255),
    serie_nfce VARCHAR(255),
    consumidor VARCHAR(255),
    id_totais INT,
    id_pagamento INT,
    id_dados_adicionais INT,
    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_emitente) REFERENCES emitente(id),
    FOREIGN KEY (id_totais) REFERENCES totais(id),
    FOREIGN KEY (id_pagamento) REFERENCES pagamento(id),
    FOREIGN KEY (id_dados_adicionais) REFERENCES dados_adicionais(id)
);

-- Tabela para os Itens da Nota Fiscal
CREATE TABLE IF NOT EXISTS item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_nfe INT NOT NULL,
    numero_item INT NOT NULL,
    codigo_produto VARCHAR(255),
    descricao VARCHAR(255) NOT NULL,
    quantidade DECIMAL(10, 4) NOT NULL,
    unidade VARCHAR(255) NOT NULL,
    valor_unitario DECIMAL(10, 2) NOT NULL,
    desconto_item DECIMAL(10, 2),
    valor_total_item DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (id_nfe) REFERENCES nfe(id) ON DELETE CASCADE
);