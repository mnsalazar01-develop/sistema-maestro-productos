# ==============================================================================
# PROGRAMA: app.py (PARTE A DE C)
# VERSIÓN: 1.7.0
# DESCRIPCIÓN: Sistema Maestro de Clasificación de Productos Genéricos Retail
# MODIFICACIÓN: Desacoplamiento total del diccionario a tabla paramétrica SQL.
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
    st.markdown("Sube tu archivo plano o CSV con la columna `nombre` para clasificarlo automáticamente mediante la matriz paramétrica de Supabase.")

    # Función interna para clasificar un producto basado en las reglas dinámicas descargadas
    def clasificar_texto_parametrizado(nombre_recibido, mapa_reglas=None):
        texto = str(nombre_recibido).lower().strip()
        
        # Validación dinámica recorriendo la matriz paramétrica viva de la base de datos
        if mapa_reglas:
            for palabra_clave, id_subcat in mapa_reglas.items():
                if palabra_clave in texto:
                    return id_subcat
        return None

    # Componente visual para aceptar archivos planos CSV
    archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_v170")
    
    if archivo_subido:
        st.success("¡Archivo plano cargado con éxito en la memoria web!")
        
        # Extracción y mapeo en caliente de la nueva tabla de control viva
        matriz_reglas_vivas = {}
        try:
            # Consultamos la tabla paramétrica en la nube
            res_reglas = supabase.table("matriz_diccionario_reglas").select("*").execute()
            if res_reglas and hasattr(res_reglas, 'data') and res_reglas.data:
                df_reglas_mapeo = pd.DataFrame(res_reglas.data)
                
                # Mapeo posicional ciego: buscamos la columna de texto clave y la de enlace de subcategoría
                col_clave = [c for c in df_reglas_mapeo.columns if "clave" in c.lower() or c.lower() == "palabra_clave"][0]
                col_subcat = [c for c in df_reglas_mapeo.columns if "subcat" in c.lower() or "enlace" in c.lower()][0]
                
                for _, fila_r in df_reglas_mapeo.iterrows():
                    token_clave = str(fila_r[col_clave]).lower().strip()
                    id_destino = int(fila_r[col_subcat])
                    matriz_reglas_vivas[token_clave] = id_destino
        except Exception as e:
            # Si la API se desconecta por reversión de RLS o red, el sistema notifica y evita la caída
            st.sidebar.warning("⚠️ Alerta: Matriz paramétrica offline. El sistema requiere privilegios de lectura.")
            matriz_reglas_vivas = None
            
        try:
            df = pd.read_csv(archivo_subido, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(archivo_subido, encoding='latin-1')
        
        if 'nombre' not in df.columns:
            st.error("❌ Error: Tu archivo plano debe contener una columna llamada exactamente 'nombre' (en minúsculas).")
        else:
            st.markdown("### 🧠 Pre-visualización de la Clasificación Automática Parametrizada")
            productos_clasificados = []
            no_clasificados = []
            
            for idx, fila in df.iterrows():
                nombre_prod = fila['nombre']
                id_subcat = clasificar_texto_parametrizado(nombre_prod, matriz_reglas_vivas)
                
                if id_subcat:
                    productos_clasificados.append({
                        "nombre_producto": nombre_prod,
                        "id_enlace_subcat": id_subcat
                    })
                else:
                    no_clasificados.append({"nombre": nombre_prod})
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Productos Listos para Supabase", len(productos_clasificados))
                if productos_clasificados:
                    st.dataframe(pd.DataFrame(productos_clasificados), use_container_width=True)
            with col2:
                st.metric("Productos sin clasificar (Omitidos)", len(no_clasificados))
                if no_clasificados:
                    df_omitidos = pd.DataFrame(no_clasificados)
                    st.dataframe(df_omitidos, use_container_width=True)
                    
                    csv_omitidos = df_omitidos.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⚠️ Descargar Omitidos para revisión",
                        data=csv_omitidos,
                        file_name="productos_omitidos.csv",
                        mime="text/csv",
                        key="btn_descargar_omitidos_v170"
                    )
            
            if productos_clasificados:
                if st.button("🚀 Confirmar y Enviar Datos a Supabase Cloud", key="btn_enviar_productos_v170"):
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
    
    # Añadimos la nueva tabla paramétrica al selector visual para poder auditarla desde Streamlit
    tabla_seleccionada = st.selectbox(
        "Selecciona la tabla que deseas visualizar:",
        ["categorias", "subcategorias", "productos", "matriz_diccionario_reglas"],
        key="selector_tablas_v170"
    )
    
    if st.button("🔄 Refrescar datos de Supabase", key="btn_refrescar_maestro_v170"):
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
                st.error(f"Error al consultar la tabla {tabla_seleccionada} en Supabase: {e}")

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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_descargar_excel_v170"
        )
