# ==============================================================================
# PROGRAMA SATÉLITE: maestro_datos.py (PARTE A DE B)
# VERSIÓN: 1.0.0 (MÓDULO SUELTO RAÍZ)
# DESCRIPCIÓN: Visualizador y Extractor de Tablas del Ecosistema Retail
# MODIFICACIÓN: Creación como módulo independiente plano en la raíz del proyecto.
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# Configuración independiente de la ventana web
st.set_page_config(
    page_title="Módulo Maestro de Datos - Retail",
    page_icon="📊",
    layout="wide"
)

# Inicialización local de la conexión a la base de datos de Supabase
@st.cache_resource
def init_supabase_local() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_supabase_local()
    st.sidebar.success("⚡ Conexión Dedicada Activa")
except Exception as e:
    st.sidebar.error(f"❌ Error de Conexión: {e}")

st.title("📊 Maestro de Datos y Auditoría en Tiempo Real")
st.markdown("Monitorea el estado de la taxonomía e inventarios guardados en tu base de datos cloud.")

# Selector exclusivo en pantalla de las entidades físicas del negocio
tabla_seleccionada = st.selectbox(
    "Selecciona la tabla que deseas auditar y visualizar:",
    ["categorias", "subcategorias", "productos", "matriz_diccionario_reglas"],
    key="satelite_selector_maestro"
)

if st.button("🔄 Refrescar y Consultar Datos de Supabase", key="btn_refrescar_satelite"):
    with st.spinner(f"Estableciendo conexión y descargando registros de la tabla '{tabla_seleccionada}'..."):
        try:
            # Ejecutamos la sentencia SELECT masiva en el servidor cloud
            respuesta = supabase.table(tabla_seleccionada).select("*").execute()
            
            if respuesta and hasattr(respuesta, 'data') and respuesta.data:
                df_resultado = pd.DataFrame(respuesta.data)
                
                # Formateo de marcas de tiempo para visualización de operaciones comerciales
                columnas_fecha = [c for c in df_resultado.columns if "fecha" in c.lower() or "registro" in c.lower()]
                for col_f in columnas_fecha:
                    try:
                        df_resultado[col_f] = pd.to_datetime(df_resultado[col_f]).dt.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        pass
                
                # Despliegue de métrica de densidad de registros
                st.metric(f"Total de registros activos en '{tabla_seleccionada}'", len(df_resultado))
                st.dataframe(df_resultado, use_container_width=True)
                
                # Almacenamos el set de datos en la sesión para el sub-módulo de exportación
                st.session_state["df_satelite_actual"] = df_resultado
                st.session_state["tabla_satelite_actual"] = tabla_seleccionada
            else:
                st.warning(f"Atención: La tabla '{tabla_seleccionada}' se encuentra actualmente en cero registros.")
                if "df_satelite_actual" in st.session_state: 
                    st.session_state["df_satelite_actual"] = None
        except Exception as e:
            st.error(f"Error al intentar consultar la tabla '{tabla_seleccionada}' en Supabase: {e}")
# ==============================================================================
# SUB-MÓDULO: EXPORTADOR BINARIO COMERCIAL A EXCEL
# ==============================================================================
if "df_satelite_actual" in st.session_state and st.session_state["df_satelite_actual"] is not None:
    st.markdown("---")
    st.markdown("### 📥 Exportación y Descarga de Reportes")
    
    # Extraemos las variables guardadas en la sesión activa de la pantalla
    df_para_excel = st.session_state["df_satelite_actual"]
    nombre_tabla_activa = st.session_state["tabla_satelite_actual"]
    
    # Inicializamos el búfer de memoria de Python para la transferencia de bytes
    buffer_excel = io.BytesIO()
    
    # Empaquetamos el DataFrame usando openpyxl asignándole el nombre real de la tabla a la pestaña
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        df_para_excel.to_excel(writer, index=False, sheet_name=nombre_tabla_activa)
    
    # Extraemos el torrente binario generado por el compilador
    data_excel_binaria = buffer_excel.getvalue()
    nombre_archivo_salida = f"reporte_maestro_{nombre_tabla_activa}.xlsx"
    
    # Componente nativo de Streamlit para la descarga local de archivos comerciales
    st.download_button(
        label=f"🟢 Descargar tabla '{nombre_tabla_activa}' en formato Excel comercial",
        data=data_excel_binaria,
        file_name=nombre_archivo_salida,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_descargar_excel_satelite"
    )
