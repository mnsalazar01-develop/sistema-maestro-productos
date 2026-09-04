import sys
import requests  # Petición directa libre de bloqueos
import streamlit as st
from supabase import create_client, Client

# CONFIGURACIÓN DE PÁGINA (Diseño ancho para aprovechar espacio)
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

# FUNCIÓN PARA FIRMAR URL
def obtener_url_firmada(nombre_archivo: str, expiracion_segundos: int = 1200):
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
            datos_firma = respuesta.json()
            url_relativa_firmada = datos_firma.get("signedURL")
            return f"{URL_NUEVA.rstrip('/')}/storage/v1{url_relativa_firmada}"
        return None
    except:
        return None

# --- INTERFAZ DE USUARIO EN STREAMLIT ---
st.title("🗂️ Administrador Avanzado de Catálogo")
st.write("Visualiza tus 646 fotos mediante URLs firmadas y personaliza el tamaño de previsualización.")

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
    
    # ZONA DE CONTROLES: Buscador y Slider de tamaño lado a lado
    col_busqueda, col_slider = st.columns([2, 1])
    
    with col_busqueda:
        busqueda = st.text_input("🔍 Buscar foto por nombre:", placeholder="Ej: producto_01")
        
    with col_slider:
        # El slider controla cuántas imágenes entran por fila (A más columnas, más pequeñas se ven)
        columnas_por_fila = st.slider(
            "📐 Tamaño de las imágenes (Columnas por fila):", 
            min_value=2, 
            max_value=10, 
            value=4,
            help="Menos columnas = Fotos Grandes. Más columnas = Fotos Pequeñas."
        )
    
    # Filtrado por texto
    if busqueda:
        fotos_filtradas = [f for f in lista_actual if busqueda.lower() in f.lower()]
    else:
        fotos_filtradas = lista_actual

    st.write(f"Mostrando {len(fotos_filtradas)} resultados:")

    # CREACIÓN DINÁMICA DE LA CUADRÍCULA
    columnas = st.columns(columnas_por_fila)
    
    for indice, nombre_archivo in enumerate(fotos_filtradas):
        columna_actual = columnas[indice % columnas_por_fila]
        url_segura = obtener_url_firmada(nombre_archivo)
        
        with columna_actual:
            with st.container(border=True):
                if url_segura:
                    st.image(url_segura, use_container_width=True)
                    # Recortamos el texto si hay muchas columnas para que no se desconfigure el diseño
                    limite_texto = 35 // columnas_por_fila
                    nombre_corto = f"{nombre_archivo[:limite_texto]}..." if len(nombre_archivo) > limite_texto else nombre_archivo
                    st.caption(f"📄 {nombre_corto}")
                    
                    try:
                        st.download_button(
                            label="📥",
                            data=url_segura,
                            file_name=nombre_archivo,
                            key=f"btn_{indice}",
                            use_container_width=True
                        )
                    except:
                        pass
                else:
                    st.error("⚠️ Error")
else:
    st.info("Presiona el botón de 'Escanear Almacenamiento' para cargar tus imágenes por primera vez.")
