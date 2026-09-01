import streamlit as st
import streamlit.components.v1 as components
import json
from supabase import create_client, Client

# 1. CONFIGURACIÓN DE LA PÁGINA Y CONEXIÓN A SUPABASE
st.set_page_config(layout="wide", page_title="Maquetador Profesional de Ofertas")
st.title("🎨 Maquetador Drag & Drop con Sincronización a Supabase")

# Inicialización del cliente de Supabase (Sustituye con tus credenciales seguras de st.secrets)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "tu-anon-key-de-supabase")

@st.cache_resource
def inicializar_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = inicializar_supabase()

# 2. ESTADO GLOBAL DE LA SESIÓN (Navegación y Memoria Volátil)
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = 1

if "config_paginas" not in st.session_state:
    st.session_state.config_paginas = {}

# Carga inicial de ofertas desde Supabase (Si la sesión está vacía)
if "ofertas" not in st.session_state:
    # En producción usarás: 
    # respuesta = supabase.table("ofertas").select("*").execute()
    # st.session_state.ofertas = respuesta.data
    st.session_state.ofertas = [
        {"id_oferta": 101, "id_producto": 501, "nombre": "Champú Anticaspa", "precio_oferta": 4.99, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 102, "id_producto": 502, "nombre": "Detergente Líquido", "precio_oferta": 12.50, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 103, "id_producto": 503, "nombre": "Café Molido 500g", "precio_oferta": 3.20, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 104, "id_producto": 504, "nombre": "Leche Entera 1L", "precio_oferta": 1.10, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 105, "id_producto": 505, "nombre": "Aceite de Oliva", "precio_oferta": 8.95, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 106, "id_producto": 506, "nombre": "Arroz Integral 1kg", "precio_oferta": 1.80, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
    ]

# 3. CONTROLES SUPERIORES DE NAVEGACIÓN Y PLANTILLAS
st.markdown("### 🛠️ Panel de Control y Configuración de Plantillas")
with st.container(border=True):
    # Añadimos los botones de paginación para cambiar con un clic
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1, 1, 1, 2, 2, 2], vertical_alignment="center")
    
    with nav_col1:
        if st.button("◀ Anterior", use_container_width=True) and st.session_state.pagina_actual > 1:
            st.session_state.pagina_actual -= 1
            st.rerun()
            
    with nav_col2:
        st.markdown(f"<h3 style='text-align: center; margin:0;'>Pág. {st.session_state.pagina_actual}</h3>", unsafe_allow_html=True)
        
    with nav_col3:
        if st.button("Siguiente ▶", use_container_width=True):
            st.session_state.pagina_actual += 1
            st.rerun()

    # Recuperación de la página activa
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

# Definición automática de la rejilla CSS Grid
def calcular_layout_grid(num_slots):
    if num_slots == 1: return "1fr", "1fr"
    if num_slots == 2: return "repeat(2, 1fr)", "1fr"
    if num_slots in (3, 4): return "repeat(2, 1fr)", "repeat(2, 1fr)"
    if num_slots in (5, 6): return "repeat(2, 1fr)", "repeat(3, 1fr)"
    return "repeat(2, 1fr)", "repeat(4, 1fr)"

columnas_css, filas_css = calcular_layout_grid(slots_deseados)

# 4. GENERADOR DEL COMPONENTE INTERACTIVO DRAG & DROP
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
        elif o['numero_pagina'] is None:
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
            <h4 style="margin:0; font-size:14px; color:#475569; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">📦 Banco de Ofertas</h4>
            <div id="banco">{banco_html}</div>
        </div>
        <div class="canvas">
            <h4 style="margin:0 0 10px 0; font-size:14px; color:#475569;">📖 Cuadrante de Diseño — Página {pagina}</h4>
            <div class="grid-folleto">{slots_html}</div>
        </div>
        <script>
            let draggedNode = null;
            document.querySelectorAll('.product-card').forEach(card => {{
                card.addEventListener('dragstart', () => {{ draggedNode = card; card.style.opacity = '0.4'; }});
                card.addEventListener('dragend', () => {{ draggedNode = card; card.style.opacity = '1'; }});
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

# 5. RENDERIZADO DE LA UI DRAG & DROP Y CAPTURA DE EVENTOS
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

# 6. CÁLCULO MATEMÁTICO DE FILAS / COLUMNAS E INYECCIÓN DE OUTPUT
st.markdown(f"### 📊 Registros Procesados de la Página {pag_act}")

# Generación blindada en una línea compacta para evitar fallos del formateador
filas_tabla_ofertas = [{"id_oferta": o["id_oferta"], "id_producto": o["id_producto"], "id_campana": 12, "numero_pagina": o["numero_pagina"], "posicion_slot": o["posicion_slot"], "precio_oferta": o["precio_oferta"], "posicion_mix": tipo_distribucion, "sub_molde_estilo": sub_estilo, "numero_fila": ((int(o["posicion_slot"]) - 1) // 2) + 1, "numero_columna": ((int(o["posicion_slot"]) - 1) % 2) + 1} for o in st.session_state.ofertas if o["numero_pagina"] == pag_act]

if filas_tabla_ofertas:
    st.dataframe(filas_tabla_ofertas, use_container_width=True)
else:
    st.info("Ninguna oferta asignada en esta hoja todavía. Arrastra ítems para poblar la rejilla.")

# 7. BOTÓN DE SINCRONIZACIÓN DIRECTA (UPSERT MASIVO)
if st.button("💾 Ejecutar UPSERT Masivo en Supabase", type="primary", use_container_width=True):
    if filas_tabla_ofertas:
        try:
            # Ejecuta la sincronización contra tu tabla real 'ofertas' mapeando por clave primaria
            resultado = supabase.table("ofertas").upsert(filas_tabla_ofertas).execute()
            st.success(f"¡Sincronización Exitosa! {len(resultado.data)} registros sincronizados en public.ofertas.")
            st.toast("Base de datos actualizada con éxito", icon="⚡")
        except Exception as e:
            st.error(f"Error al conectar con Supabase: {str(e)}")
    else:
        st.warning("No hay registros asignados para guardar en esta página.")
