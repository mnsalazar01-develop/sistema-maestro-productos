import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA DE STREAMLIT
st.set_page_config(
    page_title="Inicializador Batch - Retail",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

st.title("⚡ Inicializador por Lote - Estructura de Subcategorías")
st.markdown("Consola técnica de saneamiento profundo para vaciar residuos y re-sembrar el árbol unificado del 1 al 46.")
st.markdown("---")

# 3. DICCIONARIO SEMILLA UNIFICADO (FUSIÓN SERVILLETAS ID 34 - EXTINCIÓN ID 53)
SEMILLA_SUBCATEGORIAS = [
    {"id_subcat": 1, "id_enlace_cat": 1, "nombre_subcat": "🥩 Carnicería / Frigorífico"},
    {"id_subcat": 2, "id_enlace_cat": 1, "nombre_subcat": "🧀 Charcutería y Delicateses"},
    {"id_subcat": 3, "id_enlace_cat": 1, "nombre_subcat": "🍎 Frutería"},
    {"id_subcat": 4, "id_enlace_cat": 1, "nombre_subcat": "🥦 Verdulería / Legumbres Frescas"},
    {"id_subcat": 5, "id_enlace_cat": 1, "nombre_subcat": "🐟 Pescadería Fresca"},
    {"id_subcat": 6, "id_enlace_cat": 1, "nombre_subcat": "🥖 Panadería"},
    {"id_subcat": 7, "id_enlace_cat": 1, "nombre_subcat": "🍰 Pastelería y Repostería"},
    {"id_subcat": 8, "id_enlace_cat": 2, "nombre_subcat": "🌾 Granos, Legumbres y Café"},
    {"id_subcat": 9, "id_enlace_cat": 2, "nombre_subcat": "🫓 Harinas, Pastas y Almidones"},
    {"id_subcat": 10, "id_enlace_cat": 2, "nombre_subcat": "🛢️ Aceites Comestibles"},
    {"id_subcat": 11, "id_enlace_cat": 2, "nombre_subcat": "🧈 Grasas y Margarinas"},
    {"id_subcat": 12, "id_enlace_cat": 2, "nombre_subcat": "🥫 Víveres y Enlatados"},
    {"id_subcat": 13, "id_enlace_cat": 2, "nombre_subcat": "🍓 Conservas y Dulcería"},
    {"id_subcat": 14, "id_enlace_cat": 2, "nombre_subcat": "🍯 Salsas y Aderezos"},
    {"id_subcat": 15, "id_enlace_cat": 2, "nombre_subcat": "🧂 Condimentos y Especias"},
    {"id_subcat": 16, "id_enlace_cat": 2, "nombre_subcat": "🫖 Desayuno, Golosinas y Snacks"},
    {"id_subcat": 17, "id_enlace_cat": 3, "nombre_subcat": "🥛 Lácteos y Leches Líquidas"},
    {"id_subcat": 18, "id_enlace_cat": 3, "nombre_subcat": "🍧 Yogures y Derivados"},
    {"id_subcat": 19, "id_enlace_cat": 3, "nombre_subcat": "🍕 Comidas Preparadas y Congelados"},
    {"id_subcat": 20, "id_enlace_cat": 3, "nombre_subcat": "🥦 Vegetales Congelados"},
    {"id_subcat": 21, "id_enlace_cat": 3, "nombre_subcat": "🍦 Helados y Paletas"},
    {"id_subcat": 22, "id_enlace_cat": 4, "nombre_subcat": "💧 Agua Mineral y Sifones"},
    {"id_subcat": 23, "id_enlace_cat": 4, "nombre_subcat": "🧃 Bebidas, Jugos y Néctares"},
    {"id_subcat": 24, "id_enlace_cat": 4, "nombre_subcat": "🥤 Refrescos y Sodas Carbonatadas"},
    {"id_subcat": 25, "id_enlace_cat": 4, "nombre_subcat": "⚡ Bebidas Energéticas"},
    {"id_subcat": 26, "id_enlace_cat": 4, "nombre_subcat": "🥃 Ron y Licores Nacionales"},
    {"id_subcat": 27, "id_enlace_cat": 4, "nombre_subcat": "🍺 Cervezas y Maltas"},
    {"id_subcat": 28, "id_enlace_cat": 4, "nombre_subcat": "🍷 Vinos de Mesa"},
    {"id_subcat": 29, "id_enlace_cat": 4, "nombre_subcat": "🍾 Whisky y Destilados"},
    {"id_subcat": 30, "id_enlace_cat": 5, "nombre_subcat": "🧼 Jabón de Baño y Tocador"},
    {"id_subcat": 31, "id_enlace_cat": 5, "nombre_subcat": "🧴 Champú y Acondicionadores"},
    {"id_subcat": 32, "id_enlace_cat": 5, "nombre_subcat": "🪒 Desodorantes y Aseo Personal"},
    {"id_subcat": 33, "id_enlace_cat": 5, "nombre_subcat": "🪥 Crema y Pasta Dental"},
    {"id_subcat": 34, "id_enlace_cat": 5, "nombre_subcat": "🧻 Papel Higiénico, Servilletas y Pañuelos"},
    {"id_subcat": 35, "id_enlace_cat": 5, "nombre_subcat": "💄 Maquillaje y Cosméticos"},
    {"id_subcat": 36, "id_enlace_cat": 5, "nombre_subcat": "🧴 Cuidado de la Piel"},
    {"id_subcat": 37, "id_enlace_cat": 6, "nombre_subcat": "🧺 Detergentes y Jabón de Lavar"},
    {"id_subcat": 38, "id_enlace_cat": 6, "nombre_subcat": "🌸 Suavizantes de Ropa"},
    {"id_subcat": 39, "id_enlace_cat": 6, "nombre_subcat": "🧹 Limpiadores y Desengrasantes"},
    {"id_subcat": 40, "id_enlace_cat": 6, "nombre_subcat": "🧪 Desinfectantes y Cloro"},
    {"id_subcat": 41, "id_enlace_cat": 6, "nombre_subcat": "🧽 Lavaplatos Líquidos y en Crema"},
    {"id_subcat": 42, "id_enlace_cat": 7, "nombre_subcat": "🐕 Alimentos para Mascotas"},
    {"id_subcat": 43, "id_enlace_cat": 7, "nombre_subcat": "👶 Pañales Infantiles"},
    {"id_subcat": 44, "id_enlace_cat": 7, "nombre_subcat": "🍼 Fórmulas Infantiles"},
    {"id_subcat": 45, "id_enlace_cat": 7, "nombre_subcat": "💊 Farmacia / Medicamentos"},
    {"id_subcat": 46, "id_enlace_cat": 7, "nombre_subcat": "🛠️ Ferretería Ligera y Eléctricos"}
]

st.markdown("### 📋 Vista Previa de la Semilla Relacional (Estándar Unificado)")
df_preview = pd.DataFrame(SEMILLA_SUBCATEGORIAS)
df_preview.index = df_preview.index + 1
df_preview.index.name = "N°"
st.dataframe(df_preview.rename(columns={"id_subcat": "ID Destino", "id_enlace_cat": "ID Categoría", "nombre_subcat": "Nombre de Subcategoría"}), use_container_width=True)

st.warning("⚠️ ¡ADVERTENCIA CRÍTICA DE INFRAESTRUCTURA! Presionar el botón inferior ejecutará una purga atómica en cascada. Se borrarán todas las subcategorías desfasadas del servidor (incluyendo el ID 53) y se re-sembrará esta lista exacta.")

# Campo de confirmación manual para evitar ejecuciones accidentales
confirmacion = st.checkbox("Entiendo los riesgos y confirmo que la casa se pondrá en orden de forma inmutable [CN1].")

if st.button("🚀 Ejecutar Limpieza y Siembra por Lote", disabled=not confirmacion):
    with st.spinner("Procesando la purga relacional en caliente..."):
        try:
            # PASO 1: Vaciado seguro en cascada mediante la API externa (Freno a residuos de Producción)
            supabase.table("matriz_diccionario_reglas").delete().neq("id_enlace_subcat", 0).execute()
            supabase.table("catalogo").delete().neq("id_enlace_subcat", 0).execute()
            supabase.table("subcategorias").delete().neq("id_subcat", 0).execute()
            st.info("🗑️ Fase 1 Concluida: Tablas hijo e infraestructura de pasillos vaciada con éxito.")
            
            # PASO 2: Inyección atómica masiva del bulto unificado desde la memoria RAM del script
            supabase.table("subcategorias").insert(SEMILLA_SUBCATEGORIAS).execute()
            
            # PASO 3: Corrientazo de refrescamiento síncrono
            supabase.rpc("pgrst_watch").execute() if hasattr(supabase, 'rpc') else None
            
            st.balloons()
            st.success("🎉 ¡Felicidades! La casa está oficialmente en orden. Se inyectaron las 46 subcategorías de forma contigua en internet.")
            st.info("💡 El entorno cloud está sincronizado con la lógica de tu cargador masivo. Puedes regresar a tus operaciones habituales.")
        except Exception as e_batch:
            st.error(f"❌ Error durante el despliegue batch: {e_batch}")
            st.markdown("""
            ### 💡 Nota de Soporte:
            Si el comando de borrado es bloqueado, asegúrate de que tus tablas de Supabase no posean filas bloqueadas por políticas RLS restrictivas de escritura o restricciones de llaves foráneas externas no contempladas en este módulo satélite [5.1].
            """)
