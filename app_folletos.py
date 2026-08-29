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
                    
