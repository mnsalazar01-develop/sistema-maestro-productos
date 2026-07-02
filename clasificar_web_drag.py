import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA WEB DE STREAMLIT
st.set_page_config(
    page_title="Clasificador Drag & Drop Web",
    page_icon="🖱️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. HERENCIA DE CONEXIÓN SEGURA INDEPENDIENTE CON LAS LLAVES DE LA COMPAÑÍA
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

st.title("🖱️ Clasificador Interactivo Drag & Drop Web")
st.markdown("Mueve los productos con el mouse directamente en el navegador para reclasificar pasillos en caliente en la nube. ¡100% libre de instalaciones en tu PC!")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA DE ARTÍCULOS EN DEPÓSITO (ID 12) Y SUBCATEGORIAS DESTINO CORE
def descargar_datos_clasificador_web():
    try:
        # Descargamos los productos que están temporalmente en el bolsón general de Víveres (ID 12)
        res_cat = supabase.table("catalogo").select("id_catalogo, nombre_catalogo").eq("id_enlace_subcat", 12).limit(30).execute()
        
        # Traemos el listado completo de subcategorías existentes para poblar la grilla de internet
        res_sub = supabase.table("subcategorias").select("id_subcat, nombre_subcat").order("id_subcat", ascending=True).execute()
        
        if res_cat and hasattr(res_cat, 'data') and res_sub and hasattr(res_sub, 'data'):
            return res_cat.data, res_sub.data
    except Exception as e_load:
        st.sidebar.error(f"⚠️ Error al leer datos desde internet: {e_load}")
    return [], []

lista_pendientes, lista_subcats = descargar_datos_clasificador_web()

# 4. PARACHOQUES DE INTERNET: EVITA LA EJECUCIÓN SI NO HAY ELEMENTOS EN EL DEPÓSITO GENERAL
if not lista_pendientes:
    st.success("🎉 ¡Excelente! No quedan productos pendientes con la clasificación básica de Víveres (ID 12) en la nube.")
    st.stop()

# 5. INYECCIÓN DEL LIENZO GRÁFICO AVANZADO MEDIANTE HTML5 + JAVASCRIPT EMBEBIDO
# Preparamos las estructuras JSON seguras para pasárselas al frame del navegador
json_pendientes = json.dumps(lista_pendientes)
# Costura v1.0.2: Reparamos de forma estricta el contenedor de la tupla numérica de validación
subcats_filtradas = [s for s in lista_subcats if s["id_subcat"] in (1, 2, 9, 16)]
json_subcats = json.dumps(subcats_filtradas)

html_drag_and_drop = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; margin: 0; padding: 10px; color: #333; }}
        .contenedor-global {{ display: flex; gap: 20px; }}
        .columna-izq {{ flex: 1; background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; min-height: 500px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .columna-der {{ flex: 3; background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; min-height: 500px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .grilla-destinos {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .caja-destino {{ background: #e9ecef; border: 2px dashed #ced4da; border-radius: 6px; padding: 10px; min-height: 400px; transition: all 0.2s ease; }}
        .caja-destino.dragover {{ background: #d1ecf1; border-color: #17a2b8; }}
        .item-producto {{ background: #ffffff; border: 1px solid #ced4da; border-radius: 4px; padding: 10px; margin-bottom: 8px; cursor: grab; font-size: 13px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.05); user-select: none; }}
        .item-producto:active {{ cursor: grabbing; }}
        h3 {{ margin-top: 0; font-size: 15px; color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 5px; }}
    </style>
</head>
<body>

<div class="contenedor-global">
    <div class="columna-izq">
        <h3>📋 Depósito General (ID 12)</h3>
        <div id="lista-origen" class="caja-origen" ondragover="permitirDrop(event)"></div>
    </div>
    
    <div class="columna-der">
        <h3>📥 Arrastra aquí para refinar la subcategoría comercial:</h3>
        <div id="contenedor-grid" class="grilla-destinos"></div>
    </div>
</div>

<script>
    const productos = {json_pendientes};
    const subcategorias = {json_subcats};

    const divOrigen = document.getElementById("lista-origen");
    productos.forEach(p => {{
        const item = document.createElement("div");
        item.className = "item-producto";
        item.id = p.id_catalogo;
        item.draggable = true;
        item.innerText = p.id_catalogo + " - " + p.nombre_catalogo;
        item.addEventListener("dragstart", arrastrar);
        divOrigen.appendChild(item);
    }});

    const divGrid = document.getElementById("contenedor-grid");
    subcategorias.forEach(s => {{
        const col = document.createElement("div");
        col.className = "columna-destino-individual";
        
        const titulo = document.createElement("h4");
        titulo.style.margin = "0 0 5px 0";
        titulo.style.fontSize = "13px";
        titulo.innerText = s.nombre_subcat;
        
        const caja = document.createElement("div");
        caja.className = "caja-destino";
        caja.id = "subcat-" + s.id_subcat;
        caja.addEventListener("dragover", permitirDrop);
        caja.addEventListener("dragenter", dragEnter);
        caja.addEventListener("dragleave", dragLeave);
        caja.addEventListener("drop", soltar);
        
        col.appendChild(titulo);
        col.appendChild(caja);
        divGrid.appendChild(col);
    }});

    function arrastrar(ev) {{
        ev.dataTransfer.setData("text_id", ev.target.id);
        ev.dataTransfer.setData("text_contenido", ev.target.innerText);
    }}

    function permitirDrop(ev) {{
        ev.preventDefault();
    }}

    function dragEnter(ev) {{
        ev.target.classList.add("dragover");
    }}

    function dragLeave(ev) {{
        ev.target.classList.remove("dragover");
    }}

    function soltar(ev) {{
        ev.preventDefault();
        ev.target.classList.remove("dragover");
        
        const id_producto = ev.dataTransfer.getData("text_id");
        const contenido = ev.dataTransfer.getData("text_contenido");
        const elemento_arrastrado = document.getElementById(id_producto);
        
        if (ev.target.classList.contains("caja-destino")) {{
            ev.target.appendChild(elemento_arrastrado);
            const id_subcat_destino = ev.target.id.split("-");
            
            window.parent.postMessage({{
                type: "streamlit:setComponentValue",
                value: {{ id_prod: id_producto, id_sub: id_subcat_destino[1], txt: contenido }}
            }, "*");
        }}
    }}
</script>

</body>
</html>
"""

# 6. CAPTURA DEL PULSO DE RETORNO Y EJECUCIÓN DEL UPDATE EN LA NUBE
evento_retorno = components.html(html_drag_and_drop, height=580, scrolling=False)

if evento_retorno is not None and isinstance(evento_retorno, dict):
    id_catalogo_afectado = evento_retorno.get("id_prod")
    id_subcat_asignada = evento_retorno.get("id_sub")
    texto_articulo = evento_retorno.get("txt")
    
    if id_catalogo_afectado and id_subcat_asignada:
        try:
            # Saneamiento v1.0.2: Forzamos el casteo limpio a entero para inyectar en la base de datos real
            supabase.table("catalogo").update({
                "id_enlace_subcat": int(id_subcat_asignada)
            }).eq("id_catalogo", int(id_catalogo_afectado)).execute()
            
            st.toast(f"🔄 Reclasificado: {texto_articulo}", icon="⚡")
            st.rerun()
        except Exception as e_update_web:
            st.error(f"❌ Error de persistencia relacional en internet: {e_update_web}")
