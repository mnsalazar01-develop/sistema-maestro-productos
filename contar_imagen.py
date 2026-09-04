import sys
import requests  # Petición directa libre de bloqueos
import streamlit as st
from supabase import create_client, Client

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide")

# 1. CARGA DE CREDENCIALES GLOBALES
try:
    URL_NUEVA = st.secrets["supabase"]["url"]
    KEY_NUEVA = st.secrets["supabase"]["key"]
except Exception as e:
    st.error(f"❌ Error al leer las claves de acceso de st.secrets: {e}")
    st.stop()

# 2. CONEXIÓN SEGURA CON SUPABASE
@st.cache_resource
def init_supabase_local() -> Client:
    return create_client(URL_NUEVA, KEY_NUEVA)

try:
    supabase = init_supabase_local()
except Exception as e:
    st.error(f"❌ Error de Conexión Base: {e}")
    st.stop()

# FUNCIÓN PARA OBTENER LOS NOMBRES DE ARCHIVOS
def obtener_todos_los_archivos():
    api_url = f"{URL_NUEVA.rstrip('/')}/storage/v1/object/list/imagenes"
    headers = {
        "Authorization": f"Bearer {KEY_NUEVA}",
        "ApiKey": KEY_NUEVA,
        "Content-Type": "application/json"
    }
    payload = {
        "prefix": "",
        "limit": 1000,
        "offset": 0,
        "sortBy": {"column": "name", "order": "asc"}
    }
    try:
        respuesta = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if respuesta.status_code != 200:
            return None
        archivos = respuesta.json()
        return [a.get('name') for a in archivos if a.get('name') != '.emptyFolderPlaceholder']
    except:
        return None

# NUEVA FUNCIÓN: FIRMAR URL PARA BUCKETS PRIVADOS
def obtener_url_firmada(nombre_archivo: str, expiracion_segundos: int = 1200):
    """
    Solicita una URL firmada a la API de Supabase para poder visualizar 
    un archivo dentro de un bucket privado de forma temporal (20 minutos).
    """
    api_url = f"{URL_NUEVA.rstrip('/')}/storage/v1/object/sign/imagenes/{nombre_archivo}"
    headers = {
        "Authorization": f"Bearer {KEY_NUEVA}",
        "ApiKey": KEY_NUEVA,
        "Content-Type": "application/json"
    }
    payload = {
        "expiresIn": expiracion_segundos
    }
    try:
        respuesta = requests.post(api_url, headers=headers, json=payload, timeout=10)
        if respuesta.status_code == 200:
            # La API nos devuelve un JSON con la ruta relativa firmada
            datos_firma = respuesta.json()
            url_relativa_firmada = datos_firma.get("signedURL")
            # Unimos la URL base de tu Supabase con la ruta firmada que nos entregó
            url_completa_firmada = f"{URL_NUEVA.rstrip('/')}/storage/v1{url_relativa_firmada}"
            return url_completa_firmada
        return None
    except:
        return None

# --- INTERFAZ DE USUARIO EN STREAMLIT ---
st.title("🗂️ Administrador Avanzado de Catálogo (Seguro/Firmado)")
st.write("Visualiza tus 646 fotos mediante URLs firmadas temporalmente.")

# Botón superior de escaneo rápido
if st.button("📊 Escanear Almacenamiento en Tiempo Real", use_container_width=True):
    with st.spinner("Sincronizando con el servidor de Supabase..."):
        imagenes = obtener_todos_los_archivos()
        if imagenes is not None:
            st.session_state['lista_fotos'] = imagenes
            st.success(f"¡Sincronizado! Se detectaron **{len(imagenes)}** archivos en el servidor.")
        else:
            st.error("No se pudo conectar con el almacenamiento.")

if 'lista_fotos' not in st.session_state:
    imagenes_iniciales = obtener_todos_los_archivos()
    if imagenes_iniciales:
        st.session_state['lista_fotos'] = imagenes_iniciales
    else:
        st.session_state['lista_fotos'] = []

lista_actual = st.session_state['lista_fotos']

if lista_actual:
    st.metric(label="📸 Total de Imágenes Detectadas", value=f"{len(lista_actual)} archivos")
    
    # Buscador por texto
    busqueda = st.text_input("🔍 Buscar foto por nombre:", placeholder="Ej: producto_01")
    if busqueda:
        fotos_filtradas = [f for f in lista_actual if busqueda.lower() in f.lower()]
    else:
        fotos_filtradas = lista_actual

    st.write(f"Mostrando {len(fotos_filtradas)} resultados:")

    # Cuadrícula adaptativa de 4 columnas
    columnas_por_fila = 4
    columnas = st.columns(columnas_por_fila)
    
    for indice, nombre_archivo in enumerate(fotos_filtradas):
        columna_actual = columnas[indice % columnas_por_fila]
        
        # Generamos la firma válida antes de dibujar la foto
        url_segura = obtener_url_firmada(nombre_archivo)
        
        with columna_actual:
            with st.container(border=True):
                if url_segura:
                    # Renderiza la foto protegida usando el token temporal
                    st.image(url_segura, use_container_width=True)
                    st.caption(f"📄 {nombre_archivo[:25]}..." if len(nombre_archivo) > 25 else f"📄 {nombre_archivo}")
                    
                    # Botón para descargar el archivo directamente a la PC
                    # Nota: Para descargar un archivo binario mediante URL firmada en Streamlit de forma óptima
                    # descargamos el contenido a través de requests al hacer click.
                    try:
                        # Preparamos la descarga
                        st.download_button(
                            label="Descargar",
                            data=url_segura, # Pasa el enlace seguro
                            file_name=nombre_archivo,
                            key=f"btn_{indice}"
                        )
                    except:
                        pass
                else:
                    st.error(f"⚠️ Error al firmar: {nombre_archivo[:15]}")
else:
    st.info("Presiona el botón de 'Escanear Almacenamiento' para cargar tus imágenes por primera vez.")
