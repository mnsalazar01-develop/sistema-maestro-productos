# ==============================================================================
# PROGRAMA SATÉLITE: maestro_datos.py (BLOQUE ÚNICO COMPLETO)
# VERSIÓN: 1.0.0 (INTEGRACIÓN TAXONOMÍA REAL VENEZUELA)
# DESCRIPCIÓN: Libro Maestro de Existencias - Visualizador y Extractor Comercial
# MODIFICACIÓN: Conexión estricta a 'catalogo' con pasillos textuales en espejo.
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# 1. CONFIGURACIÓN CORPORATIVA DE LA VENTANA WEB DE PRODUCCIÓN
st.set_page_config(
    page_title="Libro Maestro de Existencias",
    page_icon="📊",
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

st.title("📊 Libro Maestro de Existencias")
st.markdown("Auditoría visual en tiempo real de los artículos almacenados en el catálogo central.")
st.markdown("---")

# 3. MÁSCARA DE TRADUCCIÓN LOCAL: GLOSARIO DE PASILLOS EN ESPEJO EXACTO CON EL CARGADOR
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

with st.spinner("Descargando registros desde la nube..."):
    try:
        # Consultamos directamente tu tabla física real 'catalogo'
        res_maestro = supabase.table("catalogo").select("nombre_catalogo, id_subcat").execute()
        
        if res_maestro and hasattr(res_maestro, 'data') and res_maestro.data:
            registros_raw = res_maestro.data
            
            # Mapeamos los datos crudos aplicando la máscara de traducción caribeña
            registros_procesados = []
            for r in registros_raw:
                id_num = r.get("id_subcat", 0)
                nombre_pasillo = MAPA_PASILLOS_VENEZUELA.get(id_num, f"Familia {id_num}")
                registros_procesados.append({
                    "Descripción del Artículo": r.get("nombre_catalogo", "SIN NOMBRE"),
                    "Pasillo / Departamento": nombre_pasillo,
                    "id_subcat_interno": id_num
                })
            
            df_maestro = pd.DataFrame(registros_procesados)
            
            # ORDENAMIENTO DE AUDITURÍA: Secuencial por ID de Pasillo + Alfabético interno de la A a la Z
            df_maestro = df_maestro.sort_values(by=["id_subcat_interno", "Descripción del Artículo"], ascending=[True, True]).reset_index(drop=True)
            
            # 4. RENDERIZADO DE ALTA DENSIDAD INICIANDO EL CONTEO EN 1
            df_maestro.index = df_maestro.index + 1
            df_maestro.index.name = "N° de Ítem"
            
            st.metric("Total de Artículos Consolidados en Nube", len(df_maestro))
            
            # Mostramos en pantalla únicamente las columnas comerciales limpias para el ojo humano
            st.dataframe(df_maestro[["Descripción del Artículo", "Pasillo / Departamento"]], use_container_width=True)
            
            # 5. EXTRACTOR BINARIO COMERCIAL (DESCARGA DIRECTA A EXCEL CLEAN)
            st.markdown("---")
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                # El archivo de Excel se genera con la ordenación relacional y el conteo humano
                df_maestro[["Descripción del Artículo", "Pasillo / Departamento"]].to_excel(writer, sheet_name="Existencias_Nivel_5", index=True)
            
            st.download_button(
                label="📥 Exportar Libro Maestro a Formato Excel (.xlsx)",
                data=buffer_excel.getvalue(),
                file_name="libro_maestro_existencias.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_descargar_excel_maestro"
            )
        else:
            st.warning("⚠️ El Libro Maestro se encuentra vacío. No hay registros clasificados en la tabla 'catalogo'.")
            
    except Exception as e_maestro:
        st.error(f"❌ Error de comunicación con la base de datos: {e_maestro}")
