# ==============================================================================
# SCRIPT UTILLERO: test_conexion_supabase.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.0.0 (AUDITORÍA VISUAL DE ESQUEMAS FÍSICOS EN SUPABASE)
# DESCRIPCIÓN: Extractor de metadatos de tablas y columnas vivas en la nube.
# ==============================================================================

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Auditor de Esquemas Supabase", page_icon="🕵️‍♂️")

st.title("🕵️‍♂️ Auditor de Esquemas y Tablas Cloud")
st.markdown("Consultando las entrañas del esquema público de PostgreSQL para verificar nombres reales de tablas y campos.")
st.markdown("---")

# Reutilizamos las credenciales seguras heredadas de tus secrets locales
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    st.success("⚡ Conexión física con el cliente de Supabase establecida.")
except Exception as e_conn:
    st.error(f"❌ Error al leer las llaves de secrets: {e_conn}")
    st.stop()

st.markdown("### 📊 Tablas y Estructuras Detectadas en tu Proyecto:")

with st.spinner("Escaneando el diccionario de datos de Supabase..."):
    try:
        # Ejecutamos una consulta directa al catálogo del sistema (information_schema) de PostgreSQL
        # para mapear de forma infalible qué tablas y columnas existen de verdad en la nube.
        respuesta_esquema = supabase.table("information_schema.columns").select("table_name, column_name, data_type").eq("table_schema", "public").execute()
        
        if respuesta_esquema and hasattr(respuesta_esquema, 'data') and respuesta_esquema.data:
            datos_raw = respuesta_esquema.data
            
            # Agrupamos las columnas por tabla de forma limpia para que sea ultra legible
            esquema_maestro = {}
            for fila in datos_raw:
                t_name = fila["table_name"]
                c_name = fila["column_name"]
                d_type = fila["data_type"]
                if t_name not in esquema_maestro:
                    esquema_maestro[t_name] = []
                esquema_maestro[t_name].append(f"   🔹 Campo: {c_name} ({d_type})")
            
            # Pintamos la radiografía real en la pantalla de la aplicación
            for tabla, columnas in esquema_maestro.items():
                st.code(f"📁 TABLA DETECTADA: {tabla}", language="markdown")
                for col in columnas:
                    st.markdown(col)
                st.markdown("---")
                
            st.balloons()
            st.info("💡 Compara los nombres que ves arriba con la palabra 'catalogo'. Cualquier diferencia de mayúsculas o letras es el motivo del error PGRST125.")
        else:
            st.warning("⚠️ La API de Supabase respondió con éxito, pero reportó que el esquema 'public' está completamente VACÍO. No hay tablas creadas todavía.")
            
    except Exception as e_auditoria:
        st.error(f"❌ El servidor de Supabase bloqueó la consulta de metadatos. Detalle: {e_auditoria}")
        st.markdown("""
        ### 🛠️ Cómo solucionarlo si la consulta fue bloqueada:
        Si el panel de seguridad de tu cuenta Supabase tiene bloqueada la consulta al catálogo del sistema, la forma manual e infalible es entrar a tu cuenta web en **supabase.com**, ir al **Table Editor** en el menú izquierdo y mirar el nombre exacto de la tabla que creaste bajo el esquema `public`.
        """)
