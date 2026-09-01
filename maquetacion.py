import streamlit as st
import streamlit.components.v1 as components
import json
from supabase import create_client, Client

# Configuración de la página en modo ancho completo sin barra lateral
st.set_page_config(layout="wide", page_title="Maquetador Profesional de Ofertas")
st.title("🎨 Maquetador Drag & Drop — Filtro por Campaña")

# 1. CONEXIÓN Y CONFIGURACIÓN DE SUPABASE
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "tu-key-de-supabase")

@st.cache_resource
def inicializar_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = inicializar_supabase()

# Inicialización de estados de navegación en session_state
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = 1

if "config_paginas" not in st.session_state:
    st.session_state.config_paginas = {}

# 2. PANEL DE SELECCIÓN DE CAMPAÑA (Filtro Principal)
st.markdown("### 🔍 Selección de Campaña de Trabajo")
with st.container(border=True):
    col_campana, col_info = st.columns([1, 3], vertical_alignment="center")
    with col_campana:
        id_campana_activa = st.number_input(
            "Ingrese el ID de la Campaña:", 
            min_value=1, 
            value=12, 
            key="input_id_campana"
        )
    with col_info:
        st.caption("⚠️ Al cambiar el ID de la campaña se descargará el surtido real de ofertas y productos vinculados directamente desde Supabase.")

# 3. CONSULTA RELACIONAL EN TIEMPO REAL (Armado del Banco de Datos)
try:
    # Traemos las ofertas de la campaña seleccionada realizando el JOIN implícito con la tabla productos
    respuesta = supabase.table("ofertas").select("*, productos(nombre, url_imagen)").eq("id_campana", id_campana_activa).execute()
    ofertas_campana = respuesta.data
    
    # Procesamos el mapeo de datos para alimentar de forma correcta el componente gráfico
    for o in ofertas_campana:
        if o.get("productos"):
            o["nombre"] = o["productos"].get("nombre") or f"Prod #{o['id_producto']}"
            o["img"] = o["productos"].get("url_imagen") or "https://picsum.photos"
        else:
            o["nombre"] = f"Oferta sin producto (#{o['id_oferta']})"
            o["img"] = "https://picsum.photos"
            
    st.session_state.ofertas = ofertas_campana
    
except Exception as e:
    st.error(f"Error al consultar datos relacionales en Supabase: {str(e)}")
    st.session_state.ofertas = []

# 4. CONTROLES DE LA PÁGINA SELECCIONADA (Navegación por Clic)
st.markdown("### 🛠️ Configuración de la Hoja del Folleto")
with st.container(border=True):
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1.5, 1, 1.5, 3, 3, 3], vertical_alignment="center")
    
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
        tipo_distribucion = st.selectbox(
            "Distribución (`posicion_mix`):",
            ["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"],
            index=["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"].index(cfg["distribucion"])
        )
        st.session_state.config_paginas[pag_act]["distribucion"] = tipo_distribucion
        
    with nav_col6:
        sub_estilo = st.selectbox(
            "Estilo (`sub_molde_estilo`):",
            ["Estándar", "Destacado", "Compacto"],
            index=["Estándar", "Destacado", "Compacto"].index(cfg["estilo"])
        )
        st.session_state.config_paginas[pag_act]["estilo"] = sub_estilo

def calcular_layout_grid(num_slots):
    if num_slots == 1: return "1fr", "1fr"
    if num_slots == 2: return "repeat(2, 1fr)", "1fr"
    if num_slots in (3, 4): return "repeat(2, 1fr)", "repeat(2, 1fr)"
    if num_slots in (5, 6): return "repeat(2, 1fr)", "repeat(3, 1fr)"
    return "repeat(2, 1fr)", "repeat(4, 1fr)"

columnas_css, filas_css = calcular_layout_grid(slots_deseados)

# 5. CONSTRUCTOR DEL COMPONENTE HTML VISUAL
def generar_canvas_ofertas(ofertas, pagina, num_slots, cols, rows):
    banco_html = ""
    slots_ocupados = {}

    for o in ofertas:
        card_html = f'''
        <div class="product-card" draggable="true" id="{o['id_oferta']}">
            <img src="{o['img']}">
            <div class="info">
                <span class="name">{o['nombre']}</span>
                <span class="price">${o['precio_oferta']}</span>
            </div>
        </div>
        '''
        if o['numero_pagina'] == pagina and o['posicion_slot']:
            slots_ocupados[int(o['posicion_slot'])] = card_html
        elif o['numero_pagina'] is None or o['numero_pagina'] == "":
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
# 6. RENDERIZADO DE LA UI DRAG & DROP Y CAPTURA DE EVENTOS
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

# 7. PREPARACIÓN DE OUTPUT Y CÁLCULOS MATEMÁTICOS DE MAQUETA (Fila y Columna)
st.markdown(f"### 📊 Registros Procesados de la Página {pag_act}")

# Generación en una sola línea compacta para garantizar la resiliencia del compilador frente a sangrías
filas_tabla_ofertas = [{"id_oferta": o["id_oferta"], "id_producto": o["id_producto"], "id_campana": id_campana_activa, "numero_pagina": o["numero_pagina"], "posicion_slot": o["posicion_slot"], "precio_oferta": o["precio_oferta"], "posicion_mix": tipo_distribucion, "sub_molde_estilo": sub_estilo, "numero_fila": ((int(o["posicion_slot"]) - 1) // 2) + 1, "numero_columna": ((int(o["posicion_slot"]) - 1) % 2) + 1} for o in st.session_state.ofertas if o["numero_pagina"] == pag_act]

if filas_tabla_ofertas:
    st.dataframe(filas_tabla_ofertas, use_container_width=True)
else:
    st.info("Ninguna oferta asignada en esta hoja todavía. Arrastra elementos desde el banco de la campaña.")

# 8. EJECUCIÓN DIRECTA DEL UPSERT EN SUPABASE
if st.button("💾 Guardar Configuración y Distribución en Supabase", type="primary", use_container_width=True):
    if filas_tabla_ofertas:
        try:
            # Enviamos los datos directamente a Postgresql mapeando sobre la PK id_oferta
            resultado = supabase.table("ofertas").upsert(filas_tabla_ofertas).execute()
            st.success(f"¡Sincronización Completada! {len(resultado.data)} registros guardados con éxito para el generador automático.")
            st.toast("Base de datos en la nube actualizada", icon="⚡")
        except Exception as e:
            st.error(f"Error al impactar la tabla ofertas en Supabase: {str(e)}")
    else:
        st.warning("La maqueta actual no cuenta con elementos asignados para persistir.")
