# ==============================================================================
# PROGRAMA: app.py (MENÚ PRINCIPAL Y ENRUTADOR RAÍZ)
# VERSIÓN: 3.1.0
# DESCRIPCIÓN: Panel Central y Enrutador Plano del Sistema Maestro de Productos
# MODIFICACIÓN: Eliminación de inicio.py. Bienvenido integrado en la raíz.
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide"
)

# 2. DEFINICIÓN DE LLAMADAS A PROGRAMAS SATÉLITES EN EL MISMO NIVEL
# Todos los archivos residen sueltos en el directorio raíz del proyecto
llamada_cargar = st.Page("cargar.py", title="Cargar Inventario", icon="📤")
llamada_maestro = st.Page("maestro.py", title="Maestro de Datos", icon="📊")
llamada_reglas = st.Page("reglas.py", title="Mantenedor de Reglas", icon="⚙️")

# 3. CONSTRUCCIÓN DE LA NAVEGACIÓN EN LA BARRA LATERAL
# Añadimos las llamadas directas a los archivos sueltos
enrutador = st.navigation([
    llamada_cargar,
    llamada_maestro,
    llamada_reglas
])

# 4. COMPONENTE DE BIENVENIDA INTEGRADO (Evita crear un inicio.py)
# Si el usuario no ha hecho clic en ninguna opción, se muestra este bloque
if "current_page" not in st.session_state:
    st.title("🏭 Centro de Operaciones Retail - Menú Principal")
    st.markdown("---")
    st.markdown("""
    ### Bienvenido al Ecosistema de Taxonomía de Productos Genéricos
    
    Utiliza el menú desplegable de la **barra lateral izquierda** para ingresar directamente a los programas satélites operativos de la empresa:
    
    * **📤 Cargar Inventario (`cargar.py`)**: Procesador de archivos planos CSV con cruce paramétrico dinámico.
    * **📊 Maestro de Datos (`maestro.py`)**: Visualizador de tablas de Supabase en tiempo real y descarga a Excel.
    * **⚙️ Mantenedor de Reglas (`reglas.py`)**: Panel para inyectar y actualizar tokens de clasificación en caliente.
    """)
    st.info("💡 Consejo de ingeniería: Todos los programas satélites residen sueltos en la raíz de tu proyecto para evitar problemas de rutas de red.")

# 5. EJECUCIÓN DEL MOTOR DE NAVEGACIÓN PLANO
enrutador.run()
