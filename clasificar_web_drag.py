# ==============================================================================
# PROGRAMA SATÉLITE: clasificar_web_drag.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 3.0.0 (CONSOLA DE REFINE DE SURTIDO - INMUNE A CORTE DE PERSISTENCIA)
# DESCRIPCIÓN: Panel de Clasificación Nativa 100% Python sin Intermediarios JS
# MODIFICACIÓN: Uso de st.dataframe con selección de filas para forzar guardado duro.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA DE CLASIFICACIÓN DE STREAMLIT
st.set_page_config(
    page_title="Refinar Catálogo",
    page_icon="🖱️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. HERENCIA DE CONEXIÓN SEGURA INDEPENDIENTE CON LAS LLAVES DE LA COMPAÑÍA
@st.cache_resource
def init_supabase_local() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_supabase_local()
except Exception as e:
    st.error(f"❌ Error de Conexión Base: {e}")
    st.stop()

st.title("🖱️ Consola de Refine y Clasificación de Catálogo")
st.markdown("Selecciona los productos de la grilla para reubicar o corregir su subcategoría comercial de forma permanente en la nube.")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA DE LOS 372 ARTÍCULOS COMPLETOS Y EL MASTER DE SUBCATEGORIAS
@st.cache_data(ttl=2)
def descargar_datos_consola_refine():
    try:
        # Descargamos el catálogo completo con su subcategoría grabada en internet
        res_cat = supabase.table("catalogo").select("id_catalogo, nombre_catalogo, id_enlace_subcat").order("id_catalogo").execute()
        # Descargamos las subcategorías oficiales (1 al 46) para mapear descripciones
        res_sub = supabase.table("subcategorias").select("id_subcat, nombre_subcat").order("id_subcat").execute()
        
        if res_cat and hasattr(res_cat, 'data') and res_sub and hasattr(res_sub, 'data'):
            return pd.DataFrame(res_cat.data), pd.DataFrame(res_sub.data)
    except Exception as e_load:
        st.sidebar.error(f"⚠️ Error al leer datos desde internet: {e_load}")
    return pd.DataFrame(), pd.DataFrame()

df_productos, df_subcats = descargar_datos_consola_refine()

# 4. PARACHOQUES DE SEGURIDAD RELACIONAL
if df_productos.empty or df_subcats.empty:
    st.info("💡 Esperando consistencia de datos... Asegúrate de tener registros en tus tablas cloud.")
    st.stop()

# 5. CONSTRUCCIÓN DEL MAPA DE INTERCAMBIO EN LA MEMORIA RAM
mapa_subcats_id_a_nombre = {int(fila["id_subcat"]): str(fila["nombre_subcat"]) for _, fila in df_subcats.iterrows()}
mapa_subcats_nombre_a_id = {str(fila["nombre_subcat"]): int(fila["id_subcat"]) for _, fila in df_subcats.iterrows()}

# Inyectamos de forma temporal la string del pasillo dentro del dataframe para la lectura del operador
df_productos["Subcategoría Actual en Nube"] = df_productos["id_enlace_subcat"].map(mapa_subcats_id_a_nombre).fillna("⚠️ Renglón Huérfano / Depósito general")

# 6. DISTRIBUCIÓN DE LA PANTALLA EN DOS PANELES DE ALTA DENSIDAD VISUAL
col_tabla, col_formulario = st.columns([2, 1])

with col_tabla:
    st.markdown("### 📋 Surtido Registrado de la Compañía (372 SKUs)")
    st.caption("Haz clic en la casilla de la izquierda para seleccionar el producto que deseas mover [5.1].")
    
    # Formateamos el dataframe para exhibición limpia
    df_visualizacion = df_productos[["id_catalogo", "nombre_catalogo", "Subcategoría Actual en Nube"]].rename(columns={
        "id_catalogo": "ID SKU",
        "nombre_catalogo": "Descripción del Artículo"
    })
    
    # Activamos la grilla interactiva nativa con selección de fila única estructurada
    seleccion_tabla = st.dataframe(
        df_visualizacion,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single"
    )

with col_formulario:
    st.markdown("### 📥 Módulo de Reubicación Cloud")
    
    # Verificamos si el operario hizo clic sobre un producto de la grilla
    indices_seleccionados = seleccion_tabla.get("selection", {}).get("rows", [])
    
    if indices_seleccionados:
        # Extraemos la fila exacta de la memoria RAM usando el índice de pantalla
        idx_fila = indices_seleccionados[0]
        id_sku_seleccionado = int(df_visualizacion.iloc[idx_fila]["ID SKU"])
        nombre_prod_seleccionado = str(df_visualizacion.iloc[idx_fila]["Descripción del Artículo"])
        subcat_actual_prod = str(df_visualizacion.iloc[idx_fila]["Subcategoría Actual en Nube"])
        
        st.info(f"📦 **Artículo a procesar:**\n{nombre_prod_seleccionado}\n\n📍 **Ubicación actual:** {subcat_actual_prod}")
        
        # Selector dinámico nativo alimentado de las 46 subcategorías puras de internet
        lista_opciones_combobox = list(mapa_subcats_nombre_a_id.keys())
        subcat_destino_seleccionada = st.selectbox(
            "Selecciona la nueva variedad comercial de destino:",
            options=lista_opciones_combobox
        )
        
        id_subcat_destino_numeric = mapa_subcats_nombre_a_id[subcat_destino_seleccionada]
        
        if st.button("🚀 Confirmar y Guardar Cambios en Nube", use_container_width=True, key="btn_guardar_refine_v300"):
            with st.spinner("Modificando registro directamente en el disco duro de Supabase..."):
                try:
                    # PERSISTENCIA PURA DE BACKEND: Inmune a bloqueos del navegador o iframes de red
                    supabase.table("catalogo").update({
                        "id_enlace_subcat": int(id_subcat_destino_numeric)
                    }).eq("id_catalogo", int(id_sku_seleccionado)).execute()
                    
                    st.toast(f"✅ ¡Guardado Permanente! {nombre_prod_seleccionado} movido a {subcat_destino_seleccionada}.", icon="💾")
                    
                    # Limpiamos la caché interna de Streamlit para forzar una nueva lectura real en el siguiente milisegundo
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e_update_puro:
                    st.error(f"❌ Error definitivo de persistencia relacional: {e_update_puro}")
    else:
        st.info("💡 Por favor, toca o selecciona un producto de la tabla de la izquierda para habilitar el panel de guardado permanente.")
