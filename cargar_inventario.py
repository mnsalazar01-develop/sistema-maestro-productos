# ==============================================================================
# PROGRAMA SATÉLITE: cargar_productos.py (PARTE A DE B)
# VERSIÓN: 1.2.1 (CORRECCIÓN DE TYPEERROR VISUAL)
# DESCRIPCIÓN: Normalizador y Limpiador Léxico Manual de Productos Nivel 5
# MODIFICACIÓN: Inyección de parámetro entero en st.columns(2) contra caídas.
# ==============================================================================

import streamlit as st
import pandas as pd
import re

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Normalizador de Productos - Retail",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Declaramos la ruta de regreso al Menú Principal
pagina_principal = "app.py"

# 2. BOTÓN DE RETORNO AL LAUNCHPAD CENTRAL CORREGIDO (Inmune a TypeError)
col_volver, col_vacia = st.columns(2) # Especificamos el número de columnas para el diseño gráfico
with col_volver:
    if st.button("⬅️ Menú Principal", use_container_width=True, key="btn_volver_menu_prod_local_v121"):
        st.switch_page(pagina_principal)

st.title("📝 Normalizador Léxico de Productos (Nivel 5)")
st.markdown("Herramienta local autónoma para corregir sintaxis y estandarizar nombres comerciales antes del catálogo.")
st.markdown("---")

# Función interna local que limpia y formatea la descripción de un producto
def normalizar_descripcion_retail(nombre_bruto):
    # Convertimos a string y pasamos a mayúsculas
    texto = str(nombre_bruto).upper().strip()
    
    # Expresión regular local para eliminar caracteres especiales molestos (como #, $, %, @, *, etc.)
    texto = re.sub(r'[#\$%@\*\+=\[\]\{\}\/\\]', '', texto)
    
    # Eliminamos espacios dobles o triples entre palabras y los convertimos en un solo espacio limpio
    texto = " ".join(texto.split())
    
    return texto

st.subheader("📋 Consola de Depuración de Nombres")
st.markdown("Introduce la descripción del artículo en bruto para procesar su estructura:")

# Mapa de respaldo local con las familias del supermercado
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
# Diseño del contenedor del formulario local interactivo
with st.form("formulario_normalizador_manual_v121", clear_on_submit=False):
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        nombre_ingresado = st.text_input(
            "Escribe la descripción del Producto en bruto (Sucia o con errores):",
            placeholder="Ej:   ##bIfe   de_esPaldilla!! de res premium**  ",
            help="Coloca el texto con espacios extra o caracteres especiales para probar el limpiador."
        ).strip()
        
        codigo_barras = st.text_input(
            "Código de Barras / GTIN (Numérico local):",
            placeholder="Ej: 7501055310012",
            max_chars=14
        ).strip()

    with col_f2:
        subcat_seleccionada = st.selectbox(
            "Asociar de forma estricta a la subcategoría de destino:",
            options=[f"{id_f} - {nombre_f}" for id_f, nombre_f in familias_respaldo.items()],
            help="Selecciona la familia correspondiente de tu taxonomía de confianza."
        )
        
        precio_sugerido = st.number_input(
            "Costo base estimado comercial (USD):",
            min_value=0.00,
            value=0.00,
            step=0.01,
            format="%.2f"
        )

    st.markdown("---")
    # Botón operativo de ejecución del formulario en RAM
    boton_procesar_manual = st.form_submit_button("🚀 Procesar, Normalizar y Verificar Producto")
    
    if boton_procesar_manual:
        if not nombre_ingresado:
            st.error("❌ Error de Validación: El cuadro de texto se encuentra vacío. Escribe un nombre.")
        else:
            # Ejecutamos la función de limpieza léxica local pura de la Parte A
            nombre_limpio_final = normalizar_descripcion_retail(nombre_ingresado)
            id_subcat_final = int(subcat_seleccionada.split(" - ")[0])
            
            st.balloons()
            st.success("🎉 ¡Nombre comercial corregido y estandarizado con éxito en memoria local!")
            
            # Despliegue de la Ficha Técnica Comercial Normalizada en pantalla
            st.markdown("### 📋 Ficha Técnica Estandarizada (Estándar Retail)")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.info(f"**📦 Descripción Limpia:** `{nombre_limpio_final}`")
                st.write(f"**🏷️ Familia Asociada:** {subcat_seleccionada}")
            with col_t2:
                st.write(f"**🔢 Código de Control GTIN:** {codigo_barras if codigo_barras else 'N/A'}")
                st.write(f"**💵 Costo de Operación:** ${precio_sugerido:.2f} USD")
            
            # Sub-módulo local de exportación a texto plano para el portapapeles del usuario
            st.markdown("---")
            reporte_texto = (
                f"=== FICHA DE PRODUCTO NORMALIZADA ===\n"
                f"DESCRIPCION: {nombre_limpio_final}\n"
                f"SUBCATEGORIA_ID: {id_subcat_final}\n"
                f"GTIN: {codigo_barras if codigo_barras else 'N/A'}\n"
                f"COSTO_USD: {precio_sugerido:.2f}\n"
                f"====================================="
            )
            
            st.download_button(
                label="📥 Descargar Ficha Técnica (.txt) para tu bitácora",
                data=reporte_texto,
                file_name=f"producto_{id_subcat_final}.txt",
                mime="text/plain",
                key="btn_descargar_txt_manual_v121"
            )
