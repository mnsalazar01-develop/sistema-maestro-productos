# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE 1 DE 3)
# VERSIÓN: 4.3.0 (RUTA EXPLÍCITA DE ESQUEMA - PUBLIC.SUBCATEGORIAS)
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
st.markdown("Clasificación automatizada local enlazada dinámicamente a las llaves relacionales de tu base de datos cloud.")
st.markdown("---")

# 4. DESCARGA EN VIVO CON RUTA DE ESQUEMA ABSOLUTA (EVITA CEGUERA DE POSTGREST)
def descargar_mapa_subcategorias_cloud():
    try:
        # Costura v4.3.0: Prefijo de esquema explícito 'public.' para romper el bloqueo de internet
        res_sub = supabase.table("public.subcategorias").select("id_subcat, nombre_subcat").execute()
        if res_sub and hasattr(res_sub, 'data') and res_sub.data:
            # Mapeamos de forma síncrona el entero con la string real de la base de datos
            return {int(item["id_subcat"]): item["nombre_subcat"] for item in res_sub.data}
    except Exception as e_mapa:
        st.sidebar.error(f"⚠️ Error al sincronizar subcategorías cloud: {e_mapa}")
    return {}

MAPA_PASILLOS_VENEZUELA = descargar_mapa_subcategorias_cloud()

if not MAPA_PASILLOS_VENEZUELA:
    st.error("❌ Alerta de Tubería: No se pudieron descargar las subcategorías desde la tabla 'subcategorias' en internet. Verifica que tenga registros.")
    st.stop()

# 5. MATRIZ INTEGRAL PURGADA DE RAÍCES COMPLEMENTARIAS HISTÓRICAS
DICCIONARIO_REGLAS = {
    "carne": 1, "res ": 1, "bistec": 1, "molida": 1, "pollo": 1, "pechuga": 1, "cerdo": 1, "lagart": 1,
    "solom": 1, "solomito": 1, "pulpa": 1, "chocoz": 1, "muchach": 1, "coch": 1, "cochin": 1,
    "charc": 2, "jamón": 2, "mortad": 2, "salchic": 2, "tocin": 2, "queso": 2, "choriz": 2, "pastrami": 2,
    "pan ": 6, "baguet": 6, "canill": 6, "acem": 6, "torta": 7, "ponqu": 7, "hojald": 7, "pastel": 7, "cake": 7,
    "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "garbanz": 8, "café": 8,
    "harin": 9, "har": 9, "fororo": 9, "maicena": 9, "pasta": 9, "espagu": 9, "fideo": 9,
    "aceit": 10, "oliva": 10, "mantec": 11, "margar": 11, "manteq": 11, "atún": 12, "sardin": 12, "pepito": 12, "enlat": 12,
    "mermel": 13, "conserv": 13, "panela": 13, "pande": 13, "mayon": 14, "mostaz": 14, "sal ": 15, "orég": 15,
    "avena": 16, "cereal": 16, "corn": 16, "azúcar": 16,
    "lech": 17, "crema": 17, "lact": 17, "yog": 18, "yogu": 18, "nugget": 19, "papas cong": 19, "brocol cong": 20, "helad": 21, "palet": 21,
    "agua": 22, "mineral": 22, "jugo": 23, "nectar": 23, "refres": 24, "soda": 24, "cola": 24,
    "energ": 25, "red bull": 25, "ron ": 26, "caciqu": 26, "cerve": 27, "frías": 27, "vino": 28, "tinto": 28, "whis": 29, "bucan": 29,
    "jabón": 30, "champú": 31, "acondic": 31, "crema dent": 33, "pasta dent": 33, "colgat": 33, 
    "papel hig": 34, "toilet": 34, "servill": 34, "maquill": 35, "labial": 35, "deterg": 36, "ace ": 36, "ariel": 36, "suaviz": 37, "downy": 37, 
    "limpia": 38, "cloro": 38, "lysol": 39, "axion": 40, "mascot": 41, "perrar": 41, "gatar": 41, "pamp": 42, "formul": 43, "tornill": 44, "clav": 44
}

# ##############################################################################
# BANNER INFERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 1 DE 3 <<<
# ##############################################################################
# ##############################################################################
# BANNER SUPERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 2 DE 3 <<<
# ##############################################################################
# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE 2 DE 3)
# VERSIÓN: 4.3.0 (RUTA EXPLÍCITA DE ESQUEMA - PUBLIC.SUBCATEGORIAS)
# DESCRIPCIÓN: La Cascada Completa de los 7 Niveles de Exclusión con Filtros RAE
# ==============================================================================

def clasificar_texto_local(nombre_recibido):
    texto = str(nombre_recibido).strip()
    texto_lower = texto.lower()
    
    # FILTRO ORTOGRÁFICO PUNITIVO SELECTIVO: Castiga la falta de tilde en sustantivos puros
    if "atun" in texto_lower and "atún" not in texto_lower: return None
    if "cafe" in texto_lower and "café" not in texto_lower: return None
    if "champu" in texto_lower and "champú" not in texto_lower: return None
    if "jamon" in texto_lower and "jamón" not in texto_lower: return None
    if "platano" in texto_lower and "plátano" not in texto_lower: return None
    if "limon" in texto_lower and "limón" not in texto_lower: return None
    if "frias" in texto_lower and "frías" not in texto_lower: return None
    if "brocoli" in texto_lower and "brócoli" not in texto_lower: return None
    if "champiñon " in texto_lower and "champiñón " not in texto_lower: return None
    
    # Parachoques de adjetivos: Exige tilde estricta en el sustantivo pero no penaliza derivados relacionales
    if "jabon" in texto_lower and "jabón" not in texto_lower and "jabonoso" not in texto_lower: return None
    if "azucar" in texto_lower and "azúcar" not in texto_lower and "azucarada" not in texto_lower: return None

    # --- NIVEL 1: PRIORIDAD SUPREMA DE PANADERÍA, HARINAS Y FERRETERÍA DE CONSUMO ---
    if "pan para perro" in texto_lower or "pan de perro" in texto_lower or "pan caliente" in texto_lower: return 6
    if "harin" in texto_lower or "har " in texto_lower or "harina" in texto_lower: return 9
    if "santa teresa" in texto_lower or "cacique" in texto_lower or "pampero" in texto_lower: return 26
    if "arena s" in texto_lower: return 41
    if "filtro" in texto_lower: return 44
    if "aluminio" in texto_lower: return 44
    if "paño" in texto_lower: return 38

    # --- NIVEL 2: MÓDULO INFANTIL, HIGIENE ÍNTIMA Y TRATAMIENTO BUCAL DENTAL ---
    if "perrarin" in texto_lower or "gatarin" in texto_lower or "mascot" in texto_lower or "para perro" in texto_lower or "para gato" in texto_lower: return 41
    if "crema dent" in texto_lower or "pasta dent" in texto_lower or "colgat" in texto_lower or "enjuague" in texto_lower or "plax" in texto_lower or "hilo dent" in texto_lower: return 33
    if "crema corp" in texto_lower or "crema para p" in texto_lower or "talco" in texto_lower or "desod" in texto_lower or "axila" in texto_lower: return 32
    if "crema cero" in texto_lower or "pañalitis" in texto_lower or "pañal" in texto_lower or "pañale" in texto_lower: return 42
    if "colonia" in texto_lower or "toallita" in texto_lower: return 43 if "bebé" in texto_lower else 32
    if "oxigenad" in texto_lower: return 32
    if "jabón de b" in texto_lower: return 32
    if "jabon liquido de avena" in texto_lower or "jabón líquido de avena" in texto_lower: return 32
    if "toalla" in texto_lower or "sanitari" in texto_lower or "protect" in texto_lower or "diario" in texto_lower: return 34 if ("toalla" in texto_lower or "sanitari" in texto_lower) else 32
    if "tampon" in texto_lower: return 34
    if "afeit" in texto_lower: return 32
    if "champú" in texto_lower or "shamp" in texto_lower: return 31

    # --- NIVEL 3: LAVANDERÍA, DESINFECTANTES Y UTENSILIOS DE PLANCHAS ---
    if "jabón de pa" in texto_lower or "panela azul" in texto_lower or "panela bla" in texto_lower or "jabón de cuaba" in texto_lower: return 36
    if "desinf" in texto_lower or "cloro" in texto_lower or "lysol" in texto_lower: return 39
    if "lavap" in texto_lower or "crema lava" in texto_lower or "axion" in texto_lower or "esponja" in texto_lower: return 40
    if "fiambre" in texto_lower or "choriz" in texto_lower or "pastrami" in texto_lower: return 2

    # --- NIVEL 4: CONDIMENTOS INTERCEPTORES, VEGETALES INDUSTRIALES Y PROTEÍNAS ---
    if "canela" in texto_lower or "pimient" in texto_lower or "cubito" in texto_lower or "comin" in texto_lower or "onoto" in texto_lower or "alcapar" in texto_lower or "bicarbonat" in texto_lower: return 15
    if "salsa" in texto_lower or "ketchup" in texto_lower or "boloñes" in texto_lower or "pasta de tom" in texto_lower or "vinagr" in texto_lower: return 14
    if "carne" in texto_lower or "res " in texto_lower or "bistec" in texto_lower or "molida" in texto_lower or "pollo" in texto_lower or "pechuga" in texto_lower or "cerdo" in texto_lower or "morcil" in texto_lower or "huevo" in texto_lower or "lagart" in texto_lower: return 1
    if "endiablado" in texto_lower or "champiñon" in texto_lower or "champiñón" in texto_lower or "champiño" in texto_lower: return 12
    if "atún" in texto_lower or "sardin" in texto_lower or "enlat" in texto_lower: return 5 if ("rueda" in texto_lower or "filet" in texto_lower or "lomo" in texto_lower) else 12

    # --- NIVEL 5: SNACKS SALADOS, BEBIDAS ENVASETADAS Y MOLIENDAS TRADICIONALES DE MAÍZ ---
    if "papas frit" in texto_lower or "platanit" in texto_lower or "dorito" in texto_lower or "mani " in texto_lower or "maní" in texto_lower or "chistri" in texto_lower or "cheeto" in texto_lower or "natuchip" in texto_lower or "tortilla" in texto_lower: return 16
    if "crema de arroz" in texto_lower or "cerelac" in texto_lower: return 16
    if "cachapa" in texto_lower: return 9
    if "yog" in texto_lower or "yogu" in texto_lower or "yogurt" in texto_lower: return 18
    if "galleta" in texto_lower or "galleta de s" in texto_lower or "galletas de s" in texto_lower: return 9
    if "chocola" in texto_lower or "samba" in texto_lower or "cri-cri" in texto_lower or "cricri" in texto_lower: return 16
    if "helad" in texto_lower: return 21
    if "jugo" in texto_lower or "nectar" in texto_lower or "néctar" in texto_lower or "bebida de" in texto_lower or "yukery" in texto_lower or "natulac" in texto_lower or "frica" in texto_lower or "té " in texto_lower or "té" in texto_lower: return 23
    if "refres" in texto_lower or "hit" in texto_lower or "chinotto" in texto_lower or "soda" in texto_lower or "cola" in texto_lower: return 24
    if "cerve" in texto_lower or "frías" in texto_lower or "malt" in texto_lower or "ron" in texto_lower: return 27 if "cerve" in texto_lower or "frías" in texto_lower or "malt" in texto_lower else 26
    if "chicha" in texto_lower: return 16 if "polvo" in texto_lower else 17

    # --- NIVEL 6: SUPER-GLOSARIO DE FERIA VENEZOLANA AMPLIADO ---
    if any(x in texto_lower for x in ["cambur", "plátano", "fresa", "manzan", "naranj", "mandra", "parch", "guanab", "guayab", "patil", "meloc", "melon", "melón", "lecho", "pina", "piña", "mango", "pumar", "nispe", "grap", "toronj", "limón", "coco ", "uva ", "pana"]): return 3
    if any(x in texto_lower for x in ["ceboll", "tomate", "piment", "ajic", "aji ", "ají ", "ajo ", "puerro", "cilan", "perej", "celeri", "aliño", "ceboti", "ceboul", "papa ", "yuca ", "ocum", "ñame ", "auyam", "batat", "zanah", "jengib", "lechu", "repol", "brócoli", "colif", "espin", "vaina", "beren", "calab", "pepin", "aguac", "jojot", "acelg", "chayot", "albahac", "menta", "yautia", "malanga", "colombian", "remolach", "vainit"]): return 4
    if "pasa" in texto_lower: return 13
    if "gel antibac" in texto_lower or "antibacterial" in texto_lower: return 30

    # --- NIVEL 7: EXTRACCIÓN PRIMITIVA DE DESPENSA LIMPIA ---
    if "musa" in texto_lower or "amaril" in texto_lower or "amarill" in texto_lower: return 2
    if "arroz" in texto_lower or "gran" in texto_lower: return 8
    if "pasta" in texto_lower or "espagu" in texto_lower: return 9
    if "lech" in texto_lower or "lact" in texto_lower or "crema" in texto_lower or "natilla" in texto_lower: return 17
    if "agua" in texto_lower: return 22
    if "aceit" in texto_lower: return 10
    if "sal " in texto_lower: return 15
    for k, v in DICCIONARIO_REGLAS.items():
        if k in texto_lower: return v
    return None

# ##############################################################################
# BANNER INFERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 2 DE 3 <<<
# ##############################################################################
# ##############################################################################
# BANNER SUPERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 3 DE 3 <<<
# ##############################################################################
# ==============================================================================
# PROGRAMA SATÉLITE: cargar_inventario.py (PARTE 3 DE 3)
# VERSIÓN: 4.3.0 (RUTA EXPLÍCITA DE ESQUEMA - PUBLIC.SUBCATEGORIAS)
# DESCRIPCIÓN: Interfaz de Auditoría por Columnas, Conteo Correlativo e Inyector Cloud
# ==============================================================================

archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_inventario_v430")

if archivo_subido:
    try: df = pd.read_csv(archivo_subido, encoding='utf-8')
    except UnicodeDecodeError: df = pd.read_csv(archivo_subido, encoding='latin-1')
    
    if 'nombre' not in df.columns:
        st.error("❌ Error: Tu archivo plano debe contener una columna llamada exactamente 'nombre' (en minúsculas).")
    else:
        st.markdown("### 🧠 Auditoría Visual Previa (Clasificación Local)")
        productos_clasificados, no_clasificados = [], []
        
        for idx, fila in df.iterrows():
            nombre_prod = fila['nombre']
            id_subcat = clasificar_texto_local(nombre_prod)
            
            # Buscamos en caliente la Llave Foránea exacta dentro del mapa fresco de internet
            if id_subcat and id_subcat in MAPA_PASILLOS_VENEZUELA:
                productos_clasificados.append({
                    "nombre_catalogo": str(nombre_prod).strip(),
                    "Pasillo / Departamento": MAPA_PASILLOS_VENEZUELA[id_subcat],
                    "id_subcat_interno": id_subcat
                })
            else:
                no_clasificados.append({"nombre": str(nombre_prod).strip()})
        
        col_tab1, col_tab2 = st.columns(2)
        with col_tab1:
            st.metric("Artículos Aprobados para el Catálogo", len(productos_clasificados))
            if productos_clasificados:
                df_previa = pd.DataFrame(productos_clasificados).sort_values(by=["id_subcat_interno", "nombre_catalogo"], ascending=[True, True]).reset_index(drop=True)
                df_previa.index = df_previa.index + 1
                df_previa.index.name = "N° de Ítem"
                st.dataframe(df_previa[["nombre_catalogo", "Pasillo / Departamento"]], use_container_width=True)
                
        with col_tab2:
            st.metric("Artículos Rechazados / Sin Clasificar", len(no_clasificados))
            if no_clasificados:
                df_omitidos = pd.DataFrame(no_clasificados).sort_values(by="nombre", ascending=True).reset_index(drop=True)
                df_omitidos.index = df_omitidos.index + 1
                df_omitidos.index.name = "N° de Ítem"
                st.dataframe(df_omitidos[["nombre"]], use_container_width=True)
            else:
                st.success("🎉 ¡Excelente! Cero artículos rechazados en este lote.")
        
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if productos_clasificados:
                if st.button("🚀 Confirmar y Guardar Registros en Catálogo Cloud", key="btn_enviar_catalogo_v430"):
                    with st.spinner("Inyectando registros en bloques de 50 hacia la tabla 'catalogo'..."):
                        TAMANO_LOTE, total_guardados, error_registrado = 50, 0, None
                        for i in range(0, len(productos_clasificados), TAMANO_LOTE):
                            lote_actual = productos_clasificados[i:i + TAMANO_LOTE]
                            try:
                                # Forzamos también el prefijo explícito en el insert para asegurar la ruta de inyección
                                payload = [{"nombre_catalogo": p["nombre_catalogo"], "id_subcat": p["id_subcat_interno"]} for p in lote_actual]
                                supabase.table("public.catalogo").insert(payload).execute()
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
                df_omitidos_down = pd.DataFrame(no_clasificados).sort_values(by="nombre", ascending=True).reset_index(drop=True)
                csv_omitidos = df_omitidos_down.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⚠️ Descargar Rechazados para revisión",
                    data=csv_omitidos,
                    file_name="productos_omitidos.csv",
                    mime="text/csv",
                    key="btn_descargar_omitidos_local_v430"
                )
                
# ##############################################################################
# BANNER INFERIOR: >>> CARGAR_INVENTARIO.PY - PARTE 3 DE 3 <<<
# ##############################################################################
