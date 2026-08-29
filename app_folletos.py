import streamlit as st
import pandas as pd
import numpy as np

# Configuración avanzada de la interfaz
st.set_page_config(
    page_title="SmartLayout AI - Gestión de Folletos",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados para mejorar el contraste visual y la experiencia de usuario
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #4f46e5 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 SmartLayout AI: Motor Avanzado de Maquetación")
st.markdown("""
Sistema de optimización espacial para la tabla `public.ofertas`. Distribuye inventarios masivos
de ofertas aplicando algoritmos de restricciones espaciales y jerarquía comercial.
""")

# --- CONFIGURACIÓN DE PARÁMETROS COMERCIALES (SIDEBAR) ---
st.sidebar.header("🎯 Parámetros de la Campaña")
id_campana = st.sidebar.number_input("ID de Campaña (Supabase)", min_value=1, value=102, step=1)
paginas_totales = st.sidebar.slider("Límite de Páginas del Folleto", min_value=2, max_value=32, value=4)

st.sidebar.markdown("---")
st.sidebar.header("📐 Reglas del Algoritmo")
criterio_orden = st.sidebar.selectbox(
    "Criterio de Prioridad para Slots Calientes",
    options=["Favoritos Primero ⭐", "Mayor Precio 💰", "Combinado (Fav + Precio) 📊"]
)

# --- SIMULACIÓN DE DATOS INICIALES CON ATRIBUTOS COMERCIALES ---
@st.cache_data
def generar_inventario_crudo(campana_id):
    """Simula el estado inicial de ofertas que vienen de Supabase (sin maquetar o parcial)"""
    np.random.seed(10)
    num_productos = 45
    
    categorias = ['Carnes y Pescados', 'Lácteos', 'Abarrotes', 'Bebidas', 'Limpieza', 'Cuidado Personal']
    productos_nombres = [
        "Aceite de Oliva Extra Virgen 1L", "Leche Entera Pack x6", "Arroz Integral 1kg",
        "Detergente Líquido Concentrado", "Filete de Salmón Fresco 500g", "Pechuga de Pollo 1kg",
        "Refresco de Cola 2.5L", "Cerveza Premium Pack x12", "Café Tostado Molido 500g",
        "Papel Higiénico 12 rollos", "Shampoo Control Caspa", "Queso Gouda Tajado 250g"
    ]
    
    # Asegurar nombres variados
    nombres = [f"{np.random.choice(productos_nombres)} #{i}" for i in range(1, num_productos + 1)]
    
    df = pd.DataFrame({
        'id_oferta': range(1001, 1001 + num_productos),
        'id_producto': np.random.randint(5000, 9999, size=num_productos),
        'nombre_producto': nombres,
        'categoria': [np.random.choice(categorias) for _ in range(num_productos)],
        'precio_oferta': np.round(np.random.uniform(3.99, 89.99, size=num_productos), 2),
        'es_favorita': np.random.choice([True, False], size=num_productos, p=[0.25, 0.75]),
        'en_lista_compras': [False] * num_productos,
        'oferta_comprada': [False] * num_productos,
        'id_campana': campana_id,
        # Campos de distribución (inicialmente vacíos para simular el reto de llenado inteligente)
        'numero_pagina': [None] * num_productos,
        'posicion_slot': [None] * num_productos,
        'alineacion': [None] * num_productos,
        'posicion_mix': [None] * num_productos,
        'sub_molde_estilo': [None] * num_productos,
        'numero_fila': [None] * num_productos,
        'numero_columna': [None] * num_productos
    })
    
    # Pre-llenar un par de registros para validar comportamiento
    df.loc[0, ['numero_pagina', 'posicion_slot', 'alineacion', 'numero_fila', 'numero_columna']] = [1, 1, 'C', 1, 1]
    df.loc[0, ['sub_molde_estilo', 'posicion_mix']] = ['Grid_2x2', 'Destacado']
    
    return df

if 'df_smart_ofertas' not in st.session_state or st.session_state.get('last_campana') != id_campana:
    st.session_state['df_smart_ofertas'] = generar_inventario_crudo(id_campana)
    st.session_state['last_campana'] = id_campana

df_ofertas = st.session_state['df_smart_ofertas']

# --- MOTOR DE INTELIGENCIA DE DISTRIBUCIÓN (ALGORITMO DETRÁS DE ESCENAS) ---
def ejecutar_algoritmo_smart(df, config_moldes, paginas_limite, criterio):
    """
    Algoritmo de optimización espacial con eliminación de colisiones.
    Organiza el inventario basándose en matrices de espacio físico real.
    """
    df_trabajo = df.copy()
    
    # 1. Clasificar y ordenar el inventario según su relevancia comercial (Criterio Inteligente)
    if criterio == "Favoritos Primero ⭐":
        df_trabajo = df_trabajo.sort_values(by=['es_favorita', 'precio_oferta'], ascending=[False, False])
    elif criterio == "Mayor Precio 💰":
        df_trabajo = df_trabajo.sort_values(by='precio_oferta', ascending=False)
    else: # Combinado
        df_trabajo['score_comercial'] = df_trabajo['precio_oferta'] + (df_trabajo['es_favorita'].astype(int) * 50)
        df_trabajo = df_trabajo.sort_values(by='score_comercial', ascending=False)
        df_trabajo = df_trabajo.drop(columns=['score_comercial'])

    # Extraer los productos que aún no han sido fijados manualmente por el usuario
    fijos = df_trabajo['numero_pagina'].notna() & df_trabajo['numero_fila'].notna() & df_trabajo['numero_columna'].notna()
    df_fijos = df_trabajo[fijos]
    df_libres = df_trabajo[~fijos]
    
    productos_a_ubicar = df_libres.to_dict('records')
    lista_final_fijos = df_fijos.to_dict('records')
    
    # Mapas de ocupación por página para evitar colisiones absolutas
    # Estructura: ocupacion[pagina] = set((fila, columna))
    ocupacion = {p: set() for p in range(1, paginas_limite + 1)}
    
    # Registrar los espacios ocupados por productos fijos
    for item in lista_final_fijos:
        p = int(item['numero_pagina'])
        f = int(item['numero_fila'])
        c = int(item['numero_columna'])
        if p in ocupacion:
            ocupacion[p].add((f, c))

    # Ejecutar ruteo espacial sobre las páginas del folleto
    idx_prod = 0
    total_libres = len(productos_a_ubicar)
    
    for p in range(1, paginas_limite + 1):
        if idx_prod >= total_libres:
            break
            
        # Determinar la grilla matemática según el molde elegido para esta página
        molde = config_moldes.get(p, "Grid_3x3")
        if molde == "Grid_2x2":
            filas_max, cols_max = 2, 2
        elif molde == "Grid_4x4":
            filas_max, cols_max = 4, 4
        else: # Grid_3x3 por defecto
            filas_max, cols_max = 3, 3
            
        slot_counter = 1
        
        # Iterar la matriz espacial de la página
        for f in range(1, filas_max + 1):
            for c in range(1, cols_max + 1):
                if idx_prod >= total_libres:
                    break
                    
                # Si la celda está ocupada por un elemento fijo del usuario, saltar
                if (f, c) in ocupacion[p]:
                    slot_counter += 1
                    continue
                
                # Asignar el producto con mayor prioridad comercial a esta celda
                prod = productos_a_ubicar[idx_prod]
                prod['numero_pagina'] = p
                prod['numero_fila'] = f
                prod['numero_columna'] = c
                prod['posicion_slot'] = slot_counter
                prod['sub_molde_estilo'] = molde
                prod['posicion_mix'] = "Zona Caliente" if slot_counter <= 2 else "Estándar"
                # Forzar restricción unaria CHECK (I, C, D) de forma estética según su columna
                prod['alineacion'] = 'I' if c == 1 else 'D' if c == cols_max else 'C'
                
                # Registrar espacio ocupado y avanzar
                ocupacion[p].add((f, c))
                lista_final_fijos.append(prod)
                idx_prod += 1
                slot_counter += 1

    # Re-empacar aquellos productos que no cupieron en el límite de páginas
    while idx_prod < total_libres:
        prod = productos_a_ubicar[idx_prod]
        prod['numero_pagina'] = None
        prod['numero_fila'] = None
        prod['numero_columna'] = None
        prod['posicion_slot'] = None
        prod['sub_molde_estilo'] = None
        prod['alineacion'] = None
        lista_final_fijos.append(prod)
        idx_prod += 1

    return pd.DataFrame(lista_final_fijos)


# --- INTERFAZ GRÁFICA CONTROLADORA ---
tab_config, tab_visor, tab_auditoria = st.tabs([
    "🎯 1. Configuración Estructural", 
    "🗺️ 2. Espejo Visual de Páginas", 
    "🛡️ 3. Auditoría de Datos & SQL"
])

# --- PESTAÑA 1: CONFIGURACIÓN ESTRUCTURAL ---
with tab_config:
    st.subheader("Asignación de Estilos de Maquetación por Página")
    st.write("Define el esqueleto de diseño de cada página. El motor adaptará el flujo de datos a estas matrices.")
    
    # Generar selectores dinámicos para los moldes de cada página
    col_paginas = st.columns(min(paginas_totales, 4))
    config_moldes = {}
    
    for idx in range(1, paginas_totales + 1):
        col_idx = (idx - 1) % 4
        with col_paginas[col_idx]:
            # Guardar la estructura deseada para cada página
            config_moldes[idx] = st.selectbox(
                f"Estructura Pág. {idx}", 
                options=["Grid_2x2", "Grid_3x3", "Grid_4x4"], 
                index=1, 
                key=f"molde_p_{idx}"
            )
            
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        st.info("💡 **Llenado Inteligente Automático:** Ordenará el inventario por relevancia comercial, buscará espacios vacíos y auto-calculará slots y coordenadas cartesianas eliminando colisiones.")
    with col_btn2:
        if st.button("🚀 Ejecutar Llenado Inteligente Global", use_container_width=True):
            df_optimizado = ejecutar_algoritmo_smart(df_ofertas, config_moldes, paginas_totales, criterio_orden)
            st.session_state['df_smart_ofertas'] = df_optimizado
            st.success("¡Algoritmo ejecutado! Distribución libre de colisiones generada.")
            st.rerun()
        
        st.subheader("📝 Modificaciones y Ajustes Finos Manuales")
        st.caption("Puedes alterar cualquier celda. El sistema protegerá las claves primarias pero respetará tus cambios de diseño.")
        
        # Editor interactivo avanzado
        df_editable = st.data_editor(
        df_ofertas,
        column_config={
            "id_oferta": st.column_config.NumberColumn("ID Oferta", disabled=True),
            "nombre_producto": st.column_config.TextColumn("Producto", disabled=True),
            "precio_oferta": st.column_config.NumberColumn("Precio", format="$ %.2f", disabled=True),
            "es_favorita": st.column_config.CheckboxColumn("⭐ Destacado", disabled=True),
            "numero_pagina": st.column_config.NumberColumn("Página Assig.", min_value=1, max_value=paginas_totales),
            "posicion_slot": st.column_config.NumberColumn("Slot"),
            "numero_fila": st.column_config.NumberColumn("Fila X"),
            "numero_columna": st.column_config.NumberColumn("Columna Y"),
            "alineacion": st.column_config.SelectboxColumn("Alineación (CHECK)", options=["I", "C", "D"]),
            "sub_molde_estilo": st.column_config.TextColumn("Estilo"),
            "categoria": st.column_config.TextColumn("Categoría", disabled=True)
        },
        hide_index=True,
        key="global_smart_editor"
        )
        
        if st.button("💾 Consolidar Cambios Manuales en Memoria"):
        st.session_state['df_smart_ofertas'] = df_editable
        st.toast("Cambios manuales guardados.", icon="💾")
        st.rerun()
        
        # --- PESTAÑA 2: ESPEJO VISUAL DE PÁGINAS ---
        with tab_visor:
        st.subheader("🗺️ Visor de Layout y Zonificación Comercial")
        
        # Filtrar visualización por página activa
        pag_ver = st.select_slider("Hojear Folleto (Página Actual)", options=list(range(1, paginas_totales + 1)))
        
        molde_actual = config_moldes.get(pag_ver, "Grid_3x3")
        if molde_actual == "Grid_2x2":
        f_lim, c_lim = 2, 2
        elif molde_actual == "Grid_4x4":
        f_lim, c_lim = 4, 4
        else:
        f_lim, c_lim = 3, 3
        
        st.write(f"Estructura de la página: **{molde_actual}** ({f_lim}x{c_lim} Espacios)")
        
        # Filtrar ofertas correspondientes a esta página
        df_pag_vis = df_ofertas[df_ofertas['numero_pagina'] == pag_ver]
        
        # Dibujar la matriz física del folleto
        for f in range(1, f_lim + 1):
        cols_layout = st.columns(c_lim)
        for c in range(1, c_lim + 1):
            with cols_layout[c-1]:
                # Buscar el producto que coincide exactamente con la celda cartesiana
                celda_prod = df_pag_vis[(df_pag_vis['numero_fila'] == f) & (df_pag_vis['numero_columna'] == c)]
                
                if len(celda_prod) > 1:
                    # Alerta Inteligente de Colisión Espacial
                    st.markdown(f"""
                    <div style="border: 2px solid #ef4444; border-radius: 8px; padding: 12px; background-color: #fee2e2; color: #991b1b; text-align: center; min-height: 140px;">
                        <span style="font-weight: bold; font-size: 1.1rem;">⚠️ COLISIÓN DE ESPACIO</span><br>
                        <span style="font-size: 0.85rem;">{len(celda_prod)} productos asignados a la Fila {f}, Col {c}.</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif not celda_prod.empty:
                    row = celda_prod.iloc[0]
                    is_fav = row['es_favorita']
                    fav_badge = "⭐ DESTACADO" if is_fav else "REGULAR"
                    border_color = "#3b82f6" if not is_fav else "#eab308"
                    bg_color = "#ffffff" if not is_fav else "#fef9c3"
                    
                    st.markdown(f"""
                    <div style="border: 2px solid {border_color}; border-radius: 8px; padding: 12px; background-color: {bg_color}; color: #1e293b; min-height: 140px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b; font-weight: bold;">
                            <span>Slot {int(row['posicion_slot'])}</span>
                            <span style="color: {border_color};">{fav_badge}</span>
                        </div>
                        <h4 style="margin: 6px 0; font-size: 1rem; color: #0f172a;">{row['nombre_producto']}</h4>
                        <p style="margin: 0; font-weight: bold; font-size: 1.2rem; color: #dc2626;">${row['precio_oferta']}</p>
                        <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid #e2e8f0; font-size: 0.75rem; color: #475569;">
                            Cat: <b>{row['categoria']}</b><br>
                            Alin: <b>{row['alineacion']}</b> | Mix: <b>{row['posicion_mix']}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Celda libre mapeada
                    st.markdown(f"""
                    <div style="border: 2px dashed #cbd5e1; border-radius: 8px; padding: 12px; background-color: #f8fafc; text-align: center; color: #94a3b8; min-height: 140px; display: flex; flex-direction: column; justify-content: center;">
                        <span style="font-size: 0.8rem; font-weight: 500;">Espacio Disponible</span>
                        <span style="font-size: 0.75rem; font-style: italic;">Fila {f} · Col {c}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # --- PESTAÑA 3: AUDITORÍA DE DATOS Y SQL ---
        with tab_auditoria:
        st.header("🛡️ Consistencia de Datos e Integración Relacional")
        
        # 1. Reporte Estadístico del Folleto
        totales = len(df_ofertas)
        asignados = len(df_ofertas[df_ofertas['numero_pagina'].notna()])
        huerfanos = totales - asignados
        
        col_st1, col_st2, col_st3 = st.columns(3)
        col_st1.metric("Total Ofertas de Campaña", totales)
        col_st2.metric("Ubicadas en Catálogo", asignados, f"{asignados/totales*100:.1f}%")
        col_st3.metric("Productos Sin Espacio (Huérfanos)", huerfanos, delta=f"-{huerfanos}" if huerfanos > 0 else "0", delta_color="inverse")
        
        if huerfanos > 0:
        st.warning(f"⚠️ Alerta: Tienes {huerfanos} productos fuera del catálogo porque superaste el límite de páginas ({paginas_totales}). Aumenta las páginas en la barra lateral o incrementa la densidad de las grillas.")
        
        st.subheader("⚡ Script Transaccional Optimizado para Supabase / PostgreSQL")
        st.write("Este código aplica los cambios utilizando un bloque controlado `BEGIN ... COMMIT`. Si ocurre un solo fallo de integridad, se revierte todo automáticamente.")
        
        # Construcción limpia de la query
        queries = []
        queries.append(f"-- Sincronización inteligente de Layout - Campaña {id_campana}")
        queries.append("BEGIN;")
        
        for _, r in df_ofertas.iterrows():
        # Procesar valores nulos para formato SQL nativo
        p_pag = int(r['numero_pagina']) if pd.notna(r['numero_pagina']) else "NULL"
        p_slot = int(r['posicion_slot']) if pd.notna(r['posicion_slot']) else "NULL"
        p_alin = f"'{r['alineacion']}'" if pd.notna(r['alineacion']) else "NULL"
        p_mix = f"'{r['posicion_mix']}'" if pd.notna(r['posicion_mix']) else "NULL"
        p_est = f"'{r['sub_molde_estilo']}'" if pd.notna(r['sub_molde_estilo']) else "NULL"
        p_fil = int(r['numero_fila']) if pd.notna(r['numero_fila']) else "NULL"
        p_col = int(r['numero_columna']) if pd.notna(r['numero_columna']) else "NULL"
        
        q = (f"UPDATE public.ofertas SET "
             f"numero_pagina = {p_pag}, posicion_slot = {p_slot}, alineacion = {p_alin}, "
             f"posicion_mix = {p_mix}, sub_molde_estilo = {p_est}, numero_fila = {p_fil}, numero_columna = {p_col} "
             f"WHERE id_oferta = {r['id_oferta']};")
        queries.append(q)
        
        queries.append("COMMIT;")
        sql_completo = "\n".join(queries)
        
        st.code(sql_completo, language="sql")
        
        # Descargas
        csv_bytes = df_ofertas.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Actualización de Catálogo (CSV)", csv_bytes, f"smart_layout_{id_campana}.csv", "text/csv")
