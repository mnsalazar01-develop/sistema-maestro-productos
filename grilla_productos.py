# ==============================================================================
# PROGRAMA SATÉLITE: grilla_productos_v168.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.6.8
# DESCRIPCIÓN: Grilla de catálogo con creación de productos, modificación de
#              productos incluyendo actualización de imagen. Imágenes subidas
#              al bucket "imagenes" con formato img_AAAAMMDD_HHMMSS.ext y URL
#              completa guardada en base de datos (get_public_url).
# REGLAS: Sin panel lateral | Versión en nombre de archivo | Sin filtros check
#         | URLs firmadas solo filtradas | Subcategoría dependiente de categoría
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client
from datetime import datetime

# ------------------------------------------------------------------------------
# CONSTANTES DE VERSIÓN Y CONFIGURACIÓN
# ------------------------------------------------------------------------------
VERSION_PROGRAMA = "1.6.9.3"
NOMBRE_PROGRAMA = "Grilla de Productos"
BUCKET_IMAGENES = "imagenes"

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

st.title(f"📦 {NOMBRE_PROGRAMA}")
st.markdown(f"**Versión {VERSION_PROGRAMA}** — Imágenes con URL completa desde bucket 'imagenes'.")
st.markdown("---")

# ------------------------------------------------------------------------------
# FUNCIÓN AUXILIAR: Normalizar valores pandas (np.nan → None/valor por defecto)
# ------------------------------------------------------------------------------
def safe_str(val, default=""):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return str(val) if val != default else default

def safe_float(val, default=0.0):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_bool(val, default=False):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return bool(val)

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

# 3.1 FUNCIÓN PARA FIRMAR URL DE IMAGEN (soporta URL completa o ruta relativa)
@st.cache_data(ttl=3600)
def firmar_url_imagen(url_imagen: str, duracion_segundos: int = 3600) -> str:
    if not url_imagen or pd.isna(url_imagen):
        return ""
    url_str = str(url_imagen).strip()
    supabase_url = st.secrets["supabase"]["url"]
    bucket_name = BUCKET_IMAGENES
    file_path = ""
    try:
        # CASO A: URL completa de Supabase Storage
        if supabase_url in url_str and "/storage/v1/object/public/" in url_str:
            partes = url_str.split("/storage/v1/object/public/")
            if len(partes) == 2:
                bucket_y_path = partes[1]
                bucket_name = bucket_y_path.split("/")[0]
                file_path = "/".join(bucket_y_path.split("/")[1:])
        # CASO B: Ruta relativa
        elif not url_str.startswith("http") and "." in url_str:
            file_path = url_str
        # CASO C: URL externa u otro formato
        else:
            return url_str
        if not file_path:
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
    return url_str

# ------------------------------------------------------------------------------
# FUNCIÓN: SUBIR IMAGEN A STORAGE Y RETORNAR URL COMPLETA
# ------------------------------------------------------------------------------
def subir_imagen_storage(archivo) -> str:
    """
    Sube una imagen al bucket 'imagenes' de Supabase Storage.
    Retorna la URL completa (pública) del archivo subido.
    Formato de nombre: img_AAAAMMDD_HHMMSS.ext
    """
    try:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = archivo.name.split(".")[-1].lower()
        nombre_archivo = f"img_{timestamp_str}.{ext}"
        file_bytes = archivo.getvalue()
        mime_type = archivo.type

        supabase.storage.from_(BUCKET_IMAGENES).upload(
            path=nombre_archivo,
            file=file_bytes,
            file_options={"content-type": mime_type}
        )

        # Retornar URL completa (pública) del archivo
        url_completa = str(supabase.storage.from_(BUCKET_IMAGENES).get_public_url(nombre_archivo))
        return url_completa
    except Exception as e:
        st.error(f"❌ Error crítico en Supabase Storage: {e}")
        return ""


# -----------------------------------------------------------------------------
# FUNCIÓN: ELIMINAR IMAGEN DE STORAGE DESDE URL COMPLETA
# -----------------------------------------------------------------------------
def eliminar_imagen_storage(url_imagen: str) -> bool:
    """
    Extrae el file_path desde una URL pública completa de Supabase Storage
    y elimina el objeto del bucket. Retorna True si no hay imagen, si se
    eliminó correctamente, o si ya no existía (not_found).
    """
    if not url_imagen or pd.isna(url_imagen):
        return True
    url_str = str(url_imagen).strip()
    supabase_url = st.secrets["supabase"]["url"]
    bucket_name = BUCKET_IMAGENES
    file_path = ""
    try:
        # CASO A: URL completa de Supabase Storage
        if supabase_url in url_str and "/storage/v1/object/public/" in url_str:
            partes = url_str.split("/storage/v1/object/public/")
            if len(partes) == 2:
                bucket_y_path = partes[1]
                bucket_name = bucket_y_path.split("/")[0]
                file_path = "/".join(bucket_y_path.split("/")[1:])
        # CASO B: Ruta relativa
        elif not url_str.startswith("http") and "." in url_str:
            file_path = url_str
        else:
            return True  # URL externa, no gestionada por este bucket
        if not file_path:
            return True
        supabase.storage.from_(bucket_name).remove([file_path])
        return True
    except Exception as e:
        err = str(e).lower()
        if "not found" in err or "not_found" in err or "notfound" in err or "does not exist" in err:
            return True  # Ya no existe, consideramos éxito
        st.warning(f"⚠️ No se pudo eliminar la imagen del storage: {e}")
        return False

# 4. CARGA DE DATOS EN MEMORIA
df_categorias = cargar_categorias()
df_subcategorias = cargar_subcategorias()
df_productos_raw = cargar_productos()

if df_productos_raw.empty:
    st.warning("⚠️ No se encontraron productos en la base de datos o la tabla está vacía.")
    st.stop()

# 5. ENRIQUECIMIENTO DEL DATASET
df = df_productos_raw.copy()

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

# MAPEOS PARA RECLASIFICACIÓN Y CREACIÓN
lista_categorias = sorted(df_categorias["nombre"].dropna().unique().tolist()) if not df_categorias.empty else []
mapa_cat_nombre_a_id = dict(zip(df_categorias["nombre"], df_categorias["id_cat"])) if not df_categorias.empty else {}
mapa_subcat_nombre_a_id = dict(zip(df_subcategorias["nombre"], df_subcategorias["id_subcat"])) if not df_subcategorias.empty else {}
mapa_subcat_a_cat_id = dict(zip(df_subcategorias["nombre"], df_subcategorias["id_cat"])) if not df_subcategorias.empty else {}

# ------------------------------------------------------------------------------
# 6. RESUMEN DEL CATÁLOGO
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

# ------------------------------------------------------------------------------
# 7. FILTROS DE BÚSQUEDA
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
        opciones_subcat = ["Todas"] + (sorted(df_subcategorias["nombre"].dropna().unique().tolist()) if not df_subcategorias.empty else [])
    filtro_subcat = st.selectbox("Subcategoría:", opciones_subcat, label_visibility="collapsed")

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

#if len(df_filtrado) != len(df):
    #st.info(f"📌 Mostrando **{len(df_filtrado)}** de **{len(df)}** productos según filtros aplicados.")

# ------------------------------------------------------------------------------
# 9. GRILLA DE VISUALIZACIÓN (SOLO LECTURA)
# ------------------------------------------------------------------------------
st.markdown(f"### 📋 Catálogo de Productos — `{len(df_filtrado)}` registros")

if df_filtrado.empty:
    st.info("💡 No hay productos que coincidan con los filtros seleccionados.")
else:
    if "url_imagen" in df_filtrado.columns:
        df_filtrado["url_imagen"] = df_filtrado["url_imagen"].apply(
            lambda x: firmar_url_imagen(x, 3600)
        )

    columnas_display = [
        "url_imagen", "id_producto", "codigo_barras", "nombre", "marca",
        "tamano", "unidad", "nombre_cat", "nombre_subcat",
        "es_favorito", "alta_demanda", "es_estrategico", "cod_verif",
    ]
    columnas_existentes = [c for c in columnas_display if c in df_filtrado.columns]
    df_display = df_filtrado[columnas_existentes].copy()

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
    df_display.rename(columns=renombres, inplace=True)

    if "ID" in df_display.columns:
        df_display = df_display.sort_values(by="ID", ascending=True).reset_index(drop=True)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        column_config={
            "Imagen": st.column_config.ImageColumn("Imagen", help="Vista previa firmada", width="small"),
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
        },
        hide_index=True
    )

    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name="grilla_productos.csv",
        mime="text/csv"
    )


# ==============================================================================
# 10. PANEL DE CREACIÓN DE NUEVO PRODUCTO
# ==============================================================================
st.markdown("### ➕ Crear Nuevo Producto")

with st.expander("Desplegar formulario de creación", expanded=False):

    col_cat_crear, col_subcat_crear = st.columns(2)
    with col_cat_crear:
        nueva_cat_crear = st.selectbox(
            "Categoría del nuevo producto:",
            lista_categorias,
            index=0,
            key="sel_cat_crear"
        )
    with col_subcat_crear:
        id_cat_crear = mapa_cat_nombre_a_id.get(nueva_cat_crear)
        subcats_crear = []
        if id_cat_crear is not None and not df_subcategorias.empty:
            subcats_crear = sorted(
                df_subcategorias[df_subcategorias["id_cat"] == id_cat_crear]["nombre"].dropna().unique().tolist()
            )
        if not subcats_crear:
            st.warning(f"⚠️ La categoría '{nueva_cat_crear}' no tiene subcategorías.")
        nueva_subcat_crear = st.selectbox(
            "Subcategoría:",
            subcats_crear if subcats_crear else ["— Sin subcategorías —"],
            disabled=not subcats_crear,
            key="sel_subcat_crear"
        )

    with st.form("form_crear_producto", clear_on_submit=True):
        st.markdown(f"**Categoría seleccionada:** {nueva_cat_crear} → **{nueva_subcat_crear if subcats_crear else '—'}**")

        col1, col2, col3 = st.columns(3)
        with col1:
            new_nombre = st.text_input("Nombre del Producto *", placeholder="Ej: Leche Entera 1L")
        with col2:
            new_marca = st.text_input("Marca", placeholder="Ej: Colun")
        with col3:
            new_codigo = st.text_input("Código de Barras", placeholder="Ej: 7800000001")

        col4, col5 = st.columns(2)
        with col4:
            new_tamano = st.number_input("Tamaño:", min_value=0.0, step=0.01, value=0.0)
        with col5:
            new_unidad = st.selectbox(
                "Unidad de medida:",
                ['gr', 'kg', 'ml', 'lt', 'unidad'],
                index=0,
                key="sel_unidad_crear"
            )

        col6, col7, col8, col9 = st.columns(4)
        with col6:
            new_fav = st.checkbox("⭐ Favorito", value=False)
        with col7:
            new_dem = st.checkbox("🔥 Alta Demanda", value=False)
        with col8:
            new_est = st.checkbox("🎯 Estratégico", value=False)
        with col9:
            new_verif = st.checkbox("✅ Cod. Verif.", value=False)

        st.markdown("---")

        col_img_up, col_img_prev = st.columns([2, 1])
        with col_img_up:
            archivo_imagen = st.file_uploader(
                "📎 Subir imagen del producto:",
                type=["png", "jpg", "jpeg", "webp", "gif"],
                help="Formatos soportados: PNG, JPG, JPEG, WEBP, GIF. Máx. 5MB recomendado."
            )
        with col_img_prev:
            if archivo_imagen is not None:
                st.image(archivo_imagen, caption="Vista previa", width=150)
            else:
                st.markdown("<div style='height:100px;display:flex;align-items:center;justify-content:center;color:#888;'>Sin imagen</div>", unsafe_allow_html=True)

        st.markdown("---")
        btn_crear = st.form_submit_button("💾 Guardar Nuevo Producto en la Nube", type="primary", use_container_width=True)

        if btn_crear:
            if not new_nombre.strip():
                st.error("❌ El nombre del producto es obligatorio.")
            elif not subcats_crear:
                st.error("❌ Debe seleccionar una categoría con subcategorías disponibles.")
            elif nueva_subcat_crear == "— Sin subcategorías —":
                st.error("❌ Debe seleccionar una subcategoría válida.")
            else:
                id_subcat_crear = mapa_subcat_nombre_a_id.get(nueva_subcat_crear)

                payload_insert = {
                    "nombre": new_nombre.strip(),
                    "id_cat": int(id_cat_crear),
                    "id_subcat": int(id_subcat_crear),
                    "marca": new_marca.strip() if new_marca.strip() else None,
                    "codigo_barras": new_codigo.strip() if new_codigo.strip() else None,
                    "tamano": new_tamano if new_tamano > 0 else None,
                    "unidad": new_unidad.strip() if new_unidad.strip() else None,
                    "es_favorito": new_fav,
                    "alta_demanda": new_dem,
                    "es_estrategico": new_est,
                    "cod_verif": new_verif,
                }

                try:
                    res_insert = supabase.table("productos").insert(payload_insert).execute()

                    if res_insert and hasattr(res_insert, 'data') and res_insert.data:
                        nuevo_id = res_insert.data[0]["id_producto"]
                        url_imagen_completa = None

                        if archivo_imagen is not None:
                            url_imagen_completa = subir_imagen_storage(archivo_imagen)
                            if url_imagen_completa:
                                supabase.table("productos").update({"url_imagen": url_imagen_completa}).eq("id_producto", nuevo_id).execute()

                        st.success(f"✅ Producto '{new_nombre}' creado exitosamente con ID {nuevo_id}.")
                        if url_imagen_completa:
                            st.info(f"🖼️ Imagen: {url_imagen_completa}")

                        cargar_productos.clear()
                        firmar_url_imagen.clear()
                        st.rerun()
                    else:
                        st.error("❌ No se pudo obtener el ID del producto creado.")

                except Exception as e:
                    error_msg = str(e)
                    if "duplicate key value violates unique constraint" in error_msg and "productos_codigo_barras_key" in error_msg:
                        st.error(f"❌ El código de barras '{new_codigo}' ya existe en otro producto. Usa uno diferente.")
                    else:
                        st.error(f"❌ Error al crear producto: {e}")

st.markdown("---")

# ==============================================================================
# 11. PANEL DE MODIFICACIÓN DE PRODUCTOS
# ==============================================================================
st.markdown("### ✏️ Modificación de Productos")
st.markdown("Selecciona un producto de la grilla superior para editar sus datos, reclasificarlo o actualizar su imagen.")

if not df_filtrado.empty:
    opciones_producto = {
        f"ID {row['id_producto']} — {row['nombre']} ({safe_str(row.get('marca'), '')})": row
        for _, row in df_filtrado.iterrows()
    }

    producto_sel_key = st.selectbox(
        "Seleccionar producto a modificar:",
        list(opciones_producto.keys()),
        index=None,
        placeholder="Elige un producto...",
        key="sel_producto"
    )

    if producto_sel_key:
        prod = opciones_producto[producto_sel_key]

        prod_nombre = safe_str(prod.get("nombre"), "")
        prod_marca = safe_str(prod.get("marca"), "")
        prod_codigo = safe_str(prod.get("codigo_barras"), "")
        prod_tamano = safe_float(prod.get("tamano"), 0.0)
        prod_unidad = safe_str(prod.get("unidad"), "")
        prod_fav = safe_bool(prod.get("es_favorito"), False)
        prod_dem = safe_bool(prod.get("alta_demanda"), False)
        prod_est = safe_bool(prod.get("es_estrategico"), False)
        prod_verif = safe_bool(prod.get("cod_verif"), False)
        prod_cat = safe_str(prod.get("nombre_cat"), lista_categorias[0] if lista_categorias else "")
        prod_subcat = safe_str(prod.get("nombre_subcat"), "")
        prod_id_cat = prod.get("id_cat")
        prod_id_subcat = prod.get("id_subcat")
        prod_url_imagen = safe_str(prod.get("url_imagen"), "")
        id_prod = int(prod["id_producto"])

        # Mostrar imagen actual firmada
        col_img, col_info = st.columns([1, 4])
        with col_img:
            if prod_url_imagen:
                st.image(firmar_url_imagen(prod_url_imagen, 3600), width=120)
            else:
                st.markdown("🖼️ *Sin imagen*")
        with col_info:
            st.markdown(f"**{prod_nombre}** | Marca: {prod_marca or '—'} | Código: {prod_codigo or '—'}")
            st.markdown(f"📂 Actual: **{prod_cat or '—'}** → **{prod_subcat or '—'}**")
            if prod_url_imagen:
                st.caption(f"🖼️ URL imagen: `{prod_url_imagen}`")

        st.markdown("---")

        # CATEGORÍA Y SUBCATEGORÍA FUERA DEL FORMULARIO (mismo nivel)
        st.markdown("#### Nueva Clasificación")

        col_cat_mod, col_subcat_mod = st.columns(2)
        with col_cat_mod:
            nueva_cat = st.selectbox(
                "Nueva Categoría:",
                lista_categorias,
                index=lista_categorias.index(prod_cat) if prod_cat in lista_categorias else 0,
                key="sel_nueva_cat"
            )
        with col_subcat_mod:
            id_cat_nueva = mapa_cat_nombre_a_id.get(nueva_cat)
            subcats_disponibles = []
            if id_cat_nueva is not None and not df_subcategorias.empty:
                subcats_disponibles = sorted(
                    df_subcategorias[df_subcategorias["id_cat"] == id_cat_nueva]["nombre"].dropna().unique().tolist()
                )
            if not subcats_disponibles:
                st.warning(f"⚠️ Sin subcategorías.")
            idx_subcat = subcats_disponibles.index(prod_subcat) if prod_subcat in subcats_disponibles else 0
            nueva_subcat = st.selectbox(
                "Nueva Subcategoría:",
                subcats_disponibles if subcats_disponibles else ["— Sin subcategorías —"],
                index=idx_subcat if subcats_disponibles else 0,
                disabled=not subcats_disponibles,
                key="sel_nueva_subcat"
            )

        # FORMULARIO DE MODIFICACIÓN CON ACTUALIZACIÓN DE IMAGEN
        with st.form("form_modificar_producto", clear_on_submit=False):
            st.markdown(f"**Clasificación seleccionada:** {nueva_cat} → **{nueva_subcat if subcats_disponibles else '—'}**")

            st.markdown("---")

            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                edit_nombre = st.text_input("Nombre:", value=prod_nombre)
            with col_e2:
                edit_marca = st.text_input("Marca:", value=prod_marca)
            with col_e3:
                edit_codigo = st.text_input("Código de Barras:", value=prod_codigo)

            col_e4, col_e5 = st.columns(2)
            with col_e4:
                edit_tamano = st.number_input("Tamaño:", value=prod_tamano, step=0.01)
            with col_e5:
                idx_unidad = ['gr', 'kg', 'ml', 'lt', 'unidad'].index(prod_unidad) if prod_unidad in ['gr', 'kg', 'ml', 'lt', 'unidad'] else 0
            edit_unidad = st.selectbox(
                "Unidad de medida:",
                ['gr', 'kg', 'ml', 'lt', 'unidad'],
                index=idx_unidad,
                key="sel_unidad_mod"
            )

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                edit_fav = st.checkbox("⭐ Favorito", value=prod_fav)
            with col_f2:
                edit_dem = st.checkbox("🔥 Alta Demanda", value=prod_dem)
            with col_f3:
                edit_est = st.checkbox("🎯 Estratégico", value=prod_est)
            with col_f4:
                edit_verif = st.checkbox("✅ Cod. Verif.", value=prod_verif)

            st.markdown("---")

            # ACTUALIZACIÓN DE IMAGEN
            st.markdown("#### 🖼️ Actualizar Imagen del Producto")
            col_img_up, col_img_prev = st.columns([2, 1])
            with col_img_up:
                nueva_imagen = st.file_uploader(
                    "📎 Subir nueva imagen (dejar vacío para mantener la actual):",
                    type=["png", "jpg", "jpeg", "webp", "gif"],
                    help="Si seleccionas una imagen, reemplazará la actual. Deja vacío para conservar la imagen existente."
                )
            with col_img_prev:
                if nueva_imagen is not None:
                    st.image(nueva_imagen, caption="Nueva imagen", width=150)
                else:
                    if prod_url_imagen:
                        st.image(firmar_url_imagen(prod_url_imagen, 3600), caption="Imagen actual", width=150)
                    else:
                        st.markdown("<div style='height:100px;display:flex;align-items:center;justify-content:center;color:#888;'>Sin imagen</div>", unsafe_allow_html=True)

            st.markdown("---")
            btn_guardar = st.form_submit_button("💾 Guardar Cambios en la Nube", type="primary", use_container_width=True)

            if btn_guardar:
                if not subcats_disponibles:
                    st.error("❌ No se puede guardar: la categoría seleccionada no tiene subcategorías.")
                else:
                    id_prod = int(prod["id_producto"])
                    campos_update = {}

                    id_cat_nueva_db = mapa_cat_nombre_a_id.get(nueva_cat)
                    id_subcat_nueva_db = mapa_subcat_nombre_a_id.get(nueva_subcat)

                    prod_id_cat_norm = None if (prod_id_cat is None or (isinstance(prod_id_cat, float) and np.isnan(prod_id_cat))) else int(prod_id_cat)
                    prod_id_subcat_norm = None if (prod_id_subcat is None or (isinstance(prod_id_subcat, float) and np.isnan(prod_id_subcat))) else int(prod_id_subcat)

                    if id_cat_nueva_db is not None and prod_id_cat_norm != id_cat_nueva_db:
                        campos_update["id_cat"] = int(id_cat_nueva_db)
                    if id_subcat_nueva_db is not None and prod_id_subcat_norm != id_subcat_nueva_db:
                        campos_update["id_subcat"] = int(id_subcat_nueva_db)

                    if edit_nombre.strip() != prod_nombre:
                        campos_update["nombre"] = edit_nombre.strip()
                    if edit_marca.strip() != prod_marca:
                        campos_update["marca"] = edit_marca.strip() if edit_marca.strip() else None
                    if edit_codigo.strip() != prod_codigo:
                        campos_update["codigo_barras"] = edit_codigo.strip() if edit_codigo.strip() else None
                    if edit_tamano != prod_tamano:
                        campos_update["tamano"] = edit_tamano
                    if edit_unidad.strip() != prod_unidad:
                        campos_update["unidad"] = edit_unidad.strip() if edit_unidad.strip() else None
                    if edit_fav != prod_fav:
                        campos_update["es_favorito"] = edit_fav
                    if edit_dem != prod_dem:
                        campos_update["alta_demanda"] = edit_dem
                    if edit_est != prod_est:
                        campos_update["es_estrategico"] = edit_est
                    if edit_verif != prod_verif:
                        campos_update["cod_verif"] = edit_verif

                    # SUBIR NUEVA IMAGEN SI SE SELECCIONÓ
                    if nueva_imagen is not None:
                        url_imagen_nueva = subir_imagen_storage(nueva_imagen)
                        if url_imagen_nueva:
                            campos_update["url_imagen"] = url_imagen_nueva
                        else:
                            st.warning("⚠️ Los datos del producto se guardaron, pero falló la carga de la nueva imagen.")

                    if campos_update:
                        try:
                            supabase.table("productos").update(campos_update).eq("id_producto", id_prod).execute()

                            msg_exito = f"✅ Producto ID {id_prod} actualizado correctamente."
                            if "url_imagen" in campos_update:
                                msg_exito += " 🖼️ Imagen actualizada."
                            st.success(msg_exito)

                            cargar_productos.clear()
                            firmar_url_imagen.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al actualizar: {e}")
                    else:
                        st.info("💡 No se detectaron cambios.")

        st.markdown("---")

        # ==============================================================================
        # 11.1 ZONA PELIGROSA — ELIMINACIÓN DE PRODUCTO
        # ==============================================================================
        st.markdown("### 🗑️ Eliminar Producto")
        with st.expander("⚠️ Zona peligrosa — Eliminar permanentemente", expanded=False):
            st.error(f"Estás a punto de eliminar el producto **'{prod_nombre}'** (ID `{id_prod}`). Esta acción no se puede deshacer.")
            if prod_url_imagen:
                st.info("🖼️ La imagen asociada también será eliminada del bucket de Storage.")
            else:
                st.info("ℹ️ Este producto no tiene imagen asociada en Storage.")

            confirmar_elim = st.checkbox(
                f"Sí, confirmo que deseo eliminar permanentemente el producto ID {id_prod}",
                key=f"chk_del_{id_prod}"
            )

            btn_eliminar = st.button(
                "🗑️ Eliminar Producto Permanentemente",
                type="secondary",
                disabled=not confirmar_elim,
                key=f"btn_del_{id_prod}"
            )

            if btn_eliminar and confirmar_elim:
                # Paso 1: Eliminar imagen de Storage (si existe)
                imagen_ok = eliminar_imagen_storage(prod_url_imagen)

                if not imagen_ok:
                    st.error("❌ No se pudo limpiar la imagen del Storage. Eliminación abortada para evitar archivos huérfanos.")
                else:
                    # Paso 2: Eliminar registro de la base de datos
                    try:
                        supabase.table("productos").delete().eq("id_producto", id_prod).execute()
                        st.success(f"✅ Producto ID {id_prod} eliminado correctamente.{' Imagen limpiada del Storage.' if prod_url_imagen else ''}")

                        cargar_productos.clear()
                        firmar_url_imagen.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al eliminar el producto de la base de datos: {e}")

else:
    st.info("No hay productos disponibles para modificar.")

st.markdown("---")
st.caption(f"🔒 Conexión segura a Supabase | Crear + Modificar + Eliminar (con limpieza de Storage) | v{VERSION_PROGRAMA}")
