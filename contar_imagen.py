import sys
import requests  # Petición directa libre de bloqueos
import streamlit as st

# 2. CONEXIÓN SEGURA HEREDADA CON LAS LLAVES DE SUPABASE
@st.cache_resource
def init_supabase_local() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

    try:
        supabase = init_supabase_local()
    except Exception as e:
        st.error(f"❌ Error de Conexión Base: {e}")
        st.stop()


def contar_archivos_reales_bucket():
    st.write("🔍 Conectando con el servidor de almacenamiento de Supabase...")
    
    # Endpoint oficial de la API de Supabase para listar objetos
    api_url = f"{url.rstrip('/')}/storage/v1/object/public/imagenes"
    
    #headers = {
    #    "Authorization": f"Bearer {KEY_NUEVA}",
    #    "ApiKey": KEY_NUEVA,
    #    "Content-Type": "application/json"
    #}
    
    # Configuramos un límite de 1000 para asegurarnos de que cuente todo tu catálogo de 600 fotos de un solo golpe
    payload = {
        "prefix": "",
        "limit": 1000,
        "offset": 0,
        "sortBy": {"column": "name", "order": "asc"}
    }
    
    try:
        # Hacemos la consulta directa por POST HTTP
        respuesta = requests.post(api_url, headers=headers, json=payload, timeout=15)
        
        if respuesta.status_code != 200:
            st.error(f"❌ El servidor de Supabase rechazó la consulta (Código {respuesta.status_code})")
            return
            
        archivos_servidor = respuesta.json()
        
        # Filtramos para descontar los archivos ocultos de inicialización del sistema
        lista_imagenes_reales = [a for a in archivos_servidor if a.get('name') != '.emptyFolderPlaceholder']
        
        cantidad_total = len(lista_imagenes_reales)
        
        # Desplegamos el resultado final con un diseño limpio
        st.metric(label="📸 Total de Imágenes en Bucket", value=f"{cantidad_total} archivos")
        
        if cantidad_total > 0:
            st.success(f"✨ ¡Verificación completada! Hay **{cantidad_total} objetos** listos para usarse en tu catálogo privado.")
        else:
            st.warning("⚠️ El bucket se encuentra totalmente vacío actualmente.")
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error de red al intentar escanear el almacenamiento: {e}")

# Dibujamos un botón de prueba en la interfaz de Streamlit
if st.button("📊 Verificar Cantidad Real en el Almacenamiento", type="secondary", use_container_width=True):
    contar_archivos_reales_bucket()
