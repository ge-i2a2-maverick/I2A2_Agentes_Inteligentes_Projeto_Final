"""
Agente para extração de dados de NF-e/NFC-e de imagens (PNG/JPG) e PDF
Autor: Sistema de Extração Fiscal
Data: 2025
VERSÃO CORRIGIDA: Retorna sempre Dict/JSON, nunca strings
"""

import os
import json
import base64
from typing import Dict, Any, Union
from pathlib import Path
from io import BytesIO

from langchain_openai import ChatOpenAI
from langchain.tools import tool

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()


# Importação condicional do Streamlit
try:
    import streamlit as st
    from streamlit.runtime.uploaded_file_manager import UploadedFile
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    UploadedFile = None


# Configuração da API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def encode_image_to_base64(image_path: str) -> str:
    """Codifica uma imagem em base64 a partir de um caminho de arquivo"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def encode_bytes_to_base64(image_bytes: bytes) -> str:
    """Codifica bytes de imagem em base64"""
    return base64.b64encode(image_bytes).decode('utf-8')


def get_file_extension(filename: str) -> str:
    """Extrai a extensão do arquivo"""
    return Path(filename).suffix.lower()


def process_uploaded_file(uploaded_file) -> tuple:
    """
    Processa um arquivo do Streamlit UploadedFile
    
    Returns:
        tuple: (file_bytes, file_extension, file_name)
    """
    if STREAMLIT_AVAILABLE and isinstance(uploaded_file, UploadedFile):
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        file_extension = get_file_extension(file_name)
        # Reseta o ponteiro do arquivo para uso posterior se necessário
        uploaded_file.seek(0)
        return file_bytes, file_extension, file_name
    else:
        raise ValueError("Arquivo não é um UploadedFile válido do Streamlit")


@tool
def extract_nfe_from_image(file_path: str) -> Dict[str, Any]:
    """
    Extrai dados de NF-e/NFC-e de arquivos PNG, JPG ou PDF.
    
    Args:
        file_path: Caminho completo do arquivo (PNG, JPG ou PDF)
    
    Returns:
        Dicionário Python com os dados extraídos da nota fiscal
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            return {
                "erro": "Arquivo não encontrado",
                "mensagem": f"O arquivo '{file_path}' não existe."
            }
        
        # Lê os bytes do arquivo
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        file_extension = Path(file_path).suffix.lower()
        file_name = Path(file_path).name
        
        # Processa o arquivo usando a função auxiliar
        return _process_nfe_extraction(file_bytes, file_extension, file_name)
        
    except Exception as e:
        return {
            "erro": "Erro inesperado",
            "mensagem": str(e),
            "tipo_erro": type(e).__name__
        }


def _process_nfe_extraction(file_bytes: bytes, file_extension: str, file_name: str) -> Dict[str, Any]:
    """
    Função auxiliar para processar a extração de NF-e de bytes
    
    Args:
        file_bytes: Bytes do arquivo
        file_extension: Extensão do arquivo (com ponto, ex: '.png')
        file_name: Nome do arquivo
    
    Returns:
        Dicionário Python com os dados extraídos
    """
    try:
        # Verifica formato suportado
        supported_formats = ['.png', '.jpg', '.jpeg', '.pdf']
        
        if file_extension not in supported_formats:
            return {
                "erro": "Formato não suportado",
                "mensagem": f"O arquivo deve ser PNG, JPG ou PDF. Formato recebido: {file_extension}"
            }
        
        # Inicializa o modelo OpenAI com visão
        llm_vision = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Template para extração estruturada
        extraction_prompt = """
Você é um especialista em extração de dados de Notas Fiscais Eletrônicas (NF-e e NFC-e) brasileiras.

Analise cuidadosamente a imagem da nota fiscal e extraia TODOS os dados visíveis seguindo EXATAMENTE a estrutura JSON abaixo.

INSTRUÇÕES IMPORTANTES:
1. Extraia apenas informações que estejam CLARAMENTE visíveis na imagem
2. Para campos opcionais, inclua-os apenas se a informação estiver presente
3. Use "null" para valores não encontrados em campos opcionais
4. Mantenha a precisão numérica exata dos valores monetários
5. Formate datas como DD/MM/AAAA e horas como HH:MM:SS
6. Para itens, numere sequencialmente começando em 1

ESTRUTURA JSON OBRIGATÓRIA:
{
  "NFe": {
    "identificacao": {
      "CNPJ_Emitente": "string",
      "Nome_Emitente": "string",
      "IE_Emitente": "string ou null",
      "Endereco_Emitente": {
        "Logradouro": "string",
        "Numero": "string ou null",
        "Bairro": "string ou null",
        "Municipio": "string",
        "UF": "string",
        "CEP": "string ou null"
      },
      "Chave_Acesso": "string ou null",
      "Protocolo_Autorizacao": "string ou null",
      "Data_Autorizacao": "string ou null",
      "Hora_Autorizacao": "string ou null",
      "Numero_NFCe": "string ou null",
      "Serie_NFCe": "string ou null",
      "Consumidor": "string ou null"
    },
    "itens": [
      {
        "Numero_Item": 1,
        "Codigo_Produto": "string ou null",
        "Descricao": "string",
        "Quantidade": 0.0,
        "Unidade": "string",
        "Valor_Unitario": 0.0,
        "Desconto_Item": 0.0,
        "Valor_Total_Item": 0.0
      }
    ],
    "totais": {
      "Qtd_Total_Itens": 0,
      "Valor_Total_Produtos": 0.0,
      "Descontos_Gerais": 0.0,
      "Acrescimos_Gerais": 0.0,
      "Valor_Total_a_Pagar": 0.0,
      "Informacao_Tributos": {
        "Total_Tributos_Incidentes": 0.0,
        "Tributos_Federais": 0.0,
        "Percentual_Federais": 0.0,
        "Tributos_Estaduais": 0.0,
        "Percentual_Estaduais": 0.0,
        "Fonte_Tributos": "string ou null",
        "Lei_Tributos": "string ou null"
      }
    },
    "pagamento": {
      "Forma_Pagamento": "string",
      "Valor_Pago": 0.0,
      "Troco": 0.0,
      "Meio_Pagamento_Detalhe": "string ou null"
    },
    "dados_adicionais": {
      "Caixa": "string ou null",
      "Operador": "string ou null",
      "Vendedor": "string ou null"
    }
  }
}

RETORNE APENAS O JSON, sem texto adicional antes ou depois.
"""
        
        # Para PDF, utilizamos extração de texto primeiro
        if file_extension == '.pdf':
            try:
                import PyPDF2
                
                # Cria um arquivo temporário para o PDF
                pdf_file = BytesIO(file_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
                
                # Usa o modelo padrão para processar texto extraído
                llm_text = ChatOpenAI(
                    model="gpt-4o",
                    temperature=0.1,
                    openai_api_key=OPENAI_API_KEY
                )
                
                prompt_text = f"{extraction_prompt}\n\nTEXTO EXTRAÍDO DO PDF:\n{text_content}"
                response = llm_text.invoke(prompt_text)
                extracted_data = response.content
                
            except ImportError:
                return {
                    "erro": "Biblioteca PyPDF2 não instalada",
                    "mensagem": "Para processar PDFs, instale: pip install PyPDF2"
                }
            except Exception as e:
                return {
                    "erro": "Erro ao processar PDF",
                    "mensagem": str(e)
                }
        
        # Para imagens (PNG/JPG)
        else:
            # Codifica a imagem em base64
            base64_image = encode_bytes_to_base64(file_bytes)
            
            # Cria a mensagem com a imagem
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": extraction_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{file_extension[1:]};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = llm_vision.invoke(messages)
            extracted_data = response.content
        
        # Limpa possíveis marcações de código do retorno
        extracted_data = extracted_data.strip()
        if extracted_data.startswith("```json"):
            extracted_data = extracted_data[7:]
        if extracted_data.startswith("```"):
            extracted_data = extracted_data[3:]
        if extracted_data.endswith("```"):
            extracted_data = extracted_data[:-3]
        extracted_data = extracted_data.strip()
        
        # Valida se é um JSON válido e RETORNA COMO DICT
        try:
            json_data = json.loads(extracted_data)
            # RETORNA O DICIONÁRIO, NÃO A STRING
            return json_data
        except json.JSONDecodeError as e:
            return {
                "erro": "Erro ao processar resposta",
                "mensagem": "O modelo não retornou um JSON válido",
                "detalhes": str(e),
                "resposta_recebida": extracted_data[:500]
            }
        
    except Exception as e:
        return {
            "erro": "Erro inesperado na extração",
            "mensagem": str(e),
            "tipo_erro": type(e).__name__
        }


# Configuração do agente
def criar_agente_nfe():
    """Cria e retorna o agente configurado para extração de NF-e"""
    
    # Inicializa o modelo LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        openai_api_key=OPENAI_API_KEY
    )
    
    # Define as ferramentas disponíveis
    tools = [extract_nfe_from_image]
    
    # Cria o prompt do agente
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um assistente especializado em extração de dados de Notas Fiscais Eletrônicas (NF-e e NFC-e).
        
Sua função é:
1. Receber o caminho de um arquivo (PNG, JPG ou PDF)
2. Usar a ferramenta extract_nfe_from_image para extrair os dados
3. Retornar o resultado como dicionário Python (JSON)

Sempre use a ferramenta disponível para processar os arquivos.
IMPORTANTE: Retorne sempre o resultado em formato de dicionário, nunca como string."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    # Cria o agente
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Cria o executor do agente
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent_executor


# Função principal de uso
def extrair_nfe(file_input: Union[str, 'UploadedFile'], retornar_json: bool = True) -> Union[str, Dict[str, Any]]:
    """
    Função principal para extrair dados de NF-e/NFC-e
    
    Args:
        file_input: Pode ser:
            - String com o caminho do arquivo (PNG, JPG ou PDF)
            - UploadedFile do Streamlit (st.file_uploader)
        retornar_json: Se True, retorna JSON string. Se False, retorna Dict Python (padrão: True)
    
    Returns:
        JSON string (se retornar_json=True) ou Dict Python com os dados extraídos
    
    Exemplo de uso:
        # Retorna JSON string (padrão)
        resultado_json = extrair_nfe("nota_fiscal.png")
        print(resultado_json)  # '{"NFe": {...}}'
        
        # Retorna Dict Python
        resultado_dict = extrair_nfe("nota_fiscal.png", retornar_json=False)
        print(resultado_dict["NFe"]["identificacao"]["Nome_Emitente"])
        
        # Com Streamlit file_uploader
        uploaded_file = st.file_uploader("Envie a nota fiscal", type=["png", "jpg", "pdf"])
        if uploaded_file:
            resultado = extrair_nfe(uploaded_file)
    """
    try:
        # Verifica se é um UploadedFile do Streamlit
        if STREAMLIT_AVAILABLE and isinstance(file_input, UploadedFile):
            file_bytes, file_extension, file_name = process_uploaded_file(file_input)
            resultado_dict = _process_nfe_extraction(file_bytes, file_extension, file_name)
        
        # Se for uma string (caminho de arquivo)
        elif isinstance(file_input, str):
            # Lê os bytes do arquivo
            if not os.path.exists(file_input):
                resultado_dict = {
                    "erro": "Arquivo não encontrado",
                    "mensagem": f"O arquivo '{file_input}' não existe."
                }
            else:
                with open(file_input, 'rb') as f:
                    file_bytes = f.read()
                
                file_extension = Path(file_input).suffix.lower()
                file_name = Path(file_input).name
                
                resultado_dict = _process_nfe_extraction(file_bytes, file_extension, file_name)
        
        else:
            resultado_dict = {
                "erro": "Tipo de entrada inválido",
                "mensagem": "O arquivo deve ser um caminho (string) ou UploadedFile do Streamlit"
            }
        
        # Retorna JSON string ou Dict conforme solicitado
        if retornar_json:
            return json.dumps(resultado_dict, ensure_ascii=False, indent=2)
        else:
            return resultado_dict
            
    except Exception as e:
        erro_dict = {
            "erro": "Erro ao processar arquivo",
            "mensagem": str(e),
            "tipo_erro": type(e).__name__
        }
        
        if retornar_json:
            return json.dumps(erro_dict, ensure_ascii=False, indent=2)
        else:
            return erro_dict


def extrair_nfe_streamlit(uploaded_file) -> Dict[str, Any]:
    """
    Função específica para uso com Streamlit (alias para extrair_nfe)
    
    Args:
        uploaded_file: Objeto retornado por st.file_uploader()
    
    Returns:
        Dicionário Python com os dados extraídos ou mensagem de erro
    
    Exemplo de uso no Streamlit:
        uploaded_file = st.file_uploader(
            "Selecione um arquivo para enviar ao LenteFiscal",
            type=["png", "jpg", "jpeg", "pdf"],
            help="Selecione uma nota fiscal eletrônica"
        )
        
        if uploaded_file:
            with st.spinner("Processando nota fiscal..."):
                resultado = extrair_nfe_streamlit(uploaded_file)
            
            if "erro" in resultado:
                st.error(f"Erro: {resultado['mensagem']}")
            else:
                st.success("Nota fiscal processada com sucesso!")
                st.json(resultado)
    """
    return extrair_nfe(uploaded_file)


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo 1: Processar uma imagem pelo caminho
    print("=== EXEMPLO 1: Processando imagem PNG (caminho) ===")
    resultado = extrair_nfe("nota_fiscal.png")
    print("Tipo do resultado:", type(resultado))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Exemplo 2: Uso direto da ferramenta (sem agente)
    print("=== EXEMPLO 2: Uso direto da ferramenta ===")
    resultado_direto = extract_nfe_from_image.invoke({"file_path": "nota_fiscal.jpg"})
    print("Tipo do resultado:", type(resultado_direto))
    print(json.dumps(resultado_direto, ensure_ascii=False, indent=2))