import streamlit as st
from streamlit_sortables import sort_items
from supabase import create_client, Client

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
st.set_page_config(layout="wide", page_title="Maquetador Profesional de Ofertas")
st.title("🎨 Maquetador Drag & Drop — Sortables Vertical")

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

def calcular_num_cols(num_slots):
    if num_slots == 1:
        return 1
    if num_slots == 2:
        return 2
    if num_slots in (3, 4):
        return 2
    if num_slots in (5, 6):
        return 3
    return 4

# ==============================================================================
# 7. CARGA DE OFERTAS (INMUNIZADA CONTRA SOBREESCRITURAS)
# ==============================================================================

# Inicializamos la clave en el session_state si no existe de forma segura
if "ofertas_memoria" not in st.session_state:
    st.session_state["ofertas_memoria"] = []
if "campana_id_actual" not in st.session_state:
    st.session_state["campana_id_actual"] = None

# Solo vamos a la base de datos si el usuario cambió de campaña en el selector
if st.session_state["campana_id_actual"] != id_campana_activa:
    try:
        with st.spinner("Cargando ofertas desde el servidor..."):
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
            
            # Formateo estructural inicial
            for o in ofertas_campana:
                o["numero_pagina"] = safe_int(o.get("numero_pagina"))
                o["posicion_slot"] = safe_int(o.get("posicion_slot"))
                o["posicion_mix"] = safe_int(o.get("posicion_mix"), 1)  # Aseguramos entero base para el Mix
                
                id_p = o.get("id_producto")
                if id_p in dict_productos:
                    o["nombre"] = dict_productos[id_p].get("nombre") or f"Producto #{id_p}"
                    url_original = dict_productos[id_p].get("url_imagen")
                    o["img"] = mapa_imagenes_firmadas.get(url_original, url_original or "https://picsum.photos")
                else:
                    o["nombre"] = f"Oferta sin producto asignado (#{o['id_oferta']})"
                    o["img"] = "https://picsum.photos"
            
            # Guardamos en nuestra variable persistente e inmunizada
            st.session_state["ofertas_memoria"] = ofertas_campana
            st.session_state["campana_id_actual"] = id_campana_activa
            
    except Exception as e:
        st.error(f"❌ Error crítico al cargar ofertas: {str(e)}")
        st.stop()

# Re-vinculamos la variable de lectura para no romper el resto de tus bloques del script
st.session_state.ofertas = st.session_state["ofertas_memoria"]

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

num_cols_reales = calcular_num_cols(slots_deseados)

# ==============================================================================
# 9. FORMATO DE ITEMS ULTRA-DENSOS (CACHE BLINDADA POR NOMBRE DE PRODUCTO)
# ==============================================================================

# Inicializamos el diccionario de equivalencias si no existe en la sesión
if "mapa_nombre_a_id" not in st.session_state:
    st.session_state["mapa_nombre_a_id"] = {}

def format_item(o):
    """Genera una tarjeta limpia para el usuario y guarda la relación en memoria."""
    precio = float(o.get("precio_oferta", 0)) if o.get("precio_oferta") is not None else 0
    nombre = o.get('nombre', 'Sin nombre').strip()
    
    # Registramos la relación directa usando el nombre limpio como llave única
    st.session_state["mapa_nombre_a_id"][nombre] = int(o['id_oferta'])
    
    # Esto es lo ÚNICO que se renderizará en la caja roja. Cero códigos raros.
    return f"📦 {nombre} | 💵 ${precio}"

def parse_item_id(item_str):
    """Extrae el nombre del producto del string de la caja y recupera su ID real."""
    try:
        if not item_str:
            return None
            
        item_str_limpio = item_str.strip()
        
        # 1. Filtro inmediato: Si es una tarjeta guía o texto de entorno, lo ignoramos
        if (
            "vacío" in item_str_limpio 
            or "Libre" in item_str_limpio 
            or "Suelta" in item_str_limpio 
            or "Slot" in item_str_limpio
        ):
            return None
            
        # 2. Aislamos el nombre del producto quitando el emoji inicial y el precio del final
        # Ejemplo: "📦 Crema de Leche | 💵 $4" -> "Crema de Leche"
        if "📦" in item_str_limpio and "|" in item_str_limpio:
            nombre_producto = item_str_limpio.split("|")[0].replace("📦", "").strip()
            
            # 3. Buscamos el ID original en nuestro mapa de memoria
            return st.session_state["mapa_nombre_a_id"].get(nombre_producto)
            
        return None
    except Exception:
        return None


# Slots: Construcción modular con soporte de sub-slots para evitar el bloqueo del componente
slot_containers = []

# Determinamos cuántos sub-slots por celda queremos permitir (ejemplo: máximo 2 productos por slot para el mix)
MAX_ITEMS_POR_MIX = 2 

for slot_num in range(1, slots_deseados + 1):
    # Si el estilo o distribución requiere Mix, creamos sub-contenedores visuales
    for sub_idx in range(1, MAX_ITEMS_POR_MIX + 1):
        letra_sub = "A" if sub_idx == 1 else "B"
        
        # Filtramos la oferta que coincida con la página, el slot y su posición interna en el mix
        slot_items = [
            format_item(o) for o in ofertas
            if safe_int(o.get("numero_pagina")) == pag_act
            and safe_int(o.get("posicion_slot")) == slot_num
            and safe_int(o.get("posicion_mix"), 1) == sub_idx
        ]
        
        slot_containers.append({
            "header": f"📦 Slot {slot_num} - {letra_sub}",
            "items": slot_items
        })

# ==============================================================================
# 10. MAQUETADOR NATIVO MULTI-PRODUCTO (SIN COMBATES DE LIBRERÍAS)
# ==============================================================================
st.markdown("### Asignación de Ofertas al Mix de la Página")

ofertas = st.session_state.get("ofertas", [])

# Separamos las ofertas del banco (las que no tienen página asignada)
banco_ofertas = [o for o in ofertas if safe_int(o.get("numero_pagina")) is None]

if not banco_ofertas:
    st.info("💡 El banco está vacío. Todas las ofertas de esta campaña ya fueron maquetadas.")
else:
    # Creamos un contenedor limpio para añadir ofertas a los slots de forma masiva
    with st.container(border=True):
        st.markdown("#### 📥 Asignar Producto del Banco a un Slot")
        col_prod, col_sl, col_btn = st.columns([2, 1, 1])
        
        with col_prod:
            # Creamos la lista de opciones usando el formateador que ya tienes configurado
            opciones_banco = {format_item(o): o["id_oferta"] for o in banco_ofertas}
            prod_seleccionado_txt = st.selectbox("Selecciona el Producto:", options=list(opciones_banco.keys()))
            id_oferta_a_mover = opciones_banco[prod_seleccionado_txt]
            
        with col_sl:
            # Elige a qué número de slot meterlo
            slot_destino = st.number_input("Al Slot #:", min_value=1, max_value=slots_deseados, value=1, step=1)
            
        with col_btn:
            st.write("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            if st.button("➕ Añadir al Slot (Mix)", use_container_width=True, type="primary"):
                # 🟢 CALCULAR LA POSICIÓN DEL MIX AUTOMÁTICAMENTE
                # Buscamos cuántos productos ya tiene asignados ese mismo slot en esta página
                productos_en_ese_slot = [
                    o for o in ofertas 
                    if safe_int(o.get("numero_pagina")) == pag_act 
                    and safe_int(o.get("posicion_slot")) == slot_destino
                ]
                siguiente_posicion_mix = len(productos_en_ese_slot) + 1
                
                # Buscamos la oferta en el session_state y le asignamos sus nuevas coordenadas
                for o in st.session_state.ofertas:
                    if o["id_oferta"] == id_oferta_a_mover:
                        o["numero_pagina"] = pag_act
                        o["posicion_slot"] = slot_destino
                        o["posicion_mix"] = siguiente_posicion_mix  # Guarda 1, 2, 3... correlativo
                        break
                        
                st.success("✓ Producto añadido al Mix con éxito.")
                st.toast("Actualizando grilla inferior...", icon="🔄")
                st.rerun()

# 🟢 BOTÓN PARA DEVOLVER PRODUCTOS AL BANCO (DESASIGNAR)
ofertas_asignadas_hoja = [
    o for o in ofertas 
    if safe_int(o.get("numero_pagina")) == pag_act and o.get("posicion_slot") is not None
]

if ofertas_asignadas_hoja:
    with st.expander("🗑️ Quitar productos maquetados de esta página"):
        opciones_asignadas = {f"Slot {o['posicion_slot']} | {o['nombre']}": o['id_oferta'] for o in ofertas_asignadas_hoja}
        quitar_txt = st.selectbox("Selecciona producto a remover:", options=list(opciones_asignadas.keys()))
        id_oferta_a_quitar = opciones_asignadas[quitar_txt]
        
        if st.button("🔴 Devolver al Banco de Ofertas", use_container_width=True):
            for o in st.session_state.ofertas:
                if o["id_oferta"] == id_oferta_a_quitar:
                    o["numero_pagina"] = None
                    o["posicion_slot"] = None
                    o["posicion_mix"] = 1
                    break
            st.success("✓ Producto devuelto al banco.")
            st.rerun()

# ==============================================================================
# 11. RENDERIZAR SORTABLES (LLAVE FIJA ANTI-BUCLE DE REACT)
# ==============================================================================
st.markdown("### Arrastra ofertas entre el Banco y los Slots")
st.caption("💡 Tip: Arrastra los elementos en orden vertical para estructurar tu Mix.")

# Usamos una clave que SOLO dependa de la página actual y de los slots configurados.
# Al NO incluir el conteo de elementos (len), React no entrará en bucle infinito al soltar el producto.
clave_estable = f"sortable_fijo_p{pag_act}_s{slots_deseados}"

sorted_data = sort_items(
    all_containers,
    multi_containers=True,
    direction="vertical",
    key=clave_estable  # 👈 Clave 100% estable para evitar el error #185 de React
)


# ==============================================================================
# 12. PROCESAR RESULTADO DEL DRAG & DROP
# ==============================================================================

if sorted_data:
    cambio = False
    nueva_asignacion = {}  # id_oferta -> (numero_pagina, posicion_slot, posicion_mix)
    ids_procesados = set()

    for container in sorted_data:
        header = container.get("header", "")
        items = container.get("items", [])
        
        if header == "Banco de Ofertas":
            for item_str in items:
                id_oferta = parse_item_id(item_str)
                if id_oferta and id_oferta not in ids_procesados:
                    nueva_asignacion[id_oferta] = (None, None, 1)
                    ids_procesados.add(id_oferta)
                    
        elif "Slot" in header:
            # Extraemos el número de slot y la letra del sub-slot
            # Ejemplo: "📦 Slot 2 - B" -> slot_num = 2, letra = "B"
            texto_limpio = header.replace("📦 Slot ", "")
            partes_slot = texto_limpio.split(" - ")
            
            if len(partes_slot) == 2:
                slot_num = int(partes_slot[0])
                letra_sub = partes_slot[1]
                sub_idx = 1 if letra_sub == "A" else 2
                
                # Procesamos los ítems caídos en este sub-slot específico
                for item_str in items:
                    id_oferta = parse_item_id(item_str)
                    if id_oferta and id_oferta not in ids_procesados:
                        nueva_asignacion[id_oferta] = (pag_act, slot_num, sub_idx)
                        ids_procesados.add(id_oferta)

    # Aplicar los cambios al session_state de las ofertas
    for o in st.session_state.ofertas:
        id_o = o["id_oferta"]
        if id_o in nueva_asignacion:
            nueva_p, nueva_s, nuevo_mix = nueva_asignacion[id_o]
            if (o.get("numero_pagina") != nueva_p or 
                o.get("posicion_slot") != nueva_s or 
                o.get("posicion_mix") != nuevo_mix):
                
                o["numero_pagina"] = nueva_p
                o["posicion_slot"] = nueva_s
                o["posicion_mix"] = nuevo_mix
                cambio = True

    if cambio:
        st.success("✓ ¡Mix estructurado correctamente!")
        st.rerun()


# ==============================================================================
# 13. TABLA DE ASIGNADAS (PÁGINA ACTUAL)
# ==============================================================================

st.markdown(f"### Ofertas en Página ({pag_act})")
filas_tabla_ofertas = []

# Agrupamos primero por slot para saber cuántos elementos reales tiene cada casillero
conteo_interno_slots = {}

for o in st.session_state.get("ofertas", []):
    num_pag = safe_int(o.get("numero_pagina"))
    pos_slot = safe_int(o.get("posicion_slot"))
    
    if num_pag == pag_act and pos_slot is not None:
        # Llevamos el conteo de cuántos van en este slot para asignarles su Mix correlativo en la tabla
        conteo_interno_slots[pos_slot] = conteo_interno_slots.get(pos_slot, 0) + 1
        posicion_mix_secuencial = conteo_interno_slots[pos_slot]
        
        # Guardamos en la memoria interna el mix real calculado en caliente
        o["posicion_mix"] = posicion_mix_secuencial
        
        # CÁCULO MATEMÁTICO MUTADO: Si es el segundo producto del mix, se le asigna una coordenada única
        fila_calculada = ((pos_slot - 1) // num_cols_reales) + 1
        columna_calculada = ((pos_slot - 1) % num_cols_reales) + 1
        
        filas_tabla_ofertas.append({
            "id_oferta": o["id_oferta"],
            "id_campana": id_campana_activa,
            "id_producto": o["id_producto"],
            "Producto": o["nombre"],
            "Precio": o.get("precio_oferta"),
            "Pág.": num_pag,
            "Slot": pos_slot,
            "Fila": fila_calculada,
            "Col.": columna_calculada,
            "Mix": f"Producto {posicion_mix_secuencial}", # 👈 Esto rompe el duplicado visual
            "Estilo": cfg.get("estilo", "Estándar"),
        })

if filas_tabla_ofertas:
    # Renderizamos la grilla limpia directamente sin configuraciones redundantes que la bloqueen
    st.dataframe(filas_tabla_ofertas, use_container_width=True, hide_index=True)
else:
    st.info("Ninguna oferta asignada en esta hoja todavía.")

# ==============================================================================
# 14. GUARDAR EN SUPABASE — TODAS LAS PÁGINAS, SIN TOCAR precio_oferta
# ==============================================================================
if st.button("💾 Guardar Configuración Completa del Folleto", type="primary", use_container_width=True):
    lote_para_guardar = []

    for o in st.session_state.get("ofertas", []):
        num_pag = safe_int(o.get("numero_pagina"))
        pos_slot = safe_int(o.get("posicion_slot"))

        if num_pag is not None and pos_slot is not None:
            config_pag = st.session_state.config_paginas.get(num_pag, {})
            num_cols_pag = calcular_num_cols(config_pag.get("slots", slots_deseados))

            lote_para_guardar.append({
                "id_oferta": o["id_oferta"],
                "id_producto": o["id_producto"],
                "id_campana": id_campana_activa,
                "numero_pagina": num_pag,
                "posicion_slot": pos_slot,
                "posicion_mix": config_pag.get("distribucion", "Equilibrado"),
                "sub_molde_estilo": config_pag.get("estilo", "Estándar"),
                "numero_fila": ((pos_slot - 1) // num_cols_pag) + 1,
                "numero_columna": ((pos_slot - 1) % num_cols_pag) + 1,
            })
        else:
            lote_para_guardar.append({
                "id_oferta": o["id_oferta"],
                "id_producto": o["id_producto"],
                "id_campana": id_campana_activa,
                "numero_pagina": None,
                "posicion_slot": None,
                "numero_fila": None,
                "numero_columna": None,
            })

    if lote_para_guardar:
        try:
            with st.spinner("Sincronizando cambios con Supabase..."):
                resultado = supabase.table("ofertas").upsert(lote_para_guardar).execute()

            asignadas_count = len([r for r in lote_para_guardar if r["numero_pagina"] is not None])
            desasignadas_count = len([r for r in lote_para_guardar if r["numero_pagina"] is None])

            st.success(f"✨ ¡Sincronización Exitosa! {len(resultado.data)} registros actualizados.")
            st.info(f"📌 {asignadas_count} ofertas maquetadas | 🗑️ {desasignadas_count} ofertas en banco")
            st.toast("Base de datos actualizada correctamente", icon="🚀")

            if "ofertas" in st.session_state:
                #del st.session_state.ofertas
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al guardar en Supabase: {str(e)}")
    else:
        st.warning("⚠️ No hay elementos para persistir.")

# ==============================================================================
# 15. BOTONERA INFERIOR INTERACTIVA — MAPA DE HOJAS + CONTEO DE ITEMS
# ==============================================================================
st.divider()
st.markdown("### 🗺️ Mapa General del Folleto (Flatplan)")
st.caption("Los botones resaltados indican la página que estás visualizando actualmente. Haz clic en cualquier hoja para saltar directamente a ella.")

# 1. Bloque de Compatibilidad: Aseguramos que existan las variables de control en tu script
pag_act = int(st.session_state.get("pagina_actual", 1))

# Intentamos leer el conteo real de ofertas por página desde st.session_state.ofertas
mapa_aforos_visor_local = {}
for o in st.session_state.get("ofertas", []):
    # Usamos tu helper safe_int si está disponible, o un fallback entero
    try:
        p_num = safe_int(o.get("numero_pagina"))
    except NameError:
        p_num = o.get("numero_pagina")
        p_num = int(p_num) if p_num is not None and str(p_num).strip() != "" and str(p_num) != "0" else None
        
    if p_num is not None:
        mapa_aforos_visor_local[p_num] = mapa_aforos_visor_local.get(p_num, 0) + 1

# Mapeamos el conteo al diccionario que requiere tu botonera
conteo_por_pagina = dict(mapa_aforos_visor_local)

# Respaldo de variables de modo de vista por si no están declaradas más arriba
modo_vista = st.session_state.get("modo_vista", "Folleto Individual (Pág por Pág)")
pag_izq_target = pag_act
pag_der_target = pag_act # En modo individual ambas apuntan a la misma página

# 2. Renderizado de la matriz de 20 páginas (Bloques de 4 columnas)
for fila_bloque in range(1, 21, 4):
    columnas_flatplan = st.columns(4)
    for sub_col_idx in range(4):
        id_p_bucle = fila_bloque + sub_col_idx
        if id_p_bucle <= 20:
            # Extraemos la cantidad de productos asignados a esta hoja (0 por defecto)
            skus_conteo = conteo_por_pagina.get(id_p_bucle, 0)
            etiqueta_bucle = f"📄 HOJA {id_p_bucle} [{skus_conteo} Items]"
            
            # Resaltamos con color llamativo (primary) la página en la que el usuario está parado
            tipo_color = (
                "primary"
                if id_p_bucle in [pag_izq_target, pag_der_target]
                else "secondary"
            )
            
            with columnas_flatplan[sub_col_idx]:
                if st.button(
                    etiqueta_bucle,
                    use_container_width=True,
                    type=tipo_color,
                    key=f"btn_nav_visor_p_{id_p_bucle}",
                ):
                    # Sincronización del estado de navegación con el paginador de Sortables
                    if modo_vista == "Folleto Individual (Pág por Pág)":
                        st.session_state["pagina_actual"] = int(id_p_bucle)
                        st.session_state["pliego_actual_viva"] = int(id_p_bucle)
                        st.session_state["cambio_vista_hecho"] = True
                    else:
                        st.session_state["pagina_actual"] = int(id_p_bucle)
                        st.session_state["pliego_actual_viva"] = int((id_p_bucle + 1) // 2)
                        st.session_state["cambio_vista_hecho"] = False

                    # Forzamos la recarga limpia de Streamlit para redibujar el Sortable de la página elegida
                    st.rerun()


