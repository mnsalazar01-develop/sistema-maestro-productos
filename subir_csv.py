import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Configura el nombre de tu archivo CSV y de la tabla
ARCHIVO_CSV = "tus_datos.csv"  # Reemplaza con el nombre de tu archivo si es diferente
NOMBRE_TABLA = "productos"     # Nombre que tendrá la tabla en tu base de datos de Neon

try:
    st.write("⏳ Leyendo el archivo CSV local...")
    df = pd.read_csv(ARCHIVO_CSV)
    
    st.write("🔐 Obteniendo la cadena de conexión desde los Secrets...")
    cadena_conexion = st.secrets["neon"]["url"]
    
    st.write("🔄 Conectando con Neon (con límite de tiempo de 5s)...")
    # Agregamos connect_timeout dentro de connect_args para evitar que la pantalla se quede negra si la red falla
    engine = create_engine(
        cadena_conexion, 
        connect_args={"connect_timeout": 5}
    )
    
    st.write(f"🚀 Creando la tabla '{NOMBRE_TABLA}' y subiendo las filas...")
    # Sube los datos. Si la tabla ya existe, la reemplaza por completo
    df.to_sql(NOMBRE_TABLA, con=engine, if_exists="replace", index=False)
    
    st.success(f"¡Todo listo! Tu tabla '{NOMBRE_TABLA}' se ha creado en Neon con éxito. 🎉")

except KeyError:
    st.error("❌ Error: No se encontró la clave ['neon']['url'] en los Secrets de tu aplicación.")
except Exception as e:
    st.error(f"❌ Ocurrió un error durante la migración: {e}")
