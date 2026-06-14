import streamlit as st
from supabase import create_client, Client

# 1. Configuración de la ventana web (Debe ser la primera línea de Streamlit)
st.set_page_config(
    page_title="Sistema Maestro de Productos", 
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# RF-01: CONEXIÓN A BASE DE DATOS CACHEADA
# ========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Inicializar la conexión global para que esté disponible en todas las vistas
try:
    st.session_state.supabase = init_supabase()
except Exception as e:
    st.error(f"❌ Error crítico de conexión en el menú: {e}")

# ========================================
# ARCHITECTURA DEL MENÚ (Navegación)
# ========================================

# Definimos las páginas del menú lateral agrupadas por módulos operativos
pantalla_inicio = st.Page("views/inicio.py", title="Inicio", icon="🏠", default=True)
pantalla_carga = st.Page("views/cargar_archivo.py", title="Cargar Inventario", icon="📤")
pantalla_tablas = st.Page("views/ver_tablas.py", title="Maestro de Datos", icon="📊")

# Inicializamos el enrutador de navegación de Streamlit
navegacion = st.navigation({
    "Operaciones Core": [pantalla_inicio, pantalla_carga],
    "Consultas y Reportes": [pantalla_tablas]
})

# Ejecutar la página seleccionada en el menú por el usuario
navegacion.run()
