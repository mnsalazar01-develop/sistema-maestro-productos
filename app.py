# ==============================================================================
# PROGRAMA: app.py (MENÚ PRINCIPAL OPERATIVO)
# VERSIÓN: 3.4.0
# DESCRIPCIÓN: Panel Central Activo del Sistema Maestro de Productos Retail
# MODIFICACIÓN: Integración de la llamada al nuevo programa cargar_productos.py
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide"
)

# 2. ENLACE DIRECTO A PROGRAMAS SATÉLITES EN EL DIRECTORIO RAÍZ
# Todos los archivos residen sueltos en el mismo nivel para evitar fallas de red
llamada_cargar = st.Page("cargar_inventario.py", title="Cargar Inventario", icon="📤")
llamada_productos = st.Page("cargar_productos.py", title="Cargar Productos", icon="📥") # Nueva llamada integrada
llamada_maestro = st.Page("maestro_datos.py", title="Maestro de Datos", icon="📊")
llamada_reglas = st.Page("diccionario_reglas.py", title="Mantenedor de Reglas", icon="⚙️")

# 3. CONSTRUCCIÓN AUTOMÁTICA DEL MENÚ DE LA BARRA LATERAL
enrutador_activo = st.navigation([
    llamada_cargar,
    llamada_productos, # Inyección en la secuencia de navegación
    llamada_maestro,
    llamada_reglas
])

# 4. COMPONENTE DE BIENVENIDA CORPORATIVO INTEGRADO
if "current_page" not in st.session_state:
    st.title("🏭 Centro de Operaciones Retail - Menú Principal")
    st.markdown("---")
    st.markdown("""
    ### Bienvenido al Ecosistema de Taxonomía de Productos Genéricos (Nivel 5)
    
    El sistema se encuentra **100% operativo** bajo un entorno parametrizado en la nube. Utiliza el menú desplegable de la **barra lateral izquierda** para navegar libremente por los módulos de la empresa:
    
    * **📤 Cargar Inventario**: Procesa catálogos masivos y mitiga errores mediante lógica adaptativa.
    * **📥 Cargar Productos**: Nueva sección operativa independiente del inventario.
    * **📊 Maestro de Datos**: Monitorea las tablas de Supabase y descarga auditorías comerciales en Excel.
    * **⚙️ Mantenedor de Reglas**: Alimenta el cerebro clasificador en caliente sin tocar el código.
    """)
    st.success("🔒 Sistema Blindado: Tablas protegidas mediante Políticas RLS y contingencias locales.")

# 5. EJECUCIÓN EN VIVO DEL ECOSISTEMA UNIFICADO
enrutador_activo.run()
