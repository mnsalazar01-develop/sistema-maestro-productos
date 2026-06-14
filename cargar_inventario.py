# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (VERSION REESTRUCTURADA CONEXIÓN)
# VERSIÓN: 1.3.0 (MÓDULO SUELTO RAÍZ)
# DESCRIPCIÓN: Procesador Masivo de Catálogos Genéricos Retail Nivel 5
# MODIFICACIÓN: Uso de st.session_state para heredar la conexión exitosa de app.py
# ==============================================================================

import streamlit as st
import pandas as pd
import io

# 1. HERENCIA DE CONEXIÓN SEGURA
# Si el programa se ejecuta a través del Menú Principal, absorbe el cliente validado
if "supabase_cliente" in st.session_state:
    supabase = st.session_state["supabase_cliente"]
else:
    # Contingencia si se ejecuta de forma totalmente aislada en local
    from supabase import create_client
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)

st.title("📤 Procesador de Inventarios en Bruto (Nivel 5)")
st.markdown("Clasificación automatizada mediante matriz de control parametrizada en la nube.")

# Función interna de cruce léxico plano
def clasificar_texto_parametrizado(nombre_recibido, mapa_reglas=None):
    texto = str(nombre_recibido).lower().strip()
    if mapa_reglas:
        for palabra_clave, id_subcat in mapa_reglas.items():
            if palabra_clave in texto:
                return id_subcat
        palabras_token = texto.split()
        if palabras_token:
            primera_palabra = palabras_token[0]
            if primera_palabra in mapa_reglas:
                return mapa_reglas[primera_palabra]
    return None

# Componente de arrastre de archivos planos CSV
archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_v130_fijo")

if archivo_subido:
    st.success("¡Archivo plano cargado con éxito en la memoria web!")
    
    # Descarga e Indexación de la Tabla Paramétrica Viva desde la Nube
    matriz_reglas_vivas = {}
    try:
        res_reglas = supabase.table("matriz_diccionario_reglas").select("palabra_clave, id_enlace_subcat").execute()
        if res_reglas and hasattr(res_reglas, 'data') and res_reglas.data:
            for fila_r in res_reglas.data:
                token_clave = str(fila_r.get("palabra_clave", "")).lower().strip()
                id_destino = int(fila_r.get("id_enlace_subcat", 0))
                if token_clave and id_destino > 0:
                    matriz_reglas_vivas[token_clave] = id_destino
            st.sidebar.success(f"🧠 Matriz en RAM: {len(matriz_reglas_vivas)} reglas listas")
        else:
            st.sidebar.warning("⚠️ La tabla de reglas se encuentra vacía en este proyecto.")
            matriz_reglas_vivas = None
    except Exception as e:
        st.sidebar.error(f"❌ Error en PostgREST: {e}")
        matriz_reglas_vivas = None

    try:
        df = pd.read_csv(archivo_subido, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(archivo_subido, encoding='latin-1')
    
    if 'nombre' not in df.columns:
        st.error("❌ Error: Tu archivo plano debe contener una columna llamada exactamente 'nombre' (en minúsculas).")
    else:
        st.markdown("### 🧠 Pre-visualización de la Clasificación Automática Parametrizada")
        productos_clasificados = []
        no_clasificados = []
        
        for idx, fila in df.iterrows():
            nombre_prod = fila['nombre']
            id_subcat = clasificar_texto_parametrizado(nombre_prod, matriz_reglas_vivas)
            if id_subcat:
                productos_clasificados.append({
                    "nombre": nombre_prod,
                    "id_subcat": id_subcat,
                    "nombre_producto": nombre_prod,
                    "id_enlace_subcat": id_subcat
                })
            else:
                no_clasificados.append({"nombre": nombre_prod})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Productos Listos para Supabase", len(productos_clasificados))
            if productos_clasificados:
                df_previa = pd.DataFrame(productos_clasificados)[["nombre", "id_subcat"]]
                st.dataframe(df_previa, use_container_width=True)
        with col2:
            st.metric("Productos sin clasificar (Omitidos)", len(no_clasificados))
            if no_clasificados:
                df_omitidos = pd.DataFrame(no_clasificados)
                st.dataframe(df_omitidos, use_container_width=True)
                
                csv_omitidos = df_omitidos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⚠️ Descargar Omitidos para revisión",
                    data=csv_omitidos,
                    file_name="productos_omitidos.csv",
                    mime="text/csv",
                    key="btn_descargar_v130"
                )
        
        if productos_clasificados:
            if st.button("🚀 Confirmar y Enviar Datos a Supabase Cloud", key="btn_enviar_v130"):
                with st.spinner("Inyectando registros en la base de datos..."):
                    exito_insercion = False
                    try:
                        payload_intento1 = [{"nombre": p["nombre"], "id_subcat": p["id_subcat"]} for p in productos_clasificados]
                        supabase.table("productos").insert(payload_intento1).execute()
                        exito_insercion = True
                    except Exception:
                        exito_insercion = False
                        
                    if not exito_insercion:
                        try:
                            payload_intento2 = [{"nombre_producto": p["nombre_producto"], "id_enlace_subcat": p["id_enlace_subcat"]} for p in productos_clasificados]
                            supabase.table("productos").insert(payload_intento2).execute()
                            exito_insercion = True
                        except Exception as e_final:
                            st.error(f"Error definitivo de persistencia en Supabase: {e_final}")
                            
                    if exito_insercion:
                        st.balloons()
                        st.success(f"¡Éxito total! Se guardaron {len(productos_clasificados)} productos genéricos en tu esquema privado de Supabase.")
