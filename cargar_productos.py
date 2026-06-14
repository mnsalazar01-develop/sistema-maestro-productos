# ==============================================================================
# PROGRAMA SATÉLITE: cargar_productos.py (PARTE A DE B)
# VERSIÓN: 1.1.0 (CONEXIÓN NUBE ACTIVA)
# DESCRIPCIÓN: Ingesta Manual Reactiva de Artículos Genéricos Nivel 5 con Persistencia
# MODIFICACIÓN: Integración del cliente Supabase usando la anon_key autorizada de la raíz.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Ingesta de Catálogo - Retail",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. HERENCIA DE CONEXIÓN SEGURA DESDE EL LAUNCHPAD CENTRAL (app.py)
if "supabase_cliente" in st.session_state:
    supabase = st.session_state["supabase_cliente"]
else:
    # Contingencia local en la raíz con tus variables de internet seguras
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)

# Declaramos la ruta de regreso al Menú Principal
pagina_principal = "app.py"

# 3. BOTÓN DE RETORNO AL LAUNCHPAD CENTRAL
col_volver, col_vacia = st.columns()
with col_volver:
    if st.button("⬅️ Menú Principal", use_container_width=True, key="btn_volver_menu_prod"):
        st.switch_page(pagina_principal)

st.title("📝 Ingesta Manual y Registro de Productos (Nivel 5)")
st.markdown("Alta reactiva de artículos nuevos con persistencia directa en la base de datos cloud.")
st.markdown("---")

st.subheader("📋 Formulario de Registro Técnico")

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
with st.form("formulario_ingesta_manual", clear_on_submit=True): # clear_on_submit=True limpia los campos al guardar con éxito
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
    st.markdown("---")
    # Botón definitivo de envío del formulario con persistencia en la base de datos cloud
    boton_guardar_manual = st.form_submit_button("🚀 Confirmar y Registrar Producto en Catálogo")
    
    if boton_guardar_manual:
        if not nombre_ingresado:
            st.error("❌ Error de Validación: Debes escribir una descripción o nombre comercial válido.")
        else:
            # Extraemos el ID numérico de la subcategoría seleccionada en el combo
            id_subcat_final = int(subcat_seleccionada.split(" - ")[0])
            
            with st.spinner("Inyectando registro en la base de datos..."):
                exito_insercion = False
                error_final = None
                
                # Intento 1: Nomenclatura estándar de tu tabla física ('nombre' / 'id_subcat')
                try:
                    payload = {
                        "nombre": nombre_ingresado.upper(),
                        "id_subcat": id_subcat_final
                    }
                    supabase.table("productos").insert(payload).execute()
                    exito_insercion = True
                except Exception as e1:
                    error_final = e1
                    exito_insercion = False
                    
                # Intento 2 (Contingencia): Nomenclatura extendida de tu tabla física ('nombre_producto' / 'id_enlace_subcat')
                if not exito_insercion:
                    try:
                        payload = {
                            "nombre_producto": nombre_ingresado.upper(),
                            "id_enlace_subcat": id_subcat_final
                        }
                        supabase.table("productos").insert(payload).execute()
                        exito_insercion = True
                    except Exception as e2:
                        error_final = e2
                        exito_insercion = False
                
                # Despliegue de resultados según el estatus de la inyección
                if exito_insercion:
                    st.balloons()
                    st.success(f"🎉 ¡Éxito total! El producto '{nombre_ingresado.upper()}' quedó guardado de forma permanente en tu tabla de Supabase.")
                    
                    # Mostramos la ficha técnica del registro consolidado en la nube
                    st.markdown("### 📋 Ficha Técnica del Artículo Guardado")
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        st.write(f"**📦 Descripción:** {nombre_ingresado.upper()}")
                        st.write(f"**🏷️ Subcategoría ID:** {id_subcat_final}")
                    with col_t2:
                        st.write(f"**🔢 Código GTIN:** {codigo_barras if codigo_barras else 'N/A'}")
                else:
                    st.error(f"❌ Error de persistencia: El servidor rechazó la inyección. Detalle: {error_final}")
