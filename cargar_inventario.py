# ##############################################################################
# BANNER SUPERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 1 DE 2 <<<
# ##############################################################################
# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE 1 DE 2)
# VERSIÓN: 2.4.0 (ORDENAMIENTO ALFABÉTICO + ESCUDO DE HIGIENE)
# DESCRIPCIÓN: Procesador Masivo de Catálogos Genéricos Retail Nivel 5
# MODIFICACIÓN: Solución a falsos positivos ("res"/"fresco") y ordenamiento A-Z.
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# 1. CONFIGURACIÓN INDEPENDIENTE DE LA VENTANA WEB DE STREAMLIT
st.set_page_config(
    page_title="Carga Masiva - Datos de Inventario",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. HERENCIA DE CONEXIÓN SEGURA INDEPENDIENTE CON LLAVES PROPIAS
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

# 3. TÍTULO PRINCIPAL (Lienzo limpio gobernado por la barra lateral de app.py)
st.title("📤 Carga por Lotes - Datos de Inventario")
st.markdown("Clasificación automatizada local mediante la matriz de reglas fijas e inyección masiva en la nube.")
st.markdown("---")

# 4. MÁSCARA DE TRADUCCIÓN LOCAL: GLOSARIO DE PASILLOS EN TEXTO VENEZOLANO
MAPA_PASILLOS_VENEZUELA = {
    1: "🥩 Carnicería / Frigorífico",
    2: "🧀 Charcutería y Delicateses",
    3: "🍎 Frutería",
    4: "🥦 Verdulería / Legumbres Frescas",
    5: "🐟 Pescadería Fresca",
    6: "🥖 Panadería",
    7: "🍰 Pastelería y Repostería",
    8: "🌾 Granos, Legumbres y Café",
    9: "🫓 Harinas, Pastas y Almidones",
    10: "🛢️ Aceites Comestibles",
    11: "🧈 Grasas y Margarinas",
    12: "🥫 Víveres y Enlatados",
    13: "🍓 Conservas y Dulcería",
    14: "🍯 Salsas y Aderezos",
    15: "🧂 Condimentos y Especias",
    16: "🫖 Desayuno y Azúcar",
    17: "🥛 Lácteos y Leches Líquidas",
    18: "🍧 Yogures y Derivados",
    19: "🍕 Comidas Preparadas y Congelados",
    22: "💧 Agua Mineral y Sifones",
    23: "🧃 Jugos y Néctares",
    24: "🥤 Refrescos y Sodas",
    25: "⚡ Bebidas Energéticas",
    26: "🥃 Ron y Licores Nacionales",
    27: "🍺 Cervezas y Maltas",
    28: "🍷 Vinos de Mesa",
    29: "🍾 Whisky y Destilados",
    30: "🧼 Jabón de Baño y Tocador",
    31: "🧴 Champú y Acondicionadores",
    32: "🪒 Desodorantes y Aseo Personal",
    33: "🪥 Crema y Pasta Dental",
    34: "🧻 Papel Higiénico y Servilletas",
    35: "💄 Maquillaje y Cosméticos",
    36: "🧺 Detergentes y Jabón de Lavar",
    37: "🌸 Suavizantes de Ropa",
    38: "🧹 Limpiadores y Desengrasantes",
    39: "🧪 Desinfectantes y Cloro",
    40: "🧽 Lavaplatos Líquidos y en Crema",
    41: "🐕 Alimentos para Mascotas",
    42: "👶 Pañales Infantiles",
    43: "🍼 Fórmulas Infantiles",
    44: "🛠️ Ferretería Ligera y Eléctricos"
}

# 5. TU DICCIONARIO DURO v1.9.0 SANEADO CONTRA FALSOS POSITIVOS Y COLISIONES
DICCIONARIO_REGLAS = {
    # Escudo Léxico Íntimo Femenino (Confina protectores/toallas en Higiene/Aseo antes de leer la res)
    "toalla": 34, "sanitari": 34, "protect": 32, "diario": 32,
    
    # Alimentos Frescos y Abreviaciones de Balanza Local (Venezuela)
    "carne": 1, "res ": 1, "bistec": 1, "molida": 1, "pollo": 1, "pechuga": 1, "cerdo": 1,
    "solom": 1, "solomito": 1, "pulpa": 1, "chocoz": 1, "muchach": 1, "coch": 1, "cochin": 1,
    "charc": 2, "jamon": 2, "jamón": 2, "mortad": 2, "salchic": 2, "tocin": 2,
    "musa": 2, "amaril": 2, "amarill": 2, "queso": 2,
    "frut": 3, "manzan": 3, "cambur": 3, "naranj": 3, "fresa": 3,
    "verdu": 4, "papa ": 4, "ceboll": 4, "tomate": 4, "zanah": 4, "aliño": 4,
    
    # Pescadería (Se remueve la palabra "fresco" suelta para no contaminar lácteos/pastas)
    "pesca": 5, "camar": 5, "marisc": 5, "merlu": 5, "pargo": 5, "carite": 5,
    
    "pan ": 6, "baguet": 6, "canill": 6, "acem": 6,
    "torta": 7, "ponqu": 7, "hojald": 7, "pastel": 7, "cake": 7,
    "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "cafe": 8, "café": 8,
    "harin": 9, "har": 9, "fororo": 9, "maicena": 9, "pasta": 9, "espagu": 9, "fideo": 9,
    "aceit": 10, "oliva": 10,
    "mantec": 11, "margar": 11, "manteq": 11,
    "atun": 12, "atún": 12, "sardin": 12, "pepito": 12, "enlat": 12,
    "mermel": 13, "conserv": 13, "panela": 13, "pande": 13,
    "mayon": 14, "salsa": 14, "ketchup": 14, "mostaz": 14,
    "sal ": 15, "pimient": 15, "condim": 15, "orég": 15,
    "avena": 16, "cereal": 16, "corn": 16, "azucar": 16, "azúcar": 16,
    "lech": 17, "crema": 17, "lact": 17, "yog": 18, "yogu": 18,
    "nugget": 19, "papas cong": 19, "brocol cong": 20, "helad": 21, "palet": 21,
    "agua": 22, "mineral": 22, "jugo": 23, "nectar": 23, "refres": 24, "soda": 24, "cola": 24,
    "energ": 25, "red bull": 25, "ron ": 26, "caciqu": 26, "cerve": 27, "frías": 27, "vino": 28, 
    "tinto": 28, "whis": 29, "bucan": 29, "jabon": 30, "jabón": 30, "shamp": 31, "champ": 31, 
    "acondic": 31, "desod": 32, "axila": 32, "crema dent": 33, "pasta dent": 33, "colgat": 33, 
    "papel hig": 34, "toilet": 34, "servill": 34, "maquill": 35, "labial": 35, "deterg": 36, 
    "ace ": 36, "ariel": 36, "suaviz": 37, "downy": 37, "limpia": 38, "cloro": 38, "desinf": 39, 
    "lysol": 39, "lavap": 40, "axion": 40, "crema lava": 40, "mascot": 41, "perrar": 41, 
    "gatar": 41, "pañal": 42, "pamp": 42, "formul": 43, "infant": 43, "ferret": 44, "tornill": 44, "clav": 44
}

# 6. FUNCIÓN DE CLASIFICACIÓN CON INTELIGENCIA DE PRESENTACIÓN FISICA DE CORTES
def clasificar_texto_local(nombre_recibido):
    texto = str(nombre_recibido).lower().strip()
    
    # Detector síncrono de cortes (Atún/Sardina) que discrimina latas de pescados frescos
    if "atun" in texto or "atún" in texto or "sardin" in texto:
        if "rueda" in texto or "filet" in texto or "lomo" in texto:
            return 5
            
    for palabra_clave, id_subcat in DICCIONARIO_REGLAS.items():
        if palabra_clave in texto:
            return id_subcat
    return None

# Componente visual para la carga de archivos planos CSV
archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_inventario_v240")
# ##############################################################################
# BANNER INFERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 1 DE 2 <<<
# ##############################################################################
# ##############################################################################
# BANNER SUPERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 2 DE 2 <<<
# ##############################################################################
# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE 2 DE 2)
# VERSIÓN: 2.5.0 (CIERRE MATUTINO - ORDENAMIENTO POR ID + ALFABÉTICO PRODUCTO)
# DESCRIPCIÓN: Bloque de Renderizado Gráfico Simétrico y Motor de Clasificación ID-AZ
# MODIFICACIÓN: sort_values ajustado por id_subcat_interno y nombre_catalogo.
# ==============================================================================

if archivo_subido:
    try:
        df = pd.read_csv(archivo_subido, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(archivo_subido, encoding='latin-1')
    
    if 'nombre' not in df.columns:
        st.error("❌ Error: Tu archivo plano debe contener una columna llamada exactamente 'nombre' (en minúsculas).")
    else:
        st.markdown("### 🧠 Auditoría Visual Previa (Clasificación Local)")
        productos_clasificados = []
        no_clasificados = []
        
        for idx, fila in df.iterrows():
            nombre_prod = fila['nombre']
            id_subcat = clasificar_texto_local(nombre_prod)
            
            if id_subcat:
                nombre_pasillo = MAPA_PASILLOS_VENEZUELA.get(id_subcat, f"Subcategoría {id_subcat}")
                productos_clasificados.append({
                    "nombre_catalogo": str(nombre_prod).strip(),
                    "Pasillo / Departamento": nombre_pasillo,
                    "id_subcat_interno": id_subcat
                })
            else:
                no_clasificados.append({"nombre": nombre_prod})
        
        # 1. RENDERIZADO SIMÉTRICO DE LAS TABLAS DE AUDITORÍA CON NUEVO ORDENAMIENTO
        col_tab1, col_tab2 = st.columns(2)
        
        with col_tab1:
            st.metric("Artículos Aprobados para el Catálogo", len(productos_clasificados))
            if productos_clasificados:
                df_previa = pd.DataFrame(productos_clasificados)
                
                # REGLA SOLICITADA: Ordenamiento primario por ID de Pasillo (1, 2, 3...) + Secundario por Abecedario de Producto
                df_previa = df_previa.sort_values(
                    by=["id_subcat_interno", "nombre_catalogo"], 
                    ascending=[True, True]
                ).reset_index(drop=True)
                
                # COSTURA ESTÉTICA: Ajuste de índice correlativo real iniciando en 1 para humanos
                df_previa.index = df_previa.index + 1
                df_previa.index.name = "N° de Ítem"
                
                # Extraemos solo las columnas comerciales que ve el ojo humano en la pantalla
                st.dataframe(df_previa[["nombre_catalogo", "Pasillo / Departamento"]], use_container_width=True)
                
        with col_tab2:
            st.metric("Artículos Rechazados / Sin Clasificar", len(no_clasificados))
            if no_clasificados:
                df_omitidos = pd.DataFrame(no_clasificados)
                
                # Ordenamos alfabéticamente los omitidos para facilitar la auditoría de raíces faltantes
                df_omitidos = df_omitidos.sort_values(by="nombre", ascending=True).reset_index(drop=True)
                df_omitidos.index = df_omitidos.index + 1
                df_omitidos.index.name = "N° de Ítem"
                
                st.dataframe(df_omitidos, use_container_width=True)
        
        # 2. FILA EN ESPEJO HORIZONTAL SIMÉTRICA PARA LOS BOTONES
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if productos_clasificados:
                if st.button("🚀 Confirmar y Guardar Registros en Catálogo Cloud", key="btn_enviar_catalogo_v250"):
                    with st.spinner("Inyectando registros en bloques de 50 hacia la tabla 'catalogo'..."):
                        TAMANO_LOTE = 50
                        total_guardados = 0
                        error_registrado = None
                        
                        for i in range(0, len(productos_clasificados), TAMANO_LOTE):
                            lote_actual = productos_clasificados[i:i + TAMANO_LOTE]
                            exito_lote = False
                            
                            try:
                                payload = []
                                for p in lote_actual:
                                    payload.append({
                                        "nombre_catalogo": p["nombre_catalogo"],
                                        "id_subcat": p["id_subcat_interno"]
                                    })
                                
                                supabase.table("catalogo").insert(payload).execute()
                                exito_lote = True
                            except Exception as e_lote:
                                error_registrado = e_lote
                                exito_lote = False
                                
                            if exito_lote:
                                total_guardados += len(lote_actual)
                            else:
                                break
                                
                        if total_guardados == len(productos_clasificados):
                            st.balloons()
                            st.success(f"¡Éxito total! Se guardaron {total_guardados} productos de forma permanente en tu tabla 'catalogo'.")
                        elif total_guardados > 0:
                            st.warning(f"⚠️ Carga parcial: Se lograron salvar {total_guardados} productos, pero se detuvo por: {error_registrado}")
                        else:
                            st.error(f"❌ Error definitivo de persistencia en la tabla 'catalogo'. Detalle: {error_registrado}")
                            
        with col_btn2:
            if no_clasificados:
                csv_omitidos = df_omitidos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⚠️ Descargar Rechazados para revisión",
                    data=csv_omitidos,
                    file_name="productos_omitidos.csv",
                    mime="text/csv",
                    key="btn_descargar_omitidos_local_v250"
                )
# ##############################################################################
# BANNER INFERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 2 DE 2 <<<
# ##############################################################################
