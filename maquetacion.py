import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(layout="wide", page_title="Maquetador Profesional de Ofertas")
st.title("🎨 Configuración de Distribución y Maquetación de Folletos")

# 1. ESTADO GLOBAL (Simulación de base de datos)
if "ofertas" not in st.session_state:
    st.session_state.ofertas = [
        {"id_oferta": 101, "id_producto": 501, "nombre": "Champú Anticaspa", "precio_oferta": 4.99, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 102, "id_producto": 502, "nombre": "Detergente Líquido", "precio_oferta": 12.50, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 103, "id_producto": 503, "nombre": "Café Molido 500g", "precio_oferta": 3.20, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 104, "id_producto": 504, "nombre": "Leche Entera 1L", "precio_oferta": 1.10, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 105, "id_producto": 505, "nombre": "Aceite de Oliva", "precio_oferta": 8.95, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 106, "id_producto": 506, "nombre": "Arroz Integral 1kg", "precio_oferta": 1.80, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 107, "id_producto": 507, "nombre": "Galletas de Avena", "precio_oferta": 2.15, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
        {"id_oferta": 108, "id_producto": 508, "nombre": "Atún en Conserva", "precio_oferta": 1.45, "id_campana": 12, "numero_pagina": None, "posicion_slot": None, "img": "https://picsum.photos"},
    ]

# Registro de la configuración estructural de cada página
if "config_paginas" not in st.session_state:
    st.session_state.config_paginas = {}

# 2. CONTROLES EN LA BARRA LATERAL
st.sidebar.header("📋 Parámetros del Catálogo")
id_campana_activa = st.sidebar.number_input("ID Campaña (`id_campana`):", min_value=1, value=12)

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Configuración de la Hoja")

# Navegador de páginas
pagina_actual = st.sidebar.number_input("Seleccionar Página:", min_value=1, max_value=50, value=1)

# Inicializar datos por defecto si la página es nueva en la sesión
if pagina_actual not in st.session_state.config_paginas:
    st.session_state.config_paginas[pagina_actual] = {
        "slots": 4,
        "distribucion": "Equilibrado",
        "estilo": "Estándar"
    }

cfg = st.session_state.config_paginas[pagina_actual]

# Parámetro 1: Cantidad de slots
slots_deseados = st.sidebar.slider("Cantidad de slots:", min_value=1, max_value=8, value=cfg["slots"])
st.session_state.config_paginas[pagina_actual]["slots"] = slots_deseados

# Parámetro 2: Tipo de Distribución (mapeado a posicion_mix)
tipo_distribucion = st.sidebar.selectbox(
    "Tipo de distribución (`posicion_mix`):",
    ["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"],
    index=["Equilibrado", "Banner Superior", "Enfoque Central", "Asimétrico"].index(cfg["distribucion"])
)
st.session_state.config_paginas[pagina_actual]["distribucion"] = tipo_distribucion

# Parámetro 3: Sub Molde Estilo
sub_estilo = st.sidebar.radio(
    "Estilo visual (`sub_molde_estilo`):",
    ["Estándar", "Destacado", "Compacto"],
    index=["Estándar", "Destacado", "Compacto"].index(cfg["estilo"])
)
st.session_state.config_paginas[pagina_actual]["estilo"] = sub_estilo

# Lógica del Grid CSS para el maquetador interactivo
def calcular_layout_grid(num_slots):
    if num_slots == 1: return "1fr", "1fr"
    if num_slots == 2: return "repeat(2, 1fr)", "1fr"
    if num_slots in (3, 4): return "repeat(2, 1fr)", "repeat(2, 1fr)"
    if num_slots in (5, 6): return "repeat(2, 1fr)", "repeat(3, 1fr)"
    return "repeat(2, 1fr)", "repeat(4, 1fr)"

columnas_css, filas_css = calcular_layout_grid(slots_deseados)

# 3. GENERADOR DEL COMPONENTE HTML VISUAL
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
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; background: #f8f9fa; display: flex; gap: 20px; padding: 10px; height: 520px; box-sizing: border-box; }}
            .sidebar {{ width: 260px; background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }}
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
            <h4 style="margin:0; font-size:14px; color:#475569; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">📦 Ofertas Disponibles</h4>
            <div id="banco">{banco_html}</div>
        </div>
        <div class="canvas">
            <h4 style="margin:0 0 10px 0; font-size:14px; color:#475569;">📖 Distribución de Página: {pagina}</h4>
            <div class="grid-folleto">{slots_html}</div>
        </div>
        <script>
            let draggedNode = null;
            document.querySelectorAll('.product-card').forEach(card => {{
                card.addEventListener('dragstart', () => {{ draggedNode = card; card.style.opacity = '0.4'; }});
                card.addEventListener('dragend', () => {{ card.style.opacity = '1'; }});
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
                            value: JSON.stringify({{ 
                                id_oferta: parseInt(draggedNode.id), 
                                posicion_slot: parseInt(slot.id), 
                                numero_pagina: {pagina} 
                            }})
                        }}, '*');
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """

# 4. CAPTURA DEL EVENTO DRAG & DROP
html_renderizado = generar_canvas_ofertas(st.session_state.ofertas, pagina_actual, slots_deseados, columnas_css, filas_css)
evento_drag_drop = components.html(html_renderizado, height=540, scrolling=False)

if evento_drag_drop:
    try:
        datos = json.loads(evento_drag_drop)
        for ofer in st.session_state.ofertas:
            if ofer["id_oferta"] == datos["id_oferta"]:
                ofer["numero_pagina"] = datos["numero_pagina"]
                ofer["posicion_slot"] = datos["posicion_slot"]
    except Exception:
        pass

# 5. PREPARACIÓN E INYECCIÓN DE LA TABLA FINAL DE OUTPUT
st.markdown(f"### 📊 Vista de Registros a Guardar — Página {pagina_actual}")

filas_tabla_ofertas = []
for ofer in st.session_state.ofertas:
    if ofer["numero_pagina"] == pagina_actual:
