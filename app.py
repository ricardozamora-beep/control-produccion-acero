import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def generar_calendario_turnos(fecha_inicio, total_kg, capacidad_por_hora=500):
    """
    Calcula la distribución de carga en 3 turnos de 8h.
    Turno 3 (Noche): 22:00 - 06:00 (Inicia el domingo)
    Turno 1 (Mañana): 06:00 - 14:00
    Turno 2 (Tarde): 14:00 - 22:00
    """
    horas_necesarias = total_kg / capacidad_por_hora
    lineas_programa = []
    
    # El ciclo inicia el domingo a las 22:00
    momento_actual = datetime.combine(fecha_inicio, datetime.min.time()) + timedelta(hours=22)
    horas_restantes = horas_necesarias
    
    while horas_restantes > 0:
        hora = momento_actual.hour
        
        # Identificación de turnos
        if 6 <= hora < 14:
            nombre_turno = "Turno 1 (Mañana)"
        elif 14 <= hora < 22:
            nombre_turno = "Turno 2 (Tarde)"
        else:
            nombre_turno = "Turno 3 (Noche)"
            
        # Cálculo de horas por bloque
        horas_en_este_turno = min(8, horas_restantes)
        
        lineas_programa.append({
            "Fecha": momento_actual.strftime("%d/%m/%Y"),
            "Turno": nombre_turno,
            "Producción Planificada (kg)": int(horas_en_este_turno * capacidad_por_hora),
            "Hora Inicio": momento_actual.strftime("%H:%M"),
        })
        
        horas_restantes -= horas_en_este_turno
        momento_actual += timedelta(hours=8)
        
    return pd.DataFrame(lineas_programa)

# --- INTERFAZ DE STREAMLIT ---
st.set_page_config(page_title="Programador Planta de Barras", layout="wide")
st.title("🏭 Programación de Producción - Planta de Barras")

# 1. Carga de Catálogo
archivo_catalogo = st.file_uploader("1. Subir archivo de Catálogo", type=['csv', 'xlsx'])

if archivo_catalogo:
    st.success("Catálogo cargado.")
    
    # 2. Selección de Fecha (Habilitada tras catálogo)
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("2. Fecha de inicio (Domingo)", datetime.now())
    
    with col2:
        # Ajuste de cantidad con paso de 500kg
        cantidad_kg = st.number_input(
            "3. Cantidad Total a Producir (kg)", 
            min_value=0, 
            value=1000, 
            step=500
        )

    st.divider()

    # 3. Generar Programa
    if st.button("Generar Programa de Turnos"):
        df_resultado = generar_calendario_turnos(fecha_inicio, cantidad_kg)
        
        st.subheader(f"Calendario de Producción - Lote: {cantidad_kg} kg")
        st.dataframe(df_resultado, use_container_width=True)
        
        # Opción para descargar
        csv = df_resultado.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar Programa (CSV)",
            csv,
            "programa_produccion.csv",
            "text/csv"
        )
