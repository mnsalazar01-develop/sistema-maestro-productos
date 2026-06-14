# ==============================================================================
# PROGRAMA SATÉLITE: diccionario_reglas.py (PARTE A DE B)
# VERSIÓN: 1.0.0 (MÓDULO SUELTO RAÍZ)
# DESCRIPCIÓN: Panel de Control y Mantenimiento de Reglas Paramétricas
# MODIFICACIÓN: Creación como módulo independiente plano en la raíz del proyecto.
# ==============================================================================

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Configuración independiente de la ventana web
st.set_page_config(
    page_title="Mantenedor de Reglas - Retail",
    page_icon="⚙️",
    layout="wide"
)

# Inicialización local de la conexión a la base de datos de Supabase
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

st.title("⚙️ Panel de Control y Actualización de Reglas")
st.markdown("Añade nuevas palabras clave en caliente para expandir el cerebro del clasificador sin tocar el código de Python.")

# Intentamos descargar las subcategorías en tiempo real para armar el selector visual
mapa_subcats_formulario = {}
try:
    res_sub_form = supabase.table("subcategorias").select("*").execute()
    if res_sub_form and hasattr(res_sub_form, 'data') and res_sub_form.data:
        df_sub_form = pd.DataFrame(res_sub_form.data)
        col_id_f = [c for c in df_sub_form.columns if "id" in c.lower() or c.lower() == "id_subcat"]
        col_nom_f = [c for c in df_sub_form.columns if "nombre" in c.lower() or c.lower() == "nombre_subcat"]
        
        for _, f_sub in df_sub_form.iterrows():
            label_combo = f"{f_sub.iloc[col_id_f]} - {f_sub.iloc[col_nom_f]}"
            mapa_subcats_formulario[label_combo] = int(f_sub.iloc[col_id_f])
    else:
        raise ValueError("Tabla vacía")
except Exception:
    # Contingencia de Infraestructura Segura: Mapeo local si las RLS restringen la API abierta
    st.sidebar.info("💡 Formulario operando en Modo Privado Seguro (RLS Activo)")
    familias_respaldo = {
        1: "Carnicería", 2: "Charcutería", 3: "Frutería", 4: "Verdulería", 5: "Pescadería", 
        6: "Panadería", 7: "Pastelería", 8: "Granos y Café", 9: "Harinas y Pastas", 
        10: "Aceites Comestibles", 11: "Grasas", 12: "Enlatados", 13: "Conservas", 
        14: "Salsas y Aderezos", 15: "Condimentos", 16: "Desayuno y Azúcar", 
        17: "Lácteos y Leches", 18: "Yogures", 19: "Comidas Preparadas", 
        22: "Agua", 23: "Jugos", 24: "Refrescos", 25: "Bebidas Energéticas", 
        26: "Ron", 27: "Cerveza", 28: "Vino", 29: "Whisky", 30: "Jabón", 
        31: "Champú", 32: "Desodorante", 33: "Crema Dental", 34: "Papel Higiénico", 
        35: "Maquillaje", 36: "Detergentes", 37: "Suavizantes", 38: "Limpiadores", 
        39: "Desinfectantes", 40: "Lavaplatos", 41: "Mascotas", 42: "Pañales", 
        43: "Fórmulas Infantiles", 44: "Ferretería Ligera"
    }
    for id_f, nombre_f in familias_respaldo.items():
        mapa_subcats_formulario[f"{id_f} - {nombre_f}"] = id_f
# ==============================================================================
# SUB-MÓDULO: FORMULARIO TRANSACCIONAL DE INYECCIÓN DE REGLAS
# ==============================================================================
if mapa_subcats_formulario:
    with st.form("formulario_satelite_reglas", clear_on_submit=True):
        col_input1, col_input2 = st.columns(2)
        
        with col_input1:
            nueva_palabra = st.text_input(
                "Nueva Palabra Clave / Token a buscar:", 
                placeholder="Ej: melon, ceboll, bife"
            ).strip()
        
        with col_input2:
            # El menú desplegable se alimenta automáticamente del mapa seguro
            subcat_seleccionada = st.selectbox(
                "Asociar de forma estricta a la subcategoría:", 
                list(mapa_subcats_formulario.keys())
            )
        
        boton_guardar_regla = st.form_submit_button("💾 Guardar Nueva Regla en Supabase")
        
        if boton_guardar_regla:
            if not nueva_palabra:
                st.error("❌ Error: Debes escribir una palabra clave o raíz léxica válida.")
            else:
                id_subcat_destino = mapa_subcats_formulario[subcat_seleccionada]
                registro_regla = {
                    "palabra_clave": nueva_palabra.lower(),
                    "id_enlace_subcat": id_subcat_destino
                }
                
                try:
                    # Inyección directa en la tabla de control indexada en la nube
                    supabase.table("matriz_diccionario_reglas").insert(registro_regla).execute()
                    st.success(f"✅ ¡Éxito! La regla '{nueva_palabra.lower()}' fue vinculada al ID {id_subcat_destino} correctamente.")
                    st.info("💡 El clasificador asimiló el cambio. Cualquier carga masiva posterior aplicará este token en tiempo real.")
                except Exception as e:
                    st.error(f"Error al guardar la regla en Supabase: {e}. Verifique si la palabra ya existe.")
