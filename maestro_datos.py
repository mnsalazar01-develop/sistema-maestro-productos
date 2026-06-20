# ==============================================================================
# SCRIPT DE DIAGNÓSTICO EN TIEMPO REAL: maestro_datos.py (VERSIÓN 1.5.0 EMERGENCIAS)
# DESCRIPCIÓN: Escáner temporal de metadatos para revelar nombres de tablas reales.
# MODIFICACIÓN: Bypass directo para forzar la lectura del information_schema.
# ==============================================================================

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Auditor Supabase", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Radiografía de Tablas Cloud en Vivo")
st.markdown("Consultando las entrañas de tu PostgreSQL en internet para verificar por qué la API arroja el error PGRST125.")
st.markdown("---")

try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    st.success("⚡ Conexión con el cliente de Supabase establecida.")
except Exception as e_conn:
    st.error(f"❌ Error al leer secrets: {e_conn}")
    st.stop()

with st.spinner("Escaneando el diccionario de datos de Supabase..."):
    try:
        # Consultamos el information_schema de PostgreSQL a través del cliente de Supabase
        res_esquema = supabase.table("information_schema.columns").select("table_name, column_name").eq("table_schema", "public").execute()
        
        if res_esquema and hasattr(res_esquema, 'data') and res_esquema.data:
            datos_raw = res_esquema.data
            
            # Agrupamos los campos de forma limpia por cada nombre de tabla real
            esquema_maestro = {}
            for fila in datos_raw:
                t_name = fila["table_name"]
                c_name = fila["column_name"]
                if t_name not in esquema_maestro:
                    esquema_maestro[t_name] = []
                esquema_maestro[t_name].append(c_name)
            
            # Pintamos la radiografía real en la pantalla
            st.warning("⚠️ ESTAS SON LAS ÚNICAS TABLAS QUE EXISTEN DE VERDAD EN TU NUBE:")
            for tabla, columnas in esquema_maestro.items():
                st.code(f"📁 Nombre exacto de Tabla: {tabla}", language="markdown")
                st.write(f"   🔹 Campos detectados: {', '.join(columnas)}")
                st.markdown("---")
            st.balloons()
        else:
            st.error("❌ El esquema 'public' de tu proyecto Supabase está completamente VACÍO. No has creado ninguna tabla física todavía.")
            st.markdown("💡 Ingresa a **supabase.com**, ve a **Table Editor** y crea una tabla llamada exactamente `catalogo` con los campos `nombre_catalogo` (text) e `id_subcat` (int8).")
            
    except Exception as e_auditoria:
        st.error(f"❌ La consulta de metadatos falló: {e_auditoria}")
        st.markdown("""
        ### 🛠️ Solución Definitiva Manual:
        Si la API te arroja este bloqueo, la forma más rápida y que no falla nunca es:
        1. Entra a tu cuenta web en **supabase.com** [https://supabase.com].
        2. Abre tu proyecto y haz clic en el icono de la tabla izquierda (**Table Editor**) [https://supabase.com].
        3. Mira cómo se llama la tabla que tienes allí escrita en la lista de la izquierda [https://supabase.com].
        """)
