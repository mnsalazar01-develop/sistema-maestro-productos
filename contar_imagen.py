import sys
import requests  # Petición directa libre de bloqueos
import streamlit as st
from supabase import create_client, Client

# CONFIGURACIÓN DE PÁGINA (Para que la galería se vea amplia)
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

# FUNCIÓN PARA RECOGER TODOS LOS ARCHIVOS
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
        # Filtramos para no mostrar archivos fantasmas del sistema
        return [a.get('name') for a in archivos if a.get('name') != '.emptyFolderPlaceholder']
    except:
        return None

# --- INTERFAZ DE USUARIO EN STREAMLIT ---
st.title("🗂️ Administrador Avanzado de Catálogo")
st.write("Visualiza tus 646 fotos sin las restricciones de la web de Supabase.")

# Botón superior de escaneo rápido
if st.button("📊 Escanear Almacenamiento en Tiempo Real", use_container_width=True):
    with st.spinner("Sincronizando con el servidor de Supabase..."):
        imagenes = obtener_todos_los_archivos()
        if imagenes is not None:
            st.session_state['lista_fotos'] = imagenes
            st.success(f"¡Sincronizado! Se detectaron **{len(imagenes)}** archivos en el servidor.")
        else:
            st.error("No se pudo conectar con el almacenamiento.")

# Cargar la lista automáticamente en segundo plano si no se ha escaneado
if 'lista_fotos' not in st.session_state:
    imagenes_iniciales = obtener_todos_los_archivos()
    if imagenes_iniciales:
        st.session_state['lista_fotos'] = imagenes_iniciales
    else:
        st.session_state['lista_fotos'] = []

lista_actual = st.session_state['lista_fotos']

if lista_actual:
    # Métrica principal
    st.metric(label="📸 Total de Imágenes Detectadas", value=f"{len(lista_actual)} archivos")
    
    # BUSCADOR EN TIEMPO REAL
    busqueda = st.text_input("🔍 Buscar foto por nombre:", placeholder="Ej: producto_01")
    
    # Filtrado por texto
    if busqueda:
        fotos_filtradas = [f for f in lista_actual if busqueda.lower() in f.lower()]
    else:
        fotos_filtradas = lista_actual

    st.write(f"Mostrando {len(fotos_filtradas)} resultados:")

    # DISEÑO DE LA GALERÍA EN CUADRÍCULA (4 Columnas)
    columnas_por_fila = 4
    columnas = st.columns(columnas_por_fila)
    
    # Construcción de URLs públicas para renderizar
    url_base_publica = f"{URL_NUEVA.rstrip('/')}/storage/v1/object/public/imagenes/"

    for indice, nombre_archivo in enumerate(fotos_filtradas):
        columna_actual = columnas[indice % columnas_por_fila]
        url_imagen_completa = url_base_publica + nombre_archivo
        
        with columna_actual:
            # Contenedor visual para cada foto
            with st.container(border=True):
                # Renderiza la imagen directo desde Supabase
                st.image(url_imagen_completa, use_container_width=True)
                # Muestra el nombre recortado por estética
                st.caption(f"📄 {nombre_archivo[:25]}..." if len(nombre_archivo) > 25 else f"📄 {nombre_archivo}")
                
                # Botón individual para descargar la foto a la PC
                st.download_button(
                    label="Descargar",
                    data=url_imagen_completa,
                    file_name=nombre_archivo,
                    key=f"btn_{indice}"
                )
else:
    st.info("Presiona el botón de 'Escanear Almacenamiento' para cargar tus imágenes por primera vez.")
