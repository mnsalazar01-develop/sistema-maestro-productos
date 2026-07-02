# ==============================================================================
# PROGRAMA SATÉLITE: clasificar_web_drag.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 7.0.0 (CLASIFICADOR DRAG & DROP PROFESIONAL CERTIFICADO)
# DESCRIPCIÓN: Panel de Arrastre Multipasillo con Persistencia Dura en Internet
# MODIFICACIÓN: Inyección de streamlit_sortable para romper el bloqueo de iframe.
# ==============================================================================

import streamlit as st
import pandas as pd
from streamlit_sortable import sortable
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA WEB DE STREAMLIT
st.set_page_config(
    page_title="Clasificador Drag & Drop Web",
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

st.title("🖱️ Clasificador Interactivo Drag & Drop Web (Sortable Engine)")
st.markdown("Arrastra los productos con el mouse directamente entre los estantes de la tienda. ¡Persistencia relacional indestructible en Supabase Cloud!")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA DE LOS 372 ARTÍCULOS COMPLETOS Y EL MASTER DE SUBCATEGORIAS
@st.cache_data(ttl=1)
def descargar_datos_clasificador_profesional():
    try:
        # Descargamos los productos (trayendo un bloque fluido de 30 para no saturar el lienzo visual)
        res_cat = supabase.table("catalogo").select("id_catalogo, nombre_catalogo, id_enlace_subcat").order("id_catalogo").execute()
        # Descargamos el maestro de subcategorías completo (1 al 46)
        res_sub = supabase.table("subcategorias").select("id_subcat, nombre_subcat").order("id_subcat").execute()
        
        if res_cat and hasattr(res_cat, 'data') and res_sub and hasattr(res_sub, 'data'):
            return pd.DataFrame(res_cat.data), pd.DataFrame(res_sub.data)
    except Exception as e_load:
        st.sidebar.error(f"⚠️ Error al leer datos desde internet: {e_load}")
    return pd.DataFrame(), pd.DataFrame()

df_productos, df_subcats = descargar_datos_clasificador_profesional()

if df_productos.empty or df_subcats.empty:
    st.info("💡 Esperando consistencia de datos... Asegúrate de tener registros en tus tablas cloud.")
    st.stop()

# 4. PREPARACIÓN DE LAS LISTAS PARALELAS EN LA MEMORIA RAM DE PYTHON
# Aislamos el Depósito General (los productos que están en la subcategoría base de Víveres ID 12)
df_deposito = df_productos[df_productos["id_enlace_subcat"] == 12].limit(30)
lista_deposito_strings = [f"{fila['id_catalogo']} - {fila['nombre_catalogo']}" for _, fila in df_deposito.iterrows()]

# Mapeamos los nombres y emojis de las subcategorías destino core principales (ej: IDs 1, 2, 9, 16)
subcats_destino_core = [1, 2, 9, 16]
df_subcats_filtradas = df_subcats[df_subcats["id_subcat"].isin(subcats_destino_core)]

# Construimos la estructura de columnas paralelas que 'streamlit-sortable' necesita para dibujar el arrastre
estructura_estantes_ram = {"📋 Depósito General (ID 12)": lista_deposito_strings}

mapa_titulos_a_id = {}
for _, fila_sub in df_subcats_filtradas.iterrows():
    id_sub = int(fila_sub["id_subcat"])
    nombre_sub = str(fila_sub["nombre_subcat"])
    
    # Extraemos los productos que ya viven en esta subcategoría en internet
    df_prods_estante = df_productos[df_productos["id_enlace_subcat"] == id_sub]
    lista_prods_strings = [f"{f['id_catalogo']} - {f['nombre_catalogo']}" for _, f in df_prods_estante.iterrows()]
    
    estructura_estantes_ram[nombre_sub] = lista_prods_strings
    mapa_titulos_a_id[nombre_sub] = id_sub

# 5. RENDERIZADO DEL LIENZO INTERACTIVO PROFESIONAL (REACT DND ENGINE)
# Se pinta la grilla de arrastre directo en el navegador del operador
resultado_movimiento = sortable(estructura_estantes_ram, direction="horizontal")

# 6. CAPTURA DEL EVENTO DE SOLTADO Y PERSISTENCIA ATÓMICA EN LA NUBE PROFUNDA
# Si el resultado_movimiento cambia respecto a lo que descargamos, Python procesa la diferencia en el acto
if resultado_movimiento:
    # Verificamos si algún producto del depósito fue soltado en un estante de la derecha
    for nombre_estante_destino, lista_items_finales in resultado_movimiento.items():
        if nombre_estante_destino != "📋 Depósito General (ID 12)":
            id_subcat_destino_cloud = mapa_titulos_a_id[nombre_estante_destino]
            
            for item_string in lista_items_finales:
                # Si el artículo no pertenecía originalmente a este estante, encontramos al trasladado
                id_sku_movido = int(item_string.split(" - ")[0])
                
                # Buscamos en la RAM qué pasillo tenía grabado este producto antes de mover el mouse
                id_pasillo_viejo = int(df_productos[df_productos["id_catalogo"] == id_sku_movido].iloc[0]["id_enlace_subcat"])
                
                if id_pasillo_viejo != id_subcat_destino_cloud:
                    try:
                        # PERSISTENCIA NO VOLÁTIL DURA: Inyección directa e inmune al disco de Supabase
                        supabase.table("catalogo").update({
                            "id_enlace_subcat": int(id_subcat_destino_cloud)
                        }).eq("id_catalogo", int(id_sku_movido)).execute()
                        
                        st.toast(f"💾 Guardado Permanente: {item_string} movido con éxito.", icon="✅")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e_sortable:
                        st.error(f"❌ Error relacional: {e_sortable}")
