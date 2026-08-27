# ==============================================================================
# PROGRAMA SATÉLITE: grilla_productos.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.1.0 (BÚSQUEDA POR NOMBRE/MARCA + FILTROS CAT/SUBCAT)
# DESCRIPCIÓN: Grilla interactiva de catálogo de productos con filtros dinámicos
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA DE STREAMLIT
st.set_page_config(
    page_title="Grilla de Productos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
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

st.title("📦 Grilla de Catálogo de Productos")
st.markdown("Vista unificada del inventario retail con búsqueda inteligente y filtros por jerarquía de categorías.")
st.markdown("---")

# 3. FUNCIONES AUXILIARES DE CARGA DE DATOS MAESTROS
@st.cache_data(ttl=60)
def cargar_categorias():
    try:
        res = supabase.table("categorias").select("id_cat, nombre").execute()
        if res and hasattr(res, 'data') and res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.sidebar.error(f"⚠️ Error cargando categorías: {e}")
    return pd.DataFrame(columns=["id_cat", "nombre"])

@st.cache_data(ttl=60)
def cargar_subcategorias():
    try:
        res = supabase.table("subcategorias").select("id_subcat, id_cat, nombre").execute()
        if res and hasattr(res, 'data') and res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.sidebar.error(f"⚠️ Error cargando subcategorías: {e}")
    return pd.DataFrame(columns=["id_subcat", "id_cat", "nombre"])

@st.cache_data(ttl=60)
def cargar_productos():
    try:
        res = supabase.table("productos").select("*").execute()
        if res and hasattr(res, 'data') and res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"❌ Error cargando productos: {e}")
    return pd.DataFrame()

# 4. CARGA DE DATOS EN MEMORIA
df_categorias = cargar_categorias()
df_subcategorias = cargar_subcategorias()
df_productos_raw = cargar_productos()

if df_productos_raw.empty:
    st.warning("⚠️ No se encontraron productos en la base de datos o la tabla está vacía.")
    st.stop()

# 5. ENRIQUECIMIENTO DEL DATASET (JOINS EN MEMORIA)
df = df_productos_raw.copy()

# Merge con categorías
if not df_categorias.empty:
    df = df.merge(
        df_categorias.rename(columns={"nombre": "nombre_cat", "id_cat": "id_cat_ref"}),
        left_on="id_cat",
        right_on="id_cat_ref",
        how="left"
    )
    df.drop(columns=["id_cat_ref"], inplace=True, errors="ignore")
else:
    df["nombre_cat"] = "—"

# Merge con subcategorías
if not df_subcategorias.empty:
    df = df.merge(
        df_subcategorias.rename(columns={"nombre": "nombre_subcat", "id_subcat": "id_subcat_ref"}),
        left_on="id_subcat",
        right_on="id_subcat_ref",
        how="left"
    )
    df.drop(columns=["id_subcat_ref"], inplace=True, errors="ignore")
else:
    df["nombre_subcat"] = "—"

# 6. PANEL DE FILTROS EN SIDEBAR
st.sidebar.header("🔍 Filtros de Búsqueda")

# 6.1 CAJA DE TEXTO: Buscar por nombre, marca o código de barras
busqueda = st.sidebar.text_input(
    "Buscar producto:",
    placeholder="Nombre, marca o código de barras..."
)

# 6.2 FILTRO POR CATEGORÍA
if not df_categorias.empty:
    opciones_cat = ["Todas"] + sorted(df_categorias["nombre"].dropna().unique().tolist())
else:
    opciones_cat = ["Todas"]

filtro_cat = st.sidebar.selectbox("Categoría:", opciones_cat)

# 6.3 FILTRO POR SUBCATEGORÍA (dependiente de categoría seleccionada)
if filtro_cat != "Todas" and not df_subcategorias.empty and not df_categorias.empty:
    id_cat_sel = df_categorias.loc[df_categorias["nombre"] == filtro_cat, "id_cat"].values[0]
    subcats_filtradas = df_subcategorias[df_subcategorias["id_cat"] == id_cat_sel]["nombre"].dropna().unique().tolist()
    opciones_subcat = ["Todas"] + sorted(subcats_filtradas)
else:
    if not df_subcategorias.empty:
        opciones_subcat = ["Todas"] + sorted(df_subcategorias["nombre"].dropna().unique().tolist())
    else:
        opciones_subcat = ["Todas"]

filtro_subcat = st.sidebar.selectbox("Subcategoría:", opciones_subcat)

# 6.4 FILTROS BOOLEANOS DE NEGOCIO
st.sidebar.markdown("---")
st.sidebar.subheader("🏷️ Flags de Negocio")
col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    filtro_favorito = st.checkbox("⭐ Favoritos", value=False)
    filtro_estrategico = st.checkbox("🎯 Estratégicos", value=False)
with col_b2:
    filtro_alta_demanda = st.checkbox("🔥 Alta Demanda", value=False)
    filtro_cod_verif = st.checkbox("✅ Cod. Verif.", value=False)

# 7. APLICACIÓN DE FILTROS
mask = pd.Series([True] * len(df))

# Filtro de búsqueda por texto (nombre, marca o código de barras)
if busqueda:
    busqueda_lower = busqueda.lower()
    mask_nombre = df["nombre"].fillna("").str.lower().str.contains(busqueda_lower, na=False)
    mask_marca = df["marca"].fillna("").str.lower().str.contains(busqueda_lower, na=False)
    mask_codigo = df["codigo_barras"].fillna("").str.lower().str.contains(busqueda_lower, na=False)
    mask &= (mask_nombre | mask_marca | mask_codigo)

# Filtro por categoría
if filtro_cat != "Todas" and "nombre_cat" in df.columns:
    mask &= (df["nombre_cat"] == filtro_cat)

# Filtro por subcategoría
if filtro_subcat != "Todas" and "nombre_subcat" in df.columns:
    mask &= (df["nombre_subcat"] == filtro_subcat)

# Filtros booleanos
if filtro_favorito and "es_favorito" in df.columns:
    mask &= (df["es_favorito"] == True)
if filtro_estrategico and "es_estrategico" in df.columns:
    mask &= (df["es_estrategico"] == True)
if filtro_alta_demanda and "alta_demanda" in df.columns:
    mask &= (df["alta_demanda"] == True)
if filtro_cod_verif and "cod_verif" in df.columns:
    mask &= (df["cod_verif"] == True)

df_filtrado = df[mask].copy()

# 8. KPIs SUPERIORES
st.markdown("### 📊 Resumen del Catálogo")
col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
col_k1.metric("Total Productos", len(df))
col_k2.metric("Filtrados", len(df_filtrado))
col_k3.metric("Categorías", df_categorias["id_cat"].nunique() if not df_categorias.empty else 0)
col_k4.metric("Subcategorías", df_subcategorias["id_subcat"].nunique() if not df_subcategorias.empty else 0)
if "marca" in df.columns:
    col_k5.metric("Marcas Únicas", df["marca"].nunique())
else:
    col_k5.metric("Marcas Únicas", 0)

st.markdown("---")

# 9. PREPARACIÓN DE LA GRILLA PARA VISUALIZACIÓN
columnas_display = [
    "id_producto",
    "codigo_barras",
    "nombre",
    "marca",
    "tamano",
    "unidad",
    "nombre_cat",
    "nombre_subcat",
    "es_favorito",
    "alta_demanda",
    "es_estrategico",
    "cod_verif",
]

columnas_existentes = [c for c in columnas_display if c in df_filtrado.columns]
df_display = df_filtrado[columnas_existentes].copy()

renombres = {
    "id_producto": "ID",
    "codigo_barras": "Código de Barras",
    "nombre": "Nombre del Producto",
    "marca": "Marca",
    "tamano": "Tamaño",
    "unidad": "Unidad",
    "nombre_cat": "Categoría",
    "nombre_subcat": "Subcategoría",
    "es_favorito": "⭐ Fav",
    "alta_demanda": "🔥 Dem",
    "es_estrategico": "🎯 Est",
    "cod_verif": "✅ Verif",
}
df_display.rename(columns=renombres, inplace=True)

# Formatear booleanos como emojis
for col in ["⭐ Fav", "🔥 Dem", "🎯 Est", "✅ Verif"]:
    if col in df_display.columns:
        df_display[col] = df_display[col].apply(lambda x: "✅" if x else "❌")

# Ordenar por ID ascendente
if "ID" in df_display.columns:
    df_display = df_display.sort_values(by="ID", ascending=True).reset_index(drop=True)
    df_display.index = df_display.index + 1
    df_display.index.name = "N°"

# 10. RENDERIZADO DE LA GRILLA
st.markdown(f"### 📋 Resultados: `{len(df_filtrado)}` productos encontrados")

if df_display.empty:
    st.info("💡 No hay productos que coincidan con los filtros seleccionados. Ajusta los criterios de búsqueda.")
else:
    st.dataframe(
        df_display,
        use_container_width=True,
        height=600,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Código de Barras": st.column_config.TextColumn("Código de Barras", width="medium"),
            "Nombre del Producto": st.column_config.TextColumn("Nombre del Producto", width="large"),
            "Marca": st.column_config.TextColumn("Marca", width="medium"),
            "Tamaño": st.column_config.NumberColumn("Tamaño", format="%.2f", width="small"),
            "Unidad": st.column_config.TextColumn("Unidad", width="small"),
            "Categoría": st.column_config.TextColumn("Categoría", width="medium"),
            "Subcategoría": st.column_config.TextColumn("Subcategoría", width="medium"),
            "⭐ Fav": st.column_config.TextColumn("⭐ Fav", width="small"),
            "🔥 Dem": st.column_config.TextColumn("🔥 Dem", width="small"),
            "🎯 Est": st.column_config.TextColumn("🎯 Est", width="small"),
            "✅ Verif": st.column_config.TextColumn("✅ Verif", width="small"),
        }
    )

    csv = df_display.to_csv(index=True).encode("utf-8")
    st.download_button(
        label="📥 Descargar resultados como CSV",
        data=csv,
        file_name="grilla_productos.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("🔒 Conexión segura a Supabase | Datos en tiempo real | v1.1.0")
