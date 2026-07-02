# ==============================================================================
# PROGRAMA SATÉLITE: dashboard_catalogo.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.0.0 (LÍNEA BASE DE ANALÍTICA Y CONTROL DE SURTIDO)
# DESCRIPCIÓN: Panel de Control Gerencial para Monitoreo de Existencias Cloud
# MODIFICACIÓN: Despliegue inicial de KPIs atómicos, mix de variedad y buscador.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA DE ANALÍTICA DE STREAMLIT
st.set_page_config(
    page_title="Dashboard de Catálogo",
    page_icon="📊",
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

st.title("📊 Indicadores de Gestión y Control de Catálogo")
st.markdown("Auditoría analítica en caliente sobre la densidad del surtido e integridad de las subcategorías en la nube.")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA Y CRUDA DE DATOS EN LA NUBE (BYPASS DE CACHÉ EN VIVO)
@st.markdown_transaction if hasattr(st, 'markdown_transaction') else lambda x: x
def descargar_datos_maestros_bi():
    try:
        # Descargamos el catálogo completo de productos
        res_cat = supabase.table("catalogo").select("id_catalogo, id_enlace_subcat, nombre_catalogo").execute()
        # Descargamos el árbol unificado de subcategorías para realizar el cruce local
        res_sub = supabase.table("subcategorias").select("id_subcat, nombre_subcat").execute()
        
        if res_cat and hasattr(res_cat, 'data') and res_sub and hasattr(res_sub, 'data'):
            return pd.DataFrame(res_cat.data), pd.DataFrame(res_sub.data)
    except Exception as e_bi:
        st.sidebar.error(f"⚠️ Error de lectura HTTP cloud: {e_bi}")
    return pd.DataFrame(), pd.DataFrame()

df_productos_raw, df_subcats_raw = descargar_datos_maestros_bi()

# 4. PARACHOQUES DE RED: DETENCIÓN SEGURA SI LA NUBE ESTÁ COMPLETAMENTE VACÍA
if df_productos_raw.empty:
    st.info("💡 Catálogo Vacío: No hay productos inyectados en la tabla 'catalogo' en la nube. Carga el CSV masivo primero para encender los gráficos.")
    st.stop()

if df_subcats_raw.empty:
    st.error("❌ Quiebre Estructural: No se detectaron subcategorías sembradas en internet. Corre el instalador batch primero.")
    st.stop()

# 5. MOTOR DE RE-ACOPLAMIENTO RELACIONAL LOCAL EN LA MEMORIA RAM
# Normalizamos los tipos de datos a enteros limpios para garantizar un match perfecto sin falsos omitidos
df_productos_raw["id_enlace_subcat"] = df_productos_raw["id_enlace_subcat"].astype(int)
df_subcats_raw["id_subcat"] = df_subcats_raw["id_subcat"].astype(int)

# Ejecutamos el JOIN local simulando la consulta SQL relacional
df_master_bi = pd.merge(
    df_productos_raw,
    df_subcats_raw,
    left_on="id_enlace_subcat",
    right_on="id_subcat",
    how="inner"
)

# 6. RENDERIZADO DE ALTA DENSIDAD: BLOQUE DE KPIS ATÓMICOS DE PORTADA
total_articulos = len(df_master_bi)
subcats_activas = df_master_bi["id_subcat"].nunique()
total_subcats_existentes = len(df_subcats_raw)
cobertura_variedad = (subcats_activas / total_subcats_existentes) * 100

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    st.metric(
        label="Surtido Total de la Compañía",
        value=f"{total_articulos} Artículos",
        help="Conteo neto de SKUs individuales guardados de forma permanente en la tabla catalogo"
    )

with col_kpi2:
    st.metric(
        label="Variedad Activa de Surtido",
        value=f"{subcats_activas} de {total_subcats_existentes}",
        help="Cantidad de subcategorías que poseen al menos un producto registrado en la tienda"
    )

with col_kpi3:
    st.metric(
        label="Porcentaje de Cobertura Comercial",
        value=f"{cobertura_variedad:.1f} %",
        help="Densidad de ocupación de las familias del árbol respecto a la meta total del negocio"
    )

st.markdown("---")

# 7. GRÁFICO DINÁMICO HISTOGRAMA: TOP DE SURTIDO POR VARIEDAD LÓGICA
st.markdown("### 📊 Densidad de Productos por Subcategoría")

# Agrupamos y contamos la cantidad de productos por cada descripción con emoji
df_conteo_grafico = df_master_bi["nombre_subcat"].value_counts().reset_index()
df_conteo_grafico.columns = ["Subcategoría / Variedad", "Cantidad de SKUs"]

# Ordenamos de mayor a menor volumen comercial para la toma de decisiones gerenciales
df_conteo_grafico = df_conteo_grafico.sort_values(by="Cantidad de SKUs", ascending=False)

# Pintamos el gráfico nativo de barras horizontales de alta densidad de Streamlit
st.bar_chart(
    data=df_conteo_grafico,
    x="Subcategoría / Variedad",
    y="Cantidad de SKUs",
    use_container_width=True
)

st.markdown("---")

# 8. BUSCADOR INTELIGENTE Y GRILLA DE AUDITORÍA CON CONTEO HUMANO CORRELATIVO
st.markdown("### 🔍 Buscador de Surtido y Filtro de Auditoría Rápida")

busqueda_operador = st.text_input(
    "Filtrar catálogos al instante (Escribe una marca, palabra o raíz léxica):",
    placeholder="Ej: mary, pan, jabon, enlatado"
).strip().lower()

# Aplicamos la máscara de filtrado dinámico sobre la string
df_grilla_filtrada = df_master_bi.copy()
if busqueda_operador:
    df_grilla_filtrada = df_grilla_filtrada[
        df_grilla_filtrada["nombre_catalogo"].str.lower().str.contains(busqueda_operador) |
        df_grilla_filtrada["nombre_subcat"].str.lower().str.contains(busqueda_operador)
    ]

# Formateamos la tabla final para la lectura visual limpia del supervisor
df_grilla_final = df_grilla_filtrada[["nombre_catalogo", "nombre_subcat"]].sort_values(by="nombre_catalogo").reset_index(drop=True)

# Conteo humano correlativo riguroso partiendo estrictamente desde 1
df_grilla_final.index = df_grilla_final.index + 1
df_grilla_final.index.name = "N° de Ítem"

st.dataframe(
    df_grilla_final.rename(columns={
        "nombre_catalogo": "Descripción del Artículo Registrado",
        "nombre_subcat": "Variedad / Subcategoría Asignada"
    }),
    use_container_width=True
)
