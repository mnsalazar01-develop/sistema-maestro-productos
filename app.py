# ==============================================================================
# PROGRAMA CENTRAL: app.py (CENTRO DE CONTROL PURIFICADO)
# VERSIÓN: 4.6.0 (INTEGRACIÓN DEL DISPARADOR LOCAL SUBPROCESS PARA PYQT6)
# DESCRIPCIÓN: Panel Central Retail con Navegación por Botones y Control de Auto-Importación
# MODIFICACIÓN: Inclusión de la estación Drag & Drop mediante ejecución local aislada.
# ==============================================================================

import streamlit as st
import subprocess
import sys

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. FUNCIÓN AUXILIAR DE PORTADA: DISPARADOR SEGURO DE LA INTERFAZ DE ESCRITORIO
def lanzar_clasificador_qt_local():
    st.markdown("### 🖥️ Clasificador Visual Drag & Drop (PC Local)")
    st.markdown("Esta estación utiliza una interfaz nativa acelerada por hardware de escritorio para mover artículos con el mouse.")
    st.warning("⚠️ NOTA DE ENTORNO: Al ser una aplicación de ventanas nativa, este módulo se abrirá como una aplicación independiente en la barra de tareas de tu computadora local.")
    
    # Campo de seguridad visual para el operario de sistemas
    if st.button("🔌 Encender Ventana de Escritorio PyQt6", use_container_width=True, key="btn_lanzar_qt_v460"):
        with st.spinner("Inicializando motor de ventanas local y cargando Secrets..."):
            try:
                # Ejecutamos el script de escritorio de forma aislada en el sistema operativo local
                subprocess.Popen([sys.executable, "clasificar_catalogo_qt.py"])
                st.success("🚀 ¡Éxito! Revisa la barra de tareas de tu computadora, la ventana de clasificación interactiva ya está encendida.")
            except Exception as e_proc:
                st.error(f"❌ Fallo al inicializar el subproceso local: {e_proc}")

# 3. DEFINICIÓN DE LA PÁGINA DE PORTADA PRINCIPAL (CENTRO DE CONTROL)
def mostrar_centro_control():
    st.title("🏭 Centro de Control")
    st.markdown("Bienvenido al ecosistema modular de clasificación, control y analítica de productos.")
    st.markdown("---")

    # Costura v4.6.0: Grilla horizontal de 6 columnas de alta densidad para todas las estaciones
    col_inv, col_prod, col_maestro, col_subcat, col_saneamiento, col_bi = st.columns(6)

    with col_inv:
        st.markdown("#### Carga de Inventario")
        st.caption("Carga de archivos planos CSV mediante el diccionario de confianza.")
        if st.button("📤 Batch - Imput Inventario", use_container_width=True, key="btn_p1_inv_v460"):
            st.switch_page(pagina_inventario)

    with col_prod:
        st.markdown("#### Registrar Producto")
        st.caption("Alta manual reactiva de artículos nuevos y control multimedia.")
        if st.button("Registrar Productos", use_container_width=True, key="btn_p1_prod_v460"):
            st.switch_page(pagina_productos)

    with col_maestro:
        st.markdown("#### Maestro de Datos")
        st.caption("Visualizador de registros en tiempo real y extractor binario a formato Excel.")
        if st.button("Maestro de Datos", use_container_width=True, key="btn_p1_mae_v460"):
            st.switch_page(pagina_maestro)

    with col_subcat:
        st.markdown("#### Subcategorias")
        st.caption("Consola unificada para auditar, sembrar y actualizar las familias del automercado.")
        if st.button("Gestionar Subcategorias", use_container_width=True, key="btn_p1_sub_v460"):
            st.switch_page(pagina_subcategorias)

    with col_saneamiento:
        st.markdown("#### Saneamiento Batch")
        st.caption("Purga atómica en caliente del servidor para restablecer el árbol relacional del 1 al 46.")
        if st.button("⚡ Inicializador Batch", use_container_width=True, key="btn_p1_saneamiento_v460"):
            st.switch_page(pagina_saneamiento)

    with col_bi:
        st.markdown("#### Analítica BI")
        st.caption("Dashboard gerencial de surtido, densidad de marcas y subcategorías poco distribuidas.")
        if st.button("📊 Dashboard Analítico", use_container_width=True, key="btn_p1_bi_v460"):
            st.switch_page(pagina_dashboard)

    st.markdown("---")
    st.info("💡 Consejo técnico: Utiliza la barra lateral de la izquierda para ingresar directo a los programas o para cambiar de estación de trabajo con un clic.")

# 4. DECLARACIÓN FORMAL DE INSTANCIAS DE PÁGINAS SATÉLITES EN LA RAÍZ
pagina_inicio = st.Page(mostrar_centro_control, title="🏭 Centro de Control", icon="🏠", default=True)
pagina_inventario = st.Page("cargar_inventario.py", title="Cargar Inventario Masivo", icon="📤")
pagina_productos = st.Page("cargar_productos.py", title="Registrar Producto Manual", icon="📝")
pagina_maestro = st.Page("maestro_datos.py", title="Maestro de Datos", icon="📊")
pagina_subcategorias = st.Page("gestionar_subcategorias.py", title="Subcategorias", icon="⚙️")
pagina_saneamiento = st.Page("batch_inicializar_tablas.py", title="Saneamiento Batch", icon="⚡")
pagina_dashboard = st.Page("dashboard_catalogo.py", title="Dashboard Analítico", icon="📊")
# Costura v4.6.0: Sembramos el disparador de subproceso de la interfaz local como una página de visualización segura
pagina_qt_local = st.Page(lanzar_clasificador_qt_local, title="Clasificador Drag & Drop", icon="🖱️")

# 5. CONSTRUCCIÓN AUTOMÁTICA DEL MOTOR DE NAVEGACIÓN EN LA BARRA LATERAL
enrutador_global = st.navigation([
    pagina_inicio,
    pagina_inventario, 
    pagina_productos, 
    pagina_maestro, 
    pagina_subcategorias,
    pagina_saneamiento,
    pagina_dashboard,
    pagina_qt_local
])

# Componentes fijos de control e identidad comercial en la barra de la izquierda
st.sidebar.markdown("### 🔒 Ecosistema Retail Activo")
st.sidebar.caption("Estaciones de trabajo descentralizadas e independientes.")
st.sidebar.markdown("---")

# 6. DESPACHO CENTRAL SEGURO Y CONTROL DEL HILO DE EJECUCIÓN
enrutador_global.run()
