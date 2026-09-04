import sys
import requests  # Petición directa libre de bloqueos
import streamlit as st
from supabase import create_client, Client  # REPARADO: Importación faltante

# 1. CARGA DE CREDENCIALES GLOBALES (Para que funcionen en todo el script)
try:
    URL_NUEVA = st.secrets["supabase"]["url"]
    KEY_NUEVA = st.secrets["supabase"]["key"]
except Exception as e:
    st.error(f"❌ Error al leer las claves de acceso de st.secrets: {e}")
    st.stop()

# 2. CONEXIÓN SEGURA HEREDADA CON LAS LLAVES DE SUPABASE
@st.cache_resource
def init_supabase_local() -> Client:
    return create_client(URL_NUEVA, KEY_NUEVA)

try:
    supabase = init_supabase_local()
except Exception as e:
    st.error(f"❌ Error de Conexión Base: {e}")
    st.stop()

def contar_archivos_reales_bucket():
    st.write("🔍 Conectando con el servidor de almacenamiento de Supabase...")
    
    # Endpoint oficial de la API de Supabase para listar objetos
    api_url = f"{URL_NUEVA.rstrip('/')}/storage/v1/object/list/imagenes"
    
    headers = {
        "Authorization": f"Bearer {KEY_NUEVA}",
        "ApiKey": KEY_NUEVA,
        "Content-Type": "application/json"
    }
    
    # Configuramos un límite de 1000 para asegurar el tiro
    payload = {
        "prefix": "",
        "limit": 1000,
        "offset": 0,
        "sortBy": {"column": "name", "order": "asc"}
    }
    
    try:
        # Hacemos la consulta directa por POST HTTP
        respuesta = requests.post(api_url, headers=headers, json=payload, timeout=15)
        
        # REPARADO: Corregido '1=' por '!='
        if respuesta.status_code != 200:
            st.error(f"❌ El servidor de Supabase rechazó la consulta (Código {respuesta.status_code})")
            return
            
        archivos_servidor = respuesta.json()
        
        # Filtramos para descontar los archivos ocultos y extraer solo los nombres
        lista_imagenes_reales = [a.get('name') for a in archivos_servidor if a.get('name') != '.emptyFolderPlaceholder']
        cantidad_total = len(lista_imagenes_reales)
        
        # Desplegamos el resultado final
        st.metric(label="📸 Total de Imágenes en Bucket", value=f"{cantidad_total} archivos")
        
        if cantidad_total > 0:
            st.success(f"✨ ¡Verificación completada! Hay **{cantidad_total} objetos** listos en tu catálogo.")
            
            # SOLUCIÓN AL COPIADO: Creamos un bloque de texto descargable
            texto_descarga = "\n".join(lista_imagenes_reales)
            
            st.download_button(
                label="📥 Descargar Listado de Archivos (.txt)",
                data=texto_descarga,
                file_name="lista_imagenes_bucket.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.warning("⚠️ El bucket se encuentra totalmente vacío actualmente.")
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error de red al intentar escanear el almacenamiento: {e}")

# Dibujamos un botón de prueba en la interfaz de Streamlit
if st.button("📊 Verificar Cantidad Real en el Almacenamiento", type="primary", use_container_width=True):
    contar_archivos_reales_bucket()
