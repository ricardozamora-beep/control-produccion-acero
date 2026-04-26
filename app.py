import streamlit as st
import pandas as pd
from datetime import datetime

def main():
    st.title("Gestión de Producción - Planta de Barras")

    # 1. Carga de Catálogo (Punto de partida)
    archivo_catalogo = st.file_uploader("Subir archivo de Catálogo de Productos", type=['csv', 'xlsx'])

    if archivo_catalogo:
        st.success("Catálogo cargado exitosamente.")
        
        # 2. Selección de Fecha de Inicio (Aparece solo después de subir el catálogo)
        fecha_inicio = st.date_input("Seleccionar fecha de inicio de producción", datetime.now())
        
        st.divider()
        
        # 3. Configuración de Lotes / Cantidades
        st.subheader("Configuración de Carga")
        
        # Uso de un valor por defecto o cargado desde el catálogo
        # El step de 500 kg aplicado a los botones +/-
        cantidad_kg = st.number_input(
            "Cantidad a producir (kg)", 
            min_value=0, 
            value=1000, 
            step=500
        )
        
        st.info(f"Incremento ajustado a: 500 kg. Total actual: {cantidad_kg} kg")

        # 4. Lógica de Turnos (24h)
        st.subheader("Planificación de Turnos")
        st.write("Configuración: 3 turnos de 8 horas (Iniciando Domingo Noche)")
        
        # Aquí iría la lógica de procesamiento de datos con Pandas
        # ...
        
        if st.button("Generar Programa de Producción"):
            st.write(f"Programa generado para el {fecha_inicio} con un lote de {cantidad_kg} kg.")
            # Lógica para exportar a Excel / CSV

if __name__ == "__main__":
    main()
