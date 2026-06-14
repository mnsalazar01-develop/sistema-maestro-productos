# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE A DE B)
# VERSIÓN: 1.5.0 (MÓDULO SUELTO RAÍZ)
# DESCRIPCIÓN: Procesador Masivo de Catálogos Genéricos Retail Nivel 5
# MODIFICACIÓN: Corrección de jerarquía léxica híbrida y purificación de JSON.
# ==============================================================================

import streamlit as st
import pandas as pd
import io

# 1. HERENCIA DE CONEXIÓN GLOBAL DESDE LA SESIÓN
if "supabase_cliente" in st.session_state:
    supabase = st.session_state["supabase_cliente"]
else:
    from supabase import create_client
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)

st.title("📤 Procesador de Inventarios en Bruto (Nivel 5)")
st.markdown("Clasificación automatizada mediante matriz de control parametrizada en la nube con respaldo local.")

# El diccionario de reglas base unificado y expandido (Tu matriz de confianza)
DICCIONARIO_REGLAS = {
    # 1. Alimentos Frescos
    "carne": 1, "res ": 1, "bistec": 1, "molida": 1, "pollo": 1, "pechuga": 1, "cerdo": 1,
    "charc": 2, "jamon": 2, "jamón": 2, "mortad": 2, "salchic": 2, "tocin": 2,
    "frut": 3, "manzan": 3, "cambur": 3, "naranj": 3, "fresa": 3,
    "verdu": 4, "papa ": 4, "ceboll": 4, "tomate": 4, "zanah": 4, "aliño": 4,
    "pesca": 5, "camar": 5, "marisc": 5, "merlu": 5,
    "pan ": 6, "baguet": 6, "canill": 6, "acem": 6,
    "tort": 7, "pastg": 7, "ponqu": 7, "hojald": 7,

    # 2. Víveres (Despensa)
    "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "cafe": 8, "café": 8,
    "harin": 9, "fororo": 9, "maicena": 9, "pasta": 9, "espagu": 9, "fideo": 9,
    "aceit": 10, "oliva": 10,
    "mantec": 11, "margar": 11, "manteq": 11,
    "atun": 12, "atún": 12, "sardin": 12, "pepito": 12,
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

# Función unificada inteligente: Primero busca en la base paramétrica, si falla va al respaldo local
def clasificar_texto_hibrido(nombre_recibido, mapa_reglas_db=None):
    texto = str(nombre_recibido).lower().strip()
    
    # Prioridad 1: Clasificación Dinámica por base de datos (Si está disponible)
    if mapa_reglas_db:
        for palabra_clave, id_subcat in mapa_reglas_db.items():
            if palabra_clave in texto:
                return id_subcat
                
    # Prioridad 2: Respaldo estático local (Garantiza el éxito de tus 44 familias)
    for palabra_clave, id_subcat in DICCIONARIO_REGLAS.items():
        if palabra_clave in texto:
            return id_subcat
            
    # Prioridad 3: Autoaprendizaje léxico por primera palabra tokenizada
    palabras_token = texto.split()
    if palabras_token:
        primera_palabra = palabras_token[0]
        if mapa_reglas_db and primera_palabra in mapa_reglas_db:
            return mapa_reglas_db[primera_palabra]
        if primera_palabra in DICCIONARIO_REGLAS:
            return DICCIONARIO_REGLAS[primera_palabra]
            
    return None

# Componente visual unificado libre de TabError
archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_v180_fixed")

if archivo_subido:
    st.success("¡Archivo plano cargado con éxito en la memoria web!")
    
    # Descarga e Indexación purificada de Supabase Cloud
    subcategorias_vivas = {}
    try:
        res_reglas = supabase.table("matriz_diccionario_reglas").select("*").execute()
        if res_reglas and hasattr(res_reglas, 'data') and res_reglas.data:
            for fila_r in res_reglas.data:
                # Extracción directa y limpia por nombre clave JSON nativo
                token_clave = str(fila_r.get("palabra_clave", "")).lower().strip()
                id_destino = int(fila_r.get("id_enlace_subcat", 0))
                
                if token_clave and id_destino > 0:
                    subcategorias_vivas[token_clave] = id_destino
            st.sidebar.success(f"🧠 Matriz Dinámica cargada: {len(subcategorias_vivas)} reglas vivas.")
    except Exception as e:
        st.sidebar.warning("⚠️ Modo Inteligente en pausa. Operando con el diccionario base local.")
        subcategorias_vivas = None
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
        
        # Iteración de tu catálogo masivo de productos
        for idx, fila in df.iterrows():
            nombre_prod = fila['nombre']
            id_subcat = clasificar_texto_hibrido(nombre_prod, subcategorias_vivas)
            
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
                    key="btn_descargar_omitidos_v180"
                )
        
        if productos_clasificados:
            if st.button("🚀 Confirmar y Enviar Datos a Supabase Cloud", key="btn_enviar_productos_v180"):
                with st.spinner("Inyectando registros segmentados en la base de datos..."):
                    TAMANO_LOTE = 50
                    total_guardados = 0
                    error_registrado = None
                    
                    # Dividimos la carga en micro-bloques para no saturar las cabeceras de red
                    for i in range(0, len(productos_clasificados), TAMANO_LOTE):
                        lote_actual = productos_clasificados[i:i + TAMANO_LOTE]
                        exito_lote = False
                        
                        # Intento 1: Estructura estándar de columnas ('nombre' / 'id_subcat')
                        try:
                            payload = [{"nombre": p["nombre"], "id_subcat": p["id_subcat"]} for p in lote_actual]
                            supabase.table("productos").insert(payload).execute()
                            exito_lote = True
                        except Exception as e1:
                            error_registrado = e1
                            exito_lote = False
                            
                        # Intento 2 (Contingencia): Estructura extendida ('nombre_producto' / 'id_enlace_subcat')
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
