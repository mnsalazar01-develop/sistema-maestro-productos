import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Configura el nombre de tu archivo CSV y de la tabla
ARCHIVO_CSV = "tus_datos.csv"  # Reemplaza con el nombre de tu archivo
NOMBRE_TABLA = "productos"     # Nombre que tendrá la tabla en Neon

try:
    print("Leyendo el archivo CSV...")
    df = pd.read_csv(ARCHIVO_CSV)
    
    print("Obteniendo la cadena de conexión desde st.secrets...")
    # Extrae la URL de forma segura desde .streamlit/secrets.toml
    cadena_conexion = st.secrets["neon"]["url"]
    
    print("Conectando con Neon...")
    engine = create_engine(cadena_conexion)
    
    print(f"Creando la tabla '{NOMBRE_TABLA}' y subiendo los datos...")
    # Sube los datos. Si la tabla ya existe, la reemplaza con los datos nuevos
    df.to_sql(NOMBRE_TABLA, con=engine, if_exists="replace", index=False)
    
    print("¡Todo listo! Tu tabla se ha creado en Neon de forma segura. 🚀")

except KeyError:
    print("❌ Error: No se encontró la clave ['neon']['url'] en tu archivo .streamlit/secrets.toml")
except Exception as e:
    print(f"❌ Ocurrió un error: {e}")
