# ==============================================================================
# PROGRAMA SATÉLITE: clasificar_web_drag.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 6.0.0 (CONSOLA DE ASIGNACIÓN INTERACTIVA DE CATÁLOGO)
# DESCRIPCIÓN: Panel de Control de Surtido 100% Python con Persistencia Garantizada
# MODIFICACIÓN: Uso de botones relacionales en espejo para forzar escritura en Supabase.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA WEB DE STREAMLIT
st.set_page_config(
    page_title="Clasificador de Catálogo",
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

st.title("🖱️ Consola de Distribución y Asignación de Catálogo")
st.markdown("Herramienta interactiva para reclasificar productos en caliente. Haz clic sobre un artículo del depósito y asígnale su nueva subcategoría con un toque.")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA DE LOS 372 ARTÍCULOS COMPLETOS Y EL MASTER DE SUBCATEGORIAS
@st.cache_data(ttl=1)
def descargar_datos_consola_refine():
    try:
        # Descargamos el catálogo completo de productos
        res_cat = supabase.table("catalogo").select("id_catalogo, nombre_catalogo, id_enlace_subcat").order("nombre_catalogo").execute()
        # Descargamos las 46 subcategorías oficiales de internet
        res_sub = supabase.table("subcategorias").select("id_subcat, nombre_subcat").order("id_subcat").execute()
        
        if res_cat and hasattr(res_cat, 'data') and res_sub and hasattr(res_sub, 'data'):
            return pd.DataFrame(res_cat.data), pd.DataFrame(res_sub.data)
    except Exception as e_load:
        st.sidebar.error(f"⚠️ Error al leer datos desde internet: {e_load}")
    return pd.DataFrame(), pd.DataFrame()

df_productos, df_subcats = descargar_datos_consola_refine()

if df_productos.empty or df_subcats.empty:
    st.info("💡 Esperando consistencia de datos... Asegúrate de tener registros en tus tablas cloud.")
    st.stop()

# 4. CONSTRUCCIÓN DE MAPAS DE INTERCAMBIO EN RAM
mapa_subcats_id_a_nombre = {int(fila["id_subcat"]): str(fila["nombre_subcat"]) for _, fila in df_subcats.iterrows()}

# Separamos los productos: el Depósito General filtra estrictamente los que están en el bolsón base de Víveres (ID 12)
df_deposito = df_productos[df_productos["id_enlace_subcat"] == 12]
df_refinados = df_productos[df_productos["id_enlace_subcat"] != 12]

# 5. DISTRIBUCIÓN DE LA PANTALLA EN DOS PANELES DE ALTA DENSIDAD INTERACTIVA
col_deposito, col_estantes = st.columns([1, 2])

with col_deposito:
    st.markdown(f"### 📋 Depósito General ({len(df_deposito)} SKUs)")
    st.caption("Selecciona el artículo que deseas mover de pasillo [5.1]:")
    
    # Menú de botones de radio de alta densidad. El operador toca el producto con un clic
    opciones_deposito = {f"📦 SKU {fila['id_catalogo']} - {fila['nombre_catalogo']}": fila['id_catalogo'] for _, fila in df_deposito.iterrows()}
    
    if opciones_deposito:
        producto_seleccionado_label = st.radio(
            "Productos en depósito:",
            options=list(opciones_deposito.keys()),
            label_visibility="collapsed"
        )
        id_sku_a_mover = opciones_deposito[producto_seleccionado_label]
    else:
        st.success("🎉 ¡Felicidades! Catálogo 100% refinado. Cero productos huérfanos.")
        id_sku_a_mover = None

with col_estantes:
    st.markdown("### 📥 Estantes Relacionales de la Tienda (46 Subcategorías)")
    st.caption("Presiona el botón del departamento destino para clavar el producto en la nube de forma permanente [5.1].")
    
    if id_sku_a_mover:
        # Dibujamos una cuadrícula de botones limpia de 3 columnas responsivas nativas de Python
        cols_grilla_botones = st.columns(3)
        
        for indice_sub, fila_sub in df_subcats.iterrows():
            id_subcat_destino = int(fila_sub["id_subcat"])
            nombre_subcat_destino = str(fila_sub["nombre_subcat"])
            
            # Contamos cuántos SKUs ya viven adentro de este estante en internet
            conteo_actual_estante = len(df_refinados[df_refinados["id_enlace_subcat"] == id_subcat_destino])
            label_boton = f"{nombre_subcat_destino} ({conteo_actual_estante})"
            
            # Omitimos el botón de Víveres (ID 12) porque de ahí es de donde vienen los productos
            if id_subcat_destino != 12:
                with cols_grilla_botones[indice_sub % 3]:
                    # Al presionar el botón del pasillo, el pulso viaja por el hilo puro de Python directo a la base de datos
                    if st.button(label_boton, use_container_width=True, key=f"btn_subcat_{id_subcat_destino}"):
                        try:
                            # PERSISTENCIA INDUSTRIAL DURA: Inmune a bloqueos de iframes o navegadores
                            supabase.table("catalogo").update({
                                "id_enlace_subcat": int(id_subcat_destino)
                            }).eq("id_catalogo", int(id_sku_a_mover)).execute()
                            
                            st.toast("💾 ¡Guardado Permanente en Supabase!", icon="✅")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e_save_puro:
                            st.error(f"❌ Error de red: {e_save_puro}")
