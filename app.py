import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Configuración de la ventana web de Streamlit
st.set_page_config(
    page_title="Sistema Maestro de Productos", 
    page_icon="📦",
    layout="wide"
)

# ========================================
# RF-01: CONEXIÓN A BASE DE DATOS CACHEADA
# ========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Inicializar la conexión global de Supabase
try:
    supabase = init_supabase()
    st.sidebar.success("⚡ Conectado a Supabase Cloud")
except Exception as e:
    st.sidebar.error(f"❌ Error de conexión: {e}")

# ========================================
# ARQUITECTURA DEL MENÚ (Mediante Pestañas)
# ========================================
st.title("📦 Sistema Maestro de Clasificación de Productos")
st.markdown("Bienvenido al centro operativo de taxonomía retail.")

# Creamos las 3 secciones del menú en la parte superior de la pantalla
tab_inicio, tab_carga, tab_maestro = st.tabs(["🏠 Inicio", "📤 Cargar Inventario", "📊 Maestro de Datos"])

# ----------------------------------------
# SECCIÓN 1: INICIO
# ----------------------------------------
with tab_inicio:
    st.subheader("Panel de Bienvenida")
    st.markdown("""
    Esta aplicación web te permite estructurar tu catálogo de productos en bruto bajo el estándar de la industria.
    
    ### Tus 3 Pilares de Datos Activos:
    1. **Categorías (Nivel 1)**: Los 7 pasillos principales sembrados en Supabase.
    2. **Subcategorías (Nivel 3/4)**: Tus familias de competencia directa ya cargadas.
    3. **Productos (Nivel 5)**: Tu nueva propuesta de genéricos puros.
    """)
    st.info("Haz clic en la pestaña 'Cargar Inventario' de arriba para empezar a procesar tu archivo Excel.")

# ----------------------------------------
# SECCIÓN 2: CARGAR INVENTARIO
# ----------------------------------------
with tab_carga:
    st.subheader("Procesador de Archivos en Bruto")
    st.markdown("Sube tu archivo Excel con la columna `nombre` para clasificarlo automáticamente.")
    
    # Componente visual para arrastrar y soltar el archivo Excel
    archivo_subido = st.file_uploader("Selecciona tu archivo .xlsx de productos", type=["xlsx"])
    
    if archivo_subido:
        st.success("File uploaded successfully!")
        # Aquí procesaremos el archivo con pandas en el siguiente paso

# ----------------------------------------
# SECCIÓN 3: MAESTRO DE DATOS
# ----------------------------------------
with tab_maestro:
    st.subheader("Visualizador de Tablas en Supabase")
    st.markdown("Monitorea el estado actual de tu base de datos en tiempo real.")
    
    if st.button("🔄 Refrescar datos de Supabase"):
        try:
            # Consulta rápida de prueba para jalar tus 7 categorías de la nube
            respuesta = supabase.table("categorias").select("*").execute()
            df_cat = pd.DataFrame(respuesta.data)
            st.dataframe(df_cat, use_container_width=True)
        except Exception as e:
            st.error(f"Error al consultar Supabase: {e}")
