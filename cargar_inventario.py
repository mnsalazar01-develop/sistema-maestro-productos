# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE 1 DE 2)
# VERSIÓN: 3.0.0 (CONSOLIDACIÓN DE GLOSARIOS Y BANNERS REGLAMENTARIOS)
# DESCRIPCIÓN: Procesador Masivo de Catálogos Genéricos Retail Nivel 5
# MODIFICACIÓN: Aplicación estricta de omisión de banner inicial en Parte 1.
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
except Exception as e:
    st.sidebar.error(f"❌ Error de Conexión: {e}")

# 3. TÍTULO PRINCIPAL DE LA COMPAÑÍA (Lienzo libre gobernado por app.py)
st.title("📤 Carga por Lotes - Datos de Inventario")
st.markdown("Clasificación automatizada local mediante la matriz de reglas fijas e inyección masiva en la nube.")
st.markdown("---")

# 4. MÁSCARA DE TRADUCCIÓN LOCAL: GLOSARIO DE PASILLOS EN TEXTO VENEZOLANO RE-CALIBRADO
MAPA_PASILLOS_VENEZUELA = {
    1: "🥩 Carnicería / Frigorífico", 2: "🧀 Charcutería y Delicateses", 3: "🍎 Frutería",
    4: "🥦 Verdulería / Legumbres Frescas", 5: "🐟 Pescadería Fresca", 6: "🥖 Panadería",
    7: "🍰 Pastelería y Repostería", 8: "🌾 Granos, Legumbres y Café", 9: "🫓 Harinas, Pastas y Almidones",
    10: "🛢️ Aceites Comestibles", 11: "🧈 Grasas y Margarinas", 12: "🥫 Víveres y Enlatados",
    13: "🍓 Conservas y Dulcería", 14: "🍯 Salsas y Aderezos", 15: "🧂 Condimentos y Especias",
    16: "🫖 Desayuno, Golosinas y Snacks", 17: "🥛 Lácteos y Leches Líquidas", 18: "🍧 Yogures y Derivados",
    19: "🍕 Comidas Preparadas y Congelados", 21: "🍦 Helados y Paletas", 22: "💧 Agua Mineral y Sifones",
    23: "🧃 Bebidas, Jugos y Néctares", 24: "🥤 Refrescos y Sodas Carbonatadas", 25: "⚡ Bebidas Energéticas",
    26: "🥃 Ron y Licores Nacionales", 27: "🍺 Cervezas y Maltas", 28: "🍷 Vinos de Mesa",
    29: "🍾 Whisky y Destilados", 30: "🧼 Jabón de Baño y Tocador", 31: "🧴 Champú y Acondicionadores",
    32: "🪒 Desodorantes y Aseo Personal", 33: "🪥 Crema y Pasta Dental", 34: "🧻 Papel Higiénico y Servilletas",
    35: "💄 Maquillaje y Cosméticos", 36: "🧺 Detergentes y Jabón de Lavar", 37: "🌸 Suavizantes de Ropa",
    38: "🧹 Limpiadores y Desengrasantes", 39: "🧪 Desinfectantes y Cloro", 40: "🧽 Lavaplatos Líquidos y en Crema",
    41: "🐕 Alimentos para Mascotas", 42: "👶 Pañales Infantiles", 43: "🍼 Fórmulas Infantiles", 44: "🛠️ Ferretería Ligera y Eléctricos"
}

# 5. MATRIZ INTEGRAL RESTABLECIDA AL 100% CON REGLAS DUERAS MÁS CHORIZO
DICCIONARIO_REGLAS = {
    "carne": 1, "res ": 1, "bistec": 1, "molida": 1, "pollo": 1, "pechuga": 1, "cerdo": 1,
    "solom": 1, "solomito": 1, "pulpa": 1, "chocoz": 1, "muchach": 1, "coch": 1, "cochin": 1,
    "charc": 2, "jamon": 2, "jamón": 2, "mortad": 2, "salchic": 2, "tocin": 2, "queso": 2, "choriz": 2,
    "canill": 6, "baguet": 6, "acem": 6, "torta": 7, "ponqu": 7, "hojald": 7, "pastel": 7, "cake": 7,
    "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "garbanz": 8, "cafe": 8, "café": 8,
    "fororo": 9, "maicena": 9, "fideo": 9, "aceit": 10, "oliva": 10, "mantec": 11, "margar": 11, "manteq": 11,
    "atun": 12, "atún": 12, "sardin": 12, "pepito": 12, "enlat": 12, "mermel": 13, "conserv": 13, "panela": 13, "pande": 13,
    "mayon": 14, "mostaz": 14, "sal ": 15, "orég": 15, "avena": 16, "cereal": 16, "corn": 16, "azucar": 16, "azúcar": 16,
    "lech": 17, "crema": 17, "lact": 17, "yog": 18, "yogu": 18, "nugget": 19, "papas cong": 19, "brocol cong": 20, "helad": 21, "palet": 21,
    "agua": 22, "mineral": 22, "energ": 25, "red bull": 25, "ron ": 26, "caciqu": 26, "frías": 27, "vino": 28, "whis": 29,
    "jabon": 30, "jabón": 30, "shamp": 31, "champ": 31, "acondic": 31, "crema dent": 33, "pasta dent": 33, "colgat": 33, 
    "papel hig": 34, "toilet": 34, "servill": 34, "maquill": 35, "labial": 35, "deterg": 36, "ace ": 36, "ariel": 36, "suaviz": 37, "downy": 37, 
    "limpia": 38, "cloro": 38, "lysol": 39, "axion": 40, "mascot": 41, "perrar": 41, "gatar": 41, "pamp": 42, "formul": 43, "tornill": 44, "clav": 44
}

# 6. FUNCIÓN INTELECTUAL JERÁRQUICA EN CASCADA COMPLETA (7 NIVELACIONES DIRECTAS)
def clasificar_texto_local(nombre_recibido):
    texto = str(nombre_recibido).lower().strip()
    if "pan para perro" in texto or "pan de perro" in texto or "pan caliente" in texto: return 6
    if "harin" in texto or "har " in texto or "harina" in texto: return 9
    if "santa teresa" in texto or "cacique" in texto or "pampero" in texto: return 26
    if "arena s" in texto: return 41
    if "filtro" in texto: return 44
    if "paño" in texto: return 38
    if "perrarin" in texto or "gatarin" in texto or "mascot" in texto or "para perro" in texto or "para gato" in texto: return 41
    if "crema dent" in texto or "pasta dent" in texto or "colgat" in texto: return 33
    if "crema corp" in texto or "crema para p" in texto: return 32
    if "crema cero" in texto or "pañalitis" in texto: return 42
    if "oxigenad" in texto: return 32
    if "jabon de b" in texto or "jabón de b" in texto or "desod" in texto or "axila" in texto: return 32
    if "jabon liquido de avena" in texto or "jabón líquido de avena" in texto: return 32
    if "toalla" in texto or "sanitari" in texto or "protect" in texto or "diario" in texto: return 34 if ("toalla" in texto or "sanitari" in texto) else 32
    if "afeit" in texto: return 32
    if "champ" in texto or "shamp" in texto: return 31
    if "jabon de pa" in texto or "jabón de pa" in texto or "panela azul" in texto or "panela bla" in texto or "jabon de cuaba" in texto or "jabón de cuaba" in texto: return 36
    if "desinf" in texto or "cloro" in texto or "lysol" in texto: return 39
    if "lavap" in texto or "crema lava" in texto or "axion" in texto: return 40
    if "fiambre" in texto or "choriz" in texto: return 2
    if "canela" in texto or "pimient" in texto or "cubito" in texto: return 15
    if "salsa" in texto or "ketchup" in texto or "boloñes" in texto or "pasta de tom" in texto: return 14
    if "carne" in texto or "res " in texto or "bistec" in texto or "molida" in texto or "pollo" in texto or "pechuga" in texto or "cerdo" in texto or "morcil" in texto: return 1
    if "champiñon" in texto or "champiñón" in texto: return 12
    if "atun" in texto or "atún" in texto or "sardin" in texto or "enlat" in texto: return 5 if ("rueda" in texto or "filet" in texto or "lomo" in texto) else 12
    if "papas frit" in texto or "platanit" in texto or "dorito" in texto or "mani " in texto or "maní" in texto or "chistri" in texto or "cheeto" in texto or "natuchip" in texto: return 16
    if "crema de arroz" in texto or "cerelac" in texto: return 16
    if "yog" in texto or "yogu" in texto or "yogurt" in texto: return 18
    if "galleta" in texto or "galleta de s" in texto or "galletas de s" in texto: return 9
    if "chocola" in texto or "samba" in texto or "cri-cri" in texto or "cricri" in texto: return 16
    if "helad" in texto: return 21
    if "jugo" in texto or "nectar" in texto or "néctar" in texto or "bebida de" in texto or "yukery" in texto or "natulac" in texto or "frica" in texto: return 23
    if "refres" in texto or "hit" in texto or "chinotto" in texto or "soda" in texto or "cola" in texto: return 24
    if "cerve" in texto or "frías" in texto or "malt" in texto: return 27
    if "chicha" in texto: return 16 if "polvo" in texto else 17
    if any(x in texto for x in ["cambur", "platan", "fresa", "manzan", "naranj", "mandra", "parch", "guanab", "guayab", "patil", "meloc", "melon", "melón", "lecho", "pina", "piña", "mango", "pumar", "nispe", "grap", "toronj", "limon", "limón", "coco ", "uva "]): return 3
    if any(x in texto for x in ["ceboll", "tomate", "piment", "ajic", "aji ", "ají ", "ajo ", "puerro", "cilan", "pereg", "celeri", "aliño", "ceboti", "ceboul", "papa ", "yuca ", "ocumo", "ñame ", "auyam", "batat", "zanah", "jengib", "lechu", "repol", "brocol", "colif", "espin", "vaina", "beren", "calab", "pepin", "aguac", "jojot"]): return 4
    if "gel antibac" in texto or "antibacterial" in texto: return 30
    if "musa" in texto or "amaril" in texto or "amarill" in texto: return 2
    if "arroz" in texto or "gran" in texto: return 8
    if "pasta" in texto or "espagu" in texto: return 9
    if "lech" in texto or "lact" in texto or "crema" in texto: return 17
    if "agua" in texto: return 22
    if "aceit" in texto: return 10
    if "sal " in texto: return 15
    for k, v in DICCIONARIO_REGLAS.items():
        if k in texto: return v
    return None

# Componente visual para la carga de archivos planos CSV
archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_inventario_v300")

# ##############################################################################
# BANNER INFERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 1 DE 2 <<<
# ##############################################################################
# ##############################################################################
# BANNER SUPERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 2 DE 2 <<<
# ##############################################################################
# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE 2 DE 2)
# VERSIÓN: 3.0.0 (CONSOLIDACIÓN DE GLOSARIOS Y BANNERS REGLAMENTARIOS)
# DESCRIPCIÓN: Bloque de Renderizado Gráfico Simétrico y Motor de Clasificación ID-AZ
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
        productos_clasificados, no_clasificados = [], []
        
        for idx, fila in df.iterrows():
            nombre_prod = fila['nombre']
            id_subcat = clasificar_texto_local(nombre_prod)
            if id_subcat:
                productos_clasificados.append({
                    "nombre_catalogo": str(nombre_prod).strip(),
                    "Pasillo / Departamento": MAPA_PASILLOS_VENEZUELA.get(id_subcat, f"Subcategoría {id_subcat}"),
                    "id_subcat_interno": id_subcat
                })
            else: no_clasificados.append({"nombre": nombre_prod})
        
        # 1. RENDERIZADO SIMÉTRICO DE LAS TABLAS CON NUEVO ORDENAMIENTO DE ALTA DENSIDAD
        col_tab1, col_tab2 = st.columns(2)
        
        with col_tab1:
            st.metric("Artículos Aprobados para el Catálogo", len(productos_clasificados))
            if productos_clasificados:
                df_previa = pd.DataFrame(productos_clasificados)
                
                # ORDENAMIENTO MANDATORIO: Secuencial por Número de Pasillo + Alfabético de la A a la Z
                df_previa = df_previa.sort_values(
                    by=["id_subcat_interno", "nombre_catalogo"], 
                    ascending=[True, True]
                ).reset_index(drop=True)
                
                # Conteo Humano Correlativo iniciando estrictamente en 1
                df_previa.index = df_previa.index + 1
                df_previa.index.name = "N° de Ítem"
                
                st.dataframe(df_previa[["nombre_catalogo", "Pasillo / Departamento"]], use_container_width=True)
                
        with col_tab2:
            st.metric("Artículos Rechazados / Sin Clasificar", len(no_clasificados))
            if no_clasificados:
                df_omitidos = pd.DataFrame(no_clasificados)
                df_omitidos = df_omitidos.sort_values(by="nombre", ascending=True).reset_index(drop=True)
                df_omitidos.index = df_omitidos.index + 1
                df_omitidos.index.name = "N° de Ítem"
                
                st.dataframe(df_omitidos, use_container_width=True)
        
        # 2. FILA EN ESPEJO HORIZONTAL SIMÉTRICA PARA LOS BOTONES CORPORATIVOS
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if productos_clasificados:
                if st.button("🚀 Confirmar y Guardar Registros en Catálogo Cloud", key="btn_enviar_catalogo_v300"):
                    with st.spinner("Inyectando registros en bloques de 50 hacia la tabla 'catalogo'..."):
                        TAMANO_LOTE, total_guardados, error_registrado = 50, 0, None
                        for i in range(0, len(productos_clasificados), TAMANO_LOTE):
                            lote_actual = productos_clasificados[i:i + TAMANO_LOTE]
                            try:
                                payload = [{"nombre_catalogo": p["nombre_catalogo"], "id_subcat": p["id_subcat_interno"]} for p in lote_actual]
                                supabase.table("catalogo").insert(payload).execute()
                                total_guardados += len(lote_actual)
                            except Exception as e_lote:
                                error_registrado = e_lote
                                break
                        if total_guardados == len(productos_clasificados):
                            st.balloons()
                            st.success(f"¡Éxito total! Se guardaron {total_guardados} productos de forma permanente en tu tabla 'catalogo'.")
                        elif total_guardados > 0: st.warning(f"⚠️ Carga parcial: Se salvaron {total_guardados} ítems, error: {error_registrado}")
                        else: st.error(f"❌ Error definitivo de persistencia: {error_registrado}")
                            
        with col_btn2:
            if no_clasificados:
                csv_omitidos = df_omitidos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⚠️ Descargar Rechazados para revisión",
                    data=csv_omitidos,
                    file_name="productos_omitidos.csv",
                    mime="text/csv",
                    key="btn_descargar_omitidos_local_v300"
                )
# ##############################################################################
# BANNER INFERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 2 DE 2 <<<
# ##############################################################################
