# ==============================================================================
# PROGRAMA: app.py (PARTE A DE C)
# VERSIÓN: 1.8.0
# DESCRIPCIÓN: Sistema Maestro de Clasificación de Productos Genéricos Retail
# MODIFICACIÓN: Distribución oficial balanceada en 3 bloques continuos.
# ==============================================================================

import streamlit as st
import pandas as pd
import io
from supabase import create_client, Client

# Configuración de la ventana web de Streamlit
st.set_page_config(
    page_title="Sistema Maestro de Productos", 
    page_icon="📦",
    layout="wide"
)

# ========================================
# RF-01: CONEXIÓN A BASE DE DATOS CACHEADA
# ========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Inicializar la conexión global de Supabase
try:
    supabase = init_supabase()
    st.sidebar.success("⚡ Conectado a Supabase Cloud")
except Exception as e:
    st.sidebar.error(f"❌ Error de conexión: {e}")

# ========================================
# ARQUITECTURA DEL MENÚ (Mediante Pestañas)
# ========================================
st.title("📦 Sistema Maestro de Clasificación de Productos")
st.markdown("Bienvenido al centro operativo de taxonomía retail.")

# Creamos las 4 secciones del menú en la parte superior de la pantalla
tab_inicio, tab_carga, tab_maestro, tab_reglas = st.tabs([
    "🏠 Inicio", 
    "📤 Cargar Inventario", 
    "📊 Maestro de Datos",
    "⚙️ Mantenedor de Reglas"
])

# ----------------------------------------
# SECCIÓN 1: INICIO
# ----------------------------------------
with tab_inicio:
    st.subheader("Panel de Bienvenida")
    st.markdown("""
    Esta aplicación web te permite estructurar tu catálogo de productos en bruto bajo el estándar de la industria.
    
    ### Tus 3 Pilares de Datos Activos:
    1. **Categorías (Nivel 1)**: Los 7 pasillos principales sembrados en Supabase.
    2. **Subcategorías (Nivel 3/4)**: Tus familias de competencia directa ya cargadas.
    3. **Productos (Nivel 5)**: Tu nueva propuesta de genéricos puros.
    """)
    st.info("Haz clic en la pestaña 'Cargar Inventario' de arriba para empezar a procesar tu archivo Excel.")
# ----------------------------------------
# SECCIÓN 2: CARGAR INVENTARIO (PARTE 1 DE 2)
# ----------------------------------------
with tab_carga:
    st.subheader("Procesador de Archivos en Bruto")
    st.markdown("Sube tu archivo plano o CSV con la columna `nombre` para clasificarlo automáticamente mediante la matriz paramétrica de Supabase.")

    # El diccionario de reglas base expandido masivamente (Estrategia de respaldo local)
    DICCIONARIO_REGLAS = {
        # 1. Alimentos Frescos
        "carne": 1, "res ": 1, "bistec": 1, "molida": 1, "pollo": 1, "pechuga": 1, "cerdo": 1, # Carnicería
        "charc": 2, "jamon": 2, "jamón": 2, "mortad": 2, "salchic": 2, "tocin": 2,            # Charcutería
        "frut": 3, "manzan": 3, "cambur": 3, "naranj": 3, "fresa": 3,                           # Frutería
        "verdu": 4, "papa ": 4, "ceboll": 4, "tomate": 4, "zanah": 4, "aliño": 4,               # Verdulería
        "pesca": 5, "camar": 5, "marisc": 5, "merlu": 5,                                       # Pescadería
        "pan ": 6, "baguet": 6, "canill": 6, "acem": 6,                                        # Panadería
        "tort": 7, "pastg": 7, "ponqu": 7, "hojald": 7,                                        # Pastelería

		# 2. Víveres (Despensa)
        "gran": 8, "arroz": 8, "frijol": 8, "caraota": 8, "lenteja": 8, "cafe": 8, "café": 8,   # Granos
        "harin": 9, "fororo": 9, "maicena": 9, "pasta": 9, "espagu": 9, "fideo": 9,            # Harinas y Pastas
        "aceit": 10, "oliva": 10,                                                               # Aceites Comestibles
        "mantec": 11, "margar": 11, "manteq": 11,                                               # Grasas
        "atun": 12, "atún": 12, "sardin": 12, "pepito": 12,                                     # Enlatados
        "mermel": 13, "conserv": 13,                                                            # Conservas
        "mayon": 14, "salsa": 14, "ketchup": 14, "mostaz": 14,                                  # Salsas y Aderezos
        "sal ": 15, "pimient": 15, "condim": 15, "orég": 15,                                    # Condimentos
        "avena": 16, "cereal": 16, "corn": 16, "azucar": 16, "azúcar": 16,                       # Desayuno y Azúcar

		# 3. Refrigerados y Congelados
        "lech": 17, "queso": 17, "crema": 17, "lact": 17,                                       # Lácteos y Leches
        "yog": 18, "yogu": 18,                                                                  # Yogures
        "nugget": 19, "papas cong": 19,                                                         # Comidas Preparadas
        "brocol cong": 20,                                                                      # Vegetales Congelados
        "helad": 21, "palet": 21,                                                               # Helados

		# 4. Bebidas y Bodegón
        "agua": 22, "mineral": 22,                                                              # Agua
        "jugo": 23, "nectar": 23,                                                               # Jugos
        "refres": 24, "soda": 24, "cola": 24,                                                   # Refrescos
        "energ": 25, "red bull": 25,                                                           # Bebidas Energéticas
        "ron ": 26, "caciqu": 26,                                                               # Ron
        "cerve": 27, "frías": 27,                                                               # Cerveza
        "vino": 28, "tinto": 28,                                                                # Vino
        "whis": 29, "bucan": 29,                                                                # Whisky

		# 5. Cuidado Personal e Higiene
        "jabon": 30, "jabón": 30,                                                               # Jabón
        "shamp": 31, "champ": 31, "acondic": 31,                                                # Champú
        "desod": 32, "axila": 32,                                                               # Desodorante
        "crema dent": 33, "pasta dent": 33, "colgat": 33,                                       # Cream Dental
        "papel hig": 34, "toilet": 34, "servill": 34,                                           # Papel Higiénico
        "maquill": 35, "labial": 35,                                                            # Maquillaje

		# 6. Cuidado del Hogar y Limpieza
        "deterg": 36, "ace ": 36, "ariel": 36,                                                  # Detergentes
        "suaviz": 37, "downy": 37,                                                              # Suavizantes
        "limpia": 38, "cloro": 38,                                                              # Limpiadores
        "desinf": 39, "lysol": 39,                                                              # Desinfectantes
        "lavap": 40, "axion": 40, "crema lava": 40,                                             # Lavaplatos

		# 7. Categorías Adicionales
        "mascot": 41, "perrar": 41, "gatar": 41,                                                # Mascotas
        "pañal": 42, "pamp": 42,                                                                # Pañales
        "formul": 43, "infant": 43,                                                             # Fórmulas Infantiles
        "ferret": 44, "tornill": 44, "clav": 44                                                 # Ferretería Ligera
    }
	# Componente visual para aceptar archivos planos CSV
	archivo_subido = st.file_uploader("Selecciona tu archivo plano .csv de productos", type=["csv"], key="uploader_v180")
	
	if archivo_subido:
		st.success("¡Archivo plano cargado con éxito en la memoria web!")
		
		# Extracción y mapeo posicional blindado de la tabla parametrizada
		subcategorias_vivas = {}
		try:
			res_reglas = supabase.table("matriz_diccionario_reglas").select("*").execute()
			if res_reglas and hasattr(res_reglas, 'data') and res_reglas.data:
				df_reglas_mapeo = pd.DataFrame(res_reglas.data)
				
				col_clave = [c for c in df_reglas_mapeo.columns if "clave" in c.lower() or c.lower() == "palabra_clave"]
				col_subcat = [c for c in df_reglas_mapeo.columns if "subcat" in c.lower() or "enlace" in c.lower()]
				
				for _, fila_r in df_reglas_mapeo.iterrows():
					token_clave = str(fila_r[col_clave]).lower().strip()
					id_destino = int(fila_r[col_subcat])
					subcategorias_vivas[token_clave] = id_destino
		except Exception as e:
			st.sidebar.warning("⚠️ Modo Inteligente pausado. Operando con diccionario base.")
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
			
			for idx, fila in df.iterrows():
				nombre_prod = fila['nombre']
				id_subcat = clasificar_texto_parametrizado(nombre_prod, subcategorias_vivas)
				
				if id_subcat:
					productos_clasificados.append({
						"nombre_producto": nombre_prod,
						"id_enlace_subcat": id_subcat
					})
				else:
					no_clasificados.append({"nombre": nombre_prod})
			
			col1, col2 = st.columns(2)
			with col1:
				st.metric("Productos Listos para Supabase", len(productos_clasificados))
				if productos_clasificados:
					st.dataframe(pd.DataFrame(productos_clasificados), use_container_width=True)
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
					with st.spinner("Inyectando registros en la base de datos..."):
						try:
							respuesta = supabase.table("productos").insert(productos_clasificados).execute()
							st.balloons()
							st.success(f"¡Éxito total! Se guardaron {len(productos_clasificados)} productos genéricos en Supabase.")
						except Exception as e:
							st.error(f"Error al guardar en Supabase: {e}")

# ----------------------------------------
# SECCIÓN 3: MAESTRO DE DATOS
# ----------------------------------------
with tab_maestro:
	st.subheader("Visualizador de Tablas en Supabase")
	st.markdown("Monitorea el estado actual de tu base de datos en tiempo real.")
	
	tabla_seleccionada = st.selectbox(
		"Selecciona la tabla que deseas visualizar:",
		["categorias", "subcategorias", "productos", "matriz_diccionario_reglas"],
		key="selector_tablas_v180"
	)
	
	if st.button("🔄 Refrescar datos de Supabase", key="btn_refrescar_maestro_v180"):
		with st.spinner(f"Consultando registros de la tabla {tabla_seleccionada}..."):
			try:
				respuesta = supabase.table(tabla_seleccionada).select("*").execute()
				
				if respuesta.data:
					df_resultado = pd.DataFrame(respuesta.data)
					
					if tabla_seleccionada == "productos" and "fecha_registro" in df_resultado.columns:
						df_resultado["fecha_registro"] = pd.to_datetime(df_resultado["fecha_registro"]).dt.strftime('%Y-%m-%d %H:%M')
					
					st.metric(f"Total de registros en {tabla_seleccionada}", len(df_resultado))
					st.dataframe(df_resultado, use_container_width=True)
					
					st.session_state["df_actual"] = df_resultado
					st.session_state["tabla_actual"] = tabla_seleccionada
				else:
					st.warning(f"La tabla {tabla_seleccionada} se encuentra actualmente vacía.")
					if "df_actual" in st.session_state: del st.session_state["df_actual"]
			except Exception as e:
				st.error(f"Error al consultar la tabla {tabla_seleccionada} en Supabase: {e}")

	# Sub-módulo de Exportación a Excel
	if "df_actual" in st.session_state and st.session_state["df_actual"] is not None:
		st.markdown("### 📥 Exportación Comercial")
		
		buffer_excel = io.BytesIO()
		with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
			st.session_state["df_actual"].to_excel(writer, index=False, sheet_name=st.session_state["tabla_actual"])
		
		data_excel = buffer_excel.getvalue()
		nombre_archivo = f"maestro_{st.session_state['tabla_actual']}.xlsx"
		
		st.download_button(
			label=f"🟢 Descargar tabla {st.session_state['tabla_actual']} en formato Excel",
			data=data_excel,
			file_name=nombre_archivo,
			mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
			key="btn_descargar_excel_v180"
		)

# ----------------------------------------
# SECCIÓN 4: MANTENEDOR DE REGLAS
# ----------------------------------------
with tab_reglas:
	st.subheader("⚙️ Panel de Control y Actualización de Reglas")
	st.markdown("Añade nuevas palabras clave en caliente para expandir el cerebro del clasificador sin tocar el código.")

	mapa_subcats_formulario = {}
	try:
		res_sub_form = supabase.table("subcategorias").select("*").execute()
		if res_sub_form and res_sub_form.data:
			df_sub_form = pd.DataFrame(res_sub_form.data)
			col_id_f = [c for c in df_sub_form.columns if "id" in c.lower() or c.lower() == "id_subcat"]
			col_nom_f = [c for c in df_sub_form.columns if "nombre" in c.lower() or c.lower() == "nombre_subcat"]
			
			for _, f_sub in df_sub_form.iterrows():
				label_combo = f"{f_sub.iloc[col_id_f[0]]} - {f_sub.iloc[col_nom_f[0]]}"
				mapa_subcats_formulario[label_combo] = int(f_sub.iloc[col_id_f[0]])
	except Exception as e:
		st.error(f"No se pudieron cargar las subcategorías para el formulario: {e}")

	if mapa_subcats_formulario:
		with st.form("formulario_nuevas_reglas", clear_on_submit=True):
			col_input1, col_input2 = st.columns(2)
			
			with col_input1:
				nueva_palabra = st.text_input("Nueva Palabra Clave / Token a buscar:", placeholder="Ej: melon, ceboll, bife").strip()
			
			with col_input2:
				subcat_seleccionada = st.selectbox("Asociar de forma estricta a la subcategoría:", list(mapa_subcats_formulario.keys()))
			
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
						supabase.table("matriz_diccionario_reglas").insert(registro_regla).execute()
						st.success(f"✅ ¡Éxito! La regla '{nueva_palabra.lower()}' fue enlazada al ID {id_subcat_destino} exitosamente.")
						st.info("💡 El clasificador asimiló el cambio. La próxima carga de archivo plano aplicarará la regla al instante.")
					except Exception as e:
						st.error(f"Error al guardar la regla en Supabase: {e}. Verifique si la palabra ya existe.")
