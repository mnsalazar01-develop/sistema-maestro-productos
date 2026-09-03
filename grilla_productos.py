# ==============================================================================
# PROGRAMA SATÉLITE: grilla_productos_v200.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 2.0
# DESCRIPCIÓN: Grilla compacta + panel de acciones unificado.
#              Edición inline, Duplicar/Eliminar en modal.
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
VERSION_PROGRAMA = "2.0"
NOMBRE_PROGRAMA = "Grilla de Productos"
BUCKET_IMAGENES = "imagenes"
UNIDADES = ["gr", "kg", "ml", "lt", "unidad"]

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

# Inicializar estado de edición inline
if "modo_edicion" not in st.session_state:
    st.session_state["modo_edicion"] = False
if "prod_id_edicion" not in st.session_state:
    st.session_state["prod_id_edicion"] = None

st.title(f"📦 {NOMBRE_PROGRAMA}")
st.markdown(f"**Versión {VERSION_PROGRAMA}** — Edición inline + acciones en modal.")

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

# ------------------------------------------------------------------------------
# 3. FUNCIONES AUXILIARES DE CARGA DE DATOS MAESTROS
# ------------------------------------------------------------------------------
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

# 3.1 FUNCIÓN PARA FIRMAR URL DE IMAGEN
@st.cache_data(ttl=3600)
def firmar_url_imagen(url_imagen: str, duracion_segundos: int = 3600) -> str:
    if not url_imagen or pd.isna(url_imagen):
        return ""
    url_str = str(url_imagen).strip()
    supabase_url = st.secrets["supabase"]["url"]
    bucket_name = BUCKET_IMAGENES
    file_path = ""
    try:
        if supabase_url in url_str and "/storage/v1/object/public/" in url_str:
            partes = url_str.split("/storage/v1/object/public/")
            if len(partes) == 2:
                bucket_y_path = partes[1]
                bucket_name = bucket_y_path.split("/")[0]
                file_path = "/".join(bucket_y_path.split("/")[1:])
        elif not url_str.startswith("http") and "." in url_str:
            file_path = url_str
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
        url_completa = str(supabase.storage.from_(BUCKET_IMAGENES).get_public_url(nombre_archivo))
        return url_completa
    except Exception as e:
        st.error(f"❌ Error crítico en Supabase Storage: {e}")
        return ""

# ------------------------------------------------------------------------------
# FUNCIÓN: ELIMINAR IMAGEN DE STORAGE DESDE URL COMPLETA
# ------------------------------------------------------------------------------
def eliminar_imagen_storage(url_imagen: str) -> bool:
    if not url_imagen or pd.isna(url_imagen):
        return True
    url_str = str(url_imagen).strip()
    supabase_url = st.secrets["supabase"]["url"]
    bucket_name = BUCKET_IMAGENES
    file_path = ""
    try:
        if supabase_url in url_str and "/storage/v1/object/public/" in url_str:
            partes = url_str.split("/storage/v1/object/public/")
            if len(partes) == 2:
                bucket_y_path = partes[1]
                bucket_name = bucket_y_path.split("/")[0]
                file_path = "/".join(bucket_y_path.split("/")[1:])
        elif not url_str.startswith("http") and "." in url_str:
            file_path = url_str
        else:
            return True
        if not file_path:
            return True
        supabase.storage.from_(bucket_name).remove([file_path])
        return True
    except Exception as e:
        err = str(e).lower()
        if "not found" in err or "not_found" in err or "notfound" in err or "does not exist" in err:
            return True
        st.warning(f"⚠️ No se pudo eliminar la imagen del storage: {e}")
        return False

# ==============================================================================
# DIALOGS: DUPLICAR Y ELIMINAR
# ==============================================================================

@st.dialog("📋 Duplicar Producto", width="large")
def dialog_duplicar_producto(prod: dict, df_cats: pd.DataFrame, df_subcats: pd.DataFrame,
                             mapa_cat_nombre_a_id: dict, mapa_subcat_nombre_a_id: dict):
    prod_nombre = safe_str(prod.get("nombre"), "")
    prod_marca = safe_str(prod.get("marca"), "")
    prod_tamano = safe_float(prod.get("tamano"), 0.0)
    prod_unidad = safe_str(prod.get("unidad"), "")
    prod_fav = safe_bool(prod.get("es_favorito"), False)
    prod_dem = safe_bool(prod.get("alta_demanda"), False)
    prod_est = safe_bool(prod.get("es_estrategico"), False)
    prod_verif = safe_bool(prod.get("cod_verif"), False)
    prod_cat = safe_str(prod.get("nombre_cat"), "")
    prod_subcat = safe_str(prod.get("nombre_subcat"), "")
    prod_url_imagen = safe_str(prod.get("url_imagen"), "")

    lista_categorias = sorted(df_cats["nombre"].dropna().unique().tolist()) if not df_cats.empty else []

    st.markdown(f"**Duplicando:** {prod_nombre}")
    st.markdown("---")

    col_cat, col_subcat = st.columns(2)
    with col_cat:
        dup_cat = st.selectbox(
            "Categoría:",
            lista_categorias,
            index=lista_categorias.index(prod_cat) if prod_cat in lista_categorias else 0,
            key=f"dlg_dup_cat_{prod_nombre[:10]}"
        )
    with col_subcat:
        id_cat_sel = mapa_cat_nombre_a_id.get(dup_cat)
        subcats_disp = []
        if id_cat_sel is not None and not df_subcats.empty:
            subcats_disp = sorted(df_subcats[df_subcats["id_cat"] == id_cat_sel]["nombre"].dropna().unique().tolist())
        idx_sub = subcats_disp.index(prod_subcat) if prod_subcat in subcats_disp else 0
        dup_subcat = st.selectbox(
            "Subcategoría:",
            subcats_disp if subcats_disp else ["— Sin subcategorías —"],
            index=idx_sub if subcats_disp else 0,
            disabled=not subcats_disp,
            key=f"dlg_dup_subcat_{prod_nombre[:10]}"
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        dup_nombre = st.text_input("Nombre del Producto *", value=f"{prod_nombre}", key=f"dlg_dup_nom_{prod_nombre[:10]}")
    with col2:
        dup_marca = st.text_input("Marca:", value=prod_marca, key=f"dlg_dup_mar_{prod_nombre[:10]}")
    with col3:
        dup_codigo = st.text_input("Código de Barras:", value="", placeholder="Dejar vacío si no aplica", key=f"dlg_dup_cod_{prod_nombre[:10]}")

    col4, col5 = st.columns(2)
    with col4:
        dup_tamano = st.number_input("Tamaño:", min_value=0.0, step=0.01, value=prod_tamano, key=f"dlg_dup_tam_{prod_nombre[:10]}")
    with col5:
        idx_unidad = UNIDADES.index(prod_unidad) if prod_unidad in UNIDADES else 0
        dup_unidad = st.selectbox(
            "Unidad de medida:",
            UNIDADES,
            index=idx_unidad,
            key=f"dlg_dup_uni_{prod_nombre[:10]}"
        )

    col6, col7, col8, col9 = st.columns(4)
    with col6:
        dup_fav = st.checkbox("⭐ Favorito", value=prod_fav, key=f"dlg_dup_fav_{prod_nombre[:10]}")
    with col7:
        dup_dem = st.checkbox("🔥 Alta Demanda", value=prod_dem, key=f"dlg_dup_dem_{prod_nombre[:10]}")
    with col8:
        dup_est = st.checkbox("🎯 Estratégico", value=prod_est, key=f"dlg_dup_est_{prod_nombre[:10]}")
    with col9:
        dup_verif = st.checkbox("✅ Cod. Verif.", value=prod_verif, key=f"dlg_dup_ver_{prod_nombre[:10]}")

    st.markdown("---")
    st.markdown("#### 🖼️ Imagen del Producto")
    col_img_prev, col_img_up = st.columns([1, 2])
    with col_img_prev:
        if prod_url_imagen:
            st.image(firmar_url_imagen(prod_url_imagen, 3600), width=120)
        else:
            st.markdown("*Sin imagen*")
    with col_img_up:
        usar_misma = st.checkbox("Reutilizar imagen actual", value=True, key=f"dlg_dup_sameimg_{prod_nombre[:10]}")
        dup_archivo = None
        if not usar_misma:
            dup_archivo = st.file_uploader(
                "Subir nueva imagen:",
                type=["png", "jpg", "jpeg", "webp", "gif"],
                key=f"dlg_dup_img_{prod_nombre[:10]}"
            )

    st.markdown("---")
    if st.button("💾 Crear Copia", type="primary", use_container_width=True, key=f"dlg_dup_btn_{prod_nombre[:10]}"):
        if not dup_nombre.strip():
            st.error("❌ El nombre es obligatorio.")
            return
        if not subcats_disp:
            st.error("❌ La categoría seleccionada no tiene subcategorías.")
            return
        if dup_subcat == "— Sin subcategorías —":
            st.error("❌ Selecciona una subcategoría válida.")
            return

        id_subcat_db = mapa_subcat_nombre_a_id.get(dup_subcat)
        id_cat_db = mapa_cat_nombre_a_id.get(dup_cat)

        payload = {
            "nombre": dup_nombre.strip(),
            "id_cat": int(id_cat_db),
            "id_subcat": int(id_subcat_db),
            "marca": dup_marca.strip() if dup_marca.strip() else None,
            "codigo_barras": dup_codigo.strip() if dup_codigo.strip() else None,
            "tamano": dup_tamano if dup_tamano > 0 else None,
            "unidad": dup_unidad if dup_unidad else None,
            "es_favorito": dup_fav,
            "alta_demanda": dup_dem,
            "es_estrategico": dup_est,
            "cod_verif": dup_verif,
        }

        try:
            res = supabase.table("productos").insert(payload).execute()
            if res and hasattr(res, 'data') and res.data:
                nuevo_id = res.data[0]["id_producto"]
                url_img = None
                if usar_misma and prod_url_imagen:
                    url_img = prod_url_imagen
                    supabase.table("productos").update({"url_imagen": url_img}).eq("id_producto", nuevo_id).execute()
                elif dup_archivo is not None:
                    url_img = subir_imagen_storage(dup_archivo)
                    if url_img:
                        supabase.table("productos").update({"url_imagen": url_img}).eq("id_producto", nuevo_id).execute()

                st.success(f"✅ Copia creada con ID {nuevo_id}: '{dup_nombre}'")
                cargar_productos.clear()
                firmar_url_imagen.clear()
                st.rerun()
            else:
                st.error("❌ No se pudo obtener el ID de la copia.")
        except Exception as e:
            err = str(e)
            if "duplicate key value violates unique constraint" in err and "productos_codigo_barras_key" in err:
                st.error(f"❌ El código de barras '{dup_codigo}' ya existe. Usa uno diferente o déjalo vacío.")
            else:
                st.error(f"❌ Error al crear copia: {e}")


@st.dialog("🗑️ Eliminar Producto", width="small")
def dialog_eliminar_producto(prod: dict):
    prod_id = int(prod["id_producto"])
    prod_nombre = safe_str(prod.get("nombre"), "")
    prod_url_imagen = safe_str(prod.get("url_imagen"), "")

    st.error(f"⚠️ ¿Eliminar permanentemente **'{prod_nombre}'** (ID `{prod_id}`)?")
    st.markdown("Esta acción no se puede deshacer.")
    if prod_url_imagen:
        st.info("🖼️ La imagen asociada también será eliminada del Storage.")

    confirmar = st.checkbox("Sí, confirmo la eliminación permanente", key=f"dlg_del_conf_{prod_id}")

    if st.button("🗑️ Eliminar Permanentemente", type="secondary", disabled=not confirmar,
                 use_container_width=True, key=f"dlg_del_btn_{prod_id}"):
        imagen_ok = eliminar_imagen_storage(prod_url_imagen)
        if not imagen_ok:
            st.error("❌ No se pudo limpiar la imagen del Storage. Eliminación abortada.")
            return
        try:
            supabase.table("productos").delete().eq("id_producto", prod_id).execute()
            st.success(f"✅ Producto ID {prod_id} eliminado.{' Imagen limpiada.' if prod_url_imagen else ''}")
            cargar_productos.clear()
            firmar_url_imagen.clear()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al eliminar: {e}")


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

# MAPEOS
lista_categorias = sorted(df_categorias["nombre"].dropna().unique().tolist()) if not df_categorias.empty else []
mapa_cat_nombre_a_id = dict(zip(df_categorias["nombre"], df_categorias["id_cat"])) if not df_categorias.empty else {}
mapa_subcat_nombre_a_id = dict(zip(df_subcategorias["nombre"], df_subcategorias["id_subcat"])) if not df_subcategorias.empty else {}

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

# ==============================================================================
# 10. PANEL DE ACCIONES (selectbox ancho completo + botones debajo)
# ==============================================================================

if df_filtrado.empty:
    st.info("💡 No hay productos que coincidan con los filtros seleccionados.")
    prod_sel = None
else:
    listado_filtrado = df_filtrado.to_dict("records")

    def formateador_desambiguado(x):
        marca_lbl = x.get('marca') or 'Sin Marca'
        tamano_lbl = float(x.get('tamano')) if x.get('tamano') else 0.0
        unidad_lbl = x.get('unidad') or ''
        sku_lbl = x.get('codigo_barras') or 'SIN SKU'
        return f"{x['nombre']} | {marca_lbl} ({tamano_lbl} {unidad_lbl}) [{sku_lbl}]"

    with st.container(border=True):
        prod_sel = st.selectbox(
            "Seleccione la presentación exacta:",
            listado_filtrado,
            format_func=formateador_desambiguado,
            index=None,
            placeholder="🔍 Elige un producto para acciones...",
            key="m_sel"
        )

        if prod_sel is not None:
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("✏️ Modificar", type="primary", use_container_width=True, key="btn_modificar_v2"):
                    st.session_state["modo_edicion"] = True
                    st.session_state["prod_id_edicion"] = int(prod_sel["id_producto"])
                    st.rerun()
            with col_btn2:
                if st.button("📋 Duplicar", use_container_width=True, key="btn_duplicar_v2"):
                    dialog_duplicar_producto(prod_sel, df_categorias, df_subcategorias,
                                             mapa_cat_nombre_a_id, mapa_subcat_nombre_a_id)
            with col_btn3:
                if st.button("🗑️ Eliminar", use_container_width=True, key="btn_eliminar_v2"):
                    dialog_eliminar_producto(prod_sel)

    # ==============================================================================
    # 10.1 FORMULARIO DE EDICIÓN INLINE
    # ==============================================================================
    if st.session_state.get("modo_edicion") and st.session_state.get("prod_id_edicion"):
        prod_id_edit = st.session_state["prod_id_edicion"]

        prod_edit = None
        for p in listado_filtrado:
            if int(p["id_producto"]) == prod_id_edit:
                prod_edit = p
                break

        if prod_edit is not None:
            st.markdown("---")
            st.markdown("### ✏️ Editar Producto")

            with st.container(border=True):
                prod_nombre = safe_str(prod_edit.get("nombre"), "")
                prod_marca = safe_str(prod_edit.get("marca"), "")
                prod_codigo = safe_str(prod_edit.get("codigo_barras"), "")
                prod_tamano = safe_float(prod_edit.get("tamano"), 0.0)
                prod_unidad = safe_str(prod_edit.get("unidad"), "")
                prod_fav = safe_bool(prod_edit.get("es_favorito"), False)
                prod_dem = safe_bool(prod_edit.get("alta_demanda"), False)
                prod_est = safe_bool(prod_edit.get("es_estrategico"), False)
                prod_verif = safe_bool(prod_edit.get("cod_verif"), False)
                prod_cat = safe_str(prod_edit.get("nombre_cat"), "")
                prod_subcat = safe_str(prod_edit.get("nombre_subcat"), "")
                prod_id_cat = prod_edit.get("id_cat")
                prod_id_subcat = prod_edit.get("id_subcat")
                prod_url_imagen = safe_str(prod_edit.get("url_imagen"), "")

                st.markdown(f"**Editando:** {prod_nombre} (ID `{prod_id_edit}`)")
                st.markdown("---")

                col_cat, col_subcat = st.columns(2)
                with col_cat:
                    edit_cat = st.selectbox(
                        "Categoría:",
                        lista_categorias,
                        index=lista_categorias.index(prod_cat) if prod_cat in lista_categorias else 0,
                        key=f"inline_edit_cat_{prod_id_edit}"
                    )
                with col_subcat:
                    id_cat_sel = mapa_cat_nombre_a_id.get(edit_cat)
                    subcats_disp = []
                    if id_cat_sel is not None and not df_subcategorias.empty:
                        subcats_disp = sorted(df_subcategorias[df_subcategorias["id_cat"] == id_cat_sel]["nombre"].dropna().unique().tolist())
                    idx_sub = subcats_disp.index(prod_subcat) if prod_subcat in subcats_disp else 0
                    edit_subcat = st.selectbox(
                        "Subcategoría:",
                        subcats_disp if subcats_disp else ["— Sin subcategorías —"],
                        index=idx_sub if subcats_disp else 0,
                        disabled=not subcats_disp,
                        key=f"inline_edit_subcat_{prod_id_edit}"
                    )

                st.markdown("---")

                col1, col2, col3 = st.columns(3)
                with col1:
                    edit_nombre = st.text_input("Nombre:", value=prod_nombre, key=f"inline_edit_nom_{prod_id_edit}")
                with col2:
                    edit_marca = st.text_input("Marca:", value=prod_marca, key=f"inline_edit_mar_{prod_id_edit}")
                with col3:
                    edit_codigo = st.text_input("Código de Barras:", value=prod_codigo, key=f"inline_edit_cod_{prod_id_edit}")

                col4, col5 = st.columns(2)
                with col4:
                    edit_tamano = st.number_input("Tamaño:", value=prod_tamano, step=0.01, key=f"inline_edit_tam_{prod_id_edit}")
                with col5:
                    idx_unidad = UNIDADES.index(prod_unidad) if prod_unidad in UNIDADES else 0
                    edit_unidad = st.selectbox(
                        "Unidad de medida:",
                        UNIDADES,
                        index=idx_unidad,
                        key=f"inline_edit_uni_{prod_id_edit}"
                    )

                col6, col7, col8, col9 = st.columns(4)
                with col6:
                    edit_fav = st.checkbox("⭐ Favorito", value=prod_fav, key=f"inline_edit_fav_{prod_id_edit}")
                with col7:
                    edit_dem = st.checkbox("🔥 Alta Demanda", value=prod_dem, key=f"inline_edit_dem_{prod_id_edit}")
                with col8:
                    edit_est = st.checkbox("🎯 Estratégico", value=prod_est, key=f"inline_edit_est_{prod_id_edit}")
                with col9:
                    edit_verif = st.checkbox("✅ Cod. Verif.", value=prod_verif, key=f"inline_edit_ver_{prod_id_edit}")

                st.markdown("---")
                st.markdown("#### 🖼️ Imagen del Producto")
                col_img_prev, col_img_up = st.columns([1, 2])
                with col_img_prev:
                    if prod_url_imagen:
                        st.image(firmar_url_imagen(prod_url_imagen, 3600), width=120)
                    else:
                        st.markdown("*Sin imagen*")
                with col_img_up:
                    cambiar_img = st.checkbox("Cambiar imagen", value=False, key=f"inline_edit_chgimg_{prod_id_edit}")
                    nueva_imagen = None
                    if cambiar_img:
                        nueva_imagen = st.file_uploader(
                            "Subir nueva imagen:",
                            type=["png", "jpg", "jpeg", "webp", "gif"],
                            key=f"inline_edit_img_{prod_id_edit}"
                        )

                st.markdown("---")
                col_guardar, col_cancelar = st.columns(2)
                with col_guardar:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key=f"inline_edit_save_{prod_id_edit}"):
                        if not subcats_disp:
                            st.error("❌ La categoría seleccionada no tiene subcategorías.")
                        else:
                            campos_update = {}
                            id_cat_db = mapa_cat_nombre_a_id.get(edit_cat)
                            id_subcat_db = mapa_subcat_nombre_a_id.get(edit_subcat)
                            prod_id_cat_norm = None if (prod_id_cat is None or (isinstance(prod_id_cat, float) and np.isnan(prod_id_cat))) else int(prod_id_cat)
                            prod_id_subcat_norm = None if (prod_id_subcat is None or (isinstance(prod_id_subcat, float) and np.isnan(prod_id_subcat))) else int(prod_id_subcat)

                            if id_cat_db is not None and prod_id_cat_norm != id_cat_db:
                                campos_update["id_cat"] = int(id_cat_db)
                            if id_subcat_db is not None and prod_id_subcat_norm != id_subcat_db:
                                campos_update["id_subcat"] = int(id_subcat_db)
                            if edit_nombre.strip() != prod_nombre:
                                campos_update["nombre"] = edit_nombre.strip()
                            if edit_marca.strip() != prod_marca:
                                campos_update["marca"] = edit_marca.strip() if edit_marca.strip() else None
                            if edit_codigo.strip() != prod_codigo:
                                campos_update["codigo_barras"] = edit_codigo.strip() if edit_codigo.strip() else None
                            if edit_tamano != prod_tamano:
                                campos_update["tamano"] = edit_tamano
                            if edit_unidad != prod_unidad:
                                campos_update["unidad"] = edit_unidad if edit_unidad else None
                            if edit_fav != prod_fav:
                                campos_update["es_favorito"] = edit_fav
                            if edit_dem != prod_dem:
                                campos_update["alta_demanda"] = edit_dem
                            if edit_est != prod_est:
                                campos_update["es_estrategico"] = edit_est
                            if edit_verif != prod_verif:
                                campos_update["cod_verif"] = edit_verif

                            if cambiar_img and nueva_imagen is not None:
                                url_img_nueva = subir_imagen_storage(nueva_imagen)
                                if url_img_nueva:
                                    campos_update["url_imagen"] = url_img_nueva
                                else:
                                    st.warning("⚠️ Falló la carga de la nueva imagen. Los demás cambios se guardarán.")

                            if campos_update:
                                try:
                                    supabase.table("productos").update(campos_update).eq("id_producto", prod_id_edit).execute()
                                    st.success("✅ Producto actualizado correctamente.")
                                    st.session_state["modo_edicion"] = False
                                    st.session_state["prod_id_edicion"] = None
                                    cargar_productos.clear()
                                    firmar_url_imagen.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al actualizar: {e}")
                            else:
                                st.info("💡 No se detectaron cambios.")

                with col_cancelar:
                    if st.button("❌ Cancelar", use_container_width=True, key=f"inline_edit_cancel_{prod_id_edit}"):
                        st.session_state["modo_edicion"] = False
                        st.session_state["prod_id_edicion"] = None
                        st.rerun()
        else:
            st.warning("⚠️ El producto seleccionado ya no está disponible en los filtros actuales.")
            st.session_state["modo_edicion"] = False
            st.session_state["prod_id_edicion"] = None

    # ==============================================================================
    # 10.2 GRILLA
    # ==============================================================================
    st.markdown(f"### 📋 Catálogo — `{len(df_filtrado)}` registros")

    if "url_imagen" in df_filtrado.columns:
        df_filtrado["url_imagen"] = df_filtrado["url_imagen"].apply(
            lambda x: firmar_url_imagen(x, 3600)
        )

    columnas_display = [
        "url_imagen", "id_producto", "nombre", "marca",
        "tamano", "unidad", "nombre_cat", "nombre_subcat",
        "es_favorito", "alta_demanda", "es_estrategico", "cod_verif",
    ]
    columnas_existentes = [c for c in columnas_display if c in df_filtrado.columns]
    df_display = df_filtrado[columnas_existentes].copy()

    renombres = {
        "url_imagen": "Imagen",
        "id_producto": "ID",
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
        height=400,
        column_config={
            "Imagen": st.column_config.ImageColumn("Imagen", help="Vista previa firmada", width="small"),
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Nombre del Producto": st.column_config.TextColumn("Nombre del Producto", width="medium"),
            "Marca": st.column_config.TextColumn("Marca", width="small"),
            "Tamaño": st.column_config.NumberColumn("Tamaño", format="%.2f", width="small"),
            "Unidad": st.column_config.TextColumn("Unidad", width="small"),
            "Categoría": st.column_config.TextColumn("Categoría", width="small"),
            "Subcategoría": st.column_config.TextColumn("Subcategoría", width="small"),
            "⭐ Fav": st.column_config.TextColumn("⭐ Fav", width="small"),
            "🔥 Dem": st.column_config.TextColumn("🔥 Dem", width="small"),
            "🎯 Est": st.column_config.TextColumn("🎯 Est", width="small"),
            "✅ Verif": st.column_config.TextColumn("✅ Verif", width="small"),
        },
        hide_index=True
    )

# ==============================================================================
# 9. CREAR NUEVO PRODUCTO (PROMINENTE, ARRIBA)
# ==============================================================================
with st.expander("➕ Crear Nuevo Producto", expanded=False):

    col_cat_crear, col_subcat_crear = st.columns(2)
    with col_cat_crear:
        nueva_cat_crear = st.selectbox(
            "Categoría:",
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
                UNIDADES,
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
