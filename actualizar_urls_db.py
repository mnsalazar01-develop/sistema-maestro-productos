import sys
import streamlit as st
from supabase import create_client

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

def corregir_urls_tabla():
    st.write("🔍 Leyendo los registros de productos para analizar las URLs viejas...")
    
    try:
        # 1. Traemos todos los productos. Ajusta 'productos' si tu tabla se llama 'ofertas'
        respuesta = supabase.table("productos").select("id_producto", "url_imagen").execute()
        productos = respuesta.data
    except Exception as e:
        st.error(f"❌ Error al leer la tabla de productos: {e}")
        return

    if not productos:
        st.warning("⚠️ No se encontraron registros en la tabla.")
        return

    total = len(productos)
    st.info(f"📋 Se detectaron {total} registros. Iniciando actualización de enlaces...")
    
    # Construimos la base de la nueva URL usando el dominio del nuevo proyecto
    # Formato estándar de Supabase para storage: https://supabase.co
    url_base_nueva = f"{url.rstrip('/')}/storage/v1/object/public/imagenes/"
    
    contador_actualizados = 0
    progreso = st.progress(0)
    texto_estado = st.empty()

    # 2. Recorremos producto por producto para reescribir la URL
    for idx, p in enumerate(productos, 1):
        id_prod = p["id_producto"]
        url_vieja = p.get("url_imagen")
        
        if not url_vieja or str(url_vieja).strip() == "" or "None" in str(url_vieja):
            continue
            
        # Extraemos únicamente el nombre del archivo del final de la URL vieja
        # Ejemplo: "https://viejo.co" -> "detergente.jpg"
        nombre_archivo_foto = str(url_vieja).split("/")[-1].strip()
        
        # Armamos la nueva URL limpia apuntando a tu nuevo bucket privado
        url_nueva_completa = f"{url_base_nueva}{nombre_archivo_foto}"
        
        # Saltamos la actualización si por alguna razón la URL ya estaba corregida
        if URL_DESTINO in str(url_vieja):
            continue
            
        texto_estado.text(f"🔄 [{idx}/{total}] Corrigiendo enlace de ID {id_prod}: {nombre_archivo_foto}")
        progreso.progress(idx / total)
        
        try:
            # 3. Ejecutamos el UPDATE directo en la base de datos para este ID
            supabase.table("productos").update(
                {"url_imagen": url_nueva_completa}
            ).eq("id_producto", id_prod).execute()
            
            contador_actualizados += 1
        except Exception as e:
            st.warning(f"⚠️ No se pudo actualizar el ID {id_prod}: {e}")

    texto_estado.empty()
    st.success(f"🏁 ¡Proceso completado! Se reescribieron con éxito {contador_actualizados} enlaces en la base de datos.")

if __name__ == "__main__":
    if st.button("🔗 Corregir URLs de Imágenes a Nuevo Proyecto", type="primary", use_container_width=True):
        corregir_urls_tabla()
