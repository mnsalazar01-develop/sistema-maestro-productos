# ==============================================================================
# PROGRAMA SATÉLITE: cargar_productos.py (PARTE A DE B)
# VERSIÓN: 1.0.0 (MÓDULO SUELTO RAÍZ)
# DESCRIPCIÓN: Ingesta Manual Reactiva de Artículos Genéricos Nivel 5
# MODIFICACIÓN: Creación como módulo independiente plano en la raíz del proyecto.
# ==============================================================================

import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Ingesta de Catálogo - Retail",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Declaramos la ruta de regreso al Menú Principal exigida por el enrutador central
pagina_principal = "app.py"

# 2. BOTÓN DE RETORNO AL LAUNCHPAD CENTRAL
col_volver, col_vacia = st.columns([1, 5])
with col_volver:
    if st.button("⬅️ Menú Principal", use_container_width=True, key="btn_volver_menu_prod"):
        st.switch_page(pagina_principal)

st.title("📝 Ingesta Manual y Registro de Productos (Nivel 5)")
st.markdown("Alta reactiva de artículos nuevos y control de taxonomía retail en memoria local.")
st.markdown("---")

st.subheader("📋 Formulario de Registro Técnico")
st.markdown("Introduce las especificaciones comerciales del nuevo producto genérico puro:")

# Mapa de respaldo local con las familias del supermercado para alimentar el selector
familias_respaldo = {
    1: "Carnicería", 2: "Charcutería", 3: "Frutería", 4: "Verdulería", 5: "Pescadería", 
    6: "Panadería", 7: "Pastelería", 8: "Granos y Café", 9: "Harinas y Pastas", 
    10: "Aceites Comestibles", 11: "Grasas", 12: "Enlatados", 13: "Conservas", 
    14: "Salsas y Aderezos", 15: "Condimentos", 16: "Desayuno y Azúcar", 
    17: "Lácteos y Leches", 18: "Yogures", 19: "Comidas Preparadas", 
    22: "Agua", 23: "Jugos", 24: "Refrescos", 25: "Bebidas Energéticas", 
    26: "Ron", 27: "Cerveza", 28: "Vino", 29: "Whisky", 30: "Jabón", 
    31: "Champú", 32: "Desodorante", 33: "Crema Dental", 34: "Papel Higiénico", 
    35: "Maquillaje", 36: "Detergentes", 37: "Suavizantes", 38: "Limpiadores", 
    39: "Desinfectantes", 40: "Lavaplatos", 41: "Mascotas", 42: "Pañales", 
    43: "Fórmulas Infantiles", 44: "Ferretería Ligera"
}

# Diseño del contenedor del formulario usando grillas de alta densidad visual
with st.form("formulario_ingesta_manual", clear_on_submit=False):
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        nombre_ingresado = st.text_input(
            "Nombre comercial del Producto (Bruto / Genérico):",
            placeholder="Ej: BIFE DE ESPALDILLA DE RES PREM",
            help="Escribe la descripción tal como aparece en la factura comercial o empaque."
        ).strip()
        
        codigo_barras = st.text_input(
            "Código de Barras / GTIN (Opcional):",
            placeholder="Ej: 7501055310012",
            max_chars=14
        ).strip()

    with col_f2:
        subcat_seleccionada = st.selectbox(
            "Asociar de forma estricta a la subcategoría de destino:",
            options=[f"{id_f} - {nombre_f}" for id_f, nombre_f in familias_respaldo.items()],
            help="Selecciona la familia correspondiente de la taxonomía core."
        )
        
        precio_sugerido = st.number_input(
            "Costo base estimado comercial (USD):",
            min_value=0.00,
            value=0.00,
            step=0.01,
            format="%.2f"
        )
    st.markdown("---")
    st.markdown("#### 📸 Control Multimedia y Verificación Visual")
    st.caption("Adjunta de forma opcional una fotografía del producto para auditar el empaque o la etiqueta nutrimental.")
    
    # Componente nativo de Streamlit para cargar imágenes de productos en bruto
    foto_producto = st.file_uploader(
        "Arrastra la imagen del artículo (.jpg, .jpeg, .png)", 
        type=["jpg", "jpeg", "png"], 
        key="uploader_foto_manual"
    )
    
    if foto_producto:
        st.image(foto_producto, caption="Pre-visualización de la etiqueta del producto", width=300)

    st.markdown("---")
    # Botón definitivo de envío del formulario
    boton_guardar_manual = st.form_submit_button("🚀 Confirmar y Registrar Producto en Catálogo")
    
    if boton_guardar_manual:
        if not nombre_ingresado:
            st.error("❌ Error de Validación: Debes escribir una descripción o nombre comercial válido.")
        else:
            # Extraemos el ID numérico de la subcategoría seleccionada en el combo
            id_subcat_final = int(subcat_seleccionada.split(" - ")[0])
            
            # Estructuramos el reporte de auditoría visual en pantalla
            st.balloons()
            st.success(f"🎉 ¡Producto procesado con éxito en la memoria RAM del servidor local!")
            
            # Mostramos una tarjeta comercial con los datos que el software asimiló
            st.markdown("### 📋 Ficha Técnica del Artículo Generado")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.write(f"**📦 Descripción:** {nombre_ingresado.upper()}")
                st.write(f"**🏷️ Subcategoría ID:** {id_subcat_final}")
            with col_t2:
                st.write(f"**🔢 Código GTIN:** {codigo_barras if codigo_barras else 'N/A'}")
                st.write(f"**💵 Costo Base:** ${precio_sugerido:.2f} USD")
