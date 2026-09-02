import streamlit as st
from streamlit_sortables import sort_items
from supabase import create_client, Client

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
st.set_page_config(layout="wide", page_title="Maquetador Profesional de Ofertas")
st.title("🎨 Maquetador Drag & Drop — 100% Operativo")

# ==============================================================================
# 1. SUPABASE
# ==============================================================================
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

# ==============================================================================
# 2. ESTADOS
# ==============================================================================
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = 1
if "config_paginas" not in st.session_state:
    st.session_state.config_paginas = {}

# ==============================================================================
# 3. CAMPANAS (PAGINACIÓN BYPASS 1000)
# ==============================================================================
try:
    ids_campanas_con_ofertas = []
    limite_bloque = 1000
    offset = 0
    con_datos = True

    while con_datos:
        resp_bloque = supabase.table("ofertas")\
            .select("id_campana")\
            .range(offset, offset + limite_bloque - 1)\
            .execute()
        datos_bloque = resp_bloque.data
        if datos_bloque:
            ids_campanas_con_ofertas.extend([o["id_campana"] for o in datos_bloque if o.get("id_campana") is not None])
            offset += limite_bloque
            if len(datos_bloque) < limite_bloque:
                con_datos = False
        else:
            con_datos = False

    ids_campanas_con_ofertas = list(set(ids_campanas_con_ofertas))

    if not ids_campanas_con_ofertas:
        st.warning("⚠️ No hay campañas con ofertas registradas.")
        st.stop()

    resp_campanas = supabase.table("campanas")\
        .select("id_campana, nombre_campana")\
        .in_("id_campana", ids_campanas_con_ofertas)\
        .order("id_campana", desc=True)\
        .execute()
    lista_campanas = resp_campanas.data

    if not lista_campanas:
        st.warning("⚠️ No se emparejaron ofertas con campañas.")
        st.stop()

    dict_campanas_opciones = {f"{c['id_campana']} - {c['nombre_campana']}": c["id_campana"] for c in lista_campanas}

except Exception as e:
    st.error(f"❌ Error al filtrar campañas: {str(e)}")
    st.stop()

# ==============================================================================
# 4. SELECTOR DE CAMPAÑA
# ==============================================================================
st.markdown("### 🔍 Selección de Campaña de Trabajo")
with st.container(border=True):
    col_campana, col_info = st.columns(2)
    with col_campana:
        campana_seleccionada_label = st.selectbox(
            "Campañas con ofertas disponibles:",
            options=list(dict_campanas_opciones.keys()),
            key="selector_campana_activa"
        )
        id_campana_activa = int(dict_campanas_opciones[campana_seleccionada_label])
    with col_info:
        st.success(f"🟢 Campaña activa ID: {id_campana_activa}")

# ==============================================================================
# 5. FIRMA DE IMÁGENES EN LOTE
# ==============================================================================
@st.cache_data(ttl=1800)
def firmar_lote_imagenes(lista_urls: list) -> dict:
    dict_mapeo_firmado = {}
    if not lista_urls:
        return dict_mapeo_firmado

    supabase_url = st.secrets["supabase"]["url"]
    bucket_name = "imagenes"
    rutas_para_firmar = []
    mapeo_ruta_original = {}

    for url in lista_urls:
        if not url:
            dict_mapeo_firmado[url] = "https://picsum.photos/100"
            continue
        url_str = str(url).strip()

        if supabase_url in url_str and "/storage/v1/object/public/" in url_str:
            partes = url_str.split("/storage/v1/object/public/")
            if len(partes) == 2:
                bucket_y_path = partes[1]
                bucket_name = bucket_y_path.split("/")[0]
                file_path = "/".join(bucket_y_path.split("/")[1:])
                rutas_para_firmar.append(file_path)
                mapeo_ruta_original[file_path] = url
        elif not url_str.startswith("http") and "." in url_str:
            rutas_para_firmar.append(url_str)
            mapeo_ruta_original[url_str] = url
        else:
            dict_mapeo_firmado[url] = url_str

    if rutas_para_firmar:
        try:
            rutas_unicas = list(set(rutas_para_firmar))
            respuestas_firmas = supabase.storage.from_(bucket_name).create_signed_urls(rutas_unicas, 3600)
            for item in respuestas_firmas:
                path_archivo = item.get("path") if isinstance(item, dict) else getattr(item, "path", None)
                url_firmada = item.get("signedURL") if isinstance(item, dict) else getattr(item, "signedURL", None)
                if path_archivo and url_firmada:
                    url_orig = mapeo_ruta_original.get(path_archivo)
                    if url_orig:
                        dict_mapeo_firmado[url_orig] = url_firmada if url_firmada.startswith("http") else f"{supabase_url}{url_firmada}"
        except Exception:
            for ruta in rutas_para_firmar:
                url_orig = mapeo_ruta_original.get(ruta)
                dict_mapeo_firmado[url_orig] = url_orig

    return dict_mapeo_firmado

# ==============================================================================
# 6. HELPERS
# ==============================================================================
def safe_int(val, default=None):
    try:
        if val is None or str(val).lower() in ("null", "", "none") or str(val) == "0":
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

def calcular_layout_grid(num_slots):
    if num_slots == 1:
        return "1fr", "1fr", 1
    if num_slots == 2:
        return "repeat(2, 1fr)", "1fr", 2
    if num_slots in (3, 4):
        return "repeat(2, 1fr)", "repeat(2, 1fr)", 2
    if num_slots in (5, 6):
        return "repeat(2, 1fr)", "repeat(3, 1fr)", 3
    return "repeat(2, 1fr)", "repeat(4, 1fr)", 4

# ==============================================================================
# 7. CARGA DE OFERTAS
# ==============================================================================
if "ofertas" not in st.session_state or st.session_state.get("campana_anterior") != id_campana_activa:
    try:
        resp_ofertas = supabase.table("ofertas").select("*").eq("id_campana", id_campana_activa).execute()
        ofertas_campana = resp_ofertas.data if resp_ofertas.data else []

        lista_id_productos = list(set([o["id_producto"] for o in ofertas_campana if o.get("id_producto") is not None]))
        dict_productos = {}
        urls_totales_a_firmar = []

        if lista_id_productos:
            resp_prod = supabase.table("productos").select("id_producto, nombre, url_imagen").in_("id_producto", lista_id_productos).execute()
            if resp_prod.data:
                dict_productos = {p["id_producto"]: p for p in resp_prod.data}
                urls_totales_a_firmar = list(set([p.get("url_imagen") for p in resp_prod.data if p.get("url_imagen")]))

        mapa_imagenes_firmadas = firmar_lote_imagenes(urls_totales_a_firmar)

        for o in ofertas_campana:
            o["numero_pagina"] = safe_int(o.get("numero_pagina"))
            o["posicion_slot"] = safe_int(o.get("posicion_slot"))

            id_p = o.get("id_producto")
            if id_p in dict_productos:
                o["nombre"] = dict_productos[id_p].get("nombre") or f"Producto #{id_p}"
                url_original = dict_productos[id_p].get("url_imagen")
                o["img"] = mapa_imagenes_firmadas.get(url_original, url_original or "https://picsum.photos/100")
            else:
                o["nombre"] = f"Oferta sin producto asignado (#{o['id_oferta']})"
                o["img"] = "https://picsum.photos/100"

        st.session_state.ofertas = ofertas_campana
        st.session_state.campana_anterior = id_campana_activa
    except Exception as e:
        st.error(f"❌ Error al cargar ofertas: {str(e)}")
        st.session_state.ofertas = []

# ==============================================================================
# 8. NAVEGACIÓN
# ==============================================================================
st.markdown("### 🛠️ Configuración de la Hoja del Folleto")
pag_act = safe_int(st.session_state.pagina_actual, 1)

def avanzar_pagina():
    st.session_state.pagina_actual += 1

def retroceder_pagina():
    if st.session_state.pagina_actual > 1:
        st.session_state.pagina_actual -= 1

slots_usados = [
    safe_int(o["posicion_slot"]) for o in st.session_state.get("ofertas", [])
    if safe_int(o.get("numero_pagina")) == pag_act and safe_int(o.get("posicion_slot")) is not None
]
slot_maximo_detectado = max(slots_usados) if slots_usados else 4

if pag_act not in st.session_state.config_paginas:
    st.session_state.config_paginas[pag_act] = {"slots": slot_maximo_detectado, "distribucion": "Equilibrado", "estilo": "Estándar"}
elif slot_maximo_detectado > int(st.session_state.config_paginas[pag_act]["slots"]):
    st.session_state.config_paginas[pag_act]["slots"] = slot_maximo_detectado

cfg = st.session_state.config_paginas[pag_act]

with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns(6)
    with nav_col1:
        st.button("◀ Anterior", use_container_width=True, on_click=retroceder_pagina, disabled=(st.session_state.pagina_actual <= 1), key="btn_nav_ant")
    with nav_col2:
        st.markdown(f"<h3 style='text-align: center; margin:0; color:#0d6efd;'>Pág. {st.session_state.pagina_actual}</h3>", unsafe_allow_html=True)
    with nav_col3:
        st.button("Siguiente ▶", use_container_width=True, on_click=avanzar_pagina, key="btn_nav_sig")
    with nav_col4:
        slots_deseados = st.slider("Slots asignados:", min_value=1, max_value=8, value=int(cfg["slots"]), key=f"sld_p{pag_act}")
        st.session_state.config_paginas[pag_act]["slots"] = slots_deseados
    with nav_col5:
        st.session_state.config_paginas[pag_act]["distribucion"] = st.selectbox("Distribución:", ["Equilibrado", "Banner Superior", "Enfoque Central"], index=["Equilibrado", "Banner Superior", "Enfoque Central"].index(cfg["distribucion"]), key=f"dst_p{pag_act}")
    with nav_col6:
        st.session_state.config_paginas[pag_act]["estilo"] = st.selectbox("Estilo:", ["Estándar", "Destacado", "Compacto"], index=["Estándar", "Destacado", "Compacto"].index(cfg["estilo"]), key=f"est_p{pag_act}")

_, _, num_cols_reales = calcular_layout_grid(slots_deseados)

# ==============================================================================
# 9. DRAG & DROP OPERATIVO CON STREAMLIT-SORTABLES
# ==============================================================================
st.markdown("### 🎨 Arrastra ofertas entre el Banco y los Slots")
st.caption("💡 Arrastra una oferta del banco a un slot para asignarla. Arrastra de un slot al banco para desasignarla.")

ofertas = st.session_state.get("ofertas", [])

# Crear un diccionario de lookup por id para parsear después
ofertas_por_id = {str(o["id_oferta"]): o for o in ofertas}

# Formato de string: "id_oferta|nombre|precio"
def format_item(o):
    precio = float(o.get("precio_oferta", 0)) if o.get("precio_oferta") is not None else 0
    return f"{o['id_oferta']}|{o.get('nombre', 'Sin nombre')}|${precio:,.0f}"

def parse_item_id(item_str):
    return item_str.split("|")[0]

# Container del banco (ofertas libres)
banco_items = []
for o in ofertas:
    if safe_int(o.get("numero_pagina")) is None:
        banco_items.append(format_item(o))

# Containers de slots
slot_containers = []
for slot_num in range(1, slots_deseados + 1):
    slot_items = []
    for o in ofertas:
        if safe_int(o.get("numero_pagina")) == pag_act and safe_int(o.get("posicion_slot")) == slot_num:
            slot_items.append(format_item(o))
    slot_containers.append({
        "header": f"📍 Slot {slot_num}",
        "items": slot_items
    })

all_containers = [{"header": "📦 Banco de Ofertas", "items": banco_items}] + slot_containers

# Renderizar sortables
sorted_data = sort_items(
    all_containers,
    multi_containers=True,
    direction="vertical",
    key=f"sort_p{pag_act}_{slots_deseados}"
)

# ==============================================================================
# 10. PROCESAR RESULTADO DEL DRAG & DROP
# ==============================================================================
if sorted_data:
    cambio = False
    for container in sorted_data:
        header = container.get("header", "")
        items = container.get("items", [])

        if header == "📦 Banco de Ofertas":
            for item_str in items:
                id_oferta = int(parse_item_id(item_str))
                for o in st.session_state.ofertas:
                    if o["id_oferta"] == id_oferta:
                        if o.get("numero_pagina") is not None or o.get("posicion_slot") is not None:
                            o["numero_pagina"] = None
                            o["posicion_slot"] = None
                            cambio = True
                        break
        elif header.startswith("📍 Slot "):
            slot_num = int(header.replace("📍 Slot ", ""))
            for item_str in items:
                id_oferta = int(parse_item_id(item_str))
                for o in st.session_state.ofertas:
                    if o["id_oferta"] == id_oferta:
                        if o.get("numero_pagina") != pag_act or o.get("posicion_slot") != slot_num:
                            o["numero_pagina"] = pag_act
                            o["posicion_slot"] = slot_num
                            cambio = True
                        break

    if cambio:
        st.success("✅ Cambios aplicados. Reordenamiento guardado en memoria.")
        st.rerun()

# ==============================================================================
# 11. TABLA DE ASIGNADAS
# ==============================================================================
st.markdown(f"### 📊 Ofertas en Página {pag_act}")

filas_tabla_ofertas = []
for o in st.session_state.get("ofertas", []):
    num_pag = safe_int(o.get("numero_pagina"))
    pos_slot = safe_int(o.get("posicion_slot"))
    if num_pag == pag_act and pos_slot is not None:
        filas_tabla_ofertas.append({
            "id_oferta": o["id_oferta"],
            "id_producto": o["id_producto"],
            "id_campana": id_campana_activa,
            "numero_pagina": num_pag,
            "posicion_slot": pos_slot,
            "precio_oferta": o.get("precio_oferta"),
            "posicion_mix": cfg.get("distribucion", "Equilibrado"),
            "sub_molde_estilo": cfg.get("estilo", "Estándar"),
            "numero_fila": ((pos_slot - 1) // num_cols_reales) + 1,
            "numero_columna": ((pos_slot - 1) % num_cols_reales) + 1,
        })

if filas_tabla_ofertas:
    st.dataframe(filas_tabla_ofertas, use_container_width=True)
else:
    st.info("Ninguna oferta asignada en esta hoja todavía.")

# ==============================================================================
# 12. PREPARAR LOTE PARA GUARDAR
# ==============================================================================
filas_desasignadas = []
for o in st.session_state.get("ofertas", []):
    num_pag = safe_int(o.get("numero_pagina"))
    if num_pag is None:
        filas_desasignadas.append({
            "id_oferta": o["id_oferta"],
            "id_producto": o["id_producto"],
            "id_campana": id_campana_activa,
            "numero_pagina": None,
            "posicion_slot": None,
            "numero_fila": None,
            "numero_columna": None,
        })

lote_para_guardar = filas_tabla_ofertas + filas_desasignadas

# ==============================================================================
# 13. GUARDAR EN SUPABASE
# ==============================================================================
if st.button("💾 Guardar Configuración Completa del Folleto", type="primary", use_container_width=True):
    if lote_para_guardar:
        try:
            with st.spinner("Sincronizando cambios con Supabase..."):
                resultado = supabase.table("ofertas").upsert(lote_para_guardar).execute()
            st.success(f"✨ ¡Sincronización Exitosa! {len(resultado.data)} registros actualizados.")
            st.toast("Base de datos actualizada correctamente", icon="🚀")
            if "ofertas" in st.session_state:
                del st.session_state.ofertas
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al guardar en Supabase: {str(e)}")
    else:
        st.warning("⚠️ No hay elementos para persistir.")
