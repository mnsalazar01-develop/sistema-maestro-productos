import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QListWidget, QLabel, QAbstractItemView)
from PyQt6.QtCore import Qt
from supabase import create_client, Client

# 🔑 EXTRACTOR AUTOMÁTICO DE CREDENCIALES DESDE TU ARCHIVO SECRETS LOCAL
def cargar_credenciales_secrets():
    # Construimos la ruta física hacia la carpeta oculta de tu entorno Streamlit
    ruta_secrets = os.path.join(".streamlit", "secrets.toml")
    url_cloud, key_cloud = None, None
    
    if os.path.exists(ruta_secrets):
        with open(ruta_secrets, "r", encoding="utf-8") as f:
            lineas = f.readlines()
            for linea in lineas:
                # Removemos comentarios accidentales y espacios en blanco
                linea_limpia = linea.split("#")[0].strip()
                if "url =" in linea_limpia.lower():
                    url_cloud = linea_limpia.split("=")[1].replace('"', '').replace("'", "").strip()
                if "key =" in linea_limpia.lower():
                    key_cloud = linea_limpia.split("=")[1].replace('"', '').replace("'", "").strip()
    return url_cloud, key_cloud

SUPABASE_URL, SUPABASE_KEY = cargar_credenciales_secrets()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error Crítico: No se pudo extraer la configuración de conexión desde .streamlit/secrets.toml")
    sys.exit(1)

# Inicializamos el cliente oficial sintonizado con el ADN relacional de internet
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ListaProductosArrastrable(QListWidget):
    """Una lista personalizada que permite arrastrar y soltar elementos de catálogo"""
    def __init__(self, categoria_destino=None, parent=None):
        super().__init__(parent)
        self.categoria_destino = categoria_destino
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # Extraemos de forma limpia el ID primario y la descripción del producto arrastrado
            datos = event.mimeData().text().split(" - ")
            id_catalogo_prod = datos[0]
            nombre_producto = " - ".join(datos[1:])
            
            try:
                # Si se soltó en una caja con ID relacional válido, actualizamos Supabase
                if self.categoria_destino is not None:
                    print(f"Moviendo relacionalmente: {nombre_producto} -> ID Subcategoría: {self.categoria_destino}")
                    
                    supabase.table("catalogo").update({
                        "id_enlace_subcat": int(self.categoria_destino)
                    }).eq("id_catalogo", int(id_catalogo_prod)).execute()
                    
                else:
                    # Si regresa a la lista izquierda, lo enviamos al bolsón de Víveres General (ID 12) como parachoques
                    supabase.table("catalogo").update({
                        "id_enlace_subcat": 12 
                    }).eq("id_catalogo", int(id_catalogo_prod)).execute()

                # Pintamos el elemento de forma visual en la nueva lista de destino
                self.addItem(f"{id_catalogo_prod} - {nombre_producto}")
                
                # Consolidamos el movimiento nativo dentro del hilo de interfaz de Qt
                event.setDropAction(Qt.DropAction.MoveAction)
                event.acceptProposedAction()
                super().dropEvent(event)
            except Exception as e_drop:
                print(f"❌ Error de persistencia en red al mover: {e_drop}")

class VentanaClasificadora(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clasificador Iterativo de Catálogo - Retail Venezuela (Secrets Sync)")
        self.resize(1200, 650)

        # Contenedor central hachado horizontalmente de alta densidad visual
        widget_central = QWidget()
        layout_principal = QHBoxLayout(widget_central)
        self.setCentralWidget(widget_central)

        # --- PANEL IZQUIERDO: PRODUCTOS CON CLASIFICACIÓN DE EMERGENCIA VÍVERES (ID 12) ---
        layout_izquierdo = QVBoxLayout()
        layout_izquierdo.addWidget(QLabel("📋 Artículos en Depósito General (Víveres ID 12) - Mover para refinar:"))
        
        self.lista_pendientes = ListaProductosArrastrable(categoria_destino=None)
        layout_izquierdo.addWidget(self.lista_pendientes)
        layout_principal.addLayout(layout_izquierdo, stretch=1)

        # --- PANEL DERECHO: SUBCATEGORIAS REALES DE TU ARBOL DE PRODUCCIÓN (DESTINOS) ---
        layout_derecho = QVBoxLayout()
        layout_derecho.addWidget(QLabel("📥 Arrastra los productos aquí para reclasificar en caliente:"))

        layout_categorias = QHBoxLayout()

        # Mapeo estricto emparejado con los IDs BigInt reales de tu base de datos cloud
        self.categorias_config = [
            ("🥩 Carnicería", 1),
            ("🧀 Charcutería", 2),
            ("🫓 Harinas y Pastas", 9),
            ("🫖 Desayuno y Snacks", 16)
        ]

        self.listas_destino = {}

        for titulo, id_subcat_real in self.categorias_config:
            columna = QVBoxLayout()
            columna.addWidget(QLabel(titulo))
            
            lista_destino = ListaProductosArrastrable(categoria_destino=id_subcat_real)
            columna.addWidget(lista_destino)
            layout_categorias.addLayout(columna)
            
            self.listas_destino[id_subcat_real] = lista_destino

        layout_derecho.addLayout(layout_categorias)
        layout_principal.addLayout(layout_derecho, stretch=3)

        self.cargar_datos_supabase()

    def cargar_datos_supabase(self):
        """Descarga el estado de consistencia actual de tu tabla relacional catalogo"""
        print("Conectando con Supabase Cloud mediante Secrets...")
        try:
            # 1. Poblamos la lista izquierda trayendo los productos en el bolsón general de Víveres (ID 12)
            res_pendientes = supabase.table("catalogo").select("id_catalogo, nombre_catalogo").eq("id_enlace_subcat", 12).execute()
            for prod in res_pendientes.data:
                self.lista_pendientes.addItem(f"{prod['id_catalogo']} - {prod['nombre_catalogo']}")

            # 2. Poblamos las cajas de la derecha descargando los productos ya refinados en internet
            for _, id_subcat_real in self.categorias_config:
                res_clasificados = supabase.table("catalogo").select("id_catalogo, nombre_catalogo").eq("id_enlace_subcat", id_subcat_real).execute()
                for prod in res_clasificados.data:
                    self.listas_destino[id_subcat_real].addItem(f"{prod['id_catalogo']} - {prod['nombre_catalogo']}")
        except Exception as e_load:
            print(f"❌ Error al inicializar datos desde la API cloud: {e_load}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaClasificadora()
    ventana.show()
    sys.exit(app.exec())
