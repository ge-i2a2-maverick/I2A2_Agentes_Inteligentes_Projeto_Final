#!/usr/bin/env python3
"""
Sistema de gerenciamento de arquivos MinIO com consumidor Redis
Autor: Sistema TI
Data: 2025-10-13
"""

import json
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from minio.commonconfig import CopySource


class MinIOManager:
    """Gerenciador de operações no MinIO"""
    
    def __init__(self, endpoint: str, 
                 access_key: str, 
                 secret_key: str,
                 secure: bool = False):
        """
        Inicializa conexão com MinIO
        
        Args:
            endpoint: Endereço do servidor MinIO
            access_key: Chave de acesso
            secret_key: Chave secreta
            secure: Usar HTTPS (True) ou HTTP (False)
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        print(f"✓ Conectado ao MinIO: {endpoint}")
    
    def criar_bucket(self, bucket_name: str) -> bool:
        """
        Cria um bucket se não existir
        
        Args:
            bucket_name: Nome do bucket
            
        Returns:
            True se criado ou já existe, False em caso de erro
        """
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print(f"✓ Bucket '{bucket_name}' criado com sucesso")
            else:
                print(f"ℹ Bucket '{bucket_name}' já existe")
            return True
        except S3Error as e:
            print(f"✗ Erro ao criar bucket: {e}")
            return False
    
    def escrever_arquivo(self, bucket_name: str, object_name: str, 
                        data: Any, content_type: str = "application/octet-stream") -> bool:
        """
        Escreve arquivo no MinIO
        
        Args:
            bucket_name: Nome do bucket
            object_name: Nome do objeto/arquivo
            data: Dados a serem escritos (str, bytes ou dict)
            content_type: Tipo de conteúdo
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Converter dados conforme necessário
            if isinstance(data, dict):
                data = json.dumps(data, indent=2, ensure_ascii=False)
                content_type = "application/json"
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            data_stream = io.BytesIO(data)
            data_length = len(data)
            
            self.client.put_object(
                bucket_name,
                object_name,
                data_stream,
                data_length,
                content_type=content_type
            )
            print(f"✓ Arquivo '{object_name}' escrito no bucket '{bucket_name}'")
            return True
            
        except S3Error as e:
            print(f"✗ Erro ao escrever arquivo: {e}")
            return False
    
    def ler_arquivo(self, bucket_name: str, object_name: str, 
                    as_json: bool = False) -> Optional[Any]:
        """
        Lê arquivo do MinIO
        
        Args:
            bucket_name: Nome do bucket
            object_name: Nome do objeto/arquivo
            as_json: Se True, tenta fazer parse como JSON
            
        Returns:
            Conteúdo do arquivo ou None em caso de erro
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            # Decodificar
            data_str = data.decode('utf-8')
            
            if as_json:
                return json.loads(data_str)
            
            print(f"✓ Arquivo '{object_name}' lido do bucket '{bucket_name}'")
            return data_str
            
        except S3Error as e:
            print(f"✗ Erro ao ler arquivo: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"✗ Erro ao fazer parse JSON: {e}")
            return None
    
    def listar_arquivos(self, bucket_name: str, prefix: str = "") -> List[Dict[str, Any]]:
        """
        Lista arquivos em um bucket
        
        Args:
            bucket_name: Nome do bucket
            prefix: Prefixo para filtrar objetos
            
        Returns:
            Lista de dicionários com informações dos arquivos
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            
            file_list = []
            for obj in objects:
                file_info = {
                    "nome": obj.object_name,
                    "tamanho": obj.size,
                    "ultima_modificacao": obj.last_modified,
                    "etag": obj.etag
                }
                file_list.append(file_info)
            
            print(f"✓ Listados {len(file_list)} arquivos no bucket '{bucket_name}'")
            return file_list
            
        except S3Error as e:
            print(f"✗ Erro ao listar arquivos: {e}")
            return []
    
    def mover_arquivo(self, source_bucket: str, source_object: str,
                     dest_bucket: str, dest_object: str) -> bool:
        """
        Move arquivo de um local para outro
        
        Args:
            source_bucket: Bucket de origem
            source_object: Nome do objeto de origem
            dest_bucket: Bucket de destino
            dest_object: Nome do objeto de destino
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Criar CopySource
            copy_source = CopySource(source_bucket, source_object)
            
            # Copiar arquivo
            self.client.copy_object(
                dest_bucket,
                dest_object,
                copy_source
            )
            
            # Remover arquivo original
            self.client.remove_object(source_bucket, source_object)
            
            print(f"✓ Arquivo movido de '{source_bucket}/{source_object}' "
                  f"para '{dest_bucket}/{dest_object}'")
            return True
            
        except S3Error as e:
            print(f"✗ Erro ao mover arquivo: {e}")
            return False
        except Exception as e:
            print(f"✗ Erro ao mover arquivo: {e}")
            return False
    
    def copiar_arquivo(self, source_bucket: str, source_object: str,
                      dest_bucket: str, dest_object: str) -> bool:
        """
        Copia arquivo de um local para outro (mantém o original)
        
        Args:
            source_bucket: Bucket de origem
            source_object: Nome do objeto de origem
            dest_bucket: Bucket de destino
            dest_object: Nome do objeto de destino
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Criar CopySource
            copy_source = CopySource(source_bucket, source_object)
            
            # Copiar arquivo
            self.client.copy_object(
                dest_bucket,
                dest_object,
                copy_source
            )
            
            print(f"✓ Arquivo copiado de '{source_bucket}/{source_object}' "
                  f"para '{dest_bucket}/{dest_object}'")
            return True
            
        except S3Error as e:
            print(f"✗ Erro ao copiar arquivo: {e}")
            return False
        except Exception as e:
            print(f"✗ Erro ao copiar arquivo: {e}")
            return False
    
    def deletar_arquivo(self, bucket_name: str, object_name: str) -> bool:
        """
        Deleta arquivo do MinIO
        
        Args:
            bucket_name: Nome do bucket
            object_name: Nome do objeto
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            print(f"✓ Arquivo '{object_name}' deletado do bucket '{bucket_name}'")
            return True
        except S3Error as e:
            print(f"✗ Erro ao deletar arquivo: {e}")
            return False

    def baixar_arquivo(self, bucket_name: str, object_name: str, 
                      path_destino: str) -> bool:
        """
        Baixa arquivo do MinIO para um diretório local
        
        Args:
            bucket_name: Nome do bucket
            object_name: Nome do objeto/arquivo no MinIO
            path_destino: Caminho completo do arquivo de destino (incluindo nome)
            
        Returns:
            True se sucesso, False caso contrário
            
        Exemplo:
            minio.baixar_arquivo("meu-bucket", "relatorio.pdf", "/tmp/relatorio.pdf")
        """
        try:
            import os
            
            # Criar diretório de destino se não existir
            dest_dir = os.path.dirname(path_destino)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
                print(f"ℹ Diretório criado: {dest_dir}")
            
            # Baixar arquivo
            self.client.fget_object(bucket_name, object_name, path_destino)
            
            # Verificar se arquivo foi criado
            if os.path.exists(path_destino):
                file_size = os.path.getsize(path_destino)
                print(f"✓ Arquivo '{object_name}' baixado com sucesso")
                print(f"  Origem: {bucket_name}/{object_name}")
                print(f"  Destino: {path_destino}")
                print(f"  Tamanho: {file_size} bytes")
                return True
            else:
                print(f"✗ Arquivo não foi criado em: {path_destino}")
                return False
            
        except S3Error as e:
            print(f"✗ Erro ao baixar arquivo do MinIO: {e}")
            return False
        except OSError as e:
            print(f"✗ Erro ao criar diretório ou salvar arquivo: {e}")
            return False
        except Exception as e:
            print(f"✗ Erro inesperado ao baixar arquivo: {e}")
            return False

def exemplo_minio():
    """Exemplo de uso do MinIO"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO MINIO")
    print("="*60 + "\n")
    
    # Inicializar cliente
    minio = MinIOManager()
    
    # Criar buckets
    minio.criar_bucket("teste-bucket")
    minio.criar_bucket("destino-bucket")
    
    # Escrever arquivos
    print("\n--- Escrevendo arquivos ---")
    minio.escrever_arquivo(
        "teste-bucket",
        "arquivo1.txt",
        "Conteúdo do arquivo de texto"
    )
    
    minio.escrever_arquivo(
        "teste-bucket",
        "dados.json",
        {"nome": "João Silva", "idade": 30, "cargo": "Desenvolvedor"}
    )
    
    minio.escrever_arquivo(
        "teste-bucket",
        "relatorio.txt",
        "Relatório de vendas do mês"
    )
    
    # Listar arquivos
    print("\n--- Listando arquivos ---")
    arquivos = minio.listar_arquivos("teste-bucket")
    for arquivo in arquivos:
        print(f"  • {arquivo['nome']} - {arquivo['tamanho']} bytes")
    
    # Ler arquivos
    print("\n--- Lendo arquivos ---")
    conteudo_txt = minio.ler_arquivo("teste-bucket", "arquivo1.txt")
    print(f"Conteúdo TXT: {conteudo_txt}")
    
    dados_json = minio.ler_arquivo("teste-bucket", "dados.json", as_json=True)
    print(f"Dados JSON: {dados_json}")
    
    # Copiar arquivo
    print("\n--- Copiando arquivo ---")
    minio.copiar_arquivo(
        "teste-bucket", "arquivo1.txt",
        "destino-bucket", "arquivo1_copia.txt"
    )
    
    # Mover arquivo
    print("\n--- Movendo arquivo ---")
    minio.mover_arquivo(
        "teste-bucket", "relatorio.txt",
        "destino-bucket", "relatorio_movido.txt"
    )
    
    # Listar arquivos após mover
    print("\n--- Listando após mover ---")
    print("Bucket origem:")
    arquivos_origem = minio.listar_arquivos("teste-bucket")
    for arquivo in arquivos_origem:
        print(f"  • {arquivo['nome']}")
    
    print("Bucket destino:")
    arquivos_destino = minio.listar_arquivos("destino-bucket")
    for arquivo in arquivos_destino:
        print(f"  • {arquivo['nome']}")



if __name__ == "__main__":
    try:
        exemplo_minio()
        
        print("\n" + "="*60)
        print("DEMONSTRAÇÕES CONCLUÍDAS")
        print("="*60)
        print("\nPara iniciar o consumidor Redis:")
        print("  python app.py --mode=consumer --channel=eventos")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Erro na execução: {e}")
        import traceback
        traceback.print_exc()