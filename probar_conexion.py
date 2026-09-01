import streamlit as st
from supabase import create_client

st.title("🧪 Verificador de Relación Supabase")

# Inicialización segura de credenciales
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "tu-anon-key")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

id_campana_prueba = st.number_input("ID de Campaña para probar:", min_value=1, value=12)

if st.button("🧪 Probar Consulta Relacional"):
    try:
        # Esta es la consulta limpia que causaba el error 404
        respuesta = (
            supabase.table("ofertas")
            .select("id_oferta, id_producto, precio_oferta, productos(nombre, url_imagen)")
            .eq("id_campana", id_campana_prueba)
            .execute()
        )
        
        st.success("¡Éxito! La base de datos respondió correctamente sin error 404.")
        st.json(respuesta.data)
        
    except Exception as e:
        st.error(f"El error persiste. Detalles devueltos por el servidor: {str(e)}")
