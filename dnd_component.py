import os
import streamlit.components.v1 as components

# Resuelve la ruta al frontend/ RELATIVA a este archivo.
# Funciona desde CUALQUIER carpeta: pages/, pages/maquetacion/, src/, etc.
# Solo requisito: la carpeta frontend/ debe estar AL LADO de este archivo.
_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(_dir, "frontend")

# Declara el componente UNA VEZ. Las páginas lo importan.
dnd_maquetador = components.declare_component("dnd_maquetador", path=build_dir)
