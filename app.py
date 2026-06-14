# ==============================================================================
# PROGRAMA: app.py (MENÚ PRINCIPAL Y ENRUTADOR RAÍZ)
# VERSIÓN: 3.2.0
# DESCRIPCIÓN: Panel Central Plano del Sistema Maestro de Productos
# MODIFICACIÓN: Llamadas y enrutador comentados para evitar errores de archivo no encontrado.
# ==============================================================================

import streamlit as st

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Sistema Maestro de Productos",
    page_icon="📦",
    layout="wide"
)

# ==============================================================================
# 2. DEFINICIÓN DE LLAMADAS A PROGRAMAS SATÉLITES EN EL MISMO NIVEL (COMENTADAS)
# Todos los archivos residen sueltos en el directorio raíz del proyecto
# ==============================================================================
llamada_cargar = st.Page("cargar_inventario.py", title="Cargar Inventario", icon="📤")
llamada_maestro = st.Page("maestro_datos.py", title="Maestro de Datos", icon="📊")
# llamada_reglas = st.Page("reglas.py", title="Mantenedor de Reglas", icon="⚙️")

# ==============================================================================
# 3. CONSTRUCCIÓN DE LA NAVEGACIÓN EN LA BARRA LATERAL (COMENTADA)
# ==============================================================================
enrutador = st.navigation([
     llamada_cargar,
     llamada_maestro,
#     llamada_reglas
])

# ==============================================================================
# 4. COMPONENTE DE BIENVENIDA INTEGRADO
# Se despliega en la pantalla principal al no estar activo el enrutador dinámico
# ==============================================================================
st.title("🏭 Centro de Operaciones Retail - Menú Principal")
st.markdown("---")
st.markdown("""
### Bienvenido al Ecosistema de Taxonomía de Productos Genéricos

Esta es la estación central de control del catálogo. Próximamente se activarán los accesos directos hacia los programas satélites operativos de la empresa:

* **📤 Cargar Inventario (`cargar.py`)**: Procesador de archivos planos CSV con cruce paramétrico dinámico.
* **📊 Maestro de Datos (`maestro.py`)**: Visualizador de tablas de Supabase en tiempo real y descarga a Excel.
* **⚙️ Mantenedor de Reglas (`reglas.py`)**: Panel para inyectar y actualizar tokens de clasificación en caliente.
""")

st.info("💡 Consejo de ingeniería: Todos los programas satélites residirán sueltos en la raíz de tu proyecto para evitar problemas de rutas de red.")

# ==============================================================================
# 5. EJECUCIÓN DEL MOTOR DE NAVEGACIÓN PLANO (COMENTADA)
# ==============================================================================
enrutador.run()
