# ==============================================================================
# PROGRAMA CENTRAL: app.py (LAUNCHPAD CORPORATIVO ACTIVO)
# VERSIÓN: 4.0.0 (CONSOLIDACIÓN PRIORIDAD 1)
# DESCRIPCIÓN: Panel Central Retail con Navegación por Botones y Barra Lateral Activa
# MODIFICACIÓN: Inclusión de st.navigation expuesto con retorno nativo al Launchpad.
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"  # Barra lateral visible por defecto como brújula visual
)

# 2. DECLARACIÓN FORMAL DE INSTANCIAS DE PÁGINAS SATÉLITES EN LA RAÍZ
# Registramos 'app.py' como la raíz por defecto para habilitar el retorno nativo desde la izquierda
pagina_inicio = st.Page("app.py", title="🏭 Launchpad Central", icon="🏠", default=True)
pagina_inventario = st.Page("cargar_inventario.py", title="Cargar Inventario Masivo", icon="📤")
pagina_productos = st.Page("cargar_productos.py", title="Registrar Producto Manual", icon="📝")
pagina_maestro = st.Page("maestro_datos.py", title="Maestro de Datos", icon="📊")
pagina_reglas = st.Page("diccionario_reglas.py", title="Mantenedor de Reglas", icon="⚙️")

# 3. ENRUTADOR CENTRAL CON BARRA LATERAL VISIBLE (Indicador de Estatus Continuo)
# Al estar visible, el usuario siempre puede hacer clic en "Launchpad Central" para regresar
enrutador_global = st.navigation(
    [pagina_inicio, pagina_inventario, pagina_productos, pagina_maestro, pagina_reglas],
    position="sidebar"
)

# Colocamos un aviso de estatus corporativo fijo arriba en la barra de control de la izquierda
st.sidebar.markdown("### 🔒 Ecosistema Retail Activo")
st.sidebar.caption("Estaciones de trabajo descentralizadas e independientes.")
st.sidebar.markdown("---")

# 4. COMPONENTE VISUAL DEL PANEL DE BIENVENIDA (LAUNCHPAD INTERACTIVO)
st.title("🏭 Centro de Operaciones Retail - Menú Principal")
st.markdown("Bienvenido al ecosistema modular de taxonomía y control de productos del negocio.")
st.markdown("---")

# Estructuramos el menú visual utilizando una grilla limpia de 4 columnas de alta densidad
col_inv, col_prod, col_maestro, col_reglas = st.columns(4)

with col_inv:
    st.markdown("#### Cargar Inicial de Inventario Masivo")
    st.caption("Procesador masivo de archivos planos CSV mediante el diccionario duro de confianza.")
    if st.button("📤 Batch - Imput Inventario", use_container_width=True, key="btn_p1_inv"):
        st.switch_page(pagina_inventario)

with col_prod:
    st.markdown("#### Registrar Producto")
    st.caption("Alta manual reactiva de artículos nuevos y control multimedia.")
    if st.button("📝 Ingesta de Catálogo", use_container_width=True, key="btn_p1_prod"):
        st.switch_page(pagina_productos)

with col_maestro:
    st.markdown("#### Maestro de Datos")
    st.caption("Visualizador de registros en tiempo real y extractor binario a formato Excel.")
    if st.button("📊 Auditar Tablas", use_container_width=True, key="btn_p1_mae"):
        st.switch_page(pagina_maestro)

with col_reglas:
    st.markdown("#### Mantenedor de Reglas")
    st.caption("Panel de control para inyectar y actualizar equivalencias léxicas en caliente.")
    if st.button("⚙️ Mantenimiento de Reglas", use_container_width=True, key="btn_p1_reglas"):
        st.switch_page(pagina_reglas)

st.markdown("---")
st.info("💡 Consejo técnico: Si te encuentras trabajando dentro de un archivo secundario, utiliza el menú desplegable de la barra lateral izquierda para volver de inmediato a esta portada.")

# 5. DESPACHO CENTRAL Y CONTROL DEL HILO DE EJECUCIÓN
enrutador_global.run()
