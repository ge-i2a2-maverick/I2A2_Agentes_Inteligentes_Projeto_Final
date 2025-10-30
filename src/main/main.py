#!/usr/bin/env python3
"""
Sistema de Processamento Automático de NF-e
Autor: Sistema TI
Data: 2025-10-23

Funcionalidades:
- Monitora bucket MinIO a cada 60 segundos
- Baixa arquivos de notas fiscais (PNG, JPG, PDF)
- Extrai dados usando IA (OpenAI GPT-4 Vision)
- Salva no banco de dados MySQL
- Move arquivos processados para bucket de destino
"""

import os
import sys
import time
import json
import tempfile
import requests
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Imports dos módulos customizados
from minio_manager import MinIOManager
from nfe_extractor_agent import extrair_nfe
from nfe_manager import NFeManager, DB_CONFIG
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Configurações MinIO
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'False').lower() == 'true'

# Buckets
BUCKET_NAME_RECEBIDOS = os.getenv('BUCKET_RECEBIDOS')
BUCKET_NAME_PROCESSADOS = os.getenv('BUCKET_PROCESSADOS')
BUCKET_NAME_ERROS = os.getenv('BUCKET_ERROS', 'nfe-erros')

# Intervalo de verificação (segundos)
INTERVALO_VERIFICACAO = int(os.getenv('INTERVALO_VERIFICACAO', '60'))

# Extensões suportadas
EXTENSOES_SUPORTADAS = ['.png', '.jpg', '.jpeg', '.pdf']

# Diretório temporário para downloads
TEMP_DIR = os.getenv('TEMP_DIR')

URL_WEBHOOK = os.getenv('URL_WEBHOOK')

# ============================================================================
# CLASSE PRINCIPAL DO PROCESSADOR
# ============================================================================

class NFeProcessor:
    """Processador automático de notas fiscais do MinIO"""
    
    def __init__(self):
        """Inicializa o processador com todas as conexões necessárias"""
        self.log("="*80)
        self.log("INICIALIZANDO PROCESSADOR DE NF-e")
        self.log("="*80)
        
        # Inicializa MinIO Manager
        self.log("\n[1/3] Conectando ao MinIO...")
        try:
            self.minio = MinIOManager(
                endpoint=MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )
            self.log("✓ MinIO conectado com sucesso")
        except Exception as e:
            self.log(f"✗ Erro ao conectar MinIO: {e}", nivel="ERRO")
            raise
        
        # Inicializa NFe Manager (Banco de Dados)
        self.log("\n[2/3] Conectando ao Banco de Dados MySQL...")
        try:
            self.nfe_manager = NFeManager(DB_CONFIG)
            self.log("✓ Banco de dados conectado com sucesso")
        except Exception as e:
            self.log(f"✗ Erro ao conectar ao banco: {e}", nivel="ERRO")
            raise
        
        # Cria diretório temporário
        self.log("\n[3/3] Configurando diretório temporário...")
        self.temp_dir = Path(TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"✓ Diretório temporário: {self.temp_dir.absolute()}")
        
        # Cria buckets se não existirem
        self._criar_buckets()
        
        self.log("="*80)
        self.log("PROCESSADOR INICIALIZADO COM SUCESSO")
        self.log("="*80 + "\n")
    
    def log(self, mensagem: str, nivel: str = "INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{nivel}] {mensagem}")
    
    def _criar_buckets(self):
        """Cria os buckets necessários se não existirem"""
        self.log("\nVerificando buckets...")
        buckets = [
            BUCKET_NAME_RECEBIDOS,
            BUCKET_NAME_PROCESSADOS,
            BUCKET_NAME_ERROS
        ]
        
        for bucket in buckets:
            self.minio.criar_bucket(bucket)
    
    def _limpar_temp_dir(self):
        """Limpa o diretório temporário"""
        try:
            for arquivo in self.temp_dir.glob('*'):
                if arquivo.is_file():
                    arquivo.unlink()
            self.log("✓ Diretório temporário limpo")
        except Exception as e:
            self.log(f"⚠ Aviso ao limpar diretório temp: {e}", nivel="AVISO")
    
    def listar_arquivos_bucket(self) -> List[Dict[str, Any]]:
        """Lista arquivos no bucket de recebidos"""
        try:
            arquivos = self.minio.listar_arquivos(BUCKET_NAME_RECEBIDOS)
            
            # Filtra apenas extensões suportadas
            arquivos_validos = [
                arq for arq in arquivos 
                if Path(arq['nome']).suffix.lower() in EXTENSOES_SUPORTADAS
            ]
            
            if arquivos_validos:
                self.log(f"📄 Encontrados {len(arquivos_validos)} arquivo(s) para processar")
            
            return arquivos_validos
            
        except Exception as e:
            self.log(f"✗ Erro ao listar arquivos: {e}", nivel="ERRO")
            return []
    
    def baixar_arquivo(self, nome_arquivo: str) -> Path:
        """Baixa arquivo do MinIO para o diretório temporário"""
        try:
            # Caminho local
            caminho_local = self.temp_dir / nome_arquivo
            
            # Lê o arquivo do MinIO
            is_resultado = self.minio.baixar_arquivo(
                BUCKET_NAME_RECEBIDOS,
                nome_arquivo,
                caminho_local
            )
            
            if not is_resultado:
                raise Exception(f"Erro ao baixar {nome_arquivo}")
            
            self.log(f"  ⤓ Baixado: {nome_arquivo}")
            return caminho_local
            
        except Exception as e:
            self.log(f"  ✗ Erro ao baixar {nome_arquivo}: {e}", nivel="ERRO")
            raise
    
    def extrair_dados_nfe(self, caminho_arquivo: Path) -> Dict[str, Any]:
        """Extrai dados da NF-e usando IA"""
        try:
            self.log(f"  🔍 Extraindo dados de: {caminho_arquivo.name}")
            
            # Usa o extrator de NF-e
            resultado = extrair_nfe(str(caminho_arquivo), retornar_json=False)
            
            # Verifica se houve erro
            if "erro" in resultado:
                raise Exception(f"Erro na extração: {resultado.get('mensagem', 'Erro desconhecido')}")
            
            self.log(f"  ✓ Dados extraídos com sucesso")
            
            return resultado
            
        except Exception as e:
            self.log(f"  ✗ Erro ao extrair dados: {e}", nivel="ERRO")
            raise
    
    def salvar_no_banco(self, dados_nfe: Dict[str, Any], nome_arquivo: str) -> int:
        """Salva os dados da NF-e no banco de dados"""
        try:
            self.log(f"  💾 Salvando no banco de dados...")
            
            # Salva usando o NFeManager
            nfe_id = self.nfe_manager.salvar(dados_nfe)
            
            if nfe_id:
                self.log(f"  ✓ NF-e salva com ID: {nfe_id}")
                return nfe_id
            else:
                raise Exception("Falha ao salvar no banco de dados")
                
        except Exception as e:
            self.log(f"  ✗ Erro ao salvar no banco: {e}", nivel="ERRO")
            raise
    
    def mover_para_processados(self, nome_arquivo: str, nfe_id: int):
        """Move arquivo para bucket de processados"""
        try:
            # Nome do arquivo de destino com ID da NF-e
            extensao = Path(nome_arquivo).suffix
            nome_destino = f"nfe_{nfe_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extensao}"
            
            # Copia para bucket processados
            sucesso = self.minio.copiar_arquivo(
                BUCKET_NAME_RECEBIDOS,
                nome_arquivo,
                BUCKET_NAME_PROCESSADOS,
                nome_destino
            )
            
            if not sucesso:
                raise Exception("Falha ao copiar para bucket processados")
            
            self.log(f"  ✓ Movido para processados: {nome_destino}")
            return True
            
        except Exception as e:
            self.log(f"  ✗ Erro ao mover arquivo: {e}", nivel="ERRO")
            raise
    
    def mover_para_erros(self, nome_arquivo: str, erro_msg: str):
        """Move arquivo para bucket de erros"""
        try:
            # Nome do arquivo de destino com timestamp
            extensao = Path(nome_arquivo).suffix
            nome_destino = f"erro_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nome_arquivo}"
            
            # Copia para bucket de erros
            self.minio.copiar_arquivo(
                BUCKET_NAME_RECEBIDOS,
                nome_arquivo,
                BUCKET_NAME_ERROS,
                nome_destino
            )
            
            # Salva arquivo de log do erro
            log_erro = {
                "arquivo_original": nome_arquivo,
                "data_processamento": datetime.now().isoformat(),
                "erro": erro_msg
            }
            
            nome_log = nome_destino.replace(extensao, '.json')
            self.minio.escrever_arquivo(
                BUCKET_NAME_ERROS,
                nome_log,
                log_erro
            )
            
            self.log(f"  ⚠ Movido para bucket de erros: {nome_destino}")
            
        except Exception as e:
            self.log(f"  ✗ Erro ao mover para bucket de erros: {e}", nivel="ERRO")
    
    def deletar_do_recebidos(self, nome_arquivo: str):
        """Deleta arquivo do bucket de recebidos"""
        try:
            sucesso = self.minio.deletar_arquivo(
                BUCKET_NAME_RECEBIDOS,
                nome_arquivo
            )
            
            if sucesso:
                self.log(f"  ✓ Removido do bucket recebidos")
            else:
                raise Exception("Falha ao deletar do bucket recebidos")
                
        except Exception as e:
            self.log(f"  ✗ Erro ao deletar arquivo: {e}", nivel="ERRO")

    def enviar_web_hook(self, dados_nfe: Dict[str, Any]):
        """Enviar webhook de processados para ERP"""
        try:
            # Headers para indicar que estamos enviando JSON
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Fazer o POST request
            response = requests.post(
                url=URL_WEBHOOK,
                json=dados_nfe, 
                headers=headers,
                timeout=10
            )
            
            # Retorna True apenas se status code for 200
            sucesso = response.status_code == 200
            
            if sucesso:
                self.log(f"  ✓ Enviado webhook para ERP")
            else:
                raise Exception("Falha ao enviar webhook para ERP")
                
        except Exception as e:
            self.log(f"  ✗ Erro ao enviar webhook para ERP: {e}", nivel="ERRO")

    
    def processar_arquivo(self, info_arquivo: Dict[str, Any]) -> bool:
        """Processa um único arquivo de NF-e"""
        nome_arquivo = info_arquivo['nome']
        caminho_local = None
        
        try:
            self.log(f"{'─'*80}")
            self.log(f"📄 PROCESSANDO: {nome_arquivo}")
            self.log(f"{'─'*80}")
            
            # 1. Baixar arquivo
            caminho_local = self.baixar_arquivo(nome_arquivo)
            
            # 2. Extrair dados
            dados_nfe = self.extrair_dados_nfe(caminho_local)

            # 3. Salvar no banco
            nfe_id = self.salvar_no_banco(dados_nfe, nome_arquivo)
            
            # 4. Mover para processados
            self.mover_para_processados(nome_arquivo, nfe_id)
            
            # 5. Deletar do bucket recebidos
            self.deletar_do_recebidos(nome_arquivo)

            self.enviar_web_hook(dados_nfe)
            
            self.log(f"✓ PROCESSAMENTO CONCLUÍDO COM SUCESSO")
            return True
            
        except Exception as e:
            
            self.log(f"✗ ERRO NO PROCESSAMENTO: {e}", nivel="ERRO")
            
            # Move para bucket de erros
            self.mover_para_erros(nome_arquivo, str(e))
            
            # Tenta deletar do bucket recebidos mesmo com erro
            try:
                self.deletar_do_recebidos(nome_arquivo)
            except:
                pass
            
            return False
            
        finally:
            # Limpa arquivo local
            if caminho_local and caminho_local.exists():
                try:
                    caminho_local.unlink()
                except Exception as e:
                    self.log(f"⚠ Aviso: erro ao deletar arquivo local: {e}", nivel="AVISO")
    
    def executar_ciclo(self):
        """Executa um ciclo de processamento"""
        try:
            self.log("="*80)
            self.log(f"INICIANDO CICLO DE VERIFICAÇÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            self.log("="*80)
            
            # Lista arquivos
            arquivos = self.listar_arquivos_bucket()
            
            if not arquivos:
                self.log("ℹ Nenhum arquivo para processar")
                return
            
            # Processa cada arquivo
            total = len(arquivos)
            sucesso = 0
            erros = 0
            
            for idx, arquivo in enumerate(arquivos, 1):
                self.log(f"\n[{idx}/{total}] Processando arquivo...")
                
                if self.processar_arquivo(arquivo):
                    sucesso += 1
                else:
                    erros += 1
            
            # Relatório do ciclo
            self.log("="*80)
            self.log("CICLO CONCLUÍDO")
            self.log(f"  Total processado: {total}")
            self.log(f"  ✓ Sucesso: {sucesso}")
            self.log(f"  ✗ Erros: {erros}")
            self.log("="*80)
            
        except Exception as e:
            self.log(f"✗ Erro crítico no ciclo: {e}", nivel="ERRO")
    
    def iniciar_monitoramento(self):
        """Inicia o loop de monitoramento contínuo"""
        self.log("\n🚀 MONITORAMENTO INICIADO")
        self.log(f"   Verificando bucket '{BUCKET_NAME_RECEBIDOS}' a cada {INTERVALO_VERIFICACAO} segundos")
        self.log(f"   Pressione Ctrl+C para interromper\n")
        
        try:
            while True:
                self.executar_ciclo()
                
                # Aguarda próximo ciclo
                self.log(f"\n⏳ Aguardando {INTERVALO_VERIFICACAO} segundos até próxima verificação...\n")
                time.sleep(INTERVALO_VERIFICACAO)
                
        except KeyboardInterrupt:
            self.log("\n\n⚠ Interrupção solicitada pelo usuário")
            self.log("🛑 Encerrando processador...")
        except Exception as e:
            self.log(f"\n✗ Erro crítico: {e}", nivel="ERRO")
            raise
        finally:
            self._limpar_temp_dir()
            self.log("✓ Processador encerrado\n")


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "PROCESSADOR AUTOMÁTICO DE NF-e" + " "*33 + "║")
    print("║" + " "*20 + "Sistema LenteFiscal v1.0" + " "*34 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")
    
    try:
        # Cria e inicia o processador
        processor = NFeProcessor()
        processor.iniciar_monitoramento()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n✗ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
