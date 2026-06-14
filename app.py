# ----------------------------------------
# SECCIÓN 3: MAESTRO DE DATOS
# ----------------------------------------
with tab_maestro:
    st.subheader("Visualizador de Tablas en Supabase")
    st.markdown("Monitorea el estado actual de tu base de datos en tiempo real.")
    
    tabla_seleccionada = st.selectbox(
        "Selecciona la tabla que deseas visualizar:",
        ["categorias", "subcategorias", "productos"]
    )
    
    if st.button("🔄 Refrescar datos de Supabase", key="btn_refrescar_maestro"):
        with st.spinner(f"Consultando registros de la tabla {tabla_seleccionada}..."):
            try:
                respuesta = supabase.table(tabla_seleccionada).select("*").execute()
                
                if respuesta.data:
                    df_resultado = pd.DataFrame(respuesta.data)
                    
                    if tabla_seleccionada == "productos" and "fecha_registro" in df_resultado.columns:
                        df_resultado["fecha_registro"] = pd.to_datetime(df_resultado["fecha_registro"]).dt.strftime('%Y-%m-%d %H:%M')
                    
                    st.metric(f"Total de registros en {tabla_seleccionada}", len(df_resultado))
                    st.dataframe(df_resultado, use_container_width=True)
                    
                    # Guardamos los datos en el estado de la sesión para habilitar la descarga
                    st.session_state["df_actual"] = df_resultado
                    st.session_state["tabla_actual"] = tabla_seleccionada
                else:
                    st.warning(f"La tabla {tabla_seleccionada} se encuentra actualmente vacía.")
                    if "df_actual" in st.session_state: del st.session_state["df_actual"]
            except Exception as e:
                st.error(f"Error al consultar la tabla {tabla_seleccionada} en Supabase: {e}")

    # Sub-módulo de Exportación a Excel (Aparece solo si hay datos consultados en pantalla)
    if "df_actual" in st.session_state and st.session_state["df_actual"] is not None:
        st.markdown("### 📥 Exportación Comercial")
        
        import io
        buffer_excel = io.BytesIO()
        
        # Convertimos el DataFrame a un archivo binario de Excel real en memoria RAM
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            st.session_state["df_actual"].to_excel(writer, index=False, sheet_name=st.session_state["tabla_actual"])
        
        data_excel = buffer_excel.getvalue()
        nombre_archivo = f"maestro_{st.session_state['tabla_actual']}.xlsx"
        
        # Botón nativo de descarga de archivos de Streamlit
        st.download_button(
            label=f"🟢 Descargar tabla {st.session_state['tabla_actual']} en formato Excel",
            data=data_excel,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
