# 🚀 Guia Rápido de Comandos

## Instalação e Configuração

### 1. Clonar ou baixar o projeto
```bash
cd /caminho/do/projeto
```

### 2. Instalar dependências Python
```bash
pip install -r requirements.txt
```

### 3. Iniciar MinIO (usando Docker)
```bash
# Iniciar o MinIO
docker-compose up -d

# Verificar se está rodando
docker-compose ps

# Ver logs
docker-compose logs -f minio
```

### 4. Configurar variáveis de ambiente (opcional)
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar conforme necessário
nano .env
```

## Executar Aplicação

### Versão Básica
```bash
streamlit run app.py
```

A aplicação estará disponível em: **http://localhost:8501**

## Gerenciar MinIO

### Acessar Console Web do MinIO
```
URL: http://localhost:9001
Usuário: minioadmin
Senha: minioadmin
```

### Parar MinIO
```bash
docker-compose down
```

### Parar e remover dados
```bash
docker-compose down -v
```

### Reiniciar MinIO
```bash
docker-compose restart
```

## Testes Rápidos

### Testar conexão com MinIO
```python
from minio import Minio

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Listar buckets
buckets = client.list_buckets()
for bucket in buckets:
    print(bucket.name)
```

## Problemas Comuns

### MinIO não inicia
```bash
# Verificar portas em uso
netstat -an | grep 9000
netstat -an | grep 9001

# Verificar logs do Docker
docker-compose logs minio
```

### Erro de permissão
```bash
# Dar permissões ao volume
sudo chown -R $USER:$USER ./data
```

### Limpar cache do Streamlit
```bash
streamlit cache clear
```

## Desenvolvimento

### Executar em modo debug
```bash
streamlit run src/main/app.py --logger.level=debug
```

### Mudar porta do Streamlit
```bash
streamlit run src/main/app.py --server.port 8502
```

### Desabilitar tema escuro
```bash
streamlit run src/main/app.py --theme.base="light"
```

## Produção

### Considerações importantes para produção:
1. Use HTTPS para MinIO (configure certificados SSL)
2. Implemente autenticação robusta com banco de dados
3. Use hash de senhas (bcrypt ou argon2)
4. Configure backup do MinIO
5. Use variáveis de ambiente para todas as credenciais
6. Implemente rate limiting
7. Configure logs adequados
8. Use proxy reverso (Nginx ou Traefik)

### Exemplo de deploy com HTTPS:
```yaml
# docker-compose.prod.yml
services:
  minio:
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - /caminho/para/certs:/certs
    command: server /data --certs-dir /certs
```

## Úteis

### Backup do bucket
```bash
docker exec minio-server mc mirror /data/meu-bucket /backup/
```

### Monitorar uso
```bash
docker stats minio-server
```

### Atualizar MinIO
```bash
docker-compose pull minio
docker-compose up -d
```
