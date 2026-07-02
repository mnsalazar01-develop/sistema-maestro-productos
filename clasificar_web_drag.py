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

# ==============================================================================
# 🧠 RECEPTOR EN CALIENTE: CAPTURA LOS PULSOS DE ARRASTRE PERMANENTES DESDE LA URL
# ==============================================================================
parametros_url = st.query_params
if "id_prod" in parametros_url and "id_sub" in parametros_url:
    id_afectado = parametros_url["id_prod"]
    id_destino = parametros_url["id_sub"]
    try:
        # PERSISTENCIA INTERNET DURA: Modificamos el disco duro de Supabase mediante Python nativo
        supabase.table("catalogo").update({
            "id_enlace_subcat": int(id_destino)
        }).eq("id_catalogo", int(id_afectado)).execute()
        
        # Limpiamos los parámetros de la URL para evitar bucles infinitos de red
        st.query_params.clear()
        st.toast("💾 ¡Guardado Permanente en Supabase!", icon="✅")
        st.rerun()
    except Exception as e_url_persist:
        st.error(f"❌ Error relacional en internet: {e_url_persist}")

st.title("🖱️ Clasificador Interactivo Drag & Drop Web")
st.markdown("Mueve los productos con el mouse directamente en el navegador para reclasificar pasillos en caliente en la nube. ¡100% libre de instalaciones en tu PC!")
st.markdown("---")

# 3. EXTRACCIÓN SÍNCRONA DE LOS 372 ARTÍCULOS COMPLETOS Y EL 100% DE LAS SUBCATEGORIAS
def descargar_datos_clasificador_web():
    try:
        # Descargamos todos los productos de tu catálogo cloud de Producción
        res_cat = supabase.table("catalogo").select("id_catalogo, nombre_catalogo, id_enlace_subcat").limit(400).execute()
        # Descargamos el árbol completo unificado de subcategorías (1 al 46)
        res_sub = supabase.table("subcategorias").select("id_subcat, nombre_subcat").order("id_subcat").execute()
        
        if res_cat and hasattr(res_cat, 'data') and res_sub and hasattr(res_sub, 'data'):
            return res_cat.data, res_sub.data
    except Exception as e_load:
        st.sidebar.error(f"⚠️ Error al leer datos desde internet: {e_load}")
    return [], []

lista_pendientes, lista_subcats = descargar_datos_clasificador_web()

if not lista_pendientes:
    st.info("💡 Catálogo Vacío: Carga productos primero para encender la grilla de arrastre.")
    st.stop()

# 4. PREPARACIÓN DE LAS ESTRUCTURAS JSON SEGURAS EN LA MEMORIA RAM
json_pendientes = json.dumps(lista_pendientes)
json_subcats = json.dumps(lista_subcats)

# 5. LIENZO GRÁFICO TEXTO PLANO CON MATRIZ RESPONSIVA FLEXIBLE (DREG & DROP PRO)
html_drag_and_drop_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; margin: 0; padding: 10px; color: #333; }
        .contenedor-global { display: flex; gap: 20px; }
        .columna-izq { flex: 1; background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; min-height: 650px; max-height: 650px; overflow-y: auto; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .columna-der { flex: 4; background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; min-height: 650px; max-height: 650px; overflow-y: auto; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .grilla-destinos { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
        .caja-destino { background: #e9ecef; border: 2px dashed #ced4da; border-radius: 6px; padding: 8px; min-height: 120px; max-height: 150px; overflow-y: auto; transition: all 0.2s ease; }
        .caja-destino.dragover { background: #d1ecf1; border-color: #17a2b8; }
        .item-producto { background: #ffffff; border: 1px solid #ced4da; border-radius: 4px; padding: 6px 10px; margin-bottom: 6px; cursor: grab; font-size: 12px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.05); user-select: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .item-producto:active { cursor: grabbing; }
        h3 { margin-top: 0; font-size: 15px; color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 5px; }
        h4 { margin: 0 0 4px 0; font-size: 12px; color: #212529; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
</head>
<body>

<div class="contenedor-global">
    <div class="columna-izq">
        <h3>📋 Depósito General (Sin Asignar)</h3>
        <div id="lista-origen" class="caja-origen"></div>
    </div>
    
    <div class="columna-der">
        <h3>📥 Arrastra aquí para refinar la subcategoría comercial:</h3>
        <div id="contenedor-grid" class="grilla-destinos"></div>
    </div>
</div>

<script>
    const productos = __PENDIENTES__;
    const subcategorias = __SUBCATEGORIAS__;

    const divGrid = document.getElementById("contenedor-grid");
    subcategorias.forEach(s => {
        const col = document.createElement("div");
        col.className = "columna-destino-individual";
        
        const titulo = document.createElement("h4");
        titulo.innerText = s.nombre_subcat;
        titulo.title = s.nombre_subcat;
        
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
    });

    const divOrigen = document.getElementById("lista-origen");
    productos.forEach(p => {
        const item = document.createElement("div");
        item.className = "item-producto";
        item.id = p.id_catalogo;
        item.draggable = true;
        item.title = p.nombre_catalogo;
        item.innerText = p.id_catalogo + " - " + p.nombre_catalogo;
        item.addEventListener("dragstart", arrastrar);
        
        const cajaDestino = document.getElementById("subcat-" + p.id_enlace_subcat);
        if (cajaDestino && parseInt(p.id_enlace_subcat) !== 12) {
            cajaDestino.appendChild(item);
        } else {
            divOrigen.appendChild(item);
        }
    });

    function arrastrar(ev) {
        ev.dataTransfer.setData("text_id", ev.target.id);
    }

    function permitirDrop(ev) {
        ev.preventDefault();
    }

    function dragEnter(ev) {
        ev.target.classList.add("dragover");
    }

    function dragLeave(ev) {
        ev.target.classList.remove("dragover");
    }

    function soltar(ev) {
        ev.preventDefault();
        
        let destino = ev.target;
        while (destino && !destino.classList.contains("caja-destino")) {
            destino = destino.parentElement;
        }
        
        if (destino) {
            destino.classList.remove("dragover");
            const id_producto = ev.dataTransfer.getData("text_id");
            const elemento_arrastrado = document.getElementById(id_producto);
            
            if (elemento_arrastrado) {
                destino.appendChild(elemento_arrastrado);
                const id_subcat_destino = destino.id.replace("subcat-", "");
                
                // BLINDAJE v4.0.0: Forzamos la redirección por parámetros de URL, comunicando a Python con poder inmutable
                window.parent.location.search = "?id_prod=" + id_producto + "&id_sub=" + id_subcat_destino;
            }
        }
    }
</script>

</body>
</html>
"""

# Reemplazo seguro inyectando las strings JSON sin usar f-strings peligrosas
html_final = html_drag_and_drop_template.replace("__PENDIENTES__", json_pendientes).replace("__SUBCATEGORIAS__", json_subcats)

# Pintamos el lienzo interactivo definitivo en la pantalla web
components.html(html_final, height=680, scrolling=False)
