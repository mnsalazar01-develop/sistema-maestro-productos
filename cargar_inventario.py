# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE A DE B)
# VERSIÓN: 1.1.0 (MÓDULO SUELTO RAÍZ)
# DESCRIPCIÓN: Procesador Masivo de Catálogos Genéricos Retail Nivel 5
# MODIFICACIÓN: Inyección de extractor posicional adaptativo para corregir el set en cero.
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# Configuración independiente de la ventana web
st.set_page_config(
    page_title="Módulo de Carga masiva - Retail",
    page_icon="📤",
    layout="wide"
)

# Inicialización local de la conexión a base de datos
@st.cache_resource
def init_supabase_local() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_supabase_local()
    st.sidebar.success("⚡ Conexión Dedicada Activa")
except Exception as e:
    st.sidebar.error(f"❌ Error de Conexión: {e}")

st.title("📤 Procesador de Inventarios en Bruto (Nivel 5)")
st.markdown("Clasificación automatizada mediante matriz de control parametrizada en la nube.")

# Función interna de cruce léxico plano
def clasificar_texto_parametrizado(nombre_recibido, mapa_reglas=None):
    texto = str(nombre_recibido).lower().strip()
    
    # Estrategia 1: Evaluación dinámica contra la tabla de control viva
    if mapa_reglas:
        for palabra_clave, id_subcat in mapa_reglas.items():
            if palabra_clave in texto:
                return id_subcat
                
        # Estrategia 2: Autoaprendizaje léxico por primera palabra tokenizada
        palabras_token = texto.split()
        if palabras_token:
            primera_palabra = palabras_token[0]
            if primera_palabra in mapa_reglas:
                return mapa_reglas[primera_palabra]
    return None

# Componente de arrastre de archivos planos
archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="satelite_uploader")

if archivo_subido:
    st.success("¡Archivo plano cargado con éxito en la memoria web!")

    # Descarga Diagnóstica de la Tabla Paramétrica (Versión 1.1.1)
    matriz_reglas_vivas = {}
    try:
        res_reglas = supabase.table("matriz_diccionario_reglas").select("*").execute()
        if res_reglas and hasattr(res_reglas, 'data') and res_reglas.data:
            # AUDITORÍA EN PANTALLA: Inspeccionamos la primera fila real que devuelve tu Supabase
            primera_fila_real = res_reglas.data[0]
            st.sidebar.write("📋 Columnas reales en Supabase:", list(primera_fila_real.keys()))
            st.sidebar.write("👀 Ejemplo de fila descargada:", primera_fila_real)
            
            for fila_r in res_reglas.data:
                # Extracción directa por nombres estándar (Asegurando string y entero puro)
                token_clave = str(fila_r.get("palabra_clave", "")).lower().strip()
                id_destino = int(fila_r.get("id_enlace_subcat", 0))
                
                # Si fallan los nombres estándar, intentamos por índices de posición nativos
                if not token_clave or id_destino == 0:
                    valores = list(fila_r.values())
                    # Buscamos cuál valor es texto y cuál es número entero
                    textos_fila = [v for v in valores if isinstance(v, str)]
                    numeros_fila = [v for v in valores if isinstance(v, int) and v > 7] # IDs de subcat son > 7
                    if textos_fila and numeros_fila:
                        token_clave = str(textos_fila[0]).lower().strip()
                        id_destino = int(numeros_fila[0])
                
                if token_clave and id_destino > 0:
                    matriz_reglas_vivas[token_clave] = id_destino
                    
            st.sidebar.success(f"🧠 Diccionario RAM cargado: {len(matriz_reglas_vivas)} reglas activas.")
    except Exception as e:
        st.sidebar.error(f"❌ Error en descarga paramétrica: {e}")
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
                    "nombre_producto": nombre_prod,
                    "id_subcat": id_subcat,
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
                    key="btn_descargar_omitidos_satelite"
                )
        
        if productos_clasificados:
            if st.button("🚀 Confirmar y Enviar Datos a Supabase Cloud", key="btn_enviar_productos_satelite"):
                with st.spinner("Inyectando registros en la base de datos..."):
                    exito_insercion = False
                    
                    # Intento 1: Estructura estándar de columnas ('nombre' / 'id_subcat')
                    try:
                        payload_intento1 = []
                        for p in productos_clasificados:
                            payload_intento1.append({
                                "nombre": p["nombre"],
                                "id_subcat": p["id_subcat"]
                            })
                        supabase.table("productos").insert(payload_intento1).execute()
                        exito_insercion = True
                    except Exception:
                        exito_insercion = False
                        
                    # Intento 2 (Contingencia): Estructura extendida si tu Supabase usa ('nombre_producto' / 'id_enlace_subcat')
                    if not exito_insercion:
                        try:
                            payload_intento2 = []
                            for p in productos_clasificados:
                                payload_intento2.append({
                                    "nombre_producto": p["nombre_producto"],
                                    "id_enlace_subcat": p["id_enlace_subcat"]
                                })
                            supabase.table("productos").insert(payload_intento2).execute()
                            exito_insercion = True
                        except Exception as e_final:
                            st.error(f"Error definitivo de persistencia en Supabase: {e_final}")
                            
                    if exito_insercion:
                        st.balloons()
                        st.success(f"¡Éxito total! Se guardaron {len(productos_clasificados)} productos genéricos en tu esquema privado de Supabase.")
