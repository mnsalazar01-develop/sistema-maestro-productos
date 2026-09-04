import streamlit as st

st.set_page_config(page_title="Prototipo Maquetador V0", layout="wide")
st.title("🎨 Prototipo Maquetador V0 — Grilla Visual")
st.caption("Prueba independiente: sin Drag & Drop y sin modificar el programa original.")

productos = [
    {"id_oferta": 101, "nombre": "Coca-Cola 2 L", "precio": 2.99},
    {"id_oferta": 102, "nombre": "Pepsi 2 L", "precio": 2.79},
    {"id_oferta": 103, "nombre": "Galletas Oreo", "precio": 3.49},
    {"id_oferta": 104, "nombre": "Arroz 5 lb", "precio": 6.99},
    {"id_oferta": 105, "nombre": "Aceite 1 L", "precio": 4.59},
    {"id_oferta": 106, "nombre": "Leche 1 galón", "precio": 4.99},
    {"id_oferta": 107, "nombre": "Pan Blanco", "precio": 2.49},
    {"id_oferta": 108, "nombre": "Café 12 oz", "precio": 7.99},
]

if "seleccionado" not in st.session_state:
    st.session_state.seleccionado = None
if "maqueta" not in st.session_state:
    st.session_state.maqueta = {}
if "pagina" not in st.session_state:
    st.session_state.pagina = 1
if "filas" not in st.session_state:
    st.session_state.filas = 2
if "columnas" not in st.session_state:
    st.session_state.columnas = 3

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.pagina = st.number_input("Página", 1, 20, st.session_state.pagina, 1)
    with c2:
        st.session_state.filas = st.number_input("Filas", 1, 6, st.session_state.filas, 1)
    with c3:
        st.session_state.columnas = st.number_input("Columnas", 1, 6, st.session_state.columnas, 1)

st.divider()
st.subheader("🛒 Banco de productos")
st.caption("Selecciona un producto y luego haz clic en la celda donde quieres colocarlo.")

pagina = st.session_state.pagina
colocados = {v for (p, f, c), v in st.session_state.maqueta.items() if p == pagina}
banco = [p for p in productos if p["id_oferta"] not in colocados]

cols = st.columns(4)
for i, producto in enumerate(banco):
    with cols[i % 4]:
        if st.button(f"📦 {producto['nombre']} — ${producto['precio']:.2f}",
                     key=f"producto_{producto['id_oferta']}", use_container_width=True):
            st.session_state.seleccionado = producto["id_oferta"]
            st.rerun()

if st.session_state.seleccionado is not None:
    p = next((x for x in productos if x["id_oferta"] == st.session_state.seleccionado), None)
    if p:
        st.info(f"🎯 Seleccionado: **{p['nombre']}**. Haz clic en una celda libre.")

st.divider()
st.subheader(f"📄 Página {pagina}")

for fila in range(1, st.session_state.filas + 1):
    cols = st.columns(st.session_state.columnas)
    for columna in range(1, st.session_state.columnas + 1):
        clave = (pagina, fila, columna)
        oferta_id = st.session_state.maqueta.get(clave)
        with cols[columna - 1]:
            if oferta_id is not None:
                p = next(x for x in productos if x["id_oferta"] == oferta_id)
                st.markdown(
                    f'<div style="min-height:120px;border:1px solid #d9d9d9;'
                    f'border-radius:8px;padding:14px;background:#fafafa;text-align:center;">'
                    f'<div style="font-size:12px;color:#777;">Fila {fila} · Columna {columna}</div>'
                    f'<div style="font-size:18px;font-weight:600;margin-top:8px;">{p["nombre"]}</div>'
                    f'<div style="font-size:16px;margin-top:6px;">${p["precio"]:.2f}</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"✕ Quitar", key=f"quitar_{pagina}_{fila}_{columna}",
                             use_container_width=True):
                    del st.session_state.maqueta[clave]
                    st.rerun()
            else:
                if st.button(f"＋ LIBRE\nFila {fila} · Columna {columna}",
                             key=f"celda_{pagina}_{fila}_{columna}",
                             use_container_width=True):
                    if st.session_state.seleccionado is not None:
                        for k in list(st.session_state.maqueta):
                            if st.session_state.maqueta[k] == st.session_state.seleccionado:
                                del st.session_state.maqueta[k]
                        st.session_state.maqueta[clave] = st.session_state.seleccionado
                        st.session_state.seleccionado = None
                        st.rerun()
                    else:
                        st.warning("Primero selecciona un producto del banco.")

st.divider()
st.subheader("💾 Datos de posición")
salida = []
for (p, fila, columna), oferta_id in sorted(st.session_state.maqueta.items()):
    if p == pagina:
        producto = next(x for x in productos if x["id_oferta"] == oferta_id)
        salida.append({
            "id_oferta": oferta_id,
            "nombre": producto["nombre"],
            "numero_pagina": p,
            "numero_fila": fila,
            "numero_columna": columna,
        })

if salida:
    st.dataframe(salida, hide_index=True, use_container_width=True)
else:
    st.info("Todavía no hay productos colocados en esta página.")

if st.button("🧹 Limpiar página actual", use_container_width=True):
    for k in list(st.session_state.maqueta):
        if k[0] == pagina:
            del st.session_state.maqueta[k]
    st.session_state.seleccionado = None
    st.rerun()
