import streamlit as st
from supabase import create_client

st.title("🔬 Diagnóstico de Tablas en Supabase")

# 2. CONEXIÓN SEGURA HEREDADA CON LAS LLAVES DE SUPABASE
@st.cache_resource
def init_supabase_local() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_supabase_local()
except Exception as e:
    st.error(f"❌ Error de Conexión Base: {e}")
    st.stop()

if st.button("🔍 Escanear Tablas Disponibles"):
    try:
        st.info("Consultando el diccionario de datos de la API...")
        
        # Le pedimos al catálogo de Postgres que nos diga qué tablas públicas son visibles para la API
        respuesta = supabase.table('"_analytics_meta"' if False else 'information_schema.tables')\
            .select("table_name")\
            .eq("table_schema", "public")\
            .execute()
        
        tablas_visibles = [t["table_name"] for t in respuesta.data]
        
        st.success(f"🎉 ¡Conexión establecida! Tu API tiene acceso a {len(tablas_visibles)} tablas públicas.")
        st.write("### 📝 Listado de Tablas que tu programa SÍ puede leer:")
        st.write(tablas_visibles)
        
        # Verificación directa de nombres comunes
        if "ofertas" in tablas_visibles:
            st.write("🟢 La tabla 'ofertas' existe y es visible.")
        else:
            st.write("🔴 **¡ALERTA!** La tabla 'ofertas' NO es visible para la API. Verifica si se llama diferente (ej: 'Ofertas', 'ofertas_espejo', etc.).")

    except Exception as e:
        st.write("⚠️ PostgREST bloqueó la lectura directa del catálogo. Probemos el Plan B...")
        
        # Intento de descarte rápido mesa por mesa
        tablas_a_probar = ["ofertas", "Ofertas", "ofertas_espejo", "productos", "Productos"]
        for tabla in tablas_a_probar:
            try:
                supabase.table(tabla).select("*").limit(1).execute()
                st.write(f"🟢 Conexión EXITOSA con la tabla: `{tabla}`")
            except Exception as err:
                st.write(f"🔴 Fallo total al intentar leer la tabla `{tabla}` (Código 404 u otro error).")
