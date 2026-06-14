# ==============================================================================
# PROGRAMA: app.py (MENÚ PRINCIPAL INTERACTIVO)
# VERSIÓN: 3.6.0
# DESCRIPCIÓN: Panel Central Retail con Navegación por Botones de Alta Densidad
# MODIFICACIÓN: Uso estricto de st.switch_page para mantener el aislamiento plano.
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed" # Ocultamos la barra lateral nativa por estética
)

# 2. DECLARACIÓN DE INSTANCIAS DE PÁGINAS SUELTAS EN LA RAÍZ
# Streamlit necesita conocer los archivos físicos antes de poder hacer el switch
pagina_inventario = "cargar_inventario.py"
pagina_productos = "cargar_productos.py"
pagina_maestro = "maestro_datos.py"
pagina_reglas = "diccionario_reglas.py"

# 3. INTERFAZ VISUAL DEL PANEL DE BIENVENIDA (LAUNCHPAD)
st.title("🏭 Centro de Operaciones Retail - Menú Principal")
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
