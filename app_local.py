import streamlit as st
import sqlite3
import os

# Configuración de la página
st.set_page_config(page_title="Gestor Local de Productos", layout="wide")

st.title("📦 Inventario Local de Productos")
st.write("Mostrando datos desde `Sandbox_Ofertas_2026.db` e imágenes desde `storage_local/`")

# Función para conectar a la base de datos
def obtener_productos():
    if not os.path.exists("base_temporal.db"):
        st.error("No se encontró el archivo 'Sandbox_Ofertas_2026.db'. Créalo primero con DB Browser for SQLite.")
        return []
    
    conn = sqlite3.connect("Sandbox_Ofertas_2026.db")
    cursor = conn.cursor()
    
    # Ajusta el nombre de tu tabla si es diferente a 'ofertas'
    try:
        cursor.execute("SELECT id_producto, nombre, precio_oferta, img FROM ofertas")
        datos = cursor.fetchall()
    except sqlite3.OperationalError:
        st.warning("La tabla 'ofertas' no existe todavía en tu base de datos.")
        datos = []
        
    conn.close()
    return datos

# Cargar los datos
productos = obtener_productos()

if not productos:
    st.info("No hay productos registrados para mostrar.")
else:
    # Creamos columnas para organizar las tarjetas visualmente
    cols = st.columns(3)
    
    for index, (id_prod, nombre, precio, ruta_img) in enumerate(productos):
        col_actual = cols[index % 3]
        
        with col_actual:
            st.subheader(nombre)
            
            # Verificamos si la imagen local existe antes de mostrarla
            if ruta_img and os.path.exists(ruta_img):
                st.image(ruta_img, width=200)
            else:
                st.warning("⚠️ Imagen no encontrada en disco")
                
            st.write(f"**Precio:** ${precio if precio else '0.00'}")
            st.divider()
