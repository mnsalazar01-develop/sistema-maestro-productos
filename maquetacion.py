import streamlit as st
import streamlit.components.v1 as components
import json
from supabase import create_client, Client

# Configuración de la interfaz en modo panorámico sin barra lateral
st.set_page_config(layout="wide", page_title="Maquetador Profesional de Ofertas")
st.title("🎨 Maquetador Drag & Drop — Conexión Real y Desasignación")

# 1. CONEXIÓN HEREDADA A SUPABASE
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

# Inicialización de estados de navegación en session_state
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = 1

if "config_paginas" not in st.session_state:
    st.session_state.config_paginas = {}

# ==============================================================================
# 2. FILTRADO DE CAMPAÑAS VÁLIDAS CON BYPASS DE 1000 REGISTROS (Paginación Dinámica)
# ==============================================================================
try:
    ids_campanas_con_ofertas = []
    limite_bloque = 1000
    offset = 0
    con_datos = True
    
    # Bucle de extracción masiva para romper la barrera de las 1000 filas de Supabase
    while con_datos:
        resp_bloque = supabase.table("ofertas")\
            .select("id_campana")\
            .range(offset, offset + limite_bloque - 1)\
            .execute()
            
        datos_bloque = resp_bloque.data
        
        if datos_bloque:
            ids_campanas_con_ofertas.extend([o["id_campana"] for o in datos_bloque if o.get("id_campana") is not None])
            offset += limite_bloque
            # Si el bloque trajo menos del límite, es la última página
            if len(datos_bloque) < limite_bloque:
                con_datos = False
        else:
            con_datos = False
            
    # Obtener valores únicos e inmunes al truncado
    ids_campanas_con_ofertas = list(set(ids_campanas_con_ofertas))

    if not ids_campanas_con_ofertas:
        st.warning("⚠️ No hay ninguna campaña con ofertas registradas actualmente en la base de datos.")
        st.stop()

    # Consulta final de los nombres de campañas correspondientes
    resp_campanas = supabase.table("campanas")\
        .select("id_campana, nombre_campana")\
        .in_("id_campana", ids_campanas_con_ofertas)\
        .order("id_campana", desc=True)\
        .execute()
        
    lista_campanas = resp_campanas.data
    
    if not lista_campanas:
        st.warning("⚠️ No se pudieron emparejar las ofertas con registros válidos en la tabla campanas.")
        st.stop()
        
    dict_campanas_opciones = {f"{c['id_campana']} - {c['nombre_campana']}": c['id_campana'] for c in lista_campanas}

except Exception as e:
    st.error(f"❌ Error crítico en bypass de registros de campañas: {str(e)}")
    st.stop()



# 3. PANEL DE SELECCIÓN DE CAMPAÑA FILTRADA (Corregido a st.columns(2))
st.markdown("### 🔍 Selección de Campaña de Trabajo")
with st.container(border=True):
    col_campana, col_info = st.columns(2)
    with col_campana:
        campana_seleccionada_label = st.selectbox(
            "Campañas con ofertas disponibles:",
            options=list(dict_campanas_opciones.keys()),
            key="selector_campana_activa"
        )
        id_campana_activa = dict_campanas_opciones[campana_seleccionada_label]
    with col_info:
        st.success(f"🟢 Surtido validado. Desplegando ofertas de la Campaña ID: {id_campana_activa}")

import pandas as pd  # Asegúrate de incluirlo si usas pd.isna

# Nombre de tu bucket por defecto en Supabase Storage
BUCKET_IMAGENES = "imagenes"  

# 🟢 FUNCIÓN OPTIMIZADA: FIRMA TODO EL LOTE DE UNA SOLA VEZ
@st.cache_data(ttl=1800)  # Guarda en caché por 30 minutos para evitar peticiones repetidas
def firmar_lote_imagenes(lista_urls: list) -> dict:
    """
    Recibe una lista de URLs/Rutas de imágenes y devuelve un diccionario {url_original: url_firmada}
    ejecutando una única llamada de red hacia Supabase Storage.
    """
    dict_mapeo_firmado = {}
    if not lista_urls:
        return dict_mapeo_firmado

    supabase_url = st.secrets["supabase"]["url"]
    bucket_name = "imagenes"  # Tu BUCKET_IMAGENES por defecto
    
    # Separar qué archivos pertenecen a Supabase Storage y cuáles son externos (ej: http)
    rutas_para_firmar = []
    mapeo_ruta_original = {} # Para recordar a qué URL correspondía cada archivo limpio

    for url in lista_urls:
        if not url or (hasattr(pd, 'isna') and pd.isna(url)):
            dict_mapeo_firmado[url] = "https://picsum.photos"
            continue
            
        url_str = str(url).strip()
        
        # Caso A: Es una URL pública completa de Supabase
        if supabase_url in url_str and "/storage/v1/object/public/" in url_str:
            partes = url_str.split("/storage/v1/object/public/")
            if len(partes) == 2:
                bucket_y_path = partes[1]
                bucket_name = bucket_y_path.split("/")[0]
                file_path = "/".join(bucket_y_path.split("/")[1:])
                rutas_para_firmar.append(file_path)
                mapeo_ruta_original[file_path] = url
        # Caso B: Es una ruta relativa de la base de datos
        elif not url_str.startswith("http") and "." in url_str:
            rutas_para_firmar.append(url_str)
            mapeo_ruta_original[url_str] = url
        # Caso C: Ya es una URL externa (Picsum, etc.) o ya está firmada
        else:
            dict_mapeo_firmado[url] = url_str

    # Si hay rutas internas de Supabase que firmar, hacemos UNA sola petición global
    if rutas_para_firmar:
        try:
            # Quitamos duplicados de rutas para no gastar ancho de banda
            rutas_unicas = list(set(rutas_para_firmar))
            
            # create_signed_urls acepta una lista de rutas de archivos de golpe (Máx. 1 llamada de red)
            respuestas_firmas = supabase.storage.from_(bucket_name).create_signed_urls(rutas_unicas, 3600)
            
            for item in respuestas_firmas:
                # Dependiendo de la versión de la SDK, 'item' es un diccionario o un objeto
                path_archivo = item.get("path") if isinstance(item, dict) else getattr(item, "path", None)
                url_firmada = item.get("signedURL") if isinstance(item, dict) else getattr(item, "signedURL", None)
                
                if path_archivo and url_firmada:
                    # Recuperamos la URL original del producto para armar el mapa
                    url_orig = mapeo_ruta_original.get(path_archivo)
                    if url_orig:
                        # Asegurar el prefijo si viene relativo
                        if not url_firmada.startswith("http"):
                            dict_mapeo_firmado[url_orig] = f"{supabase_url}{url_firmada}"
                        else:
                            dict_mapeo_firmado[url_orig] = url_firmada
        except Exception:
            # Fail-safe: Si falla el lote, rellenamos con las originales para no romper la app
            for ruta in rutas_para_firmar:
                url_orig = mapeo_ruta_original.get(ruta)
                dict_mapeo_firmado[url_orig] = url_orig

    return dict_mapeo_firmado

# ==============================================================================
# 0. DECLARACIÓN MATEMÁTICA DEL LAYOUT GRID (Movida arriba para evitar NameError)
# ==============================================================================
def calcular_layout_grid(num_slots):
    if num_slots == 1: return "1fr", "1fr"
    if num_slots == 2: return "repeat(2, 1fr)", "1fr"
    if num_slots in (3, 4): return "repeat(2, 1fr)", "repeat(2, 1fr)"
    if num_slots in (5, 6): return "repeat(2, 1fr)", "repeat(3, 1fr)"
    return "repeat(2, 1fr)", "repeat(4, 1fr)"

# ==============================================================================
# 4. CONSULTA DE OFERTAS INMUNE A CAMBIOS DE SELECTOR Y REFRESCAS DE PÁGINA
# ==============================================================================
# CONDICIÓN PROTEGIDA: Solo entra aquí si la app se abre por primera vez o si el usuario cambia de campaña
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
        
        # EL FORMATEO OCURRE ÚNICAMENTE AQUÍ (Dentro de la descarga inicial de la BD)
        for o in ofertas_campana:
            num_pag = o.get("numero_pagina")
            pos_slot = o.get("posicion_slot")
            
            # Si en la base de datos es 0, None o "null", en Python se inicializa explícitamente como None
            o["numero_pagina"] = int(num_pag) if num_pag is not None and str(num_pag).lower() != "null" and str(num_pag).strip() != "" and str(num_pag) != "0" else None
            o["posicion_slot"] = int(pos_slot) if pos_slot is not None and str(pos_slot).lower() != "null" and str(pos_slot).strip() != "" and str(pos_slot) != "0" else None

            id_p = o.get("id_producto")
            if id_p in dict_productos:
                o["nombre"] = dict_productos[id_p].get("nombre") or f"Producto #{id_p}"
                url_original = dict_productos[id_p].get("url_imagen")
                o["img"] = mapa_imagenes_firmadas.get(url_original, url_original or "https://picsum.photos")
            else:
                o["nombre"] = f"Oferta sin producto asignado (#{o['id_oferta']})"
                o["img"] = "https://picsum.photos"
                
        # Seteamos el estado global firme
        st.session_state.ofertas = ofertas_campana
        st.session_state.campana_anterior = id_campana_activa
        
    except Exception as e:
        st.error(f"❌ Error al procesar el banco de datos en Supabase: {str(e)}")
        st.session_state.ofertas = []

# ==============================================================================
# 5. CALLBACKS DE NAVEGACIÓN Y CONTROLES DE LA PÁGINA (Sin IDs Duplicados)
# ==============================================================================
st.markdown("### 🛠️ Configuración de la Hoja del Folleto")
pag_act = int(st.session_state.pagina_actual)

def avanzar_pagina():
    st.session_state.pagina_actual += 1
    st.session_state.ultimo_ts_procesado = 99999999999999

def retroceder_pagina():
    if st.session_state.pagina_actual > 1:
        st.session_state.pagina_actual -= 1
        st.session_state.ultimo_ts_procesado = 99999999999999

# Extraer posiciones máximas ocupadas
slots_usados = [
    int(o["posicion_slot"]) for o in st.session_state.get("ofertas",) 
    if o.get("numero_pagina") == pag_act and o.get("posicion_slot") not in (None, 0, "0")
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
        st.button("◀ Anterior", use_container_width=True, on_click=retroceder_pagina, disabled=(st.session_state.pagina_actual <= 1), key="btn_nav_ant_unique")
    with nav_col2:
        st.markdown(f"<h3 style='text-align: center; margin:0; color:#0d6efd;'>Pág. {st.session_state.pagina_actual}</h3>", unsafe_allow_html=True)
    with nav_col3:
        st.button("Siguiente ▶", use_container_width=True, on_click=avanzar_pagina, key="btn_nav_sig_unique")
    with nav_col4:
        slots_deseados = st.slider("Slots asignados:", min_value=1, max_value=8, value=int(cfg["slots"]), key=f"sld_estatico_p{pag_act}")
        st.session_state.config_paginas[pag_act]["slots"] = slots_deseados
    with nav_col5:
        st.session_state.config_paginas[pag_act]["distribucion"] = st.selectbox("Distribución:", ["Equilibrado", "Banner Superior", "Enfoque Central"], key=f"dst_p{pag_act}")
    with nav_col6:
        st.session_state.config_paginas[pag_act]["estilo"] = st.selectbox("Estilo:", ["Estándar", "Destacado", "Compacto"], key=f"est_p{pag_act}")

columnas_css, filas_css = calcular_layout_grid(slots_deseados)

# ==============================================================================
# 6. CONSTRUCTOR DEL COMPONENTE HTML VISUAL (Eliminación de Duplicados Visuales)
# ==============================================================================
def generar_canvas_ofertas(ofertas, pagina, num_slots, cols, rows):
    banco_html, slots_ocupados = "", {}
    
    for o in ofertas:
        img_url = o.get('img') if o.get('img') else "https://picsum.photos"
        raw_p = o.get('numero_pagina')
        raw_s = o.get('posicion_slot')
        
        # Clasificación estricta de booleanos (Falso si es None, vacío, "null" o el número/string 0)
        es_p = raw_p is not None and str(raw_p).lower() != "null" and str(raw_p).strip() != "" and str(raw_p) != "0"
        es_s = raw_s is not None and str(raw_s).lower() != "null" and str(raw_s).strip() != "" and str(raw_s) != "0"
        
        card = f'''<div class="product-card" draggable="true" id="{o['id_oferta']}">
            <img src="{img_url}"><div class="info"><span class="name">{o['nombre']}</span><span class="price">${o.get('precio_oferta', 0.0):,.2f}</span></div>
        </div>'''
        
        # ESTADO 1: Tiene coordenadas completas y válidas de maquetación
        if es_p and es_s:
            if int(raw_p) == pagina:
                if 1 <= int(raw_s) <= num_slots:
                    slots_ocupados[int(raw_s)] = card
                else:
                    # Si el slider se encogió y el slot ya no existe, se muestra en el banco
                    banco_html += card
            else:
                # Pertenece a otra hoja: Oculto absoluto en el DOM (No se ve en el banco)
                banco_html += f'<div style="display:none !important;" class="hidden-item-dom">{card}</div>'
                
        # ESTADO 2: El registro está libre, es cero, o no tiene maquetación (Va al banco visible)
        else:
            banco_html += card

    slots_html = "".join([f'<div class="slot" id="{i}">' + slots_ocupados.get(i, f'<div class="placeholder">Posición Slot {i}<br><span>Disponible</span></div>') + '</div>' for i in range(1, num_slots + 1)])
    
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
        body {{ font-family: system-ui, sans-serif; margin: 0; background: #f8f9fa; display: flex; gap: 20px; padding: 10px; height: 85vh; }}
        .sidebar {{ width: 280px; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; overflow-y: auto; display: flex; flex-direction: column; }}
        .sidebar.drag-over {{ background: #fff5f5; border: 2px dashed #dc3545; }}
        .canvas {{ flex: 1; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; flex-direction: column; }}
        .grid-folleto {{ display: grid; grid-template-columns: {cols}; grid-template-rows: {rows}; gap: 12px; flex: 1; min-height: 400px; }}
        .slot {{ border: 2px dashed #cbd5e1; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: center; position: relative; padding: 5px; }}
        .slot.drag-over {{ border-color: #3b82f6; background: #eff6ff; }}
        .product-card {{ background: white; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px; cursor: grab; display: flex; align-items: center; gap: 10px; width: 90%; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .product-card img {{ width: 45px; height: 45px; object-fit: cover; border-radius: 4px; pointer-events: none; }}
        .product-card .info {{ display: flex; flex-direction: column; font-size: 12px; overflow: hidden; pointer-events: none; }}
        .product-card .name {{ font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .product-card .price {{ color: #16a34a; font-weight: 700; margin-top: 2px; }}
        .placeholder {{ color: #94a3b8; font-size: 13px; text-align: center; pointer-events: none; user-select: none; }}
        .placeholder span {{ font-size: 10px; color: #cbd5e1; }}
    </style></head><body>
    <div class="sidebar" id="banco-disponibles">
        <h4 style="margin:0 0 10px 0; font-size:14px; color:#475569; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">📦 Ofertas Disponibles</h4>
        <div style="display: flex; flex-direction: column; gap:8px; min-height:400px; flex-grow:1;" id="banco-lista">{banco_html}</div>
    </div>
    <div class="canvas">
        <h4 style="margin:0 0 10px 0; font-size:14px; color:#475569;">🎨 Diseño Hoja — Página {pagina}</h4>
        <div class="grid-folleto">{slots_html}</div>
    </div>
    <script>
        let draggedNode = null;
        document.querySelectorAll('.product-card').forEach(card => {{
            card.addEventListener('dragstart', () => {{ draggedNode = card; card.style.opacity = '0.4'; }});
            card.addEventListener('dragend', () => {{ draggedNode = null; card.style.opacity = '1'; }});
        }});
        document.querySelectorAll('.slot').forEach(slot => {{
            slot.addEventListener('dragover', (e) => {{ e.preventDefault(); slot.classList.add('drag-over'); }});
            slot.addEventListener('dragleave', () => slot.classList.remove('drag-over'));
            slot.addEventListener('drop', () => {{
                slot.classList.remove('drag-over');
                if (draggedNode) {{
                    const ph = slot.querySelector('.placeholder'); if(ph) ph.remove();
                    slot.appendChild(draggedNode);
                    window.parent.postMessage({{type: 'streamlit:setComponentValue', value: JSON.stringify({{id_oferta: parseInt(draggedNode.id), posicion_slot: parseInt(slot.id), numero_pagina: {pagina}, timestamp: Date.now()}})}}, '*');
                }}
            }});
        }});
        const bZone = document.getElementById('banco-disponibles'), bLista = document.getElementById('banco-lista');
        bZone.addEventListener('dragover', (e) => {{ e.preventDefault(); bZone.classList.add('drag-over'); }});
        bZone.addEventListener('dragleave', () => bZone.classList.remove('drag-over'));
        bZone.addEventListener('drop', () => {{
            bZone.classList.remove('drag-over');
            if(draggedNode) {{
                bLista.appendChild(draggedNode);
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: JSON.stringify({{id_oferta: parseInt(draggedNode.id), posicion_slot: 0, numero_pagina: 0, timestamp: Date.now()}})}}, '*');
            }}
        }});
    </script></body></html>"""

# ==============================================================================
# 8. RENDERIZADO INTERACTIVO FINAL Y PROCESAMIENTO INMUNE (CON PUENTE REAL JS->PY)
# ==============================================================================
def generar_canvas_ofertas_corregido(ofertas, pagina, num_slots, cols, rows):
    try:
        banco_html = ""
        slots_ocupados = {}
        
        try:
            num_slots = int(float(str(num_slots).strip()))
        except (ValueError, TypeError):
            num_slots = 4

        for o in ofertas:
            if not isinstance(o, dict):
                continue
                
            img_url = o.get('img') if o.get('img') else "https://picsum.photos"
            raw_p = o.get('numero_pagina')
            raw_s = o.get('posicion_slot')
            
            es_p = raw_p is not None and str(raw_p).lower() != "null" and str(raw_p).strip() != "" and str(raw_p) != "0"
            es_s = raw_s is not None and str(raw_s).lower() != "null" and str(raw_s).strip() != "" and str(raw_s) != "0"
            
            card = f'''<div class="product-card" draggable="true" id="{o.get('id_oferta', '')}">
            <img src="{img_url}"><div class="info"><span class="name">{o.get('nombre', 'Sin Nombre')}</span><span class="price">${o.get('precio_oferta', 0)}</span></div>
            </div>'''
            
            if es_p and es_s:
                try:
                    p_int = int(float(str(raw_p).strip()))
                    s_int = int(float(str(raw_s).strip()))
                    
                    if p_int == pagina:
                        if 1 <= s_int <= num_slots:
                            slots_ocupados[s_int] = card
                        else:
                            banco_html += card
                    else:
                        banco_html += f'<div style="display:none !important;" class="hidden-item-dom">{card}</div>'
                except (ValueError, TypeError):
                    banco_html += card
            else:
                if es_p:
                    try:
                        p_int = int(float(str(raw_p).strip()))
                        if p_int != pagina:
                            banco_html += f'<div style="display:none !important;" class="hidden-item-dom">{card}</div>'
                        else:
                            banco_html += card
                    except (ValueError, TypeError):
                        banco_html += card
                else:
                    banco_html += card

        slots_html = ""
        for i in range(1, num_slots + 1):
            contenido_slot = slots_ocupados.get(i, f'<div class="placeholder">Posición Slot {i}</div>')
            slots_html += f'<div class="slot" id="{i}">{contenido_slot}</div>'
        
        # Convertimos las variables de columnas y filas a strings limpios
        style_cols = str(cols)
        style_rows = str(rows)

        return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
        body {{ font-family: system-ui, sans-serif; margin: 0; background: #f8f9fa; display: flex; gap: 20px; padding: 10px; }}
        .sidebar {{ width: 280px; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; max-height:500px; overflow-y:auto; }}
        .sidebar.drag-over {{ background: #fff5f5; border: 2px dashed #dc3545; }}
        .canvas {{ flex: 1; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; }}
        .slot {{ border: 2px dashed #cbd5e1; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: center; min-height: 90px; padding: 5px; }}
        .slot.drag-over {{ border-color: #3b82f6; background: #eff6ff; }}
        .product-card {{ background: white; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px; cursor: grab; display: flex; gap: 10px; width: 100%; box-sizing: border-box; }}
        .product-card img {{ width: 45px; height: 45px; object-fit: cover; border-radius: 4px; pointer-events: none; }}
        .product-card .info {{ display: flex; flex-direction: column; font-size: 12px; overflow: hidden; pointer-events: none; }}
        .product-card .price {{ color: #16a34a; font-weight: 700; margin-top: 2px; }}
        .product-card .name {{ font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .placeholder {{ color: #94a3b8; font-size: 13px; text-align: center; pointer-events: none; user-select: none; }}
        </style></head><body>
        <div class="sidebar" id="banco-disponibles">
            <h4 style="margin:0 0 10px 0; font-size:14px; color: #475569;">Banco Productos</h4>
            <div style="display: flex; flex-direction: column; gap:8px; min-height:400px;" id="banco-lista">{banco_html}</div>
        </div>
        <div class="canvas">
            <h4 style="margin:0 0 10px 0; font-size: 14px; color: #475569;">Diseño Hoja Página {pagina}</h4>
            <!-- Inyectamos los estilos de grilla de forma directa en el estilo del elemento para no romper las llaves CSS -->
            <div class="grid-folleto" style="display: grid; grid-template-columns: {style_cols}; grid-template-rows: {style_rows}; gap: 12px; min-height: 400px;">
                {slots_html}
            </div>
        </div>

        <script>
        function enviarDatosAStreamlit(payload) {{
            const mensaje = {{
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: JSON.stringify(payload)
            }};
            window.parent.postMessage(mensaje, "*");
        }}

        let draggedNode = null;
        document.querySelectorAll('.product-card').forEach(card => {{
            card.addEventListener('dragstart', () => {{ draggedNode = card; card.style.opacity = '0.4'; }});
            card.addEventListener('dragend', () => {{ draggedNode = null; card.style.opacity = '1'; }});
        }});
        
        document.querySelectorAll('.slot').forEach(slot => {{
            slot.addEventListener('dragover', (e) => {{ e.preventDefault(); slot.classList.add('drag-over'); }});
            slot.addEventListener('dragleave', () => slot.classList.remove('drag-over'));
            slot.addEventListener('drop', () => {{
                slot.classList.remove('drag-over');
                if (draggedNode) {{
                    const ph = slot.querySelector('.placeholder'); if(ph) ph.remove();
                    slot.appendChild(draggedNode);
                    
                    enviarDatosAStreamlit({{
                        id_oferta: draggedNode.id,
                        numero_pagina: {pagina},
                        posicion_slot: slot.id,
                        timestamp: Date.now()
                    }});
                }}
            }});
        }});
        
        const bZone = document.getElementById('banco-disponibles');
        const bLista = document.getElementById('banco-lista');
        bZone.addEventListener('dragover', (e) => {{ e.preventDefault(); bZone.classList.add('drag-over'); }});
        bZone.addEventListener('dragleave', () => bZone.classList.remove('drag-over'));
        bZone.addEventListener('drop', () => {{
            bZone.classList.remove('drag-over');
            if(draggedNode) {{
                bLista.appendChild(draggedNode);
                
                enviarDatosAStreamlit({{
                    id_oferta: draggedNode.id,
                    numero_pagina: null,
                    posicion_slot: null,
                    timestamp: Date.now()
                }});
            }}
        }});
        </script></body></html>"""
    except Exception as e:
        # Si algo falla, devolvemos un HTML plano sin llaves conflictivas para que no rompa Streamlit
        return "<h3>Error en generacion de interfaz HTML</h3>"

# Invocación limpia
lista_ofertas_segura = st.session_state.ofertas if "ofertas" in st.session_state else []
html_renderizado = generar_canvas_ofertas_corregido(
    lista_ofertas_segura, 
    int(pag_act), 
    slots_deseados, 
    columnas_css, 
    filas_css
)

# Validamos que el String sea correcto antes de renderizar
if not isinstance(html_renderizado, str) or "Error" in html_renderizado:
    st.error("Hubo un problema al estructurar los datos del lienzo visual.")
    st.stop()

with st.container():
    evento_drag_drop = st.components.v1.html(
        html_renderizado, 
        height=540, 
        scrolling=False, 
        key=f"canvas_maquetador_pag_{pag_act}"
    )

if evento_drag_drop:
    try:
        datos = json.loads(evento_drag_drop)
        evento_ts = datos.get("timestamp", 0)
        
        if evento_ts > st.session_state.get("ultimo_ts_procesado", 0):
            id_mod = datos.get("id_oferta")
            nueva_p = datos.get("numero_pagina")
            nuevo_s = datos.get("posicion_slot")
            cambio = False
            
            if "ofertas" in st.session_state:
                for ofer in st.session_state.ofertas:
                    if str(ofer.get("id_oferta")) == str(id_mod):
                        val_p = None if nueva_p is None else int(nueva_p)
                        val_s = None if nuevo_s is None else int(nuevo_s)
                        
                        if ofer.get("numero_pagina") != val_p or ofer.get("posicion_slot") != val_s:
                            ofer["numero_pagina"] = val_p
                            ofer["posicion_slot"] = val_s
                            cambio = True
                
                st.session_state.ultimo_ts_procesado = evento_ts
                if cambio:
                    st.rerun()
    except Exception:
        pass



# ==============================================================================
# 9. PREPARACIÓN DE OUTPUT Y CÁLCULOS MATEMÁTICOS DE MAQUETA
# ==============================================================================
st.markdown(f"### 📊 Registros Procesados de la Página {pag_act}")

# Detectamos de manera segura el ID numérico de la campaña activa
id_campana_real = 0
if "selector_campana_activa" in st.session_state and "dict_campanas_opciones" in locals():
    label = st.session_state["selector_campana_activa"]
    id_campana_real = dict_campanas_opciones.get(label, 0)
elif "id_campana_activa" in locals():
    id_campana_real = id_campana_activa

# Detectamos configuración de layout actual
tipo_distribucion = cfg.get("distribucion", "Equilibrado") if 'cfg' in locals() else "Equilibrado"
sub_estilo = cfg.get("estilo", "Estándar") if 'cfg' in locals() else "Estándar"

# ¡CORREGIDO!: Inicialización de lista vacía para evitar el SyntaxError
filas_tabla_ofertas = []

if "ofertas" in st.session_state:
    for o in st.session_state.ofertas:
        if o.get("numero_pagina") is not None and str(o["numero_pagina"]) != "null" and int(o["numero_pagina"]) == pag_act:
            slot = o.get("posicion_slot")
            
            num_fila = ((int(slot) - 1) // 2) + 1 if slot else None
            num_columna = ((int(slot) - 1) % 2) + 1 if slot else None
            
            fila = {
                "id_oferta": o.get("id_oferta"),
                "id_producto": o.get("id_producto"),
                "id_campana": int(id_campana_real),
                "numero_pagina": int(o["numero_pagina"]),
                "posicion_slot": int(slot) if slot else None,
                "precio_oferta": o.get("precio_oferta"),
                "posicion_mix": tipo_distribucion,
                "sub_molde_estilo": sub_estilo,
                "numero_fila": num_fila,
                "numero_columna": num_columna
            }
            filas_tabla_ofertas.append(fila)

if filas_tabla_ofertas:
    st.dataframe(filas_tabla_ofertas, use_container_width=True)
else:
    st.info("Ninguna oferta asignada en esta hoja todavía. Arrastra elementos desde el banco de la campaña.")


# ==============================================================================
# 10. EJECUCIÓN DIRECTA DEL UPSERT MULTI-PÁGINA EN SUPABASE (BOTÓN ÚNICO BLINDADO)
# ==============================================================================
lote_para_guardar = filas_tabla_ofertas

if st.button("Guardar Configuración Completa del Folleto", type="primary", use_container_width=True):
    if lote_para_guardar:
        with st.spinner("Sincronizando cambios con Supabase..."):
            try:
                # Actualización directa por ID en Supabase
                resultado = supabase.table("ofertas").upsert(lote_para_guardar).execute()
                st.success("¡Sincronización Exitosa! Se actualizaron los registros en la nube.")
                st.toast("Base de datos actualizada correctamente", icon="✅")
                
                # Limpiamos la caché del session_state para forzar la lectura fresca de datos
                if "ofertas" in st.session_state:
                    del st.session_state.ofertas
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al impactar la tabla ofertas en Supabase: {str(e)}")
    else:
        st.warning("⚠️ La maqueta actual no cuenta con elementos cargados en esta página para persistir.")

