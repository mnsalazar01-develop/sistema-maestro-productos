# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (VERSIÓN BATCHING CORPORATIVO)
# VERSIÓN: 1.4.0 (MÓDULO SUELTO RAÍZ)
# DESCRIPCIÓN: Procesador Masivo de Catálogos Genéricos Retail Nivel 5
# MODIFICACIÓN: Segmentación de cargas en bloques de 50 para evitar error PGRST125.
# ==============================================================================

import streamlit as st
import pandas as pd
import io

# 1. ABSORCIÓN DE CONEXIÓN GLOBAL VALIDADA
if "supabase_cliente" in st.session_state:
    supabase = st.session_state["supabase_cliente"]
else:
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

# Componente visual de arrastre de archivos planos
archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_v140")

if archivo_subido:
    st.success("¡Archivo plano cargado con éxito en la memoria web!")
    
    # Descarga e Indexación de la Tabla Paramétrica
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
        st.sidebar.error(f"❌ Error en PostgREST al leer reglas: {e}")
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
                    key="btn_descargar_v140"
                )
        
        if productos_clasificados:
            if st.button("🚀 Confirmar y Enviar Datos a Supabase Cloud", key="btn_enviar_v140"):
                with st.spinner("Inyectando registros segmentados en la base de datos..."):
                    TAMANO_LOTE = 50
                    total_guardados = 0
                    error_registrado = None
                    
                    # Dividimos los productos en bloques de 50 para no saturar las cabeceras HTTP
                    for i in range(0, len(productos_clasificados), TAMANO_LOTE):
                        lote_actual = productos_clasificados[i:i + TAMANO_LOTE]
                        exito_lote = False
                        
                        # Intento 1: Nomenclatura estándar
                        try:
                            payload = [{"nombre": p["nombre"], "id_subcat": p["id_subcat"]} for p in lote_actual]
                            supabase.table("productos").insert(payload).execute()
                            exito_lote = True
                        except Exception as e1:
                            error_registrado = e1
                            exito_lote = False
                            
                        # Intento 2 (Contingencia): Nomenclatura extendida
                        if not exito_lote:
                            try:
                                payload = [{"nombre_producto": p["nombre_producto"], "id_enlace_subcat": p["id_enlace_subcat"]} for p in lote_actual]
                                supabase.table("productos").insert(payload).execute()
                                exito_lote = True
                            except Exception as e2:
                                error_registrado = e2
                                exito_lote = False
                                
                        if exito_lote:
                            total_guardados += len(lote_actual)
                        else:
                            break
                            
                    if total_guardados == len(productos_clasificados):
                        st.balloons()
                        st.success(f"¡Éxito total! Se guardaron {total_guardados} productos genéricos en bloques seguros.")
                    elif total_guardados > 0:
                        st.warning(f"Carga parcial: Se lograron salvar {total_guardados} productos, pero el proceso se detuvo por: {error_registrado}")
                    else:
                        st.error(f"Error definitivo de persistencia: {error_registrado}")
