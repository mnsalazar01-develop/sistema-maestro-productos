# ==============================================================================
# PROGRAMA: app.py (MENÚ PRINCIPAL INTERACTIVO CORREGIDO)
# VERSIÓN: 3.7.0
# DESCRIPCIÓN: Panel Central Retail con Navegación por Botones y Mapa Oculto
# MODIFICACIÓN: Inclusión de st.Page y st.navigation(position="hidden") contra excepciones.
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. DECLARACIÓN FORMAL DE PÁGINAS SATÉLITES SUELTAS EN LA RAÍZ
# Esto le enseña al servidor los caminos físicos para que st.switch_page no falle
pag_inventario = st.Page("cargar_inventario.py", title="Cargar Inventario")
pag_productos = st.Page("cargar_productos.py", title="Cargar Productos")
pag_maestro = st.Page("maestro_datos.py", title="Maestro de Datos")
pag_reglas = st.Page("diccionario_reglas.py", title="Mantenedor de Reglas")

# 3. MOTOR DE NAVES DECLARADO EN MODO OCULTO (Evita el error de API)
enrutador_oculto = st.navigation(
    [pag_inventario, pag_productos, pag_maestro, pag_reglas],
    position="hidden" # Esconde la barra lateral nativa pero registra las rutas en RAM
)

# 4. INTERFAZ VISUAL DEL PANEL DE BIENVENIDA (LAUNCHPAD)
st.title("🏭 Centro de Operaciones Retail - Menú Principal")
st.markdown("Bienvenido al ecosistema modular de taxonomía y control de productos.")
st.markdown("---")

# Estructuramos el menú visual utilizando una grilla limpia de 4 columnas
col_inv, col_prod, col_maestro, col_reglas = st.columns(4)

with col_inv:
    st.markdown("#### Cargar Inventario")
    st.caption("Procesador masivo de archivos planos CSV mediante el diccionario duro de confianza.")
    if st.button("📤 Procesar Catálogo", use_container_width=True, key="btn_h_inv"):
        st.switch_page(pag_inventario)

with col_prod:
    st.markdown("#### Registrar Producto")
    st.caption("Alta manual reactiva de artículos nuevos y control multimedia.")
    if st.button("📝 Ingesta de Catálogo", use_container_width=True, key="btn_h_reg"):
        st.switch_page(pag_productos)

with col_maestro:
    st.markdown("#### Maestro de Datos")
    st.caption("Visualizador de registros en tiempo real y extractor binario a formato Excel.")
    if st.button("📊 Auditar Tablas", use_container_width=True, key="btn_h_mae"):
        st.switch_page(pag_maestro)

with col_reglas:
    st.markdown("#### Mantenedor de Reglas")
    st.caption("Panel de control para inyectar y actualizar equivalencias léxicas en caliente.")
    if st.button("⚙️ Gestionar Diccionario", use_container_width=True, key="btn_h_reglas"):
        st.switch_page(pag_reglas)

st.markdown("---")
st.info("🔒 Seguridad de Procesos: Cada estación de trabajo se ejecuta de forma aislada en su propio espacio de memoria RAM.")
