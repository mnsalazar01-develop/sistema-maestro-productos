# ==============================================================================
# PROGRAMA: app.py
# VERSIÓN: 1.3.0
# DESCRIPCIÓN: Sistema Maestro de Clasificación de Productos Genéricos Retail
# MODIFICACIÓN: Se migró el cargador masivo de formato Excel (.xlsx) a formato de archivo plano (.csv).
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# Configuración de la ventana web de Streamlit
st.set_page_config(
    page_title="Sistema Maestro de Productos", 
    page_icon="📦",
    layout="wide"
)

# ========================================
# RF-01: CONEXIÓN A BASE DE DATOS CACHEADA
# ========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Inicializar la conexión global de Supabase
try:
    supabase = init_supabase()
    st.sidebar.success("⚡ Conectado a Supabase Cloud")
except Exception as e:
    st.sidebar.error(f"❌ Error de conexión: {e}")

# ========================================
# ARQUITECTURA DEL MENÚ (Mediante Pestañas)
# ========================================
st.title("📦 Sistema Maestro de Clasificación de Productos")
st.markdown("Bienvenido al centro operativo de taxonomía retail.")

# Creamos las 3 secciones del menú en la parte superior de la pantalla
tab_inicio, tab_carga, tab_maestro = st.tabs(["🏠 Inicio", "📤 Cargar Inventario", "📊 Maestro de Datos"])

# ----------------------------------------
# SECCIÓN 1: INICIO
# ----------------------------------------
with tab_inicio:
    st.subheader("Panel de Bienvenida")
    st.markdown("""
    Esta aplicación web te permite estructurar tu catálogo de productos en bruto bajo el estándar de la industria.
    
    ### Tus 3 Pilares de Datos Activos:
    1. **Categorías (Nivel 1)**: Los 7 pasillos principales sembrados en Supabase.
    2. **Subcategorías (Nivel 3/4)**: Tus familias de competencia directa ya cargadas.
    3. **Productos (Nivel 5)**: Tu nueva propuesta de genéricos puros.
    """)
    st.info("Haz clic en la pestaña 'Cargar Inventario' de arriba para empezar a procesar tu archivo Excel.")

# ----------------------------------------
# SECCIÓN 2: CARGAR INVENTARIO
# ----------------------------------------
with tab_carga:
    st.subheader("Procesador de Archivos en Bruto")
    st.markdown("Sube tu archivo plano o CSV con la columna `nombre` para clasificarlo automáticamente mediante reglas de retail.")
    
    # El diccionario de reglas que traduce palabras clave en IDs de subcategorías de Supabase
    DICCIONARIO_REGLAS = {
        "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "cafe": 8, "café": 8,
        "harin": 9, "fororo": 9, "maicena": 9,
        "aceit": 10, "oliva": 10,
        "mantec": 11, "margar": 11, "manteq": 11,
        "atun": 12, "atún": 12, "sardin": 12,
        "mayon": 14, "salsa": 14, "ketchup": 14,
        "sal ": 15, "pimient": 15,
        "avena": 16, "cereal": 16,
        "lech": 17, "queso": 17, "crema": 17,
        "yog": 18,
        "jabon": 30, "jabón": 30,
        "shamp": 31, "champ": 31,
        "desod": 32,
        "crema dent": 33, "pasta dent": 33,
        "papel hig": 34
    }

    def clasificar_texto(nombre_recibido):
        texto = str(nombre_recibido).lower().strip()
        for palabra_clave, id_subcat in DICCIONARIO_REGLAS.items():
            if palabra_clave in texto:
                return id_subcat
        return None

    # Componente visual reconfigurado estrictamente para aceptar archivos planos CSV
    archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"])
    
    if archivo_subido:
        st.success("¡Archivo plano cargado con éxito en la memoria web!")
        
        try:
            df = pd.read_csv(archivo_subido, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(archivo_subido, encoding='latin-1')
        
        if 'nombre' not in df.columns:
            st.error("❌ Error: Tu archivo plano debe contener una columna llamada exactamente 'nombre' (en minúsculas).")
        else:
            st.markdown("### 🧠 Pre-visualización de la Clasificación Automática")
            productos_clasificados = []
            no_clasificados = []
            
            for idx, fila in df.iterrows():
                nombre_prod = fila['nombre']
                id_subcat = clasificar_texto(nombre_prod)
                
                if id_subcat:
                    productos_clasificados.append({
                        "nombre_producto": nombre_prod,
                        "id_enlace_subcat": id_subcat
                    })
                else:
                    no_clasificados.append({"Producto No Clasificado": nombre_prod})
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Productos Listos para Supabase", len(productos_clasificados))
                if productos_clasificados:
                    st.dataframe(pd.DataFrame(productos_clasificados), use_container_width=True)
            with col2:
                st.metric("Productos sin clasificar (Omitidos)", len(no_clasificados))
                if no_clasificados:
                    st.dataframe(pd.DataFrame(no_clasificados), use_container_width=True)
            
            if productos_clasificados:
                if st.button("🚀 Confirmar y Enviar Datos a Supabase Cloud", key="btn_enviar_productos"):
                    with st.spinner("Inyectando registros en la base de datos..."):
                        try:
                            respuesta = supabase.table("productos").insert(productos_clasificados).execute()
                            st.balloons()
                            st.success(f"¡Éxito total! Se guardaron {len(productos_clasificados)} productos genéricos en Supabase.")
                        except Exception as e:
                            st.error(f"Error al guardar en Supabase: {e}")

# ----------------------------------------
# SECCIÓN 3: MAESTRO DE DATOS
# ----------------------------------------
with tab_maestro:
    st.subheader("Visualizador de Tablas en Supabase")
    st.markdown("Monitorea el estado actual de tu base de datos en tiempo real.")
    
    tabla_seleccionada = st.selectbox(
        "Selecciona la tabla que deseas visualizar:",
        ["categorias", "subcategorias", "productos"]
    )
    
    if st.button("🔄 Refrescar datos de Supabase", key="btn_refrescar_maestro"):
        with st.spinner(f"Consultando registros de la tabla {tabla_seleccionada}..."):
            try:
                respuesta = supabase.table(tabla_seleccionada).select("*").execute()
                
                if respuesta.data:
                    df_resultado = pd.DataFrame(respuesta.data)
                    
                    if tabla_seleccionada == "productos" and "fecha_registro" in df_resultado.columns:
                        df_resultado["fecha_registro"] = pd.to_datetime(df_resultado["fecha_registro"]).dt.strftime('%Y-%m-%d %H:%M')
                    
                    st.metric(f"Total de registros en {tabla_seleccionada}", len(df_resultado))
                    st.dataframe(df_resultado, use_container_width=True)
                    
                    st.session_state["df_actual"] = df_resultado
                    st.session_state["tabla_actual"] = tabla_seleccionada
                else:
                    st.warning(f"La tabla {tabla_seleccionada} se encuentra actualmente vacía.")
                    if "df_actual" in st.session_state: del st.session_state["df_actual"]
            except Exception as e:
                st.error(f"Error al consultar la tabla {tabla_seleccionada} in Supabase: {e}")

    # Sub-módulo de Exportación a Excel
    if "df_actual" in st.session_state and st.session_state["df_actual"] is not None:
        st.markdown("### 📥 Exportación Comercial")
        
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            st.session_state["df_actual"].to_excel(writer, index=False, sheet_name=st.session_state["tabla_actual"])
        
        data_excel = buffer_excel.getvalue()
        nombre_archivo = f"maestro_{st.session_state['tabla_actual']}.xlsx"
        
        st.download_button(
            label=f"🟢 Descargar tabla {st.session_state['tabla_actual']} en formato Excel",
            data=data_excel,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
