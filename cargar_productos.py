# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE A DE B)
# VERSIÓN: 1.9.0 (INTEGREGACIÓN INTELIGENCIA COMERCIAL)
# DESCRIPCIÓN: Procesador Masivo de Catálogos Genéricos Retail Nivel 5
# MODIFICACIÓN: Detector de cortes frescos (atún/sardina) e inclusión de la tabla 'catalogo'.
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA WEB DE STREAMLIT
st.set_page_config(
    page_title="Módulo de Carga masiva - Retail",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. HERENCIA DE CONEXIÓN SEGURA DIRECTA DESDE LOS SECRETS DE LA RAÍZ
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

# Declaramos la ruta de regreso al Launchpad central
pagina_principal = "app.py"

# 3. BOTÓN DE RETORNO DIRECTO SUELTO
if st.button("⬅️ Volver al Menú Principal", use_container_width=True, key="btn_regresar_launchpad_inv_v190"):
    st.switch_page(pagina_principal)

st.title("📤 Procesador de Inventarios en Bruto (Nivel 5)")
st.markdown("Clasificación automatizada mediante matriz de reglas fijas e inyección masiva segmentada.")
st.markdown("---")

# El diccionario de reglas base unificado y corregido con términos naturales del retail
DICCIONARIO_REGLAS = {
    # 1. Alimentos Frescos
    "carne": 1, "res ": 1, "bistec": 1, "molida": 1, "pollo": 1, "pechuga": 1, "cerdo": 1,
    "charc": 2, "jamon": 2, "jamón": 2, "mortad": 2, "salchic": 2, "tocin": 2,
    "frut": 3, "manzan": 3, "cambur": 3, "naranj": 3, "fresa": 3,
    "verdu": 4, "papa ": 4, "ceboll": 4, "tomate": 4, "zanah": 4, "aliño": 4,
    
    # Pescadería (Prioridad de raíces y cortes del mar)
    "pesca": 5, "camar": 5, "marisc": 5, "merlu": 5, "fresco": 5,
    
    "pan ": 6, "baguet": 6, "canill": 6, "acem": 6,
    "torta": 7, "ponqu": 7, "hojald": 7, "pastel": 7, "cake": 7, # Removido 'pastg' por términos limpios

    # 2. Víveres (Despensa)
    "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "cafe": 8, "café": 8,
    "harin": 9, "fororo": 9, "maicena": 9, "pasta": 9, "espagu": 9, "fideo": 9,
    "aceit": 10, "oliva": 10,
    "mantec": 11, "margar": 11, "manteq": 11,
    
    # Enlatados genéricos (Capturados si no cumplen la excepción de corte fresco)
    "atun": 12, "atún": 12, "sardin": 12, "pepito": 12, "enlat": 12,
    
    "mermel": 13, "conserv": 13,
    "mayon": 14, "salsa": 14, "ketchup": 14, "mostaz": 14,
    "sal ": 15, "pimient": 15, "condim": 15, "orég": 15,
    "avena": 16, "cereal": 16, "corn": 16, "azucar": 16, "azúcar": 16,

    # 3. Refrigerados y Congelados
    "lech": 17, "queso": 17, "crema": 17, "lact": 17,
    "yog": 18, "yogu": 18,
    "nugget": 19, "papas cong": 19,
    "brocol cong": 20,
    "helad": 21, "palet": 21,

    # 4. Bebidas y Bodegón
    "agua": 22, "mineral": 22,
    "jugo": 23, "nectar": 23,
    "refres": 24, "soda": 24, "cola": 24,
    "energ": 25, "red bull": 25,
    "ron ": 26, "caciqu": 26,
    "cerve": 27, "frías": 27,
    "vino": 28, "tinto": 28,
    "whis": 29, "bucan": 29,

    # 5. Cuidado Personal e Higiene
    "jabon": 30, "jabón": 30,
    "shamp": 31, "champ": 31, "acondic": 31,
    "desod": 32, "axila": 32,
    "crema dent": 33, "pasta dent": 33, "colgat": 33,
    "papel hig": 34, "toilet": 34, "servill": 34,
    "maquill": 35, "labial": 35,

    # 6. Cuidado del Hogar y Limpieza
    "deterg": 36, "ace ": 36, "ariel": 36,
    "suaviz": 37, "downy": 37,
    "limpia": 38, "cloro": 38,
    "desinf": 39, "lysol": 39,
    "lavap": 40, "axion": 40, "crema lava": 40,

    # 7. Categorías Adicionales
    "mascot": 41, "perrar": 41, "gatar": 41,
    "pañal": 42, "pamp": 42,
    "formul": 43, "infant": 43,
    "ferret": 44, "tornill": 44, "clav": 44
}

# FUNCIÓN DE CLASIFICACIÓN CON CRITERIO COMERCIAL INTEGRADO
def clasificar_texto_local(nombre_recibido):
    texto = str(nombre_recibido).lower().strip()
    
    # REGLA DE EXCLUSIÓN CRÍTICA (FRESCO VS ENLATADO)
    # Si detecta Atún o Sardina, pero especifica formato físico de corte, viaja al pasillo 5 (Pescadería)
    if "atun" in texto or "atún" in texto or "sardin" in texto:
        if "rueda" in texto or "filet" in texto or "lomo" in texto:
            return 5
            
    # Bucle tradicional sobre la matriz rígida hardcodeada
    for palabra_clave, id_subcat in DICCIONARIO_REGLAS.items():
        if palabra_clave in texto:
            return id_subcat
    return None

# Componente visual para la carga de archivos planos
archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_inventario_v190")
if archivo_subido:
    try:
        df = pd.read_csv(archivo_subido, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(archivo_subido, encoding='latin-1')
    
    if 'nombre' not in df.columns:
        st.error("❌ Error: Tu archivo plano debe contener una columna llamada exactamente 'nombre' (en minúsculas).")
    else:
        st.markdown("### 🧠 Pre-visualización de la Clasificación Automática Local")
        productos_clasificados = []
        no_clasificados = []
        
        # Iteración del catálogo masivo utilizando el diccionario duro de confianza
        for idx, fila in df.iterrows():
            nombre_prod = fila['nombre']
            id_subcat = clasificar_texto_local(nombre_prod)
            
            if id_subcat:
                # SE RESPETA EL FORMATO FIEL AL CSV ORIGINAL (Sin alteraciones tipográficas)
                productos_clasificados.append({
                    "nombre_catalogo": str(nombre_prod).strip(),
                    "id_subcat": id_subcat
                })
            else:
                no_clasificados.append({"nombre": nombre_prod})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Productos Aceptados (Locales)", len(productos_clasificados))
            if productos_clasificados:
                # Creamos el DataFrame para la visualización comercial ordenada
                df_previa = pd.DataFrame(productos_clasificados)[["nombre_catalogo", "id_subcat"]]
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
                    key="btn_descargar_omitidos_local_v190"
                )
        
        # SUB-MÓDULO DE PERSISTENCIA: BOTÓN INYECTOR POR LOTES SEGUROS (BATCHING)
        if productos_clasificados:
            st.markdown("---")
            if st.button("🚀 Confirmar y Enviar Datos a Supabase Cloud", key="btn_enviar_productos_v190_fijo"):
                with st.spinner("Inyectando registros en bloques seguros de 50 hacia la tabla 'catalogo'..."):
                    TAMANO_LOTE = 50
                    total_guardados = 0
                    error_registrado = None
                    
                    # Dividimos la carga masiva en paquetes pequeños para mantener ligera la cabecera HTTP
                    for i in range(0, len(productos_clasificados), TAMANO_LOTE):
                        lote_actual = productos_clasificados[i:i + TAMANO_LOTE]
                        exito_lote = False
                        
                        try:
                            # Preparamos el payload limpio alineado a tu tabla física real
                            payload = []
                            for p in lote_actual:
                                payload.append({
                                    "nombre_catalogo": p["nombre_catalogo"],
                                    "id_subcat": p["id_subcat"]
                                })
                            
                            # Disparamos la inyección hacia la tabla de la base de datos
                            supabase.table("catalogo").insert(payload).execute()
                            exito_lote = True
                        except Exception as e_lote:
                            error_registrado = e_lote
                            exito_lote = False
                            
                        if exito_lote:
                            total_guardados += len(lote_actual)
                        else:
                            # Si un paquete falla, detenemos el bucle para proteger la integridad de los datos
                            break
                            
                    # Despliegue del estatus de la carga en pantalla
                    if total_guardados == len(productos_clasificados):
                        st.balloons()
                        st.success(f"¡Éxito total! Se guardaron {total_guardados} productos genéricos en tu tabla 'catalogo' con formato fiel al archivo.")
                    elif total_guardados > 0:
                        st.warning(f"⚠️ Carga parcial: Se guardaron {total_guardados} productos, pero el proceso se detuvo por: {error_registrado}")
                    else:
                        st.error(f"❌ Error definitivo de persistencia en la tabla 'catalogo'. Detalle: {error_registrado}")
