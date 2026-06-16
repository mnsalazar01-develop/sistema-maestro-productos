# ==============================================================================
# PROGRAMA CENTRAL: app.py (CENTRO DE CONTROL ACTIVO)
# VERSIÓN: 4.2.0 (REPARACIÓN DE ATRIBUTO Y CAMBIO DE ETIQUETAS)
# DESCRIPCIÓN: Panel Central Retail con Navegación por Botones y Registro de Rutas
# MODIFICACIÓN: Uso de función de página para la portada contra AttributeError.
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. DEFINICIÓN DE LA PÁGINA DE PORTADA (CENTRO DE CONTROL)
def mostrar_centro_control():
    st.title("🏭 Centro de Control")
    st.markdown("Bienvenido al ecosistema modular de taxonomía y control de productos del negocio.")
    st.markdown("---")

    # Estructuramos el menú visual utilizando una grilla limpia de 4 columnas de alta densidad
    col_inv, col_prod, col_maestro, col_reglas = st.columns(4)

    with col_inv:
        st.markdown("#### Cargar Inicial de Inventario Masivo")
        st.caption("Procesador masivo de archivos planos CSV mediante el diccionario duro de confianza.")
        if st.button("📤 Batch - Imput Inventario", use_container_width=True, key="btn_p1_inv_v420"):
            st.switch_page(pagina_inventario)

    with col_prod:
        st.markdown("#### Registrar Producto")
        st.caption("Alta manual reactiva de artículos nuevos y control multimedia.")
        if st.button("📝 Ingesta de Catálogo", use_container_width=True, key="btn_p1_prod_v420"):
            st.switch_page(pagina_productos)

    with col_maestro:
        st.markdown("#### Maestro de Datos")
        st.caption("Visualizador de registros en tiempo real y extractor binario a formato Excel.")
        if st.button("📊 Auditar Tablas", use_container_width=True, key="btn_p1_mae_v420"):
            st.switch_page(pagina_maestro)

    with col_reglas:
        st.markdown("#### Diccionario de Reglas")  # Ajuste de título solicitado
        st.caption("Panel de control para inyectar y actualizar equivalencias léxicas en caliente.")
        if st.button("⚙️ Mantenimiento de Reglas", use_container_width=True, key="btn_p1_reglas_v420"):
            st.switch_page(pagina_reglas)

    st.markdown("---")
    st.info("💡 Consejo técnico: Utiliza la barra lateral de la izquierda para ingresar directo a los programas o para cambiar de estación de trabajo con un clic.")

# 3. DECLARACIÓN FORMAL DE INSTANCIAS DE PÁGINAS SATÉLITES EN LA RAÍZ
# Registramos la portada como la página inicial del sistema usando la función limpia
pagina_inicio = st.Page(mostrar_centro_control, title="🏭 Centro de Control", icon="🏠", default=True)
pagina_inventario = st.Page("cargar_inventario.py", title="Cargar Inventario Masivo", icon="📤")
pagina_productos = st.Page("cargar_productos.py", title="Registrar Producto Manual", icon="📝")
pagina_maestro = st.Page("maestro_datos.py", title="Maestro de Datos", icon="📊")
pagina_reglas = st.Page("diccionario_reglas.py", title="Mantenedor de Reglas", icon="⚙️")

# 4. CONSTRUCCIÓN AUTOMÁTICA DEL MOTOR DE NAVEGACIÓN EN LA BARRA LATERAL
enrutador_global = st.navigation([
    pagina_inicio,
    pagina_inventario, 
    pagina_productos, 
    pagina_maestro, 
    pagina_reglas
])

# Componentes fijos de control e identidad comercial en la barra de la izquierda
st.sidebar.markdown("### 🔒 Ecosistema Retail Activo")
st.sidebar.caption("Estaciones de trabajo descentralizadas e independientes.")
st.sidebar.markdown("---")

# 5. DESPACHO CENTRAL SEGURO Y CONTROL DEL HILO DE EJECUCIÓN
enrutador_global.run()
