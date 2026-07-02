# ==============================================================================
# PROGRAMA SATÉLITE: dashboard_catalogo.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.1.0 (UPGRADE DE INTELIGENCIA DE SURTIDO - ALERTAS DE DISTRICUCIÓN)
# DESCRIPCIÓN: Panel de Control Gerencial para Monitoreo de Existencias Cloud
# MODIFICACIÓN: Inclusión de matriz de detección automática de zonas muertas (SKUs < 3).
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
st.markdown("Auditoría analítica en caliente sobre la densidad del surtido, familias sub-distribuidas e integridad de la nube.")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA Y CRUDA DE DATOS EN LA NUBE (BYPASS DE CACHÉ EN VIVO)
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
    st.error("❌ Quiebre Estructural: No se detectaron subcategorías sembradas en internet. Corre el inicializador batch primero.")
    st.stop()

# 5. MOTOR DE RE-ACOPLAMIENTO RELACIONAL LOCAL EN LA MEMORIA RAM
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
    st.metric("Surtido Total de la Compañía", f"{total_articulos} Artículos")
with col_kpi2:
    st.metric("Variedad Activa de Surtido", f"{subcats_activas} de {total_subcats_existentes}")
with col_kpi3:
    st.metric("Porcentaje de Cobertura Comercial", f"{cobertura_variedad:.1f} %")

st.markdown("---")

# 7. NUEVA AUDITORÍA DE ZONAS MUERTAS: ALERTAS DE SUB-DISTRIBUCIÓN CRÍTICA
st.markdown("### 🚨 Alerta de Subcategorías Poco Distribuidas / Renglones Críticos")
st.markdown("Departamentos que poseen **menos de 3 productos registrados** en la base de datos cloud. Requieren ampliación de surtido de marcas urgente para evitar el abandono de góndolas [5.1].")

# Calculamos el conteo real por cada subcategoría del catálogo
conteo_por_subcat = df_master_bi["nombre_subcat"].value_counts().to_dict()

# Cruzamos contra el maestro de subcategorías completo para detectar también las de cero (0) registros
alertas_distribucion = []
for _, fila_sub in df_subcats_raw.iterrows():
    nom_sub = fila_sub["nombre_subcat"]
    skus_registrados = conteo_por_subcat.get(nom_sub, 0)
    
    # Filtro Comercial: Si tiene menos de 3 SKUs, entra al contenedor de atención prioritaria
    if skus_registrados < 3:
        alertas_distribucion.append({
            "Subcategoría Comercial": nom_sub,
            "Artículos Registrados": skus_registrados,
            "Diagnóstico Gerencial": "⚠️ ZONA MUERTA (Vacío en góndola)" if skus_registrados == 0 else "📉 SUB-DISTRIBUIDA (Ampliar variedad)"
        })

if alertas_distribucion:
    df_alertas_final = pd.DataFrame(alertas_distribucion).sort_values(by="Artículos Registrados", ascending=True).reset_index(drop=True)
    df_alertas_final.index = df_alertas_final.index + 1
    df_alertas_final.index.name = "N° Alerta"
    
    st.dataframe(
        df_alertas_final.style.map(
            lambda x: "background-color: #ffcccc; color: #cc0000; font-weight: bold;" if "ZONA MUERTA" in str(x) else ("background-color: #fff2cc; color: #b38600;" if "SUB-DISTRIBUIDA" in str(x) else ""),
            subset=["Diagnóstico Gerencial"]
        ),
        use_container_width=True
    )
else:
    st.success("🎉 ¡Excelente! La casa está 100% equilibrada. Todas las subcategorías comerciales poseen 3 o más productos asignados.")

st.markdown("---")

# 8. GRÁFICO DINÁMICO HISTOGRAMA: TOP DE SURTIDO POR VARIEDAD LÓGICA
st.markdown("### 📊 Densidad General de Productos por Subcategoría")
df_conteo_grafico = df_master_bi["nombre_subcat"].value_counts().reset_index()
df_conteo_grafico.columns = ["Subcategoría / Variedad", "Cantidad de SKUs"]
df_conteo_grafico = df_conteo_grafico.sort_values(by="Cantidad de SKUs", ascending=False)

st.bar_chart(
    data=df_conteo_grafico,
    x="Subcategoría / Variedad",
    y="Cantidad de SKUs",
    use_container_width=True
)

st.markdown("---")

# 9. BUSCADOR INTELIGENTE Y GRILLA DE AUDITORÍA CON CONTEO HUMANO CORRELATIVO
st.markdown("### 🔍 Buscador de Surtido y Filtro de Auditoría Rápida")
busqueda_operador = st.text_input(
    "Filtrar catálogos al instante (Escribe una marca, palabra o raíz léxica):",
    placeholder="Ej: mary, pan, jabon, enlatado",
    key="txt_busqueda_dashboard_v110"
).strip().lower()

df_grilla_filtrada = df_master_bi.copy()
if busqueda_operador:
    df_grilla_filtrada = df_grilla_filtrada[
        df_grilla_filtrada["nombre_catalogo"].str.lower().str.contains(busqueda_operador) |
        df_grilla_filtrada["nombre_subcat"].str.lower().str.contains(busqueda_operador)
    ]

df_grilla_final = df_grilla_filtrada[["nombre_catalogo", "nombre_subcat"]].sort_values(by="nombre_catalogo").reset_index(drop=True)
df_grilla_final.index = df_grilla_final.index + 1
df_grilla_final.index.name = "N° de Ítem"

st.dataframe(
    df_grilla_final.rename(columns={
        "nombre_catalogo": "Descripción del Artículo Registrado",
        "nombre_subcat": "Variedad / Subcategoría Asignada"
    }),
    use_container_width=True
)
