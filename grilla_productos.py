# ==============================================================================
# PROGRAMA SATÉLITE: grilla_productos_v160.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.6.1
# DESCRIPCIÓN: Grilla de catálogo con reclasificación dinámica. La subcategoría
#              se filtra en tiempo real según la categoría seleccionada.
#              Imágenes firmadas, filtros en área principal, persistencia Supabase.
# REGLAS: Sin panel lateral | Versión en nombre de archivo | Sin filtros check
#         | URLs firmadas solo filtradas | Subcategoría dependiente de categoría
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ------------------------------------------------------------------------------
# CONSTANTES DE VERSIÓN
# ------------------------------------------------------------------------------
VERSION_PROGRAMA = "1.6.1"
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

st.title(f"📦 {NOMBRE_PROGRAMA}")
st.markdown(f"**Versión {VERSION_PROGRAMA}** — Reclasificación dinámica: subcategoría filtrada por categoría seleccionada.")
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

# MAPEOS PARA RECLASIFICACIÓN
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

st.markdown("---")

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
# 9. GRILLA DE VISUALIZACIÓN (SOLO LECTURA)
# ------------------------------------------------------------------------------
st.markdown(f"### 📋 Catálogo de Productos — `{len(df_filtrado)}` registros")

if df_filtrado.empty:
    st.info("💡 No hay productos que coincidan con los filtros seleccionados.")
else:
    # Firmar imágenes solo de filas filtradas
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

st.markdown("---")

# ------------------------------------------------------------------------------
# 10. PANEL DE RECLASIFICACIÓN DINÁMICA (CORREGIDO v1.6.1)
# ------------------------------------------------------------------------------
st.markdown("### ✏️ Reclasificar Producto")
st.markdown("Selecciona un producto de la grilla superior para editar su categoría y subcategoría. La lista de subcategorías se filtra automáticamente según la categoría elegida.")

if not df_filtrado.empty:
    opciones_producto = {
        f"ID {row['id_producto']} — {row['nombre']} ({row.get('marca','')})": row
        for _, row in df_filtrado.iterrows()
    }

    producto_sel_key = st.selectbox(
        "Seleccionar producto a reclasificar:",
        list(opciones_producto.keys()),
        index=None,
        placeholder="Elige un producto...",
        key="sel_producto"
    )

    if producto_sel_key:
        prod = opciones_producto[producto_sel_key]

        # Mostrar datos actuales
        col_img, col_info = st.columns([1, 4])
        with col_img:
            if prod.get("url_imagen"):
                st.image(firmar_url_imagen(prod["url_imagen"], 3600), width=120)
            else:
                st.markdown("🖼️ *Sin imagen*")
        with col_info:
            st.markdown(f"**{prod['nombre']}** | Marca: {prod.get('marca','—')} | Código: {prod.get('codigo_barras','—')}")
            st.markdown(f"📂 Actual: **{prod.get('nombre_cat','—')}** → **{prod.get('nombre_subcat','—')}**")

        st.markdown("---")

        # ----------------------------------------------------------------------
        # CATEGORÍA FUERA DEL FORMULARIO (para que Streamlit recalcule subcats)
        # ----------------------------------------------------------------------
        st.markdown("#### Nueva Clasificación")

        cat_actual = prod.get("nombre_cat", lista_categorias[0] if lista_categorias else "")
        nueva_cat = st.selectbox(
            "Nueva Categoría:",
            lista_categorias,
            index=lista_categorias.index(cat_actual) if cat_actual in lista_categorias else 0,
            key="sel_nueva_cat"
        )

        # Calcular subcategorías disponibles según la categoría seleccionada
        id_cat_nueva = mapa_cat_nombre_a_id.get(nueva_cat)
        subcats_disponibles = []
        if id_cat_nueva is not None and not df_subcategorias.empty:
            subcats_disponibles = sorted(
                df_subcategorias[df_subcategorias["id_cat"] == id_cat_nueva]["nombre"].dropna().unique().tolist()
            )

        # Si no hay subcategorías para esta categoría, mostrar advertencia
        if not subcats_disponibles:
            st.warning(f"⚠️ La categoría '{nueva_cat}' no tiene subcategorías registradas.")

        # ----------------------------------------------------------------------
        # FORMULARIO CON SUBCATEGORÍA YA FILTRADA
        # ----------------------------------------------------------------------
        with st.form("form_reclasificar", clear_on_submit=False):
            col_c1, col_c2 = st.columns(2)

            with col_c1:
                st.markdown(f"**Categoría:** {nueva_cat}")

            with col_c2:
                subcat_actual = prod.get("nombre_subcat", "")
                # Si la subcategoría actual no está en la lista filtrada, seleccionar la primera
                idx_subcat = subcats_disponibles.index(subcat_actual) if subcat_actual in subcats_disponibles else 0

                nueva_subcat = st.selectbox(
                    "Nueva Subcategoría:",
                    subcats_disponibles if subcats_disponibles else ["— Sin subcategorías —"],
                    index=idx_subcat if subcats_disponibles else 0,
                    disabled=not subcats_disponibles
                )

            st.markdown("---")

            # Otros campos editables
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                edit_nombre = st.text_input("Nombre:", value=prod.get("nombre", ""))
            with col_e2:
                edit_marca = st.text_input("Marca:", value=prod.get("marca", "") or "")
            with col_e3:
                edit_codigo = st.text_input("Código de Barras:", value=prod.get("codigo_barras", "") or "")

            col_e4, col_e5 = st.columns(2)
            with col_e4:
                edit_tamano = st.number_input("Tamaño:", value=float(prod.get("tamano", 0) or 0), step=0.01)
            with col_e5:
                edit_unidad = st.text_input("Unidad:", value=prod.get("unidad", "") or "")

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                edit_fav = st.checkbox("⭐ Favorito", value=bool(prod.get("es_favorito", False)))
            with col_f2:
                edit_dem = st.checkbox("🔥 Alta Demanda", value=bool(prod.get("alta_demanda", False)))
            with col_f3:
                edit_est = st.checkbox("🎯 Estratégico", value=bool(prod.get("es_estrategico", False)))
            with col_f4:
                edit_verif = st.checkbox("✅ Cod. Verif.", value=bool(prod.get("cod_verif", False)))

            st.markdown("---")
            btn_guardar = st.form_submit_button("💾 Guardar Cambios en la Nube", type="primary", use_container_width=True)

            if btn_guardar:
                if not subcats_disponibles:
                    st.error("❌ No se puede guardar: la categoría seleccionada no tiene subcategorías.")
                else:
                    id_prod = int(prod["id_producto"])
                    campos_update = {}

                    # Reclasificación
                    id_cat_nueva_db = mapa_cat_nombre_a_id.get(nueva_cat)
                    id_subcat_nueva_db = mapa_subcat_nombre_a_id.get(nueva_subcat)

                    if id_cat_nueva_db is not None and prod.get("id_cat") != id_cat_nueva_db:
                        campos_update["id_cat"] = int(id_cat_nueva_db)
                    if id_subcat_nueva_db is not None and prod.get("id_subcat") != id_subcat_nueva_db:
                        campos_update["id_subcat"] = int(id_subcat_nueva_db)

                    # Otros campos
                    if edit_nombre != prod.get("nombre", ""):
                        campos_update["nombre"] = edit_nombre.strip()
                    if edit_marca != (prod.get("marca") or ""):
                        campos_update["marca"] = edit_marca.strip() if edit_marca else None
                    if edit_codigo != (prod.get("codigo_barras") or ""):
                        campos_update["codigo_barras"] = edit_codigo.strip() if edit_codigo else None
                    if edit_tamano != float(prod.get("tamano") or 0):
                        campos_update["tamano"] = edit_tamano
                    if edit_unidad != (prod.get("unidad") or ""):
                        campos_update["unidad"] = edit_unidad.strip() if edit_unidad else None
                    if edit_fav != bool(prod.get("es_favorito", False)):
                        campos_update["es_favorito"] = edit_fav
                    if edit_dem != bool(prod.get("alta_demanda", False)):
                        campos_update["alta_demanda"] = edit_dem
                    if edit_est != bool(prod.get("es_estrategico", False)):
                        campos_update["es_estrategico"] = edit_est
                    if edit_verif != bool(prod.get("cod_verif", False)):
                        campos_update["cod_verif"] = edit_verif

                    if campos_update:
                        try:
                            supabase.table("productos").update(campos_update).eq("id_producto", id_prod).execute()
                            st.success(f"✅ Producto ID {id_prod} actualizado correctamente.")
                            cargar_productos.clear()
                            firmar_url_imagen.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al actualizar: {e}")
                    else:
                        st.info("💡 No se detectaron cambios.")
else:
    st.info("No hay productos disponibles para reclasificar.")

st.markdown("---")
st.caption(f"🔒 Conexión segura a Supabase | Reclasificación dinámica corregida | Imágenes firmadas | v{VERSION_PROGRAMA}")
