# ==============================================================================
# PROGRAMA: app.py (ARCHIVO RAÍZ ÚNICO)
# VERSIÓN: 2.1.0
# DESCRIPCIÓN: Sistema Maestro de Clasificación de Productos Genéricos Retail
# MODIFICACIÓN: Enfoque paramétrico puro unificado en raíz sin subcarpetas.
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# Configuración de la ventana web de Streamlit
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

# Estructura superior unificada en el archivo raíz
tab_inicio, tab_carga, tab_maestro, tab_reglas = st.tabs([
    "🏠 Inicio", 
    "📤 Cargar Inventario", 
    "📊 Maestro de Datos",
    "⚙️ Mantenedor de Reglas"
])

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
