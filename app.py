# ==============================================================================
# PROGRAMA CENTRAL: app.py (LAUNCHPAD CORPORATIVO CONFIGURADO)
# VERSIÓN: 4.1.0 (REPARACIÓN DE LLAVE DUPLICADA)
# DESCRIPCIÓN: Panel Central Retail con Navegación por Botones y Control de Auto-Importación
# MODIFICACIÓN: Uso de condicional de selección para mitigar el StreamlitDuplicateElementKey.
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. DECLARACIÓN FORMAL DE INSTANCIAS DE PÁGINAS SATÉLITES EN LA RAÍZ
# Declaramos los archivos independientes que viven sueltos en el directorio raíz
pagina_inventario = st.Page("cargar_inventario.py", title="Cargar Inventario Masivo", icon="📤")
pagina_productos = st.Page("cargar_productos.py", title="Registrar Producto Manual", icon="📝")
pagina_maestro = st.Page("maestro_datos.py", title="Maestro de Datos", icon="📊")
pagina_reglas = st.Page("diccionario_reglas.py", title="Mantenedor de Reglas", icon="⚙️")

# 3. CONSTRUCCIÓN AUTOMÁTICA DEL MOTOR DE NAVEGACIÓN EN LA BARRA LATERAL
# Registramos la secuencia limpia de las 4 estaciones de trabajo del negocio
enrutador_global = st.navigation([
    pagina_inventario, 
    pagina_productos, 
    pagina_maestro, 
    pagina_reglas
])

# Componentes fijos de control e identidad comercial en la barra de la izquierda
st.sidebar.markdown("### 🔒 Ecosistema Retail Activo")
st.sidebar.caption("Estaciones de trabajo descentralizadas e independientes.")
st.sidebar.markdown("---")

# 4. TRUCO DE ARQUITECTURA: EVALUACIÓN DE PÁGINA ACTUAL
# Si el usuario NO ha seleccionado ningún archivo secundario del menú lateral,
# pintamos el Launchpad corporativo por botones en la pantalla de bienvenida.
if enrutador_global.current_page is None:
    st.title("🏭 Centro de Operaciones Retail - Menú Principal")
    st.markdown("Bienvenido al ecosistema modular de taxonomía y control de productos del negocio.")
    st.markdown("---")

    # Estructuramos el menú visual utilizando una grilla limpia de 4 columnas de alta densidad
    col_inv, col_prod, col_maestro, col_reglas = st.columns(4)

    with col_inv:
        st.markdown("#### Cargar Inicial de Inventario Masivo")
        st.caption("Procesador masivo de archivos planos CSV mediante el diccionario duro de confianza.")
        if st.button("📤 Batch - Imput Inventario", use_container_width=True, key="btn_p1_inv_fijo"):
            st.switch_page(pagina_inventario)

    with col_prod:
        st.markdown("#### Registrar Producto")
        st.caption("Alta manual reactiva de artículos nuevos y control multimedia.")
        if st.button("📝 Ingesta de Catálogo", use_container_width=True, key="btn_p1_prod_fijo"):
            st.switch_page(pagina_productos)

    with col_maestro:
        st.markdown("#### Maestro de Datos")
        st.caption("Visualizador de registros en tiempo real y extractor binario a formato Excel.")
        if st.button("📊 Auditar Tablas", use_container_width=True, key="btn_p1_mae_fijo"):
            st.switch_page(pagina_maestro)

    with col_reglas:
        st.markdown("#### Mantenedor de Reglas")
        st.caption("Panel de control para inyectar y actualizar equivalencias léxicas en caliente.")
        if st.button("⚙️ Mantenimiento de Reglas", use_container_width=True, key="btn_p1_reglas_fijo"):
            st.switch_page(pagina_reglas)

    st.markdown("---")
    st.info("💡 Consejo técnico: Utiliza la barra lateral de la izquierda para ingresar directo a los programas o para cambiar de estación de trabajo con un clic.")

# 5. DESPACHO CENTRAL SEGURO LIBRE DE COMPILACIONES DUPLICADAS
enrutador_global.run()
