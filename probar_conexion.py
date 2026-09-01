import streamlit as st
import json
from supabase import create_client

st.title("🧪 Verificador de Conexión: Método Bypass")

# 1. Credenciales seguras (Sustituye con tus variables o se leerán de .streamlit/secrets.toml)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "tu-anon-key")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Entrada de prueba
id_campana_prueba = st.number_input("ID de Campaña para realizar la prueba:", min_value=1, value=12)

if st.button("🚀 Ejecutar Consulta con Bypass"):
    try:
        # PASO A: Traer ofertas planas asociadas a la campaña (Inmune a problemas de FK)
        st.info("Paso A: Extrayendo registros desde public.ofertas...")
        resp_ofertas = supabase.table("ofertas").select("*").eq("id_campana", id_campana_prueba).execute()
        ofertas = resp_ofertas.data
        
        st.write(f"✅ Se encontraron **{len(ofertas)}** ofertas para la campaña {id_campana_prueba}.")
        
        # PASO B: Extraer los id_producto únicos implicados
        lista_ids = list(set([o["id_producto"] for o in ofertas if o.get("id_producto") is not None]))
        st.info(f"Paso B: Extrayendo {len(lista_ids)} IDs únicos de productos para la consulta indexada...")
        
        dict_productos = {}
        if lista_ids:
            # PASO C: Consultar los productos directamente por lote (Bulk In Query)
            resp_prod = supabase.table("productos").select("id_producto, nombre, url_imagen").in_("id_producto", lista_ids).execute()
            dict_productos = {p["id_producto"]: p for p in resp_prod.data}
            st.write(f"✅ Se descargaron **{len(dict_productos)}** productos asociados desde la base de datos.")
        
        # PASO D: Fusionar los diccionarios en memoria de Python
        st.info("Paso D: Fusionando registros y estructurando el banco de datos...")
        for o in ofertas:
            id_p = o.get("id_producto")
            if id_p in dict_productos:
                o["nombre_producto"] = dict_productos[id_p].get("nombre") or "Sin Nombre"
                o["url_imagen_producto"] = dict_productos[id_p].get("url_imagen") or "https://picsum.photos"
            else:
                o["nombre_producto"] = "Producto no encontrado en inventario"
                o["url_imagen_producto"] = "https://picsum.photos"
        
        # Mostrar el resultado final exitoso
        st.success("🎉 ¡Método Bypass Exitoso! Los datos se cargaron y unieron correctamente sin errores 404.")
        st.json(ofertas[:3]) # Mostramos los 3 primeros registros como muestra estructural
        
    except Exception as e:
        st.error(f"❌ Falló el método de conexión alternativo. Detalles: {str(e)}")
