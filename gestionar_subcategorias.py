# ==============================================================================
# PROGRAMA SATÉLITE: gestionar_subcategorias.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.0.0 (CONSOLA DE GOBIERNO RELACIONAL PARA PASILLOS)
# DESCRIPCIÓN: Mantenedor CRUD para el Árbol de Subcategorías de la Compañía
# MODIFICACIÓN: Enlace explícito a 'public.subcategorias' con validación FK.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA DE STREAMLIT
st.set_page_config(
    page_title="Gestión de Subcategorías",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CONEXIÓN SEGURA HEREDADA CON LAS LLAVES DE SUPABASE
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

st.title("🥦 Gestión del Árbol de Subcategorías")
st.markdown("Consola unificada para auditar, sembrar y actualizar los pasillos del automercado en la nube.")
st.markdown("---")

# 3. LECTURA SÍNCRONA DE LOS DATOS MAESTROS (TABLA MADRE CATEGORIAS)
@st.cache_data(ttl=10)
def descargar_categorias_madre():
    try:
        res = supabase.table("public.categorias").select("*").execute()
        if res and hasattr(res, 'data') and res.data:
            # Buscamos las columnas de la tabla madre dinámicamente
            df_cat = pd.DataFrame(res.data)
            col_id = [c for c in df_cat.columns if "id" in c.lower()][0]
            col_nom = [c for c in df_cat.columns if "nombre" in c.lower() or "desc" in c.lower()][0]
            return {str(fila[col_nom]): int(fila[col_id]) for _, fila in df_cat.iterrows()}
    except Exception as e:
        st.sidebar.error(f"⚠️ Alerta Categorías: {e}")
    return {"Categoría General Base (Default)": 1}

MAPA_CATEGORIAS_MADRE = descargar_categorias_madre()

# 4. AUDITORÍA VISUAL CENTRAL (SELECT EN VIVO DESDE INTERNET)
st.markdown("### 📊 Pasillos Registrados actualmente en la Nube")
try:
    res_sub = supabase.table("public.subcategorias").select("id_subcat, id_enlace_cat, nombre_subcat").execute()
    if res_sub and hasattr(res_sub, 'data') and res_sub.data:
        df_sub = pd.DataFrame(res_sub.data)
        
        # Ordenamiento de auditoría retail por ID secuencial ascendente
        df_sub = df_sub.sort_values(by="id_subcat", ascending=True).reset_index(drop=True)
        
        # Conteo humano correlativo partiendo desde 1 en la pantalla
        df_sub.index = df_sub.index + 1
        df_sub.index.name = "N° de Ítem"
        
        st.dataframe(
            df_sub.rename(columns={
                "id_subcat": "ID Pasillo",
                "id_enlace_cat": "ID Categoría Madre",
                "nombre_subcat": "Descripción de Subcategoría"
            }),
            use_container_width=True
        )
        lista_pasillos_existentes = res_sub.data
    else:
        st.info("💡 La tabla 'subcategorias' está vacía en internet. Utiliza el formulario inferior para sembrar registros.")
        lista_pasillos_existentes = []
except Exception as e_select:
    st.error(f"❌ Error al leer subcategorías: {e_select}")
    lista_pasillos_existentes = []

st.markdown("---")

# 5. FORMULARIOS OPERATIVOS (CREATE / UPDATE / DELETE)
col_crear, col_editar = st.columns(2)

with col_crear:
    st.markdown("### ➕ Sembrar Nuevo Pasillo")
    with st.form("form_crear_subcat", clear_on_submit=True):
        nuevo_id = st.number_input("Asignar ID Numérico fijo (id_subcat):", min_value=1, step=1, value=len(lista_pasillos_existentes)+1)
        nuevo_nombre = st.text_input("Nombre comercial del Pasillo (con Emojis):", placeholder="Ej: 🪵 Carbón y Leña")
        cat_madre_sel = st.selectbox("Vincular a Categoría Madre (Restricción FK):", list(MAPA_CATEGORIAS_MADRE.keys()))
        
        btn_crear = st.form_submit_button("💾 Guardar Pasillo en Nube")
        
        if btn_crear:
            if not nuevo_nombre:
                st.error("❌ Error: Debes escribir la descripción de la subcategoría.")
            else:
                payload = {
                    "id_subcat": int(nuevo_id),
                    "id_enlace_cat": MAPA_CATEGORIAS_MADRE[cat_madre_sel],
                    "nombre_subcat": nuevo_nombre.strip()
                }
                try:
                    supabase.table("public.subcategorias").insert(payload).execute()
                    st.success(f"✅ ¡Éxito! Pasillo '{nuevo_nombre}' creado con ID {nuevo_id}.")
                    st.rerun()
                except Exception as e_ins:
                    st.error(f"❌ Error de persistencia: {e_ins}")

with col_editar:
    st.markdown("### 📝 Modificar Pasillo Existente")
    if lista_pasillos_existentes:
        opciones_combo = {f"ID {p['id_subcat']} - {p['nombre_subcat']}": p for p in lista_pasillos_existentes}
        pasillo_sel = st.selectbox("Selecciona el Pasillo a editar o remover:", list(opciones_combo.keys()))
        datos_pasillo_actual = opciones_combo[pasillo_sel]
        
        with st.form("form_editar_subcat"):
            edit_nombre = st.text_input("Corregir descripción / Emojis:", value=datos_pasillo_actual["nombre_subcat"])
            edit_cat = st.selectbox("Re-vincular Categoría Madre:", list(MAPA_CATEGORIAS_MADRE.keys()))
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                btn_update = st.form_submit_button("🔄 Actualizar Nombre")
            with col_b2:
                btn_delete = st.form_submit_button("🗑️ Eliminar Registro")
                
            if btn_update:
                try:
                    supabase.table("public.subcategorias").update({
                        "nombre_subcat": edit_nombre.strip(),
                        "id_enlace_cat": MAPA_CATEGORIAS_MADRE[edit_cat]
                    }).eq("id_subcat", datos_pasillo_actual["id_subcat"]).execute()
                    st.success("✅ Registro modificado correctamente.")
                    st.rerun()
                except Exception as e_up:
                    st.error(f"❌ Fallo al actualizar: {e_up}")
                    
            if btn_delete:
                try:
                    supabase.table("public.subcategorias").delete().eq("id_subcat", datos_pasillo_actual["id_subcat"]).execute()
                    st.warning("⚠️ Registro eliminado de la base de datos cloud.")
                    st.rerun()
                except Exception as e_del:
                    st.error(f"❌ No se puede borrar (Posee productos vinculados): {e_del}")
    else:
        st.info("Aún no existen pasillos en internet para habilitar modificaciones.")
