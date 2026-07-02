# ==============================================================================
# PROGRAMA SATÉLITE: clasificar_web_drag.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 8.1.0 (BLINDAJE DE EDICIÓN EXCEL DIRECTA - PERSISTENCIA DURA CLOUD)
# DESCRIPCIÓN: Panel de Refinamiento Retail en Formato de Grilla Excel Nativa
# MODIFICACIÓN: Captura por asignación directa de variable para forzar el UPDATE.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA DE STREAMLIT
st.set_page_config(
    page_title="Editor de Catálogo Masivo",
    page_icon="📝",
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

st.title("📝 Editor Rápido de Catálogo Masivo")
st.markdown("Modifica la subcategoría de los productos haciendo clic directo sobre la celda como en Excel. ¡Guardado relacional permanente en Supabase Cloud!")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA DE LOS 372 ARTÍCULOS COMPLETOS Y EL MASTER DE SUBCATEGORIAS
@st.cache_data(ttl=1)
def descargar_datos_grilla_masiva():
    try:
        res_cat = supabase.table("catalogo").select("id_catalogo, nombre_catalogo, id_enlace_subcat").order("nombre_catalogo").execute()
        res_sub = supabase.table("subcategorias").select("id_subcat, nombre_subcat").order("id_subcat").execute()
        if res_cat and hasattr(res_cat, 'data') and res_sub and hasattr(res_sub, 'data'):
            return pd.DataFrame(res_cat.data), pd.DataFrame(res_sub.data)
    except Exception as e_load:
        st.sidebar.error(f"⚠️ Error al leer datos desde internet: {e_load}")
    return pd.DataFrame(), pd.DataFrame()

df_productos, df_subcats = descargar_datos_grilla_masiva()

if df_productos.empty or df_subcats.empty:
    st.info("💡 Esperando consistencia de datos... Asegúrate de tener registros en tus tablas cloud.")
    st.stop()

# 4. CONSTRUCCIÓN DE MAPAS DE INTERCAMBIO EN LA MEMORIA RAM
mapa_id_a_nombre = {int(f["id_subcat"]): str(f["nombre_subcat"]) for _, f in df_subcats.iterrows()}
mapa_nombre_a_id = {str(f["nombre_subcat"]): int(f["id_subcat"]) for _, f in df_subcats.iterrows()}

df_productos["Subcategoría Comercial"] = df_productos["id_enlace_subcat"].map(mapa_id_a_nombre).fillna("⚠️ Depósito General (ID 12)")

df_editable = df_productos[["id_catalogo", "nombre_catalogo", "Subcategoría Comercial"]].rename(columns={
    "id_catalogo": "ID SKU",
    "nombre_catalogo": "Descripción del Artículo"
})

st.caption("💡 Instrucción: Haz doble clic sobre la celda del pasillo, elige el destino y presiona Enter. ¡El guardado es inmediato!")

# 5. RENDERIZADO Y CAPTURA DIRECTA DE LA HOJA INTERACTIVA EXCEL NATIVA
# Al asignar el componente directo a la variable 'grilla_excel_viva', capturamos las celdas mutadas sin intermediarios
grilla_excel_viva = st.data_editor(
    df_editable,
    use_container_width=True,
    hide_index=True,
    disabled=["ID SKU", "Descripción del Artículo"],
    key="editor_maestro_catalogo_v810",
    column_config={
        "Subcategoría Comercial": st.column_config.SelectboxColumn(
            "Variedad / Departamento Destino",
            options=list(mapa_nombre_a_id.keys()),
            required=True
        )
    }
)

# 6. BI-PASS DE PERSISTENCIA DURA: Procesamos las mutaciones leyendo la variable viva del componente
if st.session_state.get("editor_maestro_catalogo_v810") and "edited_rows" in st.session_state["editor_maestro_catalogo_v810"]:
    cambios_celdas = st.session_state["editor_maestro_catalogo_v810"]["edited_rows"]
    
    if cambios_celdas:
        for indice_fila_pantalla, celda_mutada in cambios_celdas.items():
            if "Subcategoría Comercial" in celda_mutada:
                nuevo_nombre_subcat = celda_mutada["Subcategoría Comercial"]
                id_subcat_nueva_numeric = mapa_nombre_a_id[nuevo_nombre_subcat]
                
                # Extraemos el ID real del producto modificado usando la fila de la memoria RAM
                id_sku_modificado = int(df_editable.iloc[int(indice_fila_pantalla)]["ID SKU"])
                nombre_sku_modificado = str(df_editable.iloc[int(indice_fila_pantalla)]["Descripción del Artículo"])
                
                try:
                    # PERSISTENCIA ABSOLUTA DURA: Grabado real directo en el disco de Supabase Cloud
                    supabase.table("catalogo").update({
                        "id_enlace_subcat": int(id_subcat_nueva_numeric)
                    }).eq("id_catalogo", int(id_sku_modificado)).execute()
                    
                    st.toast(f"💾 ¡Guardado Permanente! {nombre_sku_modificado} asignado a {nuevo_nombre_subcat}.", icon="✅")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e_excel_save:
                    st.error(f"❌ Error de escritura relacional: {e_excel_save}")
