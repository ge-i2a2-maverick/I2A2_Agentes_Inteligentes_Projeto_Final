# Sistema Lente Fiscal agente de IA - Processador Automático de NF-e

## 📋 Descrição

Sistema automatizado para processamento de Notas Fiscais Eletrônicas (NF-e e NFC-e) usando MinIO, OpenAI GPT-4 Vision e MySQL.

## 🎯 Funcionalidades

O sistema realiza o seguinte fluxo automático:

1. **Monitora** o bucket `nfe-recebidos` no MinIO a cada 60 segundos
2. **Baixa** os arquivos (PNG, JPG, PDF) encontrados
3. **Extrai** os dados da NF-e usando IA (OpenAI GPT-4 Vision)
4. **Salva** os dados estruturados no banco de dados MySQL
5. **Move** os arquivos processados para o bucket `nfe-processados`
6. **Remove** os arquivos do bucket `nfe-recebidos`
7. **Registra erros** no bucket `nfe-erros` para arquivos com falha

## 📋 Requisitos

- Docker e Docker Compose
- Python 3.11+

## 🚀 Instalação e Execução

### 1. Iniciar os Serviços Docker

```bash
docker-compose up -d
```

Isso iniciará:
- **MinIO** na porta 9010 (API) e 9011 (Console Web)
- **Mysql** na porta 9012

### 2. Instalar dependências projeto

```bash
python3.11 -m venv .venv
pip install -r requirements.txt
```

### 3. Configure o arquivo `.env`

Copie o arquivo `.env.example` e configure as variáveis:

```bash
cp .env.example .env
nano .env
```

**Variáveis importantes:**

```bash
# MinIO
MINIO_ENDPOINT=localhost:39000
MINIO_ACCESS_KEY=usuario-admin
MINIO_SECRET_KEY=sua-senha

# MySQL
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua-senha
DB_DATABASE=nfe-database

# OpenAI
OPENAI_API_KEY=sk-proj-sua-chave-aqui

# Buckets
BUCKET_RECEBIDOS=nfe-recebidos
BUCKET_PROCESSADOS=nfe-processados
BUCKET_ERROS=nfe-erros

# Intervalo de verificação (segundos)
INTERVALO_VERIFICACAO=60
```

## ▶️ Executar a aplicação

Processo batch
```bash
python src/main/main.py
```

Portal
```bash
streamlit run src/main/app.py
```

A aplicação estará disponível em: `http://localhost:8501`

## 🔐 Credenciais de Acesso

### Aplicação Streamlit
- **Usuário**: `usuario-admin`
- **Senha**: `sua-senha`

### MinIO (se usar Docker Compose)
- **Endpoint**: `localhost:9000`
- **Access Key**: `usuario-admin`
- **Secret Key**: `sua-senha`
- **Console Web**: `http://localhost:9001`

## 📁 Estrutura do Projeto

```
.
├── src
├  └── main
├      └── main.py         # Aplicação batch   
├      └── app.py          # Portal aplicação
├      └── minio_manager.py # Gerenciador de arquivos no MinIO
├      └── nfe_extractor_agent.py # Extrator de dados com IA
├      └── nfe_manager.py # Gerenciador do banco de dados
├── init_db
    └── init.sql  
├── .env                   # Configurações (não versionar!)
├── .env.example           # Exemplo de configurações
├── requirements.txt       # Dependências Python
├── docker-compose.yml     # Configuração Docker do MinIO
└── README.md              # Este arquivo
└── LICENSE                # Licença
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **Streamlit**: Framework web para Python
- **MinIO**: Armazenamento de objetos compatível com S3
- **Mysql**: Armazenamento de Banco de dados
- **Docker**: Containerização (opcional)

## 🔄 Fluxo de Uso

1. Acesse a aplicação
2. Faça login com as credenciais
3. Na página principal:
   - Selecione um arquivo e clique em "Enviar" para upload
   - Visualize a lista de arquivos
   - Clique no botão 🗑️ para deletar arquivos
4. Use o botão "Logout" para sair

## 🐛 Troubleshooting

### Erro ao conectar ao MinIO
- Verifique se o MinIO está rodando
- Confirme as credenciais no arquivo `app.py`
- Verifique as portas (9000 para API, 9001 para console)

### Bucket não existe
- A aplicação cria automaticamente o bucket se não existir
- Verifique as permissões da access key

## 📝 Licença


## 📝 Licença

Copyright (c) 2025 João Silva

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

