import os
import io
import time
import streamlit as st

from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv


load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="LenteFiscal - Agente IA 🔍🤖",
    page_icon="🤖",
    layout="wide"
)

# Inicializar session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'lista_arquivos' not in st.session_state:
    st.session_state.lista_arquivos = []
if 'upload_key' not in st.session_state:
    st.session_state.upload_key = 0
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()


# Configurações MinIO
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'False').lower() == 'true'

BUCKET_NAME_RECEBIDOS = os.getenv('BUCKET_RECEBIDOS')
BUCKET_NAME_PROCESSADOS = os.getenv('BUCKET_PROCESSADOS')
BUCKET_NAME_ERRORS = os.getenv('BUCKET_ERROS')

ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Intervalo de atualização automática (20 segundos)
AUTO_REFRESH_INTERVAL = 20

def conectar_minio():
    """Cria conexão com o MinIO"""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        # Verificar se o bucket existe, se não, criar
        if not client.bucket_exists(BUCKET_NAME_RECEBIDOS):
            client.make_bucket(BUCKET_NAME_RECEBIDOS)
        if not client.bucket_exists(BUCKET_NAME_PROCESSADOS):
            client.make_bucket(BUCKET_NAME_PROCESSADOS)
        if not client.bucket_exists(BUCKET_NAME_ERRORS):
            client.make_bucket(BUCKET_NAME_ERRORS)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar ao MinIO: {str(e)}")
        return None

def validar_login(usuario, senha):
    """Validação simples de login - em produção, use autenticação real"""
    if usuario.strip() and senha.strip():
        if usuario == ADMIN_USER and senha == ADMIN_PASSWORD:
            return True
    return False

def logout():
    """Realiza logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.upload_key = 0
    st.rerun()

def limpar_upload():
    """Limpa o componente de upload incrementando a key"""
    st.session_state.upload_key += 1

def pagina_login():
    """Página de login"""
    st.title("LenteFiscal - Agente IA 🔍🤖")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Acesse sua conta")
        
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            senha = st.text_input("🔑 Senha", type="password", placeholder="Digite sua senha")
            
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                if not usuario.strip():
                    st.error("❌ Por favor, preencha o campo de usuário.")
                elif not senha.strip():
                    st.error("❌ Por favor, preencha o campo de senha.")
                elif validar_login(usuario, senha):
                    st.session_state.authenticated = True
                    st.session_state.username = usuario
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha inválidos.")
        
        st.info(f"💡 **Credenciais de teste:** usuário: `{ADMIN_USER}` | senha: `{ADMIN_PASSWORD}`")

def listar_arquivos_bucket(minio_client, bucket_name, titulo, mostrar_delete=False):
    """Função auxiliar para listar arquivos de um bucket com auto-refresh"""
    st.subheader(titulo)
    
    # Placeholder para o botão de refresh manual
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Atualizar", key=f"refresh_{bucket_name}"):
            st.session_state.last_refresh = time.time()
            st.rerun()
    
    try:
        # Listar objetos no bucket
        objects = list(minio_client.list_objects(bucket_name, recursive=True))
        
        if not objects:
            st.info("🔭 Nenhum arquivo encontrado.")
        else:
            st.success(f"📊 Total de arquivos: **{len(objects)}**")
            
            # Criar tabela de arquivos
            for idx, obj in enumerate(objects):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.text(f"📄 {obj.object_name}")
                
                with col2:
                    # Formatar tamanho do arquivo
                    size_kb = obj.size / 1024
                    if size_kb < 1024:
                        size_str = f"{size_kb:.2f} KB"
                    else:
                        size_str = f"{size_kb/1024:.2f} MB"
                    st.text(f"💾 {size_str}")
                
                with col3:
                    # Formatar data de modificação
                    last_modified = obj.last_modified.strftime("%d/%m/%Y %H:%M")
                    st.text(f"🕐 {last_modified}")
                
                with col4:
                    # Botão de delete (apenas se habilitado)
                    if mostrar_delete:
                        if st.button("🗑️", key=f"delete_{bucket_name}_{idx}", help="Deletar arquivo"):
                            try:
                                minio_client.remove_object(bucket_name, obj.object_name)
                                st.success(f"✅ Arquivo '{obj.object_name}' deletado!")
                                st.rerun()
                            except S3Error as e:
                                st.error(f"❌ Erro ao deletar: {str(e)}")
                
                st.markdown("---")
    
    except S3Error as e:
        st.error(f"❌ Erro ao listar arquivos: {str(e)}")

def pagina_principal():
    """Página principal com funcionalidades do MinIO"""
    # Cabeçalho com botão de logout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🔍 Gerenciamento de Arquivos Fiscais")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    st.markdown(f"**Usuário logado:** {st.session_state.username}")
    st.markdown("---")
    
    # Conectar ao MinIO
    minio_client = conectar_minio()
    
    if minio_client is None:
        st.error("❌ Não foi possível conectar ao Servidor de Arquivos. Verifique as configurações.")
        return
    
    # Seção de Upload
    st.subheader("📤 Upload de Arquivo")
    
    # Usar key dinâmica para resetar o file_uploader
    uploaded_file = st.file_uploader(
        "Selecione um arquivo para enviar ao LenteFiscal",
        type=None,
        help="Selecione qualquer tipo de arquivo para fazer upload",
        key=f"uploader_{st.session_state.upload_key}"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📄 Arquivo selecionado: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
        with col2:
            if st.button("⬆️ Enviar", use_container_width=True, key="btn_enviar"):
                try:
                    # Upload do arquivo
                    file_data = uploaded_file.getvalue()
                    file_size = len(file_data)
                    
                    minio_client.put_object(
                        BUCKET_NAME_RECEBIDOS,
                        uploaded_file.name,
                        io.BytesIO(file_data),
                        file_size,
                        content_type=uploaded_file.type
                    )
                    st.success(f"✅ Arquivo '{uploaded_file.name}' enviado com sucesso!")
                    
                    # Limpar o upload incrementando a key
                    limpar_upload()
                    
                    # Aguardar um momento e atualizar
                    time.sleep(0.5)
                    st.rerun()
                    
                except S3Error as e:
                    st.error(f"❌ Erro ao enviar arquivo: {str(e)}")
    
    st.markdown("---")
    
    # Verificar se precisa atualizar automaticamente
    tempo_atual = time.time()
    tempo_decorrido = tempo_atual - st.session_state.last_refresh
    
    # Exibir contador de tempo até próxima atualização
    tempo_restante = int(AUTO_REFRESH_INTERVAL - tempo_decorrido)
    if tempo_restante > 0:
        st.info(f"🔄 Próxima atualização automática em: **{tempo_restante}s**")
    
    # Auto-refresh a cada 20 segundos
    if tempo_decorrido >= AUTO_REFRESH_INTERVAL:
        st.session_state.last_refresh = tempo_atual
        st.rerun()
    
    # Listar arquivos dos três buckets
    listar_arquivos_bucket(
        minio_client, 
        BUCKET_NAME_RECEBIDOS, 
        "📋 Arquivos Recebidos",
        mostrar_delete=True
    )
    
    st.markdown("---")
    
    listar_arquivos_bucket(
        minio_client, 
        BUCKET_NAME_PROCESSADOS, 
        "📋 Arquivos Processados",
        mostrar_delete=False
    )
    
    st.markdown("---")
    
    listar_arquivos_bucket(
        minio_client, 
        BUCKET_NAME_ERRORS, 
        "📋 Arquivos com Problemas",
        mostrar_delete=False
    )
    
    # Timer invisível para forçar re-render
    st.markdown(
        f"""
        <script>
            setTimeout(function(){{
                window.location.reload();
            }}, {AUTO_REFRESH_INTERVAL * 1000});
        </script>
        """,
        unsafe_allow_html=True
    )

# Controle de navegação
def main():
    if not st.session_state.authenticated:
        pagina_login()
    else:
        pagina_principal()

if __name__ == "__main__":
    main()