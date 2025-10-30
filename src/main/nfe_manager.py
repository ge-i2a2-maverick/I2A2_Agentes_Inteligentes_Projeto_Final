import mysql.connector
from datetime import datetime
import json
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações do Banco de Dados Carregadas do .env ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE'),
    'port': os.getenv('DB_PORT', 3306)
}

class NFeManager:
    """
    Gerencia a conexão e as operações CRUD para os dados da NFe no MySQL,
    utilizando variáveis de ambiente para a configuração.
    """
    def __init__(self, db_config):
        # Validação básica da configuração
        if not all(db_config.values()):
            raise ValueError("As configurações do banco de dados (host, user, password, database) não foram carregadas corretamente do .env.")
        self.db_config = db_config

    def _get_connection(self):
        """Estabelece e retorna a conexão com o banco de dados."""
        return mysql.connector.connect(**self.db_config)

    # --------------------------------------------------------------------------------
    # MÉTODOS AUXILIARES (mantidos do código anterior)
    # --------------------------------------------------------------------------------

    def _insert_endereco(self, cursor, endereco_data):
        """Insere o endereço e retorna o ID."""
        sql = """
            INSERT INTO endereco (logradouro, numero, bairro, municipio, uf, cep)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        data = (
            endereco_data['Logradouro'],
            endereco_data.get('Numero'),
            endereco_data.get('Bairro'),
            endereco_data['Municipio'],
            endereco_data['UF'],
            endereco_data.get('CEP')
        )
        cursor.execute(sql, data)
        return cursor.lastrowid

    def _get_or_insert_emitente(self, cursor, identificacao_data, id_endereco):
        """Verifica se o emitente existe. Se sim, retorna o ID. Caso contrário, insere e retorna o ID."""
        cnpj = identificacao_data['CNPJ_Emitente']
        # 1. Tenta buscar
        sql_select = "SELECT id FROM emitente WHERE cnpj_emitente = %s"
        cursor.execute(sql_select, (cnpj,))
        result = cursor.fetchone()
        if result:
            return result[0] # Retorna o ID existente

        # 2. Se não existir, insere
        sql_insert = """
            INSERT INTO emitente (cnpj_emitente, nome_emitente, ie_emitente, id_endereco)
            VALUES (%s, %s, %s, %s)
        """
        data = (
            cnpj,
            identificacao_data['Nome_Emitente'],
            identificacao_data.get('IE_Emitente'),
            id_endereco
        )
        cursor.execute(sql_insert, data)
        return cursor.lastrowid
    
    def _insert_tributos(self, cursor, tributos_data):
        """Insere os dados de tributos e retorna o ID."""
        sql = """
            INSERT INTO tributos (total_tributos_incidentes, tributos_federais, percentual_federais, 
                                  tributos_estaduais, percentual_estaduais, fonte_tributos, lei_tributos)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = (
            tributos_data.get('Total_Tributos_Incidentes'),
            tributos_data.get('Tributos_Federais'),
            tributos_data.get('Percentual_Federais'),
            tributos_data.get('Tributos_Estaduais'),
            tributos_data.get('Percentual_Estaduais'),
            tributos_data.get('Fonte_Tributos'),
            tributos_data.get('Lei_Tributos')
        )
        cursor.execute(sql, data)
        return cursor.lastrowid

    def _insert_totais(self, cursor, totais_data, id_tributos):
        """Insere os totais e retorna o ID."""
        sql = """
            INSERT INTO totais (qtd_total_itens, valor_total_produtos, descontos_gerais, 
                                acrescimos_gerais, valor_total_a_pagar, id_tributos)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        data = (
            totais_data['Qtd_Total_Itens'],
            totais_data.get('Valor_Total_Produtos'),
            totais_data['Descontos_Gerais'],
            totais_data['Acrescimos_Gerais'],
            totais_data['Valor_Total_a_Pagar'],
            id_tributos
        )
        cursor.execute(sql, data)
        return cursor.lastrowid

    def _insert_pagamento(self, cursor, pagamento_data):
        """Insere o pagamento e retorna o ID."""
        sql = """
            INSERT INTO pagamento (forma_pagamento, valor_pago, troco, meio_pagamento_detalhe)
            VALUES (%s, %s, %s, %s)
        """
        data = (
            pagamento_data['Forma_Pagamento'],
            pagamento_data['Valor_Pago'],
            pagamento_data.get('Troco'),
            pagamento_data.get('Meio_Pagamento_Detalhe')
        )
        cursor.execute(sql, data)
        return cursor.lastrowid

    def _insert_dados_adicionais(self, cursor, dados_adicionais_data):
        """Insere os dados adicionais e retorna o ID."""
        sql = """
            INSERT INTO dados_adicionais (caixa, operador, vendedor)
            VALUES (%s, %s, %s)
        """
        data = (
            dados_adicionais_data.get('Caixa'),
            dados_adicionais_data.get('Operador'),
            dados_adicionais_data.get('Vendedor')
        )
        cursor.execute(sql, data)
        return cursor.lastrowid
    
    def _parse_datetime(self, data_str, hora_str):
        """Converte strings de data e hora para objetos datetime.date e datetime.time."""
        data_autorizacao = None
        hora_autorizacao = None
        
        if data_str:
            try:
                data_autorizacao = datetime.strptime(data_str, '%d/%m/%Y').date()
            except ValueError:
                print(f"Aviso: Formato de data inválido: {data_str}")

        if hora_str:
            try:
                hora_autorizacao = datetime.strptime(hora_str, '%H:%M:%S').time()
            except ValueError:
                print(f"Aviso: Formato de hora inválido: {hora_str}")
        
        return data_autorizacao, hora_autorizacao


    # --------------------------------------------------------------------------------
    # MÉTODOS CRUD (O restante da lógica é a mesma)
    # --------------------------------------------------------------------------------

    def salvar(self, nfe_json_data):
        # ... (Método salvar igual ao original)
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            nfe_data = nfe_json_data['NFe']
            identificacao = nfe_data['identificacao']
            endereco = identificacao['Endereco_Emitente']
            totais = nfe_data['totais']
            tributos = totais['Informacao_Tributos']
            pagamento = nfe_data['pagamento']
            dados_adicionais = nfe_data['dados_adicionais']
            itens = nfe_data['itens']

            # 1. Inserir tabelas base 
            id_endereco = self._insert_endereco(cursor, endereco)
            id_emitente = self._get_or_insert_emitente(cursor, identificacao, id_endereco)
            
            id_tributos = self._insert_tributos(cursor, tributos)
            id_totais = self._insert_totais(cursor, totais, id_tributos)
            
            id_pagamento = self._insert_pagamento(cursor, pagamento)
            id_dados_adicionais = self._insert_dados_adicionais(cursor, dados_adicionais)

            # 2. Inserir a NFe principal
            data_auto, hora_auto = self._parse_datetime(
                identificacao.get('Data_Autorizacao'), identificacao.get('Hora_Autorizacao')
            )

            sql_nfe = """
                INSERT INTO nfe (id_emitente, chave_acesso, protocolo_autorizacao, data_autorizacao, 
                                 hora_autorizacao, numero_nfce, serie_nfce, consumidor, 
                                 id_totais, id_pagamento, id_dados_adicionais)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            data_nfe = (
                id_emitente,
                identificacao.get('Chave_Acesso'),
                identificacao.get('Protocolo_Autorizacao'),
                data_auto,
                hora_auto,
                identificacao.get('Numero_NFCe'),
                identificacao.get('Serie_NFCe'),
                identificacao.get('Consumidor'),
                id_totais,
                id_pagamento,
                id_dados_adicionais
            )
            cursor.execute(sql_nfe, data_nfe)
            id_nfe = cursor.lastrowid

            # 3. Inserir os Itens
            sql_item = """
                INSERT INTO item (id_nfe, numero_item, codigo_produto, descricao, quantidade, 
                                  unidade, valor_unitario, desconto_item, valor_total_item)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for item in itens:
                data_item = (
                    id_nfe,
                    item['Numero_Item'],
                    item.get('Codigo_Produto'),
                    item['Descricao'],
                    item['Quantidade'],
                    item['Unidade'],
                    item['Valor_Unitario'],
                    item.get('Desconto_Item'),
                    item['Valor_Total_Item']
                )
                cursor.execute(sql_item, data_item)

            conn.commit()
            return id_nfe
        except mysql.connector.Error as err:
            print(f"Erro ao salvar NFe: {err}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn and conn.is_connected():
                conn.close()

    def ler(self, id_nfe):
        # ... (Método ler igual ao original)
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 1. Buscar dados principais (NFe, Emitente, Endereco)
            sql_nfe_base = """
                SELECT 
                    n.id, n.chave_acesso, n.protocolo_autorizacao, DATE_FORMAT(n.data_autorizacao, '%d/%m/%Y') AS data_autorizacao, 
                    TIME_FORMAT(n.hora_autorizacao, '%H:%i:%s') AS hora_autorizacao, n.numero_nfce, n.serie_nfce, n.consumidor,
                    e.cnpj_emitente, e.nome_emitente, e.ie_emitente,
                    end.logradouro, end.numero, end.bairro, end.municipio, end.uf, end.cep,
                    t.qtd_total_itens, t.valor_total_produtos, t.descontos_gerais, t.acrescimos_gerais, t.valor_total_a_pagar,
                    tr.total_tributos_incidentes, tr.tributos_federais, tr.percentual_federais, tr.tributos_estaduais, 
                    tr.percentual_estaduais, tr.fonte_tributos, tr.lei_tributos,
                    pg.forma_pagamento, pg.valor_pago, pg.troco, pg.meio_pagamento_detalhe,
                    da.caixa, da.operador, da.vendedor
                FROM nfe n
                JOIN emitente e ON n.id_emitente = e.id
                JOIN endereco end ON e.id_endereco = end.id
                JOIN totais t ON n.id_totais = t.id
                JOIN tributos tr ON t.id_tributos = tr.id
                JOIN pagamento pg ON n.id_pagamento = pg.id
                JOIN dados_adicionais da ON n.id_dados_adicionais = da.id
                WHERE n.id = %s
            """
            cursor.execute(sql_nfe_base, (id_nfe,))
            nfe_result = cursor.fetchone()

            if not nfe_result:
                return None

            # 2. Buscar Itens
            sql_itens = "SELECT * FROM item WHERE id_nfe = %s ORDER BY numero_item"
            cursor.execute(sql_itens, (id_nfe,))
            itens_result = cursor.fetchall()

            # 3. Reconstruir o JSON
            nfe_dict = {
                "NFe": {
                    "identificacao": {
                        "CNPJ_Emitente": nfe_result['cnpj_emitente'],
                        "Nome_Emitente": nfe_result['nome_emitente'],
                        "IE_Emitente": nfe_result['ie_emitente'],
                        "Endereco_Emitente": {
                            "Logradouro": nfe_result['logradouro'],
                            "Numero": nfe_result['numero'],
                            "Bairro": nfe_result['bairro'],
                            "Municipio": nfe_result['municipio'],
                            "UF": nfe_result['uf'],
                            "CEP": nfe_result['cep']
                        },
                        "Chave_Acesso": nfe_result['chave_acesso'],
                        "Protocolo_Autorizacao": nfe_result['protocolo_autorizacao'],
                        "Data_Autorizacao": nfe_result['data_autorizacao'],
                        "Hora_Autorizacao": nfe_result['hora_autorizacao'],
                        "Numero_NFCe": nfe_result['numero_nfce'],
                        "Serie_NFCe": nfe_result['serie_nfce'],
                        "Consumidor": nfe_result['consumidor']
                    },
                    "itens": [
                        {
                            "Numero_Item": item['numero_item'],
                            "Codigo_Produto": item['codigo_produto'],
                            "Descricao": item['descricao'],
                            "Quantidade": float(item['quantidade']),
                            "Unidade": item['unidade'],
                            "Valor_Unitario": float(item['valor_unitario']),
                            "Desconto_Item": float(item['desconto_item']) if item['desconto_item'] is not None else None,
                            "Valor_Total_Item": float(item['valor_total_item'])
                        } for item in itens_result
                    ],
                    "totais": {
                        "Qtd_Total_Itens": nfe_result['qtd_total_itens'],
                        "Valor_Total_Produtos": float(nfe_result['valor_total_produtos']) if nfe_result['valor_total_produtos'] is not None else None,
                        "Descontos_Gerais": float(nfe_result['descontos_gerais']),
                        "Acrescimos_Gerais": float(nfe_result['acrescimos_gerais']),
                        "Valor_Total_a_Pagar": float(nfe_result['valor_total_a_pagar']),
                        "Informacao_Tributos": {
                            "Total_Tributos_Incidentes": float(nfe_result['total_tributos_incidentes']) if nfe_result['total_tributos_incidentes'] is not None else None,
                            "Tributos_Federais": float(nfe_result['tributos_federais']) if nfe_result['tributos_federais'] is not None else None,
                            "Percentual_Federais": float(nfe_result['percentual_federais']) if nfe_result['percentual_federais'] is not None else None,
                            "Tributos_Estaduais": float(nfe_result['tributos_estaduais']) if nfe_result['tributos_estaduais'] is not None else None,
                            "Percentual_Estaduais": float(nfe_result['percentual_estaduais']) if nfe_result['percentual_estaduais'] is not None else None,
                            "Fonte_Tributos": nfe_result['fonte_tributos'],
                            "Lei_Tributos": nfe_result['lei_tributos']
                        }
                    },
                    "pagamento": {
                        "Forma_Pagamento": nfe_result['forma_pagamento'],
                        "Valor_Pago": float(nfe_result['valor_pago']),
                        "Troco": float(nfe_result['troco']) if nfe_result['troco'] is not None else None,
                        "Meio_Pagamento_Detalhe": nfe_result['meio_pagamento_detalhe']
                    },
                    "dados_adicionais": {
                        "Caixa": nfe_result['caixa'],
                        "Operador": nfe_result['operador'],
                        "Vendedor": nfe_result['vendedor']
                    }
                }
            }
            return nfe_dict
        except mysql.connector.Error as err:
            print(f"Erro ao ler NFe: {err}")
            return None
        finally:
            if conn and conn.is_connected():
                conn.close()

    def alterar(self, id_nfe, nfe_json_data):
        # ... (Método alterar igual ao original)
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            nfe_data = nfe_json_data['NFe']
            identificacao = nfe_data['identificacao']
            pagamento = nfe_data['pagamento']
            dados_adicionais = nfe_data['dados_adicionais']

            # 1. Obter IDs relacionados
            sql_get_ids = "SELECT id_pagamento, id_dados_adicionais FROM nfe WHERE id = %s"
            cursor.execute(sql_get_ids, (id_nfe,))
            ids = cursor.fetchone()

            if not ids:
                raise Exception(f"NFe com ID {id_nfe} não encontrada para alteração.")

            id_pagamento, id_dados_adicionais = ids

            # 2. Atualizar Pagamento
            sql_upd_pag = """
                UPDATE pagamento SET forma_pagamento = %s, valor_pago = %s, troco = %s, meio_pagamento_detalhe = %s
                WHERE id = %s
            """
            cursor.execute(sql_upd_pag, (
                pagamento['Forma_Pagamento'], pagamento['Valor_Pago'], pagamento.get('Troco'),
                pagamento.get('Meio_Pagamento_Detalhe'), id_pagamento
            ))

            # 3. Atualizar Dados Adicionais
            sql_upd_da = """
                UPDATE dados_adicionais SET caixa = %s, operador = %s, vendedor = %s
                WHERE id = %s
            """
            cursor.execute(sql_upd_da, (
                dados_adicionais.get('Caixa'), dados_adicionais.get('Operador'),
                dados_adicionais.get('Vendedor'), id_dados_adicionais
            ))

            # 4. Atualizar a NFe principal
            data_auto, hora_auto = self._parse_datetime(
                identificacao.get('Data_Autorizacao'), identificacao.get('Hora_Autorizacao')
            )
            
            sql_upd_nfe = """
                UPDATE nfe SET chave_acesso = %s, protocolo_autorizacao = %s, data_autorizacao = %s, 
                                hora_autorizacao = %s, numero_nfce = %s, serie_nfce = %s, consumidor = %s
                WHERE id = %s
            """
            cursor.execute(sql_upd_nfe, (
                identificacao.get('Chave_Acesso'), identificacao.get('Protocolo_Autorizacao'),
                data_auto, hora_auto, identificacao.get('Numero_NFCe'),
                identificacao.get('Serie_NFCe'), identificacao.get('Consumidor'), id_nfe
            ))

            # 5. Commit
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao alterar NFe ID {id_nfe}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn and conn.is_connected():
                conn.close()

    def listar(self, limite=10):
        # ... (Método listar igual ao original)
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            sql = """
                SELECT 
                    n.id, n.numero_nfce, n.serie_nfce, n.chave_acesso, DATE_FORMAT(n.data_autorizacao, '%d/%m/%Y') AS data_autorizacao,
                    e.nome_emitente, e.cnpj_emitente, t.valor_total_a_pagar
                FROM nfe n
                JOIN emitente e ON n.id_emitente = e.id
                JOIN totais t ON n.id_totais = t.id
                ORDER BY n.data_registro DESC
                LIMIT %s
            """
            cursor.execute(sql, (limite,))
            results = cursor.fetchall()

            # Formata para um resumo amigável
            lista_nfe = []
            for row in results:
                lista_nfe.append({
                    "ID_NFe": row['id'],
                    "NFCe_Numero": row['numero_nfce'],
                    "NFCe_Serie": row['serie_nfce'],
                    "Emitente": row['nome_emitente'],
                    "CNPJ_Emitente": row['cnpj_emitente'],
                    "Data_Autorizacao": row['data_autorizacao'],
                    "Valor_Total": float(row['valor_total_a_pagar'])
                })
            return lista_nfe
        except mysql.connector.Error as err:
            print(f"Erro ao listar NFe's: {err}")
            return []
        finally:
            if conn and conn.is_connected():
                conn.close()

# --------------------------------------------------------------------------------
# EXEMPLO DE USO
# --------------------------------------------------------------------------------

if __name__ == '__main__':
    # Simulação do resultado de um json.loads(result_json)
    DADOS_JSON_EXEMPLO = {
      "NFe": {
        "identificacao": {
          "CNPJ_Emitente": "12345678000190",
          "Nome_Emitente": "MERCADO DE TESTE LTDA",
          "IE_Emitente": "1234567890",
          "Endereco_Emitente": {
            "Logradouro": "Rua das Flores",
            "Numero": "100",
            "Bairro": "Centro",
            "Municipio": "SAO PAULO",
            "UF": "SP",
            "CEP": "01000000"
          },
          "Chave_Acesso": "43210112345678000190550010000000011234567890",
          "Protocolo_Autorizacao": "123456789012345",
          "Data_Autorizacao": "23/10/2025",
          "Hora_Autorizacao": "18:30:00",
          "Numero_NFCe": "123",
          "Serie_NFCe": "1",
          "Consumidor": "CONSUMIDOR NÃO IDENTIFICADO"
        },
        "itens": [
          {
            "Numero_Item": 1,
            "Codigo_Produto": "PROD001",
            "Descricao": "ARROZ TIPO 1 5KG",
            "Quantidade": 1.000,
            "Unidade": "UN",
            "Valor_Unitario": 20.00,
            "Valor_Total_Item": 20.00
          },
          {
            "Numero_Item": 2,
            "Codigo_Produto": "PROD002",
            "Descricao": "FEIJAO PRETO 1KG",
            "Quantidade": 2.000,
            "Unidade": "KG",
            "Valor_Unitario": 8.50,
            "Desconto_Item": 1.00,
            "Valor_Total_Item": 16.00
          }
        ],
        "totais": {
          "Qtd_Total_Itens": 2,
          "Valor_Total_Produtos": 37.00,
          "Descontos_Gerais": 0.50,
          "Acrescimos_Gerais": 0.00,
          "Valor_Total_a_Pagar": 35.50,
          "Informacao_Tributos": {
            "Total_Tributos_Incidentes": 4.50,
            "Tributos_Federais": 1.50,
            "Percentual_Federais": 4.25,
            "Tributos_Estaduais": 3.00,
            "Percentual_Estaduais": 8.50,
            "Fonte_Tributos": "IBPT",
            "Lei_Tributos": "Lei Federal 12.741/2012"
          }
        },
        "pagamento": {
          "Forma_Pagamento": "Cartão de Débito",
          "Valor_Pago": 35.50,
          "Troco": 0.00,
          "Meio_Pagamento_Detalhe": "CARTDEB"
        },
        "dados_adicionais": {
          "Caixa": "CX: 01",
          "Operador": "OP: MARIA",
          "Vendedor": "VND:144102"
        }
      }
    }

    try:
        manager = NFeManager(DB_CONFIG)
    except ValueError as e:
        print(f"Erro de Configuração: {e}")
        exit() # Sai se a configuração estiver errada

    # 1. SALVAR
    print("--- 1. SALVAR ---")
    nfe_id = manager.salvar(DADOS_JSON_EXEMPLO)
    if nfe_id:
        print(f"NFe salva com sucesso. ID: {nfe_id}")
    else:
        print("Falha ao salvar NFe.")

    # 2. LISTAR
    print("\n--- 2. LISTAR (últimas 5) ---")
    lista = manager.listar(limite=5)
    for nfe in lista:
        print(f"ID: {nfe['ID_NFe']}, Emitente: {nfe['Emitente']}, Valor: {nfe['Valor_Total']}")
    
    # 3. LER
    if nfe_id:
        print(f"\n--- 3. LER NFe ID {nfe_id} ---")
        nfe_lida = manager.ler(nfe_id)
        if nfe_lida:
            print(json.dumps(nfe_lida, indent=2))
        else:
            print(f"NFe com ID {nfe_id} não encontrada.")

        # 4. ALTERAR
        # Simula uma alteração
        print(f"\n--- 4. ALTERAR NFe ID {nfe_id} ---")
        DADOS_JSON_EXEMPLO['NFe']['pagamento']['Forma_Pagamento'] = "Dinheiro"
        DADOS_JSON_EXEMPLO['NFe']['pagamento']['Valor_Pago'] = 40.00
        DADOS_JSON_EXEMPLO['NFe']['pagamento']['Troco'] = 4.50
        DADOS_JSON_EXEMPLO['NFe']['identificacao']['Consumidor'] = "JOAO DA SILVA - CPF: 12345678900"
        
        if manager.alterar(nfe_id, DADOS_JSON_EXEMPLO):
            print(f"NFe ID {nfe_id} alterada com sucesso.")
        else:
            print(f"Falha ao alterar NFe ID {nfe_id}.")