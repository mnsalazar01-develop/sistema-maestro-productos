import streamlit as st
import streamlit.components.v1 as components
import json
from supabase import create_client, Client

# Configuración de la interfaz en modo panorámico sin barra lateral
st.set_page_config(layout="wide", page_title="Maquetador Profesional de Ofertas")
st.title("🎨 Maquetador Drag & Drop — Campañas con Ofertas Activas")

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
    # Paso A: Traer los IDs únicos de campaña que existen en la tabla ofertas
    resp_ofertas_ids = supabase.table("ofertas").select("id_campana").execute()
    ids_campanas_con_ofertas = list(set([o["id_campana"] for o in resp_ofertas_ids.data if o.get("id_campana") is not None]))

    if not ids_campanas_con_ofertas:
        st.warning("⚠️ No hay ninguna campaña con ofertas registradas actualmente en la base de datos.")
        st.stop()

    # Paso B: Consultar los nombres de la tabla campanas filtrando solo por esos IDs válidos
    resp_campanas = supabase.table("campanas").select("id_campana, nombre_campana").in_("id_campana", ids_campanas_con_ofertas).order("id_campana", desc=True).execute()
    lista_campanas = resp_campanas.data
    
    if not lista_campanas:
        st.warning("⚠️ No se pudieron emparejar las ofertas con registros válidos en la tabla campanas.")
        st.stop()
        
    # Crear diccionario para el mapeo del selector visual
    dict_campanas_opciones = {f"{c['id_campana']} - {c['nombre_campana']}": c['id_campana'] for c in lista_campanas}
except Exception as e:
    st.error(f"❌ Error al filtrar campañas con valores: {str(e)}")
    st.stop()

# 3. PANEL DE SELECCIÓN DE CAMPAÑA FILTRADA (Filtro Superior Principal)
st.markdown("### 🔍 Selección de Campaña de Trabajo")
with st.container(border=True):
    col_campana, col_info = st.columns([1, 2], vertical_alignment="center")
    with col_campana:
        campana_seleccionada_label = st.selectbox(
            "Campañas con ofertas disponibles:",
            options=list(dict_campanas_opciones.keys()),
            key="selector_campana_activa"
        )
        id_campana_activa = dict_campanas_opciones[campana_seleccionada_label]
    with col_info:
        st.success(f"🟢 Surtido validado. Desplegando ofertas activas de la Campaña ID: {id_campana_activa}")

# 4. CONSULTA INMUNE AL ERROR 404 (Ofertas + Productos vinculados)
try:
    resp_ofertas = supabase.table("ofertas").select("*").eq("id_campana", id_campana_activa).execute()
    ofertas_campana = resp_ofertas.data
    
    lista_id_productos = list(set([o["id_producto"] for o in ofertas_campana if o.get("id_producto") is not None]))
    
    dict_productos = {}
    if lista_id_productos:
        resp_prod = supabase.table("productos").select("id_producto, nombre, url_imagen").in_("id_producto", lista_id_productos).execute()
        dict_productos = {p["id_producto"]: p for p in resp_prod.data}
    
    for o in ofertas_campana:
        id_p = o.get("id_producto")
        if id_p in dict_productos:
            o["nombre"] = dict_productos[id_p].get("nombre") or f"Producto #{id_p}"
            o["img"] = dict_productos[id_p].get("url_imagen") or "https://picsum.photos"
        else:
            o["nombre"] = f"Oferta sin producto asignado (# {o['id_oferta']})"
            o["img"] = "https://picsum.photos"
            
    st.session_state.ofertas = ofertas_campana
    
except Exception as e:
    st.error(f"Error al procesar el banco de datos en Supabase: {str(e)}")
    st.session_state.ofertas = []

# 5. CONTROLES DE LA PÁGINA SELECCIONADA (Navegación Dinámica por Clic)
st.markdown("### 🛠️ Configuración de la Hoja del Folleto")
with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1, 1, 1, 2, 2, 2], vertical_alignment="center")
    
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

    pag_act = st.session_state.pagina_actual
    if pag_act not in st.session_state.config_paginas:
        st.session_state.config_paginas[pag_act] = {"slots": 4, "distribucion": "Equilibrado", "estilo": "Estándar"}
    cfg = st.session_state.config_paginas[pag_act]

    with nav_col4:
        slots_deseados = st.slider("Slots asignados:", min_value=1, max_value=8, value=cfg["slots"])
        st.session_state.config_paginas[pag_act]["slots"] = slots_deseados
        
    with nav_col5:
        tipo_distribucion = st.selectbox("Distribución (`posicion_mix`):", ["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"], index=["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"].index(cfg["distribucion"]))
        st.session_state.config_paginas[pag_act]["distribucion"] = tipo_distribucion
        
    with nav_col6:
        sub_estilo = st.selectbox("Estilo (`sub_molde_estilo`):", ["Estándar", "Destacado", "Compacto"], index=["Estándar", "Destacado", "Compacto"].index(cfg["estilo"]))
        st.session_state.config_paginas[pag_act]["estilo"] = sub_estilo

def calcular_layout_grid(num_slots):
    if num_slots == 1: return "1fr", "1fr"
    if num_slots == 2: return "repeat(2, 1fr)", "1fr"
    if num_slots in (3, 4): return "repeat(2, 1fr)", "repeat(2, 1fr)"
    if num_slots in (5, 6): return "repeat(2, 1fr)", "repeat(3, 1fr)"
    return "repeat(2, 1fr)", "repeat(4, 1fr)"

columnas_css, filas_css = calcular_layout_grid(slots_deseados)
# 6. CONSTRUCTOR DEL COMPONENTE HTML VISUAL
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
        has_page = o.get('numero_pagina') is not None and o.get('numero_pagina') != ""
        has_slot = o.get('posicion_slot') is not None and o.get('posicion_slot') != ""
        
        if has_page and has_slot and int(o['numero_pagina']) == pagina:
            slots_ocupados[int(o['posicion_slot'])] = card_html
        elif not has_page:
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
            .canvas {{ flex: 1; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; flex-direction: column; }}
            .grid-folleto {{ display: grid; grid-template-columns: {cols}; grid-template-rows: {rows}; gap: 12px; flex: 1; }}
            .slot {{ border: 2px dashed #cbd5e1; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: center; text-align: center; position: relative; padding: 5px; box-sizing: border-box; }}
            .slot.drag-over {{ border-color: #3b82f6; background: #eff6ff; }}
            .product-card {{ background: white; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px; cursor: grab; display: flex; gap: 10px; align-items: center; width: 100%; box-sizing: border-box; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            .product-card img {{ width: 45px; height: 45px; object-fit: cover; border-radius: 4px; }}
            .product-card .info {{ display: flex; flex-direction: column; font-size: 12px; overflow: hidden; }}
            .product-card .name {{ font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .product-card .price {{ color: #16a34a; font-weight: 700; margin-top: 2px; }}
            .placeholder {{ color: #94a3b8; font-size: 13px; font-weight: 500; line-height: 1.3; }}
            .placeholder span {{ font-size: 10px; color: #cbd5e1; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h4 style="margin:0; font-size:14px; color:#475569; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">📦 Banco de la Campaña</h4>
            <div id="banco" style="display:flex; flex-direction:column; gap:8px;">{banco_html}</div>
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

# 8. PREPARACIÓN DE OUTPUT Y CÁLCULOS MATEMÁTICOS DE MAQUETA (Fila y Columna)
st.markdown(f"### 📊 Registros Procesados de la Página {pag_act}")

filas_tabla_ofertas = [{"id_oferta": o["id_oferta"], "id_producto": o["id_producto"], "id_campana": int(id_campana_activa), "numero_pagina": int(o["numero_pagina"]), "posicion_slot": int(o["posicion_slot"]), "precio_oferta": o.get("precio_oferta"), "posicion_mix": tipo_distribucion, "sub_molde_estilo": sub_estilo, "numero_fila": ((int(o["posicion_slot"]) - 1) // 2) + 1 if o.get("posicion_slot") else None, "numero_columna": ((int(o["posicion_slot"]) - 1) % 2) + 1 if o.get("posicion_slot") else None} for o in st.session_state.ofertas if o.get("numero_pagina") is not None and int(o["numero_pagina"]) == pag_act]

if filas_tabla_ofertas:
    st.dataframe(filas_tabla_ofertas, use_container_width=True)
else:
    st.info("Ninguna oferta asignada en esta hoja todavía. Arrastra elementos desde el banco de la campaña.")

# 9. EJECUCIÓN DIRECTA DEL UPSERT EN SUPABASE
if st.button("💾 Guardar Configuración y Distribución en Supabase", type="primary", use_container_width=True):
    if filas_tabla_ofertas:
        try:
            resultado = supabase.table("ofertas").upsert(filas_tabla_ofertas).execute()
            st.success(f"¡Sincronización Completada! {len(resultado.data)} registros guardados con éxito para el generador automático.")
            st.toast("Base de datos en la nube actualizada", icon="⚡")
        except Exception as e:
            st.error(f"Error al impactar la tabla ofertas en Supabase: {str(e)}")
    else:
        st.warning("La maqueta actual no cuenta con elementos asignados para persistir.")
