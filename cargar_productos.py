import os
import sys
import pandas as pd
import requests

# Python lee los Secrets de la nube de forma segura
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: No se encontraron los Secrets de Supabase configurados en el sistema.")
    sys.exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Diccionario de reglas automáticas de clasificación
DICCIONARIO_REGLAS = {
    "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "cafe": 8, "café": 8,
    "harin": 9, "fororo": 9, "maicena": 9,
    "aceit": 10, "oliva": 10,
    "mantec": 11, "margar": 11, "manteq": 11,
    "atun": 12, "atún": 12, "sardin": 12,
    "mayon": 14, "salsa": 14, "ketchup": 14,
    "sal ": 15, "pimient": 15,
    "avena": 16, "cereal": 16,
    "lech": 17, "queso": 17, "crema": 17,
    "yog": 18,
    "jabon": 30, "jabón": 30,
    "shamp": 31, "champ": 31,
    "desod": 32,
    "crema dent": 33, "pasta dent": 33,
    "papel hig": 34
}

def clasificar_producto(nombre_recibido):
    texto = str(nombre_recibido).lower().strip()
    for palabra_clave, id_subcat in DICCIONARIO_REGLAS.items():
        if palabra_clave in texto:
            return id_subcat
    return None

def ejecutar_carga():
    # Buscamos de forma automatizada cualquier archivo Excel en la carpeta
    archivos_excel = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not archivos_excel:
        print("❌ Error: No se encontró ningún archivo .xlsx en la carpeta.")
        return
        
    archivo_objetivo = archivos_excel[0]
    print(f"📖 Procesando el archivo: {archivo_objetivo}...")
    
    df = pd.read_excel(archivo_objetivo)
    if 'nombre' not in df.columns:
        print("❌ Error: El Excel debe tener una columna llamada 'nombre'")
        return

    productos_a_subir = []
    for idx, fila in df.iterrows():
        nombre_prod = fila['nombre']
        id_subcat = clasificar_producto(nombre_prod)
        if id_subcat:
            productos_a_subir.append({
                "nombre_producto": nombre_prod,
                "id_enlace_subcat": id_subcat
            })

    if productos_a_subir:
        print(f"🚀 Enviando {len(productos_a_subir)} productos clasificados a Supabase...")
        url_rest = f"{SUPABASE_URL}/rest/v1/productos"
        response = requests.post(url_rest, headers=headers, json=productos_a_subir)
        
        if response.status_code in:
            print("✅ ¡Carga masiva completada con éxito en la nube usando Secrets!")
        else:
            print(f"❌ Error API Supabase: {response.status_code} - {response.text}")

if __name__ == "__main__":
    ejecutar_carga()
