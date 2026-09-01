import streamlit as st
from streamlit_dnd import dnd, apply_move
import pandas as pd
import io

st.set_page_config(
    page_title="Clasificador Maestro de Surtido — Nativo",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════
# INICIALIZACIÓN DE SESSION STATE
# ═══════════════════════════════════════════════════════════════
if "estantes" not in st.session_state:
    st.session_state.estantes = []          # [{id, nombre}, ...]
if "productos" not in st.session_state:
    st.session_state.productos = []         # [{id_catalogo, nombre_catalogo, id_enlace_subcat}, ...]
if "layout" not in st.session_state:
    st.session_state.layout = {}            # {"deposito": [ids], "estante_X": [ids], ...}
if "estantes_cargados" not in st.session_state:
    st.session_state.estantes_cargados = False
if "productos_cargados" not in st.session_state:
    st.session_state.productos_cargados = False

# ═══════════════════════════════════════════════════════════════
# CABECERA
# ═══════════════════════════════════════════════════════════════
st.title("🖱️ Panel de Refinamiento CSV Dinámico")
st.caption("Módulo 100% Nativo Streamlit · Drag & Drop vía streamlit-dnd")

# ═══════════════════════════════════════════════════════════════
# CARGA DE ARCHIVOS
# ═══════════════════════════════════════════════════════════════
with st.container(border=True):
    c1, c2 = st.columns(2)

    with c1:
        archivo_estantes = st.file_uploader(
            "⚙️ PASO 1: Estantes (.CSV)",
            type=["csv"],
            key="file_estantes",
            help="CSV con columnas: id_estante; nombre_estante"
        )

    with c2:
        archivo_productos = st.file_uploader(
            "📦 PASO 2: Artículos (.CSV)",
            type=["csv"],
            key="file_productos",
            disabled=not st.session_state.estantes_cargados,
            help="CSV con columnas: id_catalogo; nombre_catalogo; id_enlace_subcat"
        )

# ═══════════════════════════════════════════════════════════════
# PARSEO DE CSV DE ESTANTES
# ═══════════════════════════════════════════════════════════════
if archivo_estantes is not None and not st.session_state.estantes_cargados:
    try:
        df_est = pd.read_csv(archivo_estantes, sep=None, engine="python", header=None, skipinitialspace=True)
        st.session_state.estantes = []
        nuevo_layout = {"deposito": []}

        for _, row in df_est.iterrows():
            if len(row) >= 2 and pd.notna(row[0]) and str(row[0]).strip() != "":
                est_id = str(row[0]).strip()
                est_nombre = str(row[1]).strip() if pd.notna(row[1]) else f"Estante {est_id}"
                st.session_state.estantes.append({"id": est_id, "nombre": est_nombre})
                nuevo_layout[f"estante_{est_id}"] = []

        st.session_state.layout = nuevo_layout
        st.session_state.estantes_cargados = True
        st.session_state.productos_cargados = False
        st.session_state.productos = []
        st.rerun()
    except Exception as e:
        st.error(f"Error leyendo estantes: {e}")

# ═══════════════════════════════════════════════════════════════
# PARSEO DE CSV DE PRODUCTOS
# ═══════════════════════════════════════════════════════════════
if archivo_productos is not None and not st.session_state.productos_cargados:
    try:
        df_prod = pd.read_csv(archivo_productos, sep=None, engine="python", header=None, skipinitialspace=True)
        st.session_state.productos = []

        # Limpiar layout previo (conservar estantes vacíos)
        for key in st.session_state.layout:
            st.session_state.layout[key] = []

        for _, row in df_prod.iterrows():
            if len(row) >= 1 and pd.notna(row[0]) and str(row[0]).strip() != "":
                prod_id = str(row[0]).strip()
                prod_nombre = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else "Producto Sin Nombre"
                prod_subcat = str(row[2]).strip() if len(row) > 2 and pd.notna(row[2]) else ""

                st.session_state.productos.append({
                    "id_catalogo": prod_id,
                    "nombre_catalogo": prod_nombre,
                    "id_enlace_subcat": prod_subcat
                })

                # Ubicar en el estante correspondiente o en depósito
                key_estante = f"estante_{prod_subcat}"
                if prod_subcat != "" and key_estante in st.session_state.layout:
                    st.session_state.layout[key_estante].append(prod_id)
                else:
                    st.session_state.layout["deposito"].append(prod_id)

        st.session_state.productos_cargados = True
        st.rerun()
    except Exception as e:
        st.error(f"Error leyendo productos: {e}")

# ═══════════════════════════════════════════════════════════════
# RENDERIZADO DEL PANEL DE CLASIFICACIÓN
# ═══════════════════════════════════════════════════════════════
if not st.session_state.estantes_cargados:
    st.info("⬆️ Carga primero el CSV de estantes para levantar la infraestructura.")
    st.stop()

# Helper para buscar un producto por su ID
def buscar_producto(pid):
    for p in st.session_state.productos:
        if p["id_catalogo"] == pid:
            return p
    return None

# ── Columna izquierda: Depósito General ──
with st.container(border=False):
    izq, der = st.columns([1, 3])

    with izq:
        st.subheader("📋 Depósito General")
        with st.container(key="deposito", border=True):
            for pid in st.session_state.layout.get("deposito", []):
                prod = buscar_producto(pid)
                if prod:
                    with st.container(key=f"prod_{pid}", border=True):
                        st.markdown(f"**{prod['id_catalogo']}** — {prod['nombre_catalogo']}")

    # ── Columna derecha: Estantes ──
    with der:
        st.subheader("📥 Estantes Oficiales de la Tienda")
        n_estantes = len(st.session_state.estantes)
        if n_estantes > 0:
            cols = st.columns(n_estantes)
            for i, est in enumerate(st.session_state.estantes):
                with cols[i]:
                    with st.container(key=f"estante_{est['id']}", border=True):
                        st.markdown(f"**{est['nombre']}**")
                        for pid in st.session_state.layout.get(f"estante_{est['id']}", []):
                            prod = buscar_producto(pid)
                            if prod:
                                with st.container(key=f"prod_{pid}", border=True):
                                    st.markdown(f"**{prod['id_catalogo']}** — {prod['nombre_catalogo']}")

# ═══════════════════════════════════════════════════════════════
# ACTIVACIÓN DE DRAG & DROP
# ═══════════════════════════════════════════════════════════════
all_container_keys = ["deposito"] + [f"estante_{e['id']}" for e in st.session_state.estantes]
event = dnd(*all_container_keys)

if event:
    apply_move(event, st.session_state.layout)
    st.rerun()

# ═══════════════════════════════════════════════════════════════
# DESCARGA DEL CSV REFINADO
# ═══════════════════════════════════════════════════════════════
if st.session_state.productos_cargados and st.session_state.productos:
    st.divider()

    # Reconstruir asignaciones actuales desde el layout
    asignaciones = {}
    for cont_key, lista_ids in st.session_state.layout.items():
        if cont_key == "deposito":
            est_id = ""
        else:
            est_id = cont_key.replace("estante_", "")
        for pid in lista_ids:
            asignaciones[pid] = est_id

    filas_csv = []
    for prod in st.session_state.productos:
        pid = prod["id_catalogo"]
        filas_csv.append({
            "id_catalogo": pid,
            "nombre_catalogo": prod["nombre_catalogo"],
            "id_enlace_subcat": asignaciones.get(pid, "")
        })

    df_out = pd.DataFrame(filas_csv)
    buffer = io.StringIO()
    df_out.to_csv(buffer, sep=";", index=False, lineterminator="\n")
    csv_str = buffer.getvalue()

    col_dl, col_info = st.columns([1, 4])
    with col_dl:
        st.download_button(
            label="💾 Descargar CSV Refinado",
            data=csv_str,
            file_name="surtido_refinado_oficina.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_info:
        st.success(f"Listo: {len(df_out)} productos clasificados en {len(st.session_state.estantes)} estantes.")
