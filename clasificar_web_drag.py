# ==============================================================================
# PROGRAMA SATÉLITE: clasificar_web_drag.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 5.0.0 (CONSOLA INTERACTIVA DE REFINAMIENTO DE DEPARTAMENTOS)
# DESCRIPCIÓN: Panel de Clasificación Síncrona Inmune a Bloqueos de Navegador
# MODIFICACIÓN: Uso de contenedores dinámicos integrados para asegurar persistencia permanente.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA DE REFINAMIENTO DE STREAMLIT
st.set_page_config(
    page_title="Clasificador de Catálogo Web",
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

st.title("🖱️ Consola de Refinamiento de Subcategorías")
st.markdown("Transfiere los artículos entre los estantes de forma interactiva en la nube. ¡Garantía de persistencia dura en internet sin requisitos en tu PC!")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA DE LOS 372 ARTÍCULOS COMPLETOS Y EL MASTER DE SUBCATEGORIAS
@st.cache_data(ttl=1)
def descargar_datos_consola_refine():
    try:
        # Descargamos todos los productos de tu catálogo cloud de Producción
        res_cat = supabase.table("catalogo").select("id_catalogo, nombre_catalogo, id_enlace_subcat").order("nombre_catalogo").execute()
        # Descargamos el árbol completo unificado de subcategorías (1 al 46)
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

st.markdown("### 📋 Distribución Actual del Surtido (372 SKUs)")
st.markdown("Abre los estantes para auditar la mercancía. Despliega el menú del producto para reubicarlo de pasillo de forma permanente [5.1].")
st.markdown("---")

# 6. ENRUTADOR DINÁMICO DE LIENZO GRÁFICO (MATRIZ DE EXPANDERS MULTIPASILLO RESPONSIVA)
# Agrupamos los 372 productos en la memoria RAM por su ID de subcategoría actual
productos_por_pasillo = df_productos.groupby("id_enlace_subcat")

# Estructuramos la visualización de alta densidad dividiendo la pantalla en 3 columnas maestras
columnas_estantes = st.columns(3)

for indice_sub, fila_sub in df_subcats.iterrows():
    id_subcat_actual = int(fila_sub["id_subcat"])
    nombre_subcat_actual = str(fila_sub["nombre_subcat"])
    
    # Extraemos los productos asociados a este departamento en la RAM, o dejamos lista vacía
    grupo_articulos = productos_por_pasillo.get_group(id_subcat_actual) if id_subcat_actual in productos_por_pasillo.groups else pd.DataFrame()
    conteo_skus = len(grupo_articulos)
    
    # Asignamos de forma correlativa el estante a una de las 3 columnas horizontales de la pantalla
    with columnas_estantes[indice_sub % 3]:
        # El título del contenedor se actualiza en vivo indicando cuántos artículos tiene grabados adentro
        titulo_contenedor = f"{nombre_subcat_actual} ({conteo_skus} SKUs)"
        
        with st.expander(titulo_contenedor, expanded=id_subcat_actual == 12):
            if grupo_articulos.empty:
                st.caption("✨ Estante vacío. No hay productos asignados.")
            else:
                for _, prod in grupo_articulos.iterrows():
                    id_sku = int(prod["id_catalogo"])
                    nombre_sku = str(prod["nombre_catalogo"])
                    
                    # Creamos una mini-grilla horizontal de control para cada producto individual
                    col_txt, col_sel = st.columns([2, 1])
                    with col_txt:
                        st.markdown(f"**{id_sku}** - {nombre_sku}")
                    with col_sel:
                        # Menú interactivo rápido de destino nativo de Python para mover el producto
                        lista_destinos_combobox = [nombre_subcat_actual] + [n for n in mapa_subcats_nombre_a_id.keys() if n != nombre_subcat_actual]
                        nuevo_destino_sel = st.selectbox(
                            "Mover a:",
                            options=lista_destinos_combobox,
                            key=f"sel_prod_{id_sku}",
                            label_visibility="collapsed"
                        )
                        
                        # Si el operador selecciona un destino diferente al actual, se ejecuta el guardado definitivo
                        if nuevo_destino_sel != nombre_subcat_actual:
                            id_subcat_destino_numeric = mapa_subcats_nombre_a_id[nuevo_destino_sel]
                            try:
                                # PERSISTENCIA CLOUD DURA: Grabado real e indestructible en Supabase
                                supabase.table("catalogo").update({
                                    "id_enlace_subcat": int(id_subcat_destino_numeric)
                                }).eq("id_catalogo", int(id_sku)).execute()
                                
                                st.toast(f"💾 ¡Guardado Permanente! {nombre_sku} movido a {nuevo_destino_sel}.", icon="✅")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e_up_nativo:
                                st.error(f"❌ Error de persistencia: {e_up_nativo}")
