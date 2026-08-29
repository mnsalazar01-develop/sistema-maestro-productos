import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Llenado Inteligente de Folletos",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título Principal
st.title("📖 Llenado Inteligente y Layout de Folletos")
st.markdown("""
Esta aplicación web interactiva permite la distribución visual y la asignación inteligente de coordenadas de maquetación 
para la tabla `public.ofertas`. Automatiza y valida la posición de cada producto en las páginas del catálogo.
""")

# --- SIDEBAR: Parámetros del Folleto / Campaña ---
st.sidebar.header("⚙️ Configuración de Campaña")
id_campana = st.sidebar.number_input("ID de Campaña Target", min_value=1, value=100, step=1)
paginas_totales = st.sidebar.slider("Total de Páginas del Folleto", min_value=1, max_value=64, value=8)

# 2. CONEXIÓN SEGURA HEREDADA CON LAS LLAVES DE SUPABASE
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

# Simulación de Datos Iniciales (Base de Datos)
@st.cache_data
def generar_datos_simulados(campana_id, num_paginas):
    # Generamos 50 productos de ejemplo sin maquetar para esa campaña
    np.random.seed(42)
    productos = [f"Producto {i}" for i in range(1, 51)]
    ids_productos = np.random.randint(1000, 9999, size=50)
    ids_supers = np.random.randint(1, 5, size=50)
    precios = np.round(np.random.uniform(5.0, 150.0, size=50), 2)
    
    df = pd.DataFrame({
        'id_oferta': range(1, 51),
        'id_producto': ids_productos,
        'nombre_producto': productos, # Para visualización amigable en la UI
        'id_super': ids_supers,
        'precio_oferta': precios,
        'id_campana': campana_id,
        'numero_pagina': [None] * 50,
        'posicion_slot': [None] * 50,
        'alineacion': [None] * 50,
        'posicion_mix': [None] * 50,
        'sub_molde_estilo': [None] * 50,
        'numero_fila': [None] * 50,
        'numero_columna': [None] * 50
    })
    
    # Pre-llenar los primeros 15 productos para demostración
    for i in range(15):
        df.loc[i, 'numero_pagina'] = int((i // 4) + 1)
        df.loc[i, 'posicion_slot'] = int((i % 4) + 1)
        df.loc[i, 'alineacion'] = ['I', 'C', 'D'][i % 3]
        df.loc[i, 'posicion_mix'] = 'Estándar' if i % 2 == 0 else 'Destacado'
        df.loc[i, 'sub_molde_estilo'] = 'Grid_4x4' if i % 3 == 0 else 'Banner_Horiz'
        df.loc[i, 'numero_fila'] = int((i % 4) // 2 + 1)
        df.loc[i, 'numero_columna'] = int((i % 4) % 2 + 1)
        
    return df

# Inicializar el estado de la sesión para mantener los datos editados
if 'df_ofertas' not in st.session_state or st.session_state.get('current_campana') != id_campana:
    st.session_state['df_ofertas'] = generar_datos_simulados(id_campana, paginas_totales)
    st.session_state['current_campana'] = id_campana

df_ofertas = st.session_state['df_ofertas']

# --- PANELES PRINCIPALES ---
tab1, tab2, tab3 = st.tabs(["🎛️ Gestor de Layout Inteligente", "🗺️ Visor Gráfico del Folleto", "💾 Exportar y SQL"])

# --- TAB 1: GESTOR DE LAYOUT ---
with tab1:
    st.header("Asignación de Coordenadas de Distribución")
    st.write("Usa esta sección para asignar o modificar de forma inteligente las posiciones de las ofertas.")
    
    # Filtro por Página en edición
    pagina_actual = st.selectbox("Seleccionar Página a Trabajar / Visualizar:", options=list(range(1, paginas_totales + 1)))
    
    # Controles automáticos masivos
    with st.expander("🤖 Asistente de Llenado Inteligente Automatizado"):
        st.info("Distribuye los productos seleccionados secuencialmente en la página actual de forma automática.")
        col_as1, col_as2, col_as3 = st.columns(3)
        with col_as1:
            estilo_molde = st.selectbox("Estilo de Sub-Molde Base", ["Grid_2x2", "Grid_3x3", "Grid_4x4", "Destacado_Top"])
        with col_as2:
            mix_pos = st.selectbox("Comportamiento Mix", ["Regular", "Premium", "Promo_Flash"])
        with col_as3:
            alineacion_base = st.radio("Alineación Predeterminada", ["I (Izquierda)", "C (Centro)", "D (Derecha)"], horizontal=True)
            
        if st.button("🚀 Ejecutar Auto-Distribución en Página Actual"):
            # Filtrar filas que pertenezcan a esta página o que estén vacías para asignarlas aquí
            vacios = df_ofertas['numero_pagina'].isna()
            indices_a_llenar = df_ofertas[vacios].head(8).index
            
            if len(indices_a_llenar) == 0:
                st.warning("No hay productos huérfanos/sin página para asignar.")
            else:
                for idx, index_id in enumerate(indices_a_llenar):
                    slot = idx + 1
                    fila = (idx // 2) + 1
                    col = (idx % 2) + 1
                    
                    df_ofertas.at[index_id, 'numero_pagina'] = int(pagina_actual)
                    df_ofertas.at[index_id, 'posicion_slot'] = int(slot)
                    df_ofertas.at[index_id, 'alineacion'] = alineacion_base[0]
                    df_ofertas.at[index_id, 'posicion_mix'] = mix_pos
                    df_ofertas.at[index_id, 'sub_molde_estilo'] = estilo_molde
                    df_ofertas.at[index_id, 'numero_fila'] = int(fila)
                    df_ofertas.at[index_id, 'numero_columna'] = int(col)
                
                st.session_state['df_ofertas'] = df_ofertas
                st.success(f"¡Se asignaron con éxito {len(indices_a_llenar)} productos a la Página {pagina_actual}!")
                st.rerun()

    st.subheader(f"📋 Ofertas Asignadas a la Página {pagina_actual}")
    
    # Filtrar el dataframe para mostrar y editar solo la página actual
    df_pagina = df_ofertas[df_ofertas['numero_pagina'] == pagina_actual]
    
    if df_pagina.empty:
        st.write("*No hay productos asignados a esta página todavía. Usa el asistente o la tabla general de abajo.*")
    else:
        # Data Editor nativo de Streamlit con validaciones específicas
        edited_df_pagina = st.data_editor(
            df_pagina,
            column_config={
                "id_oferta": st.column_config.NumberColumn("ID Oferta", disabled=True),
                "nombre_producto": st.column_config.TextColumn("Producto", disabled=True),
                "precio_oferta": st.column_config.NumberColumn("Precio ($)", format="$ %.2f", disabled=True),
                "numero_pagina": st.column_config.NumberColumn("Página", min_value=1, max_value=paginas_totales, required=True),
                "posicion_slot": st.column_config.NumberColumn("Slot Posición", min_value=1, max_value=20),
                "alineacion": st.column_config.SelectboxColumn("Alineación", options=["I", "C", "D"], help="I: Izquierda, C: Centro, D: Derecha"),
                "posicion_mix": st.column_config.TextColumn("Posición Mix"),
                "sub_molde_estilo": st.column_config.TextColumn("Estilo Sub-Molde"),
                "numero_fila": st.column_config.NumberColumn("Fila", min_value=1, max_value=10),
                "numero_columna": st.column_config.NumberColumn("Columna", min_value=1, max_value=10),
            },
            hide_index=True,
            key=f"editor_pag_{pagina_actual}"
        )
        
        # Guardar cambios del editor de la página de vuelta al DataFrame global
        if st.button("💾 Guardar Cambios Manuales de la Página"):
            df_ofertas.update(edited_df_pagina)
            st.session_state['df_ofertas'] = df_ofertas
            st.success("Cambios de la página guardados en el buffer temporal.")
            st.rerun()

    # --- TABLA COMPLETA DE TODOS LOS PRODUCTOS ---
    st.subheader("🗂️ Inventario Total de Ofertas de la Campaña")
    st.caption("Muestra todos los registros. Puedes editar las coordenadas de cualquier fila directamente aquí.")
    
    edited_all_df = st.data_editor(
        df_ofertas,
        column_config={
            "id_oferta": st.column_config.NumberColumn("ID Oferta", disabled=True),
            "nombre_producto": st.column_config.TextColumn("Producto", disabled=True),
            "numero_pagina": st.column_config.NumberColumn("Página", min_value=1, max_value=paginas_totales),
            "posicion_slot": st.column_config.NumberColumn("Slot"),
            "alineacion": st.column_config.SelectboxColumn("Alineación", options=["I", "C", "D"]),
            "numero_fila": st.column_config.NumberColumn("Fila"),
            "numero_columna": st.column_config.NumberColumn("Columna"),
        },
        hide_index=True,
        key="editor_global"
    )
    
    if st.button("💾 Guardar Cambios en Inventario Global"):
        st.session_state['df_ofertas'] = edited_all_df
        st.success("Base de datos global actualizada de forma temporal.")
        st.rerun()


# --- TAB 2: VISOR GRÁFICO (MOCKUP DEL FOLLETO) ---
with tab2:
    st.header("🗺️ Simulación y Distribución Visual del Catálogo")
    st.write(f"Vista previa conceptual basada en cuadrículas para la **Página {pagina_actual}**.")
    
    df_visual = df_ofertas[df_ofertas['numero_pagina'] == pagina_actual].dropna(subset=['numero_fila', 'numero_columna'])
    
    if df_visual.empty:
        st.warning("⚠️ No hay suficientes datos con Fila y Columna asignadas para dibujar la cuadrícula de esta página.")
    else:
        max_filas = int(max(df_visual['numero_fila'].max(), 2))
        max_columnas = int(max(df_visual['numero_columna'].max(), 2))
        
        st.info(f"Estructura detectada en base a tus asignaciones: Cuadrícula de {max_filas} Filas × {max_columnas} Columnas")
        
        # Renderizado de la estructura visual dinámica tipo catálogo
        for f in range(1, max_filas + 1):
            cols_ui = st.columns(max_columnas)
            for c in range(1, max_columnas + 1):
                with cols_ui[c-1]:

                    # Buscar si hay un producto asignado a esta celda exacta
                    prod_celda = df_visual[(df_visual['numero_fila'] == f) & (df_visual['numero_columna'] == c)]
                    
                    if not prod_celda.empty:
                        row = prod_celda.iloc[0]
                        # Determinar emojis de alineación para enriquecer el layout visual
                        align_emoji = "⬅️" if row['alineacion'] == 'I' else "🔼" if row['alineacion'] == 'C' else "➡️"
                        
                        st.markdown(f"""
                        <div style="
                            border: 2px solid #4CAF50; 
                            border-radius: 8px; 
                            padding: 12px; 
                            background-color: #e8f5e9; 
                            margin-bottom: 10px;
                            color: #1b5e20;
                        ">
                            <span style="font-size: 0.8rem; font-weight: bold; color: #2e7d32;">
                                Slot {int(row['posicion_slot']) if pd.notna(row['posicion_slot']) else 'N/A'}
                            </span>
                            <h4 style="margin: 4px 0; color: #000;">{row['nombre_producto']}</h4>
                            <p style="margin: 0; font-weight: bold; font-size: 1.1rem; color: #d32f2f;">
                                ${row['precio_oferta']}
                            </p>
                            <hr style="margin: 8px 0; border: 0; border-top: 1px solid #c8e6c9;">
                            <p style="margin: 0; font-size: 0.8rem;">Estilo: <i>{row['sub_molde_estilo']}</i></p>
                            <p style="margin: 0; font-size: 0.8rem; font-weight: 500;">
                                Alin: {row['alineacion']} {align_emoji} | Mix: {row['posicion_mix']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="
                            border: 2px dashed #ccc; 
                            border-radius: 8px; 
                            padding: 12px; 
                            background-color: #fafafa; 
                            margin-bottom: 10px; 
                            text-align: center;
                            min-height: 140px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <span style="color: #9e9e9e; font-style: italic; font-size: 0.9rem;">
                                Celda Vacía<br>[Fila {f}, Col {c}]
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

# --- TAB 3: EXPORTAR Y SQL ---
with tab3:
    st.header("💾 Sincronización y Procesamiento de Datos")
    
    st.subheader("1. Generador de Scripts SQL UPDATE para PostgreSQL")
    st.write("Utiliza este script para aplicar todos los cambios realizados en el frontend directo en tu base de datos relacional.")
    
    # Generación dinámica del script SQL estructurado
    sql_lines = []
    sql_lines.append(f"-- Cambios de distribución de layout para id_campana = {id_campana}")
    sql_lines.append("BEGIN;")
    
    for _, r in df_ofertas.iterrows():
        if pd.notna(r['numero_pagina']):
            pag = int(r['numero_pagina'])
            slot = int(r['posicion_slot']) if pd.notna(r['posicion_slot']) else "NULL"
            alin = f"'{r['alineacion']}'" if pd.notna(r['alineacion']) else "NULL"
            mix = f"'{r['posicion_mix']}'" if pd.notna(r['posicion_mix']) else "NULL"
            estilo = f"'{r['sub_molde_estilo']}'" if pd.notna(r['sub_molde_estilo']) else "NULL"
            fila = int(r['numero_fila']) if pd.notna(r['numero_fila']) else "NULL"
            col = int(r['numero_columna']) if pd.notna(r['numero_columna']) else "NULL"
            
            query = (f"UPDATE public.ofertas SET "
                     f"numero_pagina = {pag}, posicion_slot = {slot}, alineacion = {alin}, "
                     f"posicion_mix = {mix}, sub_molde_estilo = {estilo}, numero_fila = {fila}, numero_columna = {col} "
                     f"WHERE id_oferta = {r['id_oferta']};")
            sql_lines.append(query)
            
    sql_lines.append("COMMIT;")
    sql_script = "\n".join(sql_lines)
    
    st.code(sql_script, language="sql")
    
    # Botones para descargar archivos
    st.subheader("2. Descarga de Archivos de Respaldo")
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        st.download_button(
            label="📥 Descargar Script SQL (.sql)",
            data=sql_script,
            file_name=f"update_layout_campana_{id_campana}.sql",
            mime="text/plain"
        )
        
    with col_dl2:
        csv_buffer = df_ofertas.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Layout Actual (CSV)",
            data=csv_buffer,
            file_name=f"layout_campana_{id_campana}.csv",
            mime="text/csv"
        )
                    
