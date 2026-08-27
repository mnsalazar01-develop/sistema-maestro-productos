# ==============================================================================
# PROGRAMA SATÉLITE: grilla_productos.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.2.0 (FILTROS EN ÁREA PRINCIPAL + GRILLA EDITABLE)
# DESCRIPCIÓN: Grilla interactiva y editable de catálogo de productos.
#              Filtros en el área principal. Edición inline con persistencia
#              a Supabase.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA DE STREAMLIT
st.set_page_config(
    page_title="Grilla de Productos",
    page_icon="📦",
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

st.title("📦 Grilla de Catálogo de Productos")
st.markdown("Vista unificada del inventario retail. Edita los valores directamente en la grilla y guarda los cambios en la nube.")
st.markdown("---")

# 3. FUNCIONES AUXILIARES DE CARGA DE DATOS MAESTROS
@st.cache_data(ttl=60)
def cargar_categorias():
    try:
        res = supabase.table("categorias").select("id_cat, nombre").execute()
        if res and hasattr(res, 'data') and res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"⚠️ Error cargando categorías: {e}")
    return pd.DataFrame(columns=["id_cat", "nombre"])

@st.cache_data(ttl=60)
def cargar_subcategorias():
    try:
        res = supabase.table("subcategorias").select("id_subcat, id_cat, nombre").execute()
        if res and hasattr(res, 'data') and res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"⚠️ Error cargando subcategorías: {e}")
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

# 6. FILTROS EN ÁREA PRINCIPAL (SIN SIDEBAR)
st.markdown("### 🔍 Filtros de Búsqueda")

f1, f2, f3, f4 = st.columns([2, 1.5, 1.5, 2])

with f1:
    busqueda = st.text_input(
        "Buscar producto:",
        placeholder="Nombre, marca o código de barras...",
        label_visibility="collapsed"
    )

with f2:
    if not df_categorias.empty:
        opciones_cat = ["Todas"] + sorted(df_categorias["nombre"].dropna().unique().tolist())
    else:
        opciones_cat = ["Todas"]
    filtro_cat = st.selectbox("Categoría:", opciones_cat, label_visibility="collapsed")

with f3:
    if filtro_cat != "Todas" and not df_subcategorias.empty and not df_categorias.empty:
        id_cat_sel = df_categorias.loc[df_categorias["nombre"] == filtro_cat, "id_cat"].values[0]
        subcats_filtradas = df_subcategorias[df_subcategorias["id_cat"] == id_cat_sel]["nombre"].dropna().unique().tolist()
        opciones_subcat = ["Todas"] + sorted(subcats_filtradas)
    else:
        if not df_subcategorias.empty:
            opciones_subcat = ["Todas"] + sorted(df_subcategorias["nombre"].dropna().unique().tolist())
        else:
            opciones_subcat = ["Todas"]
    filtro_subcat = st.selectbox("Subcategoría:", opciones_subcat, label_visibility="collapsed")

with f4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        filtro_favorito = st.checkbox("⭐ Fav", value=False)
    with b2:
        filtro_estrategico = st.checkbox("🎯 Est", value=False)
    with b3:
        filtro_alta_demanda = st.checkbox("🔥 Dem", value=False)
    with b4:
        filtro_cod_verif = st.checkbox("✅ Verif", value=False)

st.markdown("---")

# 7. APLICACIÓN DE FILTROS
mask = pd.Series([True] * len(df))

if busqueda:
    busqueda_lower = busqueda.lower()
    mask_nombre = df["nombre"].fillna("").str.lower().str.contains(busqueda_lower, na=False)
    mask_marca = df["marca"].fillna("").str.lower().str.contains(busqueda_lower, na=False)
    mask_codigo = df["codigo_barras"].fillna("").str.lower().str.contains(busqueda_lower, na=False)
    mask &= (mask_nombre | mask_marca | mask_codigo)

if filtro_cat != "Todas" and "nombre_cat" in df.columns:
    mask &= (df["nombre_cat"] == filtro_cat)

if filtro_subcat != "Todas" and "nombre_subcat" in df.columns:
    mask &= (df["nombre_subcat"] == filtro_subcat)

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

# 9. GRILLA EDITABLE
st.markdown(f"### 📋 Resultados: `{len(df_filtrado)}` productos — Edita directamente y luego guarda")

if df_filtrado.empty:
    st.info("💡 No hay productos que coincidan con los filtros seleccionados.")
else:
    # Columnas que se mostrarán en el editor
    columnas_editor = [
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
    columnas_existentes = [c for c in columnas_editor if c in df_filtrado.columns]
    df_edit = df_filtrado[columnas_existentes].copy()

    # Renombrar para presentación
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
    df_edit.rename(columns=renombres, inplace=True)

    # Guardar el dataframe original en session_state para comparar después
    if "df_original" not in st.session_state:
        st.session_state.df_original = df_edit.copy()

    # Configuración de columnas para el data_editor
    column_config = {
        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Código de Barras": st.column_config.TextColumn("Código de Barras", disabled=True, width="medium"),
        "Nombre del Producto": st.column_config.TextColumn("Nombre del Producto", width="large"),
        "Marca": st.column_config.TextColumn("Marca", width="medium"),
        "Tamaño": st.column_config.NumberColumn("Tamaño", format="%.2f", width="small"),
        "Unidad": st.column_config.TextColumn("Unidad", width="small"),
        "Categoría": st.column_config.TextColumn("Categoría", disabled=True, width="medium"),
        "Subcategoría": st.column_config.TextColumn("Subcategoría", disabled=True, width="medium"),
        "⭐ Fav": st.column_config.CheckboxColumn("⭐ Fav", width="small"),
        "🔥 Dem": st.column_config.CheckboxColumn("🔥 Dem", width="small"),
        "🎯 Est": st.column_config.CheckboxColumn("🎯 Est", width="small"),
        "✅ Verif": st.column_config.CheckboxColumn("✅ Verif", width="small"),
    }

    # Solo incluir columnas que existen
    column_config_filtrado = {k: v for k, v in column_config.items() if k in df_edit.columns}

    df_editado = st.data_editor(
        df_edit,
        column_config=column_config_filtrado,
        use_container_width=True,
        height=600,
        num_rows="fixed",
        key="editor_productos",
        hide_index=True
    )

    # 10. BOTÓN PARA GUARDAR CAMBIOS EN SUPABASE
    st.markdown("---")
    col_guardar, col_csv = st.columns([1, 4])

    with col_guardar:
        if st.button("💾 Guardar Cambios en la Nube", type="primary", use_container_width=True):
            cambios_realizados = 0
            errores = []

            # Comparar fila por fila con el original
            df_original = st.session_state.df_original

            # Asegurar que ambos tengan el mismo índice y columnas comparables
            cols_comparables = [c for c in df_editado.columns if c not in ["Categoría", "Subcategoría"]]

            for idx in df_editado.index:
                fila_nueva = df_editado.loc[idx]
                fila_original = df_original.loc[idx] if idx in df_original.index else None

                if fila_original is None:
                    continue

                # Detectar cambios en columnas editables
                campos_cambiados = {}
                for col in cols_comparables:
                    if col == "ID":
                        continue
                    if col in df_original.columns and fila_nueva[col] != fila_original[col]:
                        # Mapear nombres de vuelta a la base de datos
                        mapeo_inverso = {v: k for k, v in renombres.items()}
                        campo_db = mapeo_inverso.get(col, col)
                        campos_cambiados[campo_db] = fila_nueva[col]

                if campos_cambiados:
                    id_producto = int(fila_nueva["ID"])
                    try:
                        supabase.table("productos").update(campos_cambiados).eq("id_producto", id_producto).execute()
                        cambios_realizados += 1
                    except Exception as e:
                        errores.append(f"ID {id_producto}: {e}")

            if cambios_realizados > 0:
                st.success(f"✅ {cambios_realizados} producto(s) actualizado(s) correctamente en Supabase.")
                # Limpiar caché para recargar datos frescos
                cargar_productos.clear()
                st.session_state.df_original = df_editado.copy()
                st.rerun()
            elif errores:
                for err in errores:
                    st.error(f"❌ {err}")
            else:
                st.info("💡 No se detectaron cambios para guardar.")

    with col_csv:
        csv = df_editado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name="grilla_productos.csv",
            mime="text/csv"
        )

st.markdown("---")
st.caption("🔒 Conexión segura a Supabase | Datos editables en vivo | v1.2.0")
