import streamlit as st

# ===============================================================================
# COMMENT INDICADOR: >>> CODIGO UNIFICADO REPARADO v3.6.1 <<<
# MODULO: LAUNCHPAD INTERACTIVO CON NAVEGACIÓN INVISIBLE POR BOTONES PLANOS
# ===============================================================================
__version__ = "3.6.1"
__last_update__ = "2026-06-14"
__author__ = "Control Víveres Pro Team"

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed" # Ocultamos la barra lateral nativa por estética
)

# ===============================================================================
# 2. CONVERSIÓN MANDATORIA A OBJETOS DE PÁGINA NATIVOS (REPARACIÓN DE CONGELAMIENTO)
# ===============================================================================
# Streamlit exige instanciar formalmente los archivos antes de poder usar st.switch_page
pagina_inventario = st.Page("cargar_inventario.py", title="Cargar Inventario", icon="📤")
pagina_productos = st.Page("cargar_productos.py", title="Registrar Producto", icon="📝")
pagina_maestro = st.Page("maestro_datos.py", title="Maestro de Datos", icon="📊")
pagina_reglas = st.Page("diccionario_reglas.py", title="Mantenedor de Reglas", icon="⚙️")

# 3. INTERFAZ VISUAL DEL PANEL DE BIENVENIDA (LAUNCHPAD)
st.title("🏭 Centro de Operations Retail - Menú Principal")
st.markdown("Bienvenido al ecosistema modular de taxonomía y control de productos.")
st.markdown("---")

# Estructuramos el menú visual utilizando una grilla limpia de 4 columnas
col_inv, col_prod, col_maestro, col_reglas = st.columns(4)

with col_inv:
    st.markdown("#### Cargar Inventario")
    st.caption("Procesador masivo de archivos planos CSV mediante el diccionario duro de confianza.")
    if st.button("📤 Procesar Catálogo", use_container_width=True, key="btn_h_inv"):
        st.switch_page(pagina_inventario)

with col_prod:
    st.markdown("#### Registrar Producto")
    st.caption("Alta manual reactiva de artículos nuevos y control multimedia.")
    if st.button("📝 Ingesta de Catálogo", use_container_width=True, key="btn_h_reg"):
        st.switch_page(pagina_productos)

with col_maestro:
    st.markdown("#### Maestro de Datos")
    st.caption("Visualizador de registros en tiempo real y extractor binario a formato Excel.")
    if st.button("📊 Auditar Tablas", use_container_width=True, key="btn_h_mae"):
        st.switch_page(pagina_maestro)

with col_reglas:
    st.markdown("#### Mantenedor de Reglas")
    st.caption("Panel de control para inyectar y actualizar equivalencias léxicas en caliente.")
    if st.button("⚙️ Gestionar Diccionario", use_container_width=True, key="btn_h_reglas"):
        st.switch_page(pagina_reglas)

st.markdown("---")
st.info("🔒 Seguridad de Procesos: Cada estación de trabajo se ejecuta de forma aislada en su propio espacio de memoria RAM.")

# ===============================================================================
# 4. INICIALIZACIÓN SÍNCRONA DEL ENRUTADOR OCULTO (TUERCA CRÍTICA QUE FALTABA)
# ===============================================================================
# Agrupamos las instancias en el navegador y escondemos la barra nativa lateral
pg = st.navigation(
    [pagina_inventario, pagina_productos, pagina_maestro, pagina_reglas], 
    position="hidden"
)

# Despacho central obligatorio de Streamlit para mantener vivo el hilo de ejecucion
pg.run()
