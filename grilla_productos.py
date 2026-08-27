# ==============================================================================
# PROGRAMA SATÉLITE: grilla_productos_v150.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.5.0
# DESCRIPCIÓN: Grilla interactiva y editable de catálogo de productos con
#              reclasificación de categoría/subcategoría, imágenes firmadas desde
#              bucket privado, filtros en área principal y persistencia a Supabase.
# REGLAS: Sin panel lateral | Versión en nombre de archivo | Sin filtros check
#         | Optimización de firmas de imágenes | Reclasificación habilitada
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ------------------------------------------------------------------------------
# CONSTANTES DE VERSIÓN
# ------------------------------------------------------------------------------
VERSION_PROGRAMA = "1.5.0"
NOMBRE_PROGRAMA = "Grilla de Productos"

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA DE STREAMLIT
st.set_page_config(
    page_title=f"{NOMBRE_PROGRAMA} v{VERSION_PROGRAMA}",
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

# ------------------------------------------------------------------------------
# ENCABEZADO CON VERSIÓN
# ------------------------------------------------------------------------------
st.title(f"📦 {NOMBRE_PROGRAMA}")
st.markdown(f"**Versión {VERSION_PROGRAMA}** — Reclasificación de productos, imágenes firmadas y edición inline.")
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

# 3.1 FUNCIÓN PARA FIRMAR URL DE IMAGEN DESDE BUCKET PRIVADO
@st.cache_data(ttl=3600)
def firmar_url_imagen(url_imagen: str, duracion_segundos: int = 3600) -> str:
    """
    Firma una URL de imagen almacenada en un bucket privado de Supabase Storage.
    Si la URL no pertenece al proyecto de Supabase, se retorna tal cual.
    Cache TTL: 1 hora para evitar llamadas repetitivas.
    """
    if not url_imagen or pd.isna(url_imagen):
        return ""

    try:
        supabase_url = st.secrets["supabase"]["url"]
        url_str = str(url_imagen).strip()

        if supabase_url not in url_str:
            return url_str

        partes = url_str.split("/storage/v1/object/public/")
        if len(partes) == 2:
            bucket_y_path = partes[1]
            bucket_name = bucket_y_path.split("/")[0]
            file_path = "/".join(bucket_y_path.split("/")[1:])

            if not bucket_name or not file_path:
                return url_str

            res = supabase.storage.from_(bucket_name).create_signed_url(file_path, duracion_segundos)
            if res and "signedURL" in res:
                signed = res["signedURL"]
                if signed.startswith("http"):
                    return signed
                else:
                    return f"{supabase_url}{signed}"
    except Exception:
        pass

    return str(url_imagen)

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

# ------------------------------------------------------------------------------
# MAPEOS PARA RECLASIFICACIÓN (NOMBRE → ID)
# ------------------------------------------------------------------------------
lista_categorias = sorted(df_categorias["nombre"].dropna().unique().tolist()) if not df_categorias.empty else ["—"]
lista_subcategorias = sorted(df_subcategorias["nombre"].dropna().unique().tolist()) if not df_subcategorias.empty else ["—"]

mapa_cat_nombre_a_id = dict(zip(df_categorias["nombre"], df_categorias["id_cat"])) if not df_categorias.empty else {}
mapa_subcat_nombre_a_id = dict(zip(df_subcategorias["nombre"], df_subcategorias["id_subcat"])) if not df_subcategorias.empty else {}
# Mapa para validar: subcategoría → id_cat (para alertar si no coincide)
mapa_subcat_a_cat_id = dict(zip(df_subcategorias["nombre"], df_subcategorias["id_cat"])) if not df_subcategorias.empty else {}

# ------------------------------------------------------------------------------
# 6. RESUMEN DEL CATÁLOGO (PRIMERO)
# ------------------------------------------------------------------------------
st.markdown("### 📊 Resumen del Catálogo")
col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
col_k1.metric("Total Productos", len(df))
col_k2.metric("Filtrados", len(df))
col_k3.metric("Categorías", df_categorias["id_cat"].nunique() if not df_categorias.empty else 0)
col_k4.metric("Subcategorías", df_subcategorias["id_subcat"].nunique() if not df_subcategorias.empty else 0)
if "marca" in df.columns:
    col_k5.metric("Marcas Únicas", df["marca"].nunique())
else:
    col_k5.metric("Marcas Únicas", 0)

st.markdown("---")

# ------------------------------------------------------------------------------
# 7. FILTROS DE BÚSQUEDA (DESPUÉS DEL RESUMEN)
# ------------------------------------------------------------------------------
st.markdown("### 🔍 Filtros de Búsqueda")

f1, f2, f3 = st.columns([3, 2, 2])

with f1:
    busqueda = st.text_input(
        "Buscar producto:",
        placeholder="Nombre, marca o código de barras...",
        label_visibility="collapsed"
    )

with f2:
    opciones_cat = ["Todas"] + lista_categorias
    filtro_cat = st.selectbox("Categoría:", opciones_cat, label_visibility="collapsed")

with f3:
    if filtro_cat != "Todas" and not df_subcategorias.empty:
        id_cat_sel = mapa_cat_nombre_a_id.get(filtro_cat)
        subcats_filtradas = df_subcategorias[df_subcategorias["id_cat"] == id_cat_sel]["nombre"].dropna().unique().tolist()
        opciones_subcat = ["Todas"] + sorted(subcats_filtradas)
    else:
        opciones_subcat = ["Todas"] + lista_subcategorias
    filtro_subcat = st.selectbox("Subcategoría:", opciones_subcat, label_visibility="collapsed")

st.markdown("---")

# 8. APLICACIÓN DE FILTROS
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

df_filtrado = df[mask].copy()

if len(df_filtrado) != len(df):
    st.info(f"📌 Mostrando **{len(df_filtrado)}** de **{len(df)}** productos según filtros aplicados.")

# ------------------------------------------------------------------------------
# 9. GRILLA EDITABLE CON RECLASIFICACIÓN E IMÁGENES FIRMADAS
# ------------------------------------------------------------------------------
st.markdown(f"### 📋 Catálogo de Productos — `{len(df_filtrado)}` registros")

if df_filtrado.empty:
    st.info("💡 No hay productos que coincidan con los filtros seleccionados.")
else:
    # OPTIMIZACIÓN: Solo firmamos imágenes de las filas filtradas
    if "url_imagen" in df_filtrado.columns:
        df_filtrado["url_imagen"] = df_filtrado["url_imagen"].apply(
            lambda x: firmar_url_imagen(x, 3600)
        )

    columnas_editor = [
        "url_imagen",
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

    renombres = {
        "url_imagen": "Imagen",
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

    # Guardar original para comparación
    if "df_original" not in st.session_state:
        st.session_state.df_original = df_edit.copy()

    # Configuración de columnas del data_editor
    # Categoría y Subcategoría ahora son EDITABLES (SelectboxColumn)
    column_config = {
        "Imagen": st.column_config.ImageColumn(
            "Imagen",
            help="Vista previa del producto desde bucket privado (URL firmada)",
            width="small"
        ),
        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Código de Barras": st.column_config.TextColumn("Código de Barras", disabled=True, width="medium"),
        "Nombre del Producto": st.column_config.TextColumn("Nombre del Producto", width="large"),
        "Marca": st.column_config.TextColumn("Marca", width="medium"),
        "Tamaño": st.column_config.NumberColumn("Tamaño", format="%.2f", width="small"),
        "Unidad": st.column_config.TextColumn("Unidad", width="small"),
        "Categoría": st.column_config.SelectboxColumn(
            "Categoría",
            options=lista_categorias,
            required=True,
            width="medium"
        ),
        "Subcategoría": st.column_config.SelectboxColumn(
            "Subcategoría",
            options=lista_subcategorias,
            required=True,
            width="medium"
        ),
        "⭐ Fav": st.column_config.CheckboxColumn("⭐ Fav", width="small"),
        "🔥 Dem": st.column_config.CheckboxColumn("🔥 Dem", width="small"),
        "🎯 Est": st.column_config.CheckboxColumn("🎯 Est", width="small"),
        "✅ Verif": st.column_config.CheckboxColumn("✅ Verif", width="small"),
    }

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
            advertencias = []

            df_original = st.session_state.df_original
            # Todas las columnas son comparables excepto Imagen (solo lectura)
            cols_comparables = [c for c in df_editado.columns if c != "Imagen"]

            for idx in df_editado.index:
                fila_nueva = df_editado.loc[idx]
                fila_original = df_original.loc[idx] if idx in df_original.index else None

                if fila_original is None:
                    continue

                campos_cambiados = {}
                for col in cols_comparables:
                    if col == "ID":
                        continue
                    if col in df_original.columns and fila_nueva[col] != fila_original[col]:
                        # Mapeo especial para Categoría y Subcategoría (nombre → ID)
                        if col == "Categoría":
                            nuevo_id_cat = mapa_cat_nombre_a_id.get(fila_nueva[col])
                            if nuevo_id_cat is not None:
                                campos_cambiados["id_cat"] = int(nuevo_id_cat)
                        elif col == "Subcategoría":
                            nuevo_id_subcat = mapa_subcat_nombre_a_id.get(fila_nueva[col])
                            if nuevo_id_subcat is not None:
                                campos_cambiados["id_subcat"] = int(nuevo_id_subcat)
                        else:
                            mapeo_inverso = {v: k for k, v in renombres.items()}
                            campo_db = mapeo_inverso.get(col, col)
                            campos_cambiados[campo_db] = fila_nueva[col]

                # Validación: subcategoría pertenece a la categoría seleccionada
                if "id_subcat" in campos_cambiados or "id_cat" in campos_cambiados:
                    cat_actual = campos_cambiados.get("id_cat", mapa_cat_nombre_a_id.get(fila_nueva["Categoría"]))
                    subcat_actual = campos_cambiados.get("id_subcat", mapa_subcat_nombre_a_id.get(fila_nueva["Subcategoría"]))
                    cat_esperada = mapa_subcat_a_cat_id.get(fila_nueva["Subcategoría"])

                    if cat_esperada is not None and cat_actual is not None and cat_esperada != cat_actual:
                        advertencias.append(
                            f"ID {fila_nueva['ID']}: Subcategoría '{fila_nueva['Subcategoría']}' no pertenece a Categoría '{fila_nueva['Categoría']}'. "
                            f"Se guardará igual, pero verifica la reclasificación."
                        )

                if campos_cambiados:
                    id_producto = int(fila_nueva["ID"])
                    try:
                        supabase.table("productos").update(campos_cambiados).eq("id_producto", id_producto).execute()
                        cambios_realizados += 1
                    except Exception as e:
                        errores.append(f"ID {id_producto}: {e}")

            # Mostrar resultados
            if advertencias:
                for adv in advertencias:
                    st.warning(f"⚠️ {adv}")

            if cambios_realizados > 0:
                st.success(f"✅ {cambios_realizados} producto(s) actualizado(s) correctamente en Supabase.")
                cargar_productos.clear()
                firmar_url_imagen.clear()
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
st.caption(f"🔒 Conexión segura a Supabase | Reclasificación habilitada | Imágenes firmadas | v{VERSION_PROGRAMA}")
