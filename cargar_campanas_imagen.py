# =========================================================================
# >> PARTE 1 DE 4 v15.2 <<
# PROGRAMA: cargar_campanas_imagen.py | MODULO: CONFIGURACION Y LOGISTICA EN RAM
# =========================================================================
import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
from supabase import create_client, Client

APP_VERSION = "15.2"
st.set_page_config(page_title="Espejo de Carga Express", layout="wide", page_icon="")
st.title(" Central de Carga del Golpe por Pasillos (Espejo)")
st.caption(f"Copia Fiel del Programa Original Pruebas de Insercion Masiva Simultanea | v{APP_VERSION}")

# 1. CONEXION DIRECTA A TU BASE DE DATOS DE PRUEBAS
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase_client = init_supabase()

# 2. CANDADOS PERSISTENTES DE MEMORIA (Fórmula anti-congelamiento)
if "exp_cat_id" not in st.session_state:
    st.session_state.exp_cat_id = None
if "exp_sub_id" not in st.session_state:
    st.session_state.exp_sub_id = None

def trigger_cambio_pasillo():
    if "sb_cat_lab" in st.session_state and st.session_state.sb_cat_lab:
        st.session_state.exp_cat_id = st.session_state.sb_cat_lab["id_cat"]
        st.session_state.exp_sub_id = None

def trigger_cambio_subcat():
    if "sb_sub_lab" in st.session_state and st.session_state.sb_sub_lab:
        st.session_state.exp_sub_id = st.session_state.sb_sub_lab["id_subcat"]

# =========================================================================
# >> PARTE 2 DE 4 v15.3 <<
# PROGRAMA: cargar_campanas_imagen.py | MODULO: DESCARGA MAESTRA ORIGINAL v14.9.0
# =========================================================================
try:
    # 1. Descarga paginada de Ofertas
    res_o = []
    paso_o = 0
    while True:
        chunk = supabase_client.table("ofertas").select("*").range(paso_o, paso_o + 999).execute().data
        if not chunk:
            break
        res_o.extend(chunk)
        paso_o += 1000

    # 2. Descarga paginada de Productos
    res_p = []
    paso_p = 0
    while True:
        chunk = supabase_client.table("productos").select(
            "id_producto, nombre, marca, tamano, unidad, codigo_barras, id_cat, id_subcat, url_imagen"
        ).range(paso_p, paso_p + 999).execute().data
        if not chunk:
            break
        res_p.extend(chunk)
        paso_p += 1000

    # 3. Descarga normal para tablas pequeñas (menores a 1,000 filas)
    res_s = supabase_client.table("supermercados").select("id_super, nombre_supermercado").execute().data
    res_c = supabase_client.table("campanas").select("id_campana, id_super, nombre_campana, estado_campana, fecha_inicio, fecha_fin").execute().data
    form_categorias = supabase_client.table("categorias").select("id_cat, nombre").order("nombre").execute().data
    form_subcategorias = supabase_client.table("subcategorias").select("id_subcat, id_cat, nombre").order("nombre").execute().data

except Exception as e:
    st.error(f"❌ Fallo crítico de red o paginación con Supabase: {e}")
    st.stop()

# Conversión a DataFrames limpios en RAM (Nativos de la v14.9.0)
df_o = pd.DataFrame(res_o) if res_o else pd.DataFrame()
df_p = pd.DataFrame(res_p) if res_p else pd.DataFrame()
df_c = pd.DataFrame(res_c) if res_c else pd.DataFrame()
mapa_supers_ram = {int(s["id_super"]): s["nombre_supermercado"] for s in res_s} if res_s else {}

# Filtrado estricto de campañas en modo 'Pre-Oferta'
campanas_pre_oferta_global = [c for c in res_c if str(c.get("estado_campana")).strip().lower() == "pre-oferta"]
if not campanas_pre_oferta_global:
    st.info("ℹ️ Por favor, cree primero una campaña en modo 'Pre-Oferta' para activar este laboratorio.")
    st.stop()

# =========================================================================
# POOL ACTUAL: RECONSTRUCCIÓN GENERAL DE HISTÓRICOS (LÓGICA BASE v14.9.0)
# =========================================================================
df_pool_actual = pd.DataFrame()
if not df_o.empty and not df_p.empty and not df_c.empty:
    df_o_temp = df_o.copy()
    df_p_temp = df_p.copy()
    df_c_temp = df_c.copy()
    
    df_o_temp["id_producto"] = df_o_temp["id_producto"].astype(str).str.strip()
    df_p_temp["id_producto"] = df_p_temp["id_producto"].astype(str).str.strip()
    df_o_temp["id_campana"] = df_o_temp["id_campana"].fillna(0).astype(int)
    df_c_temp["id_campana"] = df_c_temp["id_campana"].fillna(0).astype(int)
    
    df_temp = pd.merge(df_o_temp, df_p_temp, on="id_producto", how="inner")
    df_pool_actual = pd.merge(df_temp, df_c_temp[["id_campana", "fecha_inicio", "fecha_fin"]], on="id_campana", how="inner")

# =========================================================================
# RENDERIZADO DE COORDENADAS SUPERIORES (INTERFAZ VISUAL)
# =========================================================================
st.markdown("#### 1. Coordenadas de Entrada Comercial")
col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns([1.2, 1.4, 1.1, 1.1, 1.4])

with col_s1:
    ids_supers_activos = sorted(list(set([int(c["id_super"]) for c in campanas_pre_oferta_global if c.get("id_super") is not None])))
    id_super_contexto = st.selectbox("Supermercado Objetivo:", options=ids_supers_activos, format_func=lambda x: mapa_supers_ram.get(x, f"ID: {x}"))
    campanas_filtradas = [c for c in campanas_pre_oferta_global if int(c.get("id_super", 0)) == id_super_contexto]

with col_s2:
    if not campanas_filtradas:
        st.error("No hay campañas en Pre-Oferta.")
        st.stop()
        
    campana_destino_sel = st.selectbox(
        "Campaña Contenedora:", 
        options=campanas_filtradas, 
        format_func=lambda x: f"ID: {x['id_campana']} | {x['nombre_campana']}"
    )
    id_campana_destino = int(campana_destino_sel["id_campana"])

with col_s5:
    columnas_elegidas = st.slider("Columnas por Fila (Densidad):", min_value=6, max_value=15, value=9, step=3)
    config_zoom = {
        6: {"altura_px": 85, "font_b": "0.72rem", "font_span": "0.62rem", "trim": 20},
        9: {"altura_px": 65, "font_b": "0.65rem", "font_span": "0.58rem", "trim": 14},
        12: {"altura_px": 50, "font_b": "0.58rem", "font_span": "0.52rem", "trim": 10},
        15: {"altura_px": 42, "font_b": "0.52rem", "font_span": "0.48rem", "trim": 8}
    }
    layout_dinamico = config_zoom.get(columnas_elegidas, config_zoom[9])

# =========================================================================
# LECTURA DE LA CAMPAÑA ACTIVA Y CANDADOS DE AMBIENTE (MÁXIMA INTEGRIDAD v14.9.0)
# =========================================================================
df_laboratorio_activo = pd.DataFrame()
tiene_registros_activos = False

try:
    # Consulta directa y obligatoria usando el ID seleccionado
    res_po_actual = supabase_client.table("pre_ofertas").select("*").eq("id_campana", id_campana_destino).execute().data
    if res_po_actual:
        df_laboratorio_activo = pd.DataFrame(res_po_actual)
        df_laboratorio_activo["id_producto"] = df_laboratorio_activo["id_producto"].astype(str).str.strip()
        if len(df_laboratorio_activo) > 0:
            tiene_registros_activos = True
except Exception:
    df_laboratorio_activo = pd.DataFrame()
    tiene_registros_activos = False

# Candados de estadísticas y diccionarios globales
if "stat_lider" not in st.session_state: st.session_state.stat_lider = 0
if "stat_otros" not in st.session_state: st.session_state.stat_otros = 0
if "stat_total" not in st.session_state: st.session_state.stat_total = 0

if "formulario_imagenes_dict" not in st.session_state or st.session_state["formulario_imagenes_dict"] is None:
    st.session_state["formulario_imagenes_dict"] = {}

# =========================================================================
# BANNER DELIMITADOR INTERNO: >>> PARTE 3 DE 4 v16.0.0 <<<
# PROGRAMA: cargar_campanas_imagen.py | MODULO: MOTOR DE PROCESAMIENTO Y RENDERIZADO
# =========================================================================

# =========================================================================
# # 3. PROCESAMIENTO GENERAL DEL POOL DE IMÁGENES (VERSIÓN 14.9.0 REGLA v15)
# =========================================================================
df_lote_express = pd.DataFrame()
lista_items = []
df_pool_unicos = pd.DataFrame()

# REGLA v15 CON VARIABLES NATIVAS: Evaluamos las tablas reales de tu v14.9.0
if not df_laboratorio_activo.empty and not df_p.empty:
    
    # Clonamos de forma segura para normalizar tipos de datos
    df_lab = df_laboratorio_activo.copy()
    df_prod = df_p.copy()
    
    df_lab["id_producto"] = df_lab["id_producto"].astype(str).str.strip()
    df_prod["id_producto"] = df_prod["id_producto"].astype(str).str.strip()
    
    # CRUCE ESTRICTO: El mosaico visual se limita a lo inyectado en la campaña activa
    df_lote_express = pd.merge(df_lab, df_prod, on="id_producto", how="inner")
    
    if not df_lote_express.empty:
        # El renderizado de v14.9.0 requiere 'precio_oferta' como columna base
        if "precio_oferta_proyectado" in df_lote_express.columns:
            df_lote_express["precio_oferta"] = df_lote_express["precio_oferta_proyectado"].astype(float)
        # =========================================================================
        # REGLA COMERCIAL DE INTEGRIDAD v15 PARA SUFIJO (L)
        # =========================================================================
        # 1. Creamos un set de productos únicos que TIENEN ofertas históricas en el supermercado filtrado
        set_productos_con_oferta_en_super = set()
        if not df_o.empty and "id_super" in df_o.columns and "id_producto" in df_o.columns:
            ofertas_del_super = df_o[df_o["id_super"].fillna(0).astype(int) == int(id_super_contexto)]
            set_productos_con_oferta_en_super = set(ofertas_del_super["id_producto"].astype(str).str.strip().tolist())
            
        # 2. El producto SOLO recibe la bandera (L) si pertenece a ese universo histórico
        df_lote_express["es_local"] = df_lote_express["id_producto"].astype(str).str.strip().isin(set_productos_con_oferta_en_super)
        
        # Conteo y fijación inmediata de estadísticas superiores de la v14.9.0
        total_pre = len(df_lote_express)
        st.session_state.stat_lider = int(df_lote_express["es_local"].sum())
        st.session_state.stat_otros = int(total_pre - st.session_state.stat_lider)
        st.session_state.stat_total = total_pre
        
        # Preparar ordenamiento estricto por pasillos comerciales
        df_lote_express["id_cat"] = df_lote_express["id_cat"].fillna(0).astype(int)
        df_lote_express["id_subcat"] = df_lote_express["id_subcat"].fillna(0).astype(int)
        df_lote_express["nombre_sort"] = df_lote_express["nombre"].fillna("").astype(str).str.strip().str.lower()
        
        # Orden final: categoría -> subcategoría -> orden alfabético
        df_pool_unicos = df_lote_express.sort_values(
            by=["id_cat", "id_subcat", "nombre_sort"],
            ascending=[True, True, True]
        )
        
        lista_items = df_pool_unicos.to_dict(orient="records")
else:
    # Si la campaña está vacía, el mosaico queda en cero forzando el Ambiente A
    st.session_state.stat_lider = 0
    st.session_state.stat_otros = 0
    st.session_state.stat_total = 0
    lista_items = []



# 2. FUNCIONES DE ACTUALIZACIÓN RÁPIDA EN MEMORIA EN VIVO
def actualizar_precio_en_memoria(id_prod, p_key):
    if "formulario_imagenes_dict" in st.session_state and p_key in st.session_state:
        st.session_state["formulario_imagenes_dict"][id_prod]["precio_valor_en_vivo"] = st.session_state[p_key]

def actualizar_marcado_en_memoria(id_prod, m_key):
    if "formulario_imagenes_dict" in st.session_state and m_key in st.session_state:
        st.session_state["formulario_imagenes_dict"][id_prod]["marcado_valor_en_vivo"] = st.session_state[m_key]

# 3. CABECERA DINÁMICA DE ESTADÍSTICAS AISLADA
@st.fragment
def renderizar_cabecera_estadisticas():
    st.write("### Resumen Ejecutivo de la Campaña")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric(label=" Imágenes Súper Líder (L)", value=st.session_state.get("stat_lider", 0))
    with metric_col2:
        st.metric(label=" Otros Supermercados", value=st.session_state.get("stat_otros", 0))
    with metric_col3:
        st.metric(label=" Total Imágenes en Campaña", value=st.session_state.get("stat_total", 0))

# 4. MOSAICO VISUAL CON NORMALIZACIÓN DE URL ENCODING Y ACCESOS FIRMADOS
@st.fragment
def dibujar_rejilla_mosaico(items_mosaico, _df_lab_activo, layout, _columnas_elegidas, _id_campana_destino):
    COLUMNAS_POR_FILA = _columnas_elegidas
    mapa_urls_firmadas = {}
    lista_archivos_firmar = []
    
    for fila_p in items_mosaico:
        url_foto = fila_p.get("url_imagen")
        if url_foto:
            nombre_archivo = str(url_foto).split("/")[-1] if "/" in str(url_foto) else str(url_foto)
            if nombre_archivo.strip():
                nombre_limpio = urllib.parse.unquote(nombre_archivo)
                lista_archivos_firmar.append(nombre_limpio)
                
    if lista_archivos_firmar:
        try:
            resp_bulk = supabase_client.storage.from_("imagenes").create_signed_urls(lista_archivos_firmar, 3600)
            if resp_bulk and isinstance(resp_bulk, list):
                for item_b in resp_bulk:
                    nombre_k = item_b.get("path")
                    url_v = item_b.get("signedURL") or item_b.get("signed_url")
                    if nombre_k and url_v:
                        nombre_base_k = str(nombre_k).split("/")[-1] if "/" in str(nombre_k) else str(nombre_k)
                        mapa_urls_firmadas[nombre_base_k] = url_v
                        mapa_urls_firmadas[urllib.parse.unquote(nombre_base_k)] = url_v
                        mapa_urls_firmadas[urllib.parse.unquote(nombre_base_k).strip().lower()] = url_v
        except Exception:
            pass

    for i in range(0, len(items_mosaico), COLUMNAS_POR_FILA):
        bloque_items = items_mosaico[i:i + COLUMNAS_POR_FILA]
        columnas_ui = st.columns(COLUMNAS_POR_FILA)
        for idx, fila_p in enumerate(bloque_items):
            with columnas_ui[idx]:
                id_p_raw = int(float(fila_p["id_producto"]))
                match_campana = pd.DataFrame()
                
                if not _df_lab_activo.empty and "id_producto" in _df_lab_activo.columns:
                    id_db_normalizado = _df_lab_activo["id_producto"].fillna(0).astype(float).astype(int).astype(str)
                    condicion_producto = (id_db_normalizado == str(id_p_raw))
                    if "id_campana" in _df_lab_activo.columns:
                        condicion_campana = (_df_lab_activo["id_campana"].astype(str) == str(_id_campana_destino))
                        match_campana = _df_lab_activo[condicion_producto & condicion_campana]
                    else:
                        match_campana = _df_lab_activo[condicion_producto]
                        
                id_pre_oferta_real = None
                precio_defecto = float(fila_p.get("precio_oferta", 0.0))
                check_inicial = False
                
                if not match_campana.empty:
                    fila_maqueta_reciente = match_campana.tail(1)
                    precio_defecto = float(fila_maqueta_reciente["precio_oferta_proyectado"].values[0])
                    id_pre_oferta_real = int(fila_maqueta_reciente["id_pre_oferta"].values[0]) if "id_pre_oferta" in fila_maqueta_reciente.columns else None
                    if "clonado_confirmado" in fila_maqueta_reciente.columns:
                        flag_db = fila_maqueta_reciente["clonado_confirmado"].values[0]
                        check_inicial = (flag_db is True or str(flag_db).strip().lower() in ["true", "t", "1"] or flag_db == 1)

                limite_caracteres = layout["trim"]
                nombre_lbl = str(fila_p.get("nombre", "")).strip().upper()[:limite_caracteres]
                marca_lbl = str(fila_p.get("marca", "Sin Marca")).strip()[:10]
                formato_empaque = f"{fila_p.get('tamano', '')} {fila_p.get('unidad', '')}".strip()
                sufijo_1 = " <span style='color: #f38ba8; font-weight: bold;'>(L)</span>" if fila_p.get("es_local", False) else ""
                
                html_especificacion = f"""
                <div style='line-height:1.1; margin-bottom:4px; height: 42px; overflow: hidden;'>
                    <b style='font-size: {layout["font_b"]}; color:#cdd6f4;'>{nombre_lbl}{sufijo_1}</b><br>
                    <span style='font-size: {layout["font_span"]}; color: #a6adc8;'>{marca_lbl} | {formato_empaque}</span>
                </div>
                """
                
                url_foto_render = fila_p.get("url_imagen")
                url_firmada_live = None
                if url_foto_render:
                    nombre_archivo_render = str(url_foto_render).split("/")[-1] if "/" in str(url_foto_render) else str(url_foto_render)
                    url_firmada_live = (
                        mapa_urls_firmadas.get(nombre_archivo_render) or
                        mapa_urls_firmadas.get(urllib.parse.unquote(nombre_archivo_render)) or
                        mapa_urls_firmadas.get(urllib.parse.unquote(nombre_archivo_render).strip().lower())
                    )
                    
                with st.container(border=True):
                    if url_firmada_live:
                        st.image(url_firmada_live, use_container_width=True)
                    else:
                        st.markdown(f"<div style='height: {layout['altura_px']}px; background-color:#1e1e2e; color:#ff6b6b; display:flex; align-items:center; justify-content:center; font-size:0.8rem; border-radius:4px;'>⚠️ Sin Foto</div>", unsafe_allow_html=True)
                    
                    st.markdown(html_especificacion, unsafe_allow_html=True)
                    
                    p_key_string = f"num_pvp_{id_p_raw}_{_id_campana_destino}"
                    m_key_string = f"chk_load_{id_p_raw}_{_id_campana_destino}"
                    
                    st.number_input("PVP ($):", min_value=0.0, value=precio_defecto, step=0.01, format="%.2f", key=p_key_string, label_visibility="collapsed")
                    st.checkbox("✓ Incluir", value=check_inicial, key=m_key_string)
                    
                    st.session_state["formulario_imagenes_dict"][id_p_raw] = {
                        "id_registro": id_pre_oferta_real,
                        "id_producto": id_p_raw,
                        "precio_key": p_key_string,
                        "marcado_key": m_key_string
                    }

# =========================================================================
# >> PARTE 4 DE 4 v15.2 <<
# PROGRAMA: cargar_campanas_imagen.py | MODULO: INTERFAZ DE AMBIENTES Y BITACORA DE AUDITORIA
# =========================================================================

if not tiene_registros_activos:
    # ---- AMBIENTE A: INITIAL VOLCADO TOTAL (SI LA CAMPAÑA ESTÁ TOTALMENTE VACÍA) ----
    st.write("---")
    st.info(f" El contenedor ID ({id_campana_destino}) está vacío en pre_ofertas. El sistema ejecutará el algoritmo de clonación dual.")
    st.markdown("##### Inicialización del Laboratorio Inteligente Multi-Súper")

    total_f1_unicos, total_f2_rescatados = 0, 0
    df_pool_molde = df_pool_actual[df_pool_actual["id_super"] == id_super_contexto].copy() if not df_pool_actual.empty else pd.DataFrame()
    set_productos_lider = set()
    df_f1_listo = pd.DataFrame()
    df_f2_listo = pd.DataFrame()

    if not df_pool_molde.empty:
        df_pool_ordenado = df_pool_molde.sort_values(by="id_oferta", ascending=False)
        df_f1_listo = df_pool_ordenado.drop_duplicates(subset=["id_producto"], keep="first").copy()
        set_productos_lider = set(df_f1_listo["id_producto"].astype(str).str.strip().tolist())
        total_f1_unicos = len(df_f1_listo)

    df_pool_resto = df_pool_actual[df_pool_actual["id_super"] != id_super_contexto].copy() if not df_pool_actual.empty else pd.DataFrame()

    if not df_pool_resto.empty:
        # CORRECCIÓN DE ORDEN MÁXIMA: Primero se filtra por el líder, luego se ordena
        df_resto_filtrado = df_pool_resto[~df_pool_resto["id_producto"].astype(str).str.strip().isin(set_productos_lider)]
        df_resto_ordenado = df_resto_filtrado.sort_values(by="id_oferta", ascending=False)
        df_f2_listo = df_resto_ordenado.drop_duplicates(subset=["id_producto"], keep="first").copy()
        total_f2_rescatados = len(df_f2_listo)

    m1, m2, m3 = st.columns(3)
    m1.metric(" SKUS Súper Líder (Fase 1)", total_f1_unicos)
    m2.metric(" SKUS Rescatados Competencia (Fase 2)", total_f2_rescatados)
    m3.metric(" Lote Total Neto Proyectado", total_f1_unicos + total_f2_rescatados)

    if st.button(" Inicializar Laboratorio Vacío con Catálogo Histórico Cruzado", use_container_width=True, type="primary"):
        if total_f1_unicos == 0 and total_f2_rescatados == 0:
            st.error(" Alerta: No se registran ofertas históricas previas en ninguna cadena comercial para poblar este contenedor.")
        else:
            lote_volcado_inicial = []
            id_operacion_limpia = int(id_campana_destino)

            if not df_f1_listo.empty:
                for _, fila_m in df_f1_listo.iterrows():
                    lote_volcado_inicial.append({
                        "id_producto": int(float(fila_m["id_producto"])),
                        "id_campana": id_operacion_limpia,
                        "id_super": int(id_super_contexto),
                        "id_sucursal": None if (pd.isna(fila_m.get("id_sucursal")) or fila_m.get("id_sucursal") is None) else fila_m.get("id_sucursal"),
                        "precio_oferta_proyectado": float(fila_m["precio_oferta"]),
                        "numero_pagina": int(float(fila_m["numero_pagina"])) if pd.notna(fila_m.get("numero_pagina")) else 0,
                        "posicion_slot": int(float(fila_m["posicion_slot"])) if pd.notna(fila_m.get("posicion_slot")) else 0,
                        "clonado_confirmado": False,
                        "alineacion": "C"
                    })

            if not df_f2_listo.empty:
                for _, fila_m in df_f2_listo.iterrows():
                    lote_volcado_inicial.append({
                        "id_campana": id_operacion_limpia,
                        "id_producto": int(float(fila_m["id_producto"])),
                        "id_super": int(id_super_contexto),
                        "id_sucursal": None,
                        "precio_oferta_proyectado": float(fila_m["precio_oferta"]),
                        "numero_pagina": int(float(fila_m["numero_pagina"])) if pd.notna(fila_m.get("numero_pagina")) else 0,
                        "posicion_slot": int(float(fila_m["posicion_slot"])) if pd.notna(fila_m.get("posicion_slot")) else 0,
                        "clonado_confirmado": False,
                        "alineacion": "C"
                    })
            try:
                with st.spinner("Sincronizando contenedores en Supabase..."):
                    # BLINDAJE LOGICO: Se eliminó el .delete() general para evitar borrado cruzado
                    chunk_size = 50
                    for index_chunk in range(0, len(lote_volcado_inicial), chunk_size):
                        sub_chunk = lote_volcado_inicial[index_chunk: index_chunk + chunk_size]
                        supabase_client.table("pre_ofertas").insert(sub_chunk).execute()

                    # Sincronización forzada en memoria para acoplar proyectados vs generados
                    st.session_state.stat_lider = int(total_f1_unicos)
                    st.session_state.stat_otros = int(total_f2_rescatados)
                    st.session_state.stat_total = int(total_f1_unicos + total_f2_rescatados)

                    st.toast(" ¡Laboratorio poblado con éxito!", icon="✅")
                    st.cache_data.clear()
                    st.rerun()
            except Exception as ex_v:
                st.error(f"Falla transaccional al inicializar lote: {ex_v}")
                st.stop()
else:
    # ---- AMBIENTE B: LA CAMPAÑA YA CONTIENE REGISTROS (MUESTRA EL MOSAICO v15) ----
    renderizar_cabecera_estadisticas()

    if 'form_categorias' in locals() and form_categorias:
        nombres_pestanas = [cat["nombre"].upper() for cat in form_categorias]
        pestanas_ui = st.tabs(nombres_pestanas)

        for index_tab, cat_info in enumerate(form_categorias):
            id_categoria_actual = cat_info["id_cat"]
            with pestanas_ui[index_tab]:
                items_del_pasillo = [item for item in lista_items if int(item.get("id_cat", 0)) == int(id_categoria_actual)]
                sub_filtradas = [s for s in form_subcategorias if int(s["id_cat"]) == int(id_categoria_actual)] if 'form_subcategorias' in locals() else []
                opciones_sub = [{"id_subcat": None, "nombre": "--- VER TODO EL PASILLO ---"}] + sub_filtradas

                sub_seleccionada = st.selectbox(
                    "Refinar surtido por subcategoría:",
                    options=opciones_sub,
                    format_func=lambda x: x["nombre"].upper(),
                    key=f"sub_tab_react_{id_categoria_actual}"
                )

                if sub_seleccionada["id_subcat"] is not None:
                    items_finales_mosaico = [item for item in items_del_pasillo if int(item.get("id_subcat", 0)) == int(sub_seleccionada["id_subcat"])]
                else:
                    items_finales_mosaico = items_del_pasillo

                if items_finales_mosaico:
                    st.caption(f"Mostrando {len(items_finales_mosaico)} artículos en este segmento")
                    dibujar_rejilla_mosaico(items_finales_mosaico, df_laboratorio_activo, layout_dinamico, columnas_elegidas, id_campana_destino)

        st.write("<br>", unsafe_allow_html=True)

        # =========================================================================
        # PANEL DE ACCIONES COMERCIALES Y LIMPIEZA DE BASE DE DATOS
        # =========================================================================
        st.write("---")
        col_btn1, col_btn2 = st.columns([2, 1]) # 2/3 para guardar, 1/3 para limpiar
        
        with col_btn1:
            disparar_rafaga = st.button("🚀 Disparar Inyección Express de Todo lo Seleccionado", use_container_width=True, type="primary")
            if disparar_rafaga:
                payload_rafaga = []
                for id_prod, referencias in st.session_state.get("formulario_imagenes_dict", {}).items():
                    marcado_final = st.session_state.get(referencias["marcado_key"], False)
                    precio_final = st.session_state.get(referencias["precio_key"], 0.0)
                    id_registro_existente = referencias.get("id_registro")
                    
                    if marcado_final or (id_registro_existente is not None):
                        registro_payload = {
                            "id_campana": int(id_campana_destino),
                            "id_producto": int(id_prod),
                            "id_super": int(id_super_contexto),
                            "precio_oferta_proyectado": float(precio_final),
                            "clonado_confirmado": bool(marcado_final),
                            "numero_pagina": 0,
                            "posicion_slot": 0,
                            "alineacion": "C"
                        }
                        if id_registro_existente is not None:
                            registro_payload["id_pre_oferta"] = int(id_registro_existente)
                        payload_rafaga.append(registro_payload)
                        
                if payload_rafaga:
                    try:
                        with st.spinner("Inyectando registros en lote masivo..."):
                            supabase_client.table("pre_ofertas").upsert(payload_rafaga).execute()
                            st.toast(f"¡Sincronización Exitosa! {len(payload_rafaga)} artículos impactados.", icon="🚀")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as err_api:
                        st.error(f"❌ Error de persistencia relacional en Supabase: {err_api}")
                else:
                    st.warning("⚠️ No se ha detectado ningún elemento modificado en la galería visual.")
                    
        with col_btn2:
            # Botón de purga con advertencia visual (Color Rojo / Destructivo)
            limpiar_laboratorio = st.button("🗑️ Vaciar y Resetear esta Campaña", use_container_width=True, type="secondary")
            if limpiar_laboratorio:
                id_limpieza_seguro = int(id_campana_destino)
                
                # SEGURO DE VIDA: Validamos que exista un ID de campaña real seleccionado en pantalla
                if id_limpieza_seguro > 0:
                    try:
                        with st.spinner("Purgando registros duplicados y basura en Supabase..."):
                            # Ejecuta el borrado condicional enfocado ÚNICA Y EXCLUSIVAMENTE en el contenedor activo
                            supabase_client.table("pre_ofertas").delete().filter("id_campana", "eq", id_limpieza_seguro).execute()
                            
                            # Reseteamos los estados de conteo superiores a cero de inmediato
                            st.session_state.stat_lider = 0
                            st.session_state.stat_otros = 0
                            st.session_state.stat_total = 0
                            if "formulario_imagenes_dict" in st.session_state:
                                st.session_state["formulario_imagenes_dict"] = {}
                                
                            st.toast("¡Campaña limpiada con éxito! Redireccionando al asistente...", icon="🧼")
                            st.cache_data.clear()
                            st.rerun() # Fuerza a Streamlit a recalcular y encender el Ambiente A
                    except Exception as err_delete:
                        st.error(f"❌ Error crítico al intentar vaciar la tabla: {err_delete}")
                else:
                    st.error("❌ No se pudo determinar el ID de la campaña. Operación abortada por seguridad.")



# =========================================================================
# ## 3. MODULO: BITÁCORA DE AUDITORÍA INFERIOR (MÁXIMA INTEGRIDAD v14.9.0)
# =========================================================================
st.write("---")
st.markdown(f"#### 3. Bitácora de Auditoria en Vivo: Campaña ID {id_campana_destino}")

if not df_lote_express.empty and 'df_pool_unicos' in locals():
    lista_tabla_inferior_completa = []
    
    for _, fila_p in df_pool_unicos.iterrows():
        id_p_raw = int(fila_p["id_producto"])
        match_campana_p2 = pd.DataFrame()
        
        # Búsqueda de coincidencia exacta en la campaña activa
        if not df_laboratorio_activo.empty and "id_producto" in df_laboratorio_activo.columns:
            match_campana_p2 = df_laboratorio_activo[df_laboratorio_activo["id_producto"].astype(str) == str(id_p_raw)]
            
        if not match_campana_p2.empty:
            # RESTAURACIÓN 14.9.0: Extracción segura con .iloc[0] para prevenir TypeErrors
            es_conf_p2 = bool(match_campana_p2["clonado_confirmado"].iloc[0]) if "clonado_confirmado" in match_campana_p2.columns else False
            val_pag_p2 = match_campana_p2["numero_pagina"].iloc[0] if "numero_pagina" in match_campana_p2.columns else 0
            
            try:
                num_pag_p2 = int(float(val_pag_p2)) if (pd.notna(val_pag_p2) and str(val_pag_p2).strip() != "") else 0
            except ValueError:
                num_pag_p2 = 0
                
            if es_conf_p2:
                status_inferior = "🟢 Sí (Included por Maquetar)"
                orden_prioridad_ram = 1  # FLOTACIÓN MÁXIMA: Sube al tope de la bitácora
            else:
                status_inferior = "❌ NO (EXC_REMOVIDO)"
                orden_prioridad_ram = 2  # FONDO
                
            precio_final_print = float(match_campana_p2["precio_oferta_proyectado"].iloc[0]) if "precio_oferta_proyectado" in match_campana_p2.columns else float(fila_p["precio_oferta"])
        else:
            status_inferior = "❌ NO (EXC_REMOVIDO)"
            orden_prioridad_ram = 2
            precio_final_print = float(fila_p["precio_oferta"])
            
        lista_tabla_inferior_completa.append({
            "Prioridad": int(orden_prioridad_ram),
            "Artículo": str(fila_p["nombre"]).strip(),
            "Marca": str(fila_p["marca"]).strip() if pd.notna(fila_p.get("marca")) else "Sin Marca",
            "Presentación": f"{fila_p['tamano']} {fila_p['unidad']}",
            "PVP Oferta ($)": precio_final_print,
            "Estado Red": status_inferior
        })
        
    df_grid_inferior = pd.DataFrame(lista_tabla_inferior_completa)
    
    if not df_grid_inferior.empty:
        # Ordenamiento estable de v14.9.0: Verdes primero, luego alfabético por artículo
        df_grid_inferior = df_grid_inferior.sort_values(by=["Prioridad", "Artículo"], ascending=[True, True]).reset_index(drop=True)
        df_grid_inferior = df_grid_inferior.drop(columns=["Prioridad"])
        
        st.info(f" Monitoreo Relacional: Mostrando **{len(df_grid_inferior)} artículos** totales en este segmento del pasillo.")
        st.dataframe(
            df_grid_inferior, 
            column_config={"PVP Oferta ($)": st.column_config.NumberColumn(format="$ %.2f")}, 
            hide_index=True, 
            use_container_width=True
        )
    else:
        st.info("Grilla vacía. Seleccione un Pasillo o Subcategoría en la cabecera superior para desplegar la bitácora.")
else:
    st.info("Grilla vacía. Seleccione un Pasillo o Subcategoría en la cabecera superior para desplegar la bitácora.")
