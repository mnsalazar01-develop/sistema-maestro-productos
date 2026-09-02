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

# 2. FILTRADO DE CAMPAÑAS VÁLIDAS CON VALORES EN OFERTAS
try:
    resp_ofertas_ids = supabase.table("ofertas").select("id_campana").execute()
    ids_campanas_con_ofertas = list(set([o["id_campana"] for o in resp_ofertas_ids.data if o.get("id_campana") is not None]))

    if not ids_campanas_con_ofertas:
        st.warning("⚠️ No hay ninguna campaña con ofertas registradas actualmente en la base de datos.")
        st.stop()

    resp_campanas = supabase.table("campanas").select("id_campana, nombre_campana").in_("id_campana", ids_campanas_con_ofertas).order("id_campana", desc=True).execute()
    lista_campanas = resp_campanas.data
    
    if not lista_campanas:
        st.warning("⚠️ No se pudieron emparejar las ofertas con registros válidos en la tabla campanas.")
        st.stop()
        
    dict_campanas_opciones = {f"{c['id_campana']} - {c['nombre_campana']}": c['id_campana'] for c in lista_campanas}
except Exception as e:
    st.error(f"❌ Error al filtrar campañas con valores: {str(e)}")
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

# 4. CONSULTA INMUNE AL ERROR 404 (Ofertas + Productos vinculados + Tipos Blindados)
try:
    resp_ofertas = supabase.table("ofertas").select("*").eq("id_campana", id_campana_activa).execute()
    ofertas_campana = resp_ofertas.data
    
    lista_id_productos = list(set([o["id_producto"] for o in ofertas_campana if o.get("id_producto") is not None]))
    
    dict_productos = {}
    urls_totales_a_firmar = []
    
    if lista_id_productos:
        resp_prod = supabase.table("productos").select("id_producto, nombre, url_imagen").in_("id_producto", lista_id_productos).execute()
        dict_productos = {p["id_producto"]: p for p in resp_prod.data}
        urls_totales_a_firmar = list(set([p.get("url_imagen") for p in resp_prod.data if p.get("url_imagen")]))
    
    mapa_imagenes_firmadas = firmar_lote_imagenes(urls_totales_a_firmar)
    
    for o in ofertas_campana:
        # --- 🟢 CORRECCIÓN CRÍTICA DE TIPOS AQUÍ ---
        num_pag = o.get("numero_pagina")
        pos_slot = o.get("posicion_slot")
        
        if num_pag is not None and str(num_pag).lower() != "null" and str(num_pag).strip() != "":
            o["numero_pagina"] = int(num_pag)
        else:
            o["numero_pagina"] = None
            
        if pos_slot is not None and str(pos_slot).lower() != "null" and str(pos_slot).strip() != "":
            o["posicion_slot"] = int(pos_slot)
        else:
            o["posicion_slot"] = None
        # -------------------------------------------

        id_p = o.get("id_producto")
        if id_p in dict_productos:
            o["nombre"] = dict_productos[id_p].get("nombre") or f"Producto #{id_p}"
            url_original = dict_productos[id_p].get("url_imagen")
            o["img"] = mapa_imagenes_firmadas.get(url_original, url_original or "https://picsum.photos")
        else:
            o["nombre"] = f"Oferta sin producto asignado (# {o['id_oferta']})"
            o["img"] = "https://picsum.photos"
            
    st.session_state.ofertas = ofertas_campana
    
except Exception as e:
    st.error(f"Error al procesar el banco de datos en Supabase: {str(e)}")
    st.session_state.ofertas = []


# =====================================================================
# FUNCTION DECLARATION (Definida primero para evitar NameError)
# =====================================================================
def calcular_layout_grid(num_slots):
    if num_slots == 1: return "1fr", "1fr"
    if num_slots == 2: return "repeat(2, 1fr)", "1fr"
    if num_slots in (3, 4): return "repeat(2, 1fr)", "repeat(2, 1fr)"
    if num_slots in (5, 6): return "repeat(2, 1fr)", "repeat(3, 1fr)"
    return "repeat(2, 1fr)", "repeat(4, 1fr)"


# =====================================================================
# 5. CONTROLES DE LA PÁGINA SELECCIONADA (Sincronización Reactiva)
# =====================================================================
st.markdown("### 🛠️ Configuración de la Hoja del Folleto")

pag_act = int(st.session_state.pagina_actual)

# 1. Al estar limpios desde la sección 4, la extracción es directa y matemática
slots_usados_en_pagina = [
    o["posicion_slot"] 
    for o in st.session_state.ofertas 
    if o["numero_pagina"] == pag_act and o["posicion_slot"] is not None
]

slot_maximo_detectado = max(slots_usados_en_pagina) if slots_usados_en_pagina else 4

# 2. Inicializar o forzar la actualización si la BD supera el estado actual
if pag_act not in st.session_state.config_paginas:
    st.session_state.config_paginas[pag_act] = {
        "slots": slot_maximo_detectado, 
        "distribucion": "Equilibrado", 
        "estilo": "Estándar"
    }
else:
    if slot_maximo_detectado > int(st.session_state.config_paginas[pag_act]["slots"]):
        st.session_state.config_paginas[pag_act]["slots"] = slot_maximo_detectado

cfg = st.session_state.config_paginas[pag_act]

with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns(6)
    
    with nav_col1:
        if st.button("◀ Anterior", use_container_width=True) and st.session_state.pagina_actual > 1:
            st.session_state.pagina_actual -= 1
            st.rerun()
            
    with nav_col2:
        st.markdown(f"<h3 style='text-align: center; margin:0; color:#0d6efd;'>Pág. {st.session_state.pagina_actual}</h3>", unsafe_allow_html=True)
        
    with nav_col3:
        if st.button("Siguiente ▶", use_container_width=True):
            st.session_state.pagina_actual += 1
            st.rerun()

    with nav_col4:
        # El key dinámico "slider_pX_sY" destruye el estado viejo si el max detectado cambia
        slots_deseados = st.slider(
            "Slots asignados:", 
            min_value=1, 
            max_value=8, 
            value=int(cfg["slots"]),
            key=f"slider_p{pag_act}_max{slot_maximo_detectado}"
        )
        st.session_state.config_paginas[pag_act]["slots"] = slots_deseados
        
    with nav_col5:
        tipo_distribucion = st.selectbox("Distribución (`posicion_mix`):", ["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"], index=["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"].index(cfg["distribucion"]))
        st.session_state.config_paginas[pag_act]["distribucion"] = tipo_distribucion
        
    with nav_col6:
        sub_estilo = st.selectbox("Estilo (`sub_molde_estilo`):", ["Estándar", "Destacado", "Compacto"], index=["Estándar", "Destacado", "Compacto"].index(cfg["estilo"]))
        st.session_state.config_paginas[pag_act]["estilo"] = sub_estilo

columnas_css, filas_css = calcular_layout_grid(slots_deseados)

# 6. CONSTRUCTOR DEL COMPONENTE HTML VISUAL (Soporta agregar y devolver ofertas)
def generar_canvas_ofertas(ofertas, pagina, num_slots, cols, rows):
    banco_html = ""
    slots_ocupados = {}

    for o in ofertas:
        card_html = f'''
        <div class="product-card" draggable="true" id="{o['id_oferta']}">
            <img src="{o['img']}">
            <div class="info">
                <span class="name">{o['nombre']}</span>
                <span class="price">${o.get('precio_oferta', 0.00)}</span>
            </div>
        </div>
        '''
        has_page = o.get('numero_pagina') is not None and o.get('numero_pagina') != "" and o.get('numero_pagina') != "null"
        has_slot = o.get('posicion_slot') is not None and o.get('posicion_slot') != "" and o.get('posicion_slot') != "null"
        
        if has_page and has_slot and int(o['numero_pagina']) == pagina:
            slots_ocupados[int(o['posicion_slot'])] = card_html
        elif not has_page or o['numero_pagina'] == "null":
            banco_html += card_html

    slots_html = ""
    for i in range(1, num_slots + 1):
        contenido = slots_ocupados.get(i, f'<div class="placeholder">Posición Slot {i}<br><span>Disponible</span></div>')
        slots_html += f'<div class="slot" id="{i}">{contenido}</div>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; background: #f8f9fa; display: flex; gap: 20px; padding: 10px; height: 500px; box-sizing: border-box; }}
            .sidebar {{ width: 280px; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }}
            .sidebar.drag-over {{ background: #fff5f5; border: 2px dashed #dc3545; }}
            .canvas {{ flex: 1; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; flex-direction: column; }}
            .grid-folleto {{ display: grid; grid-template-columns: {cols}; grid-template-rows: {rows}; gap: 12px; flex: 1; }}
            .slot {{ border: 2px dashed #cbd5e1; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: center; text-align: center; position: relative; padding: 5px; box-sizing: border-box; }}
            .slot.drag-over {{ border-color: #3b82f6; background: #eff6ff; }}
            .product-card {{ background: white; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px; cursor: grab; display: flex; gap: 10px; align-items: center; width: 100%; box-sizing: border-box; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            .product-card img {{ width: 45px; height: 45px; object-fit: cover; border-radius: 4px; }}
            .product-card .info {{ display: flex; flex-direction: column; font-size: 12px; overflow: hidden; }}
            .product-card .name {{ font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .product-card .price {{ color: #16a34a; font-weight: 700; margin-top: 2px; }}
            .placeholder {{ color: #94a3b8; font-size: 13px; font-weight: 500; line-height: 1.3; user-select:none; pointer-events:none; }}
            .placeholder span {{ font-size: 10px; color: #cbd5e1; }}
        </style>
    </head>
    <body>
        <div class="sidebar" id="banco-disponibles">
            <h4 style="margin:0; font-size:14px; color:#475569; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">📦 Banco de la Campaña</h4>
            <div style="display:flex; flex-direction:column; gap:8px; min-height:400px;" id="banco-lista">{banco_html}</div>
        </div>
        
        <div class="canvas">
            <h4 style="margin:0 0 10px 0; font-size:14px; color:#475569;">📖 Cuadrante de Diseño — Página {pagina}</h4>
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
                slot.addEventListener('dragleave', () => {{ slot.classList.remove('drag-over'); }});
                slot.addEventListener('drop', () => {{
                    slot.classList.remove('drag-over');
                    if(draggedNode) {{
                        const ph = slot.querySelector('.placeholder');
                        if(ph) ph.remove();
                        slot.appendChild(draggedNode);
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: JSON.stringify({{ id_oferta: parseInt(draggedNode.id), posicion_slot: parseInt(slot.id), numero_pagina: {pagina} }})
                        }}, '*');
                    }}
                }});
            }});

            const bancoZone = document.getElementById('banco-disponibles');
            const bancoLista = document.getElementById('banco-lista');
            
            bancoZone.addEventListener('dragover', (e) => {{ e.preventDefault(); bancoZone.classList.add('drag-over'); }});
            bancoZone.addEventListener('dragleave', () => {{ bancoZone.classList.remove('drag-over'); }});
            bancoZone.addEventListener('drop', () => {{
                bancoZone.classList.remove('drag-over');
                if(draggedNode) {{
                    bancoLista.appendChild(draggedNode);
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: JSON.stringify({{ id_oferta: parseInt(draggedNode.id), posicion_slot: null, numero_pagina: null }})
                    }}, '*');
                }}
            }});
        </script>
    </body>
    </html>
    """

# 7. RENDERIZADO DE LA UI DRAG & DROP Y CAPTURA DE EVENTOS
html_renderizado = generar_canvas_ofertas(st.session_state.ofertas, pag_act, slots_deseados, columnas_css, filas_css)
evento_drag_drop = components.html(html_renderizado, height=520, scrolling=False)

if evento_drag_drop:
    try:
        datos = json.loads(evento_drag_drop)
        for ofer in st.session_state.ofertas:
            if ofer["id_oferta"] == datos["id_oferta"]:
                ofer["numero_pagina"] = datos["numero_pagina"]
                ofer["posicion_slot"] = datos["posicion_slot"]
    except Exception:
        pass

# 8. PREPARACIÓN DE OUTPUT Y CÁLCULOS MATEMÁTICOS DE MAQUETA
st.markdown(f"### 📊 Registros Procesados de la Página {pag_act}")

filas_tabla_ofertas = [{"id_oferta": o["id_oferta"], "id_producto": o["id_producto"], "id_campana": int(id_campana_activa), "numero_pagina": int(o["numero_pagina"]), "posicion_slot": int(o["posicion_slot"]), "precio_oferta": o.get("precio_oferta"), "posicion_mix": tipo_distribucion, "sub_molde_estilo": sub_estilo, "numero_fila": ((int(o["posicion_slot"]) - 1) // 2) + 1 if o.get("posicion_slot") else None, "numero_columna": ((int(o["posicion_slot"]) - 1) % 2) + 1 if o.get("posicion_slot") else None} for o in st.session_state.ofertas if o.get("numero_pagina") is not None and str(o["numero_pagina"]) != "null" and int(o["numero_pagina"]) == pag_act]

if filas_tabla_ofertas:
    st.dataframe(filas_tabla_ofertas, use_container_width=True)
else:
    st.info("Ninguna oferta asignada en esta hoja todavía. Arrastra elementos desde el banco de la campaña.")

# 9. DETECCIÓN DE ELEMENTOS DEVUELTOS
filas_desasignadas = [{"id_oferta": o["id_oferta"], "id_producto": o["id_producto"], "id_campana": int(id_campana_activa), "numero_pagina": None, "posicion_slot": None, "numero_fila": None, "numero_columna": None} for o in st.session_state.ofertas if o.get("numero_pagina") is None or str(o["numero_pagina"]) == "null"]

# 10. EJECUCIÓN DIRECTA DEL UPSERT EN SUPABASE
if st.button("💾 Guardar Configuración y Distribución en Supabase", type="primary", use_container_width=True):
    lote_sincronizacion = filas_tabla_ofertas + filas_desasignadas
    if lote_sincronizacion:
        try:
            resultado = supabase.table("ofertas").upsert(lote_sincronizacion).execute()
            st.success(f"¡Sincronización Completada! {len(resultado.data)} registros sincronizados con éxito (maquetados y devueltos al banco).")
            st.toast("Base de datos en la nube actualizada", icon="⚡")
        except Exception as e:
            st.error(f"Error al impactar la tabla ofertas en Supabase: {str(e)}")
    else:
        st.warning("La maqueta actual no cuenta con elementos asignados para persistir.")
