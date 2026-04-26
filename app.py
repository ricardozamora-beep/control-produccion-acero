import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def generar_programa_detallado(fecha_inicio, hora_inicio, lista_productos, tiempo_cambio, paradas, mantenimientos):
    programa = []
    # Combinar fecha y hora de inicio
    momento_actual = datetime.combine(fecha_inicio, hora_inicio)
    
    for prod in lista_productos:
        nombre = prod['nombre']
        tonelaje = prod['tonelaje']
        capacidad = prod['capacidad'] # kg/h
        
        # 1. Aplicar Tiempo de Cambio (Set-up)
        if tiempo_cambio > 0:
            programa.append({
                "Fecha": momento_actual.strftime("%d/%m/%Y"),
                "Turno": calcular_nombre_turno(momento_actual),
                "Actividad": f"SET-UP: {nombre}",
                "Detalle": f"Cambio de formato ({tiempo_cambio} min)",
                "Inicio": momento_actual.strftime("%H:%M"),
            })
            momento_actual += timedelta(minutes=tiempo_cambio)

        # 2. Calcular producción
        horas_necesarias = tonelaje / capacidad
        horas_restantes = horas_necesarias
        
        while horas_restantes > 0:
            # Verificar si el momento actual cae en una PARADA o MANTENIMIENTO
            dia_actual = momento_actual.date()
            
            # Si es día libre
            if dia_actual in paradas:
                momento_actual = datetime.combine(dia_actual + timedelta(days=1), datetime.min.time() + timedelta(hours=6))
                continue
            
            # Si hay mantenimiento programado (simplificado a bloque de horas)
            # Aquí podrías añadir lógica más específica de horas de mantenimiento
            
            # Definir bloque de turno actual
            nombre_turno = calcular_nombre_turno(momento_actual)
            horas_hasta_fin_turno = calcular_horas_fin_turno(momento_actual)
            
            tiempo_a_producir = min(horas_restantes, horas_hasta_fin_turno)
            
            programa.append({
                "Fecha": momento_actual.strftime("%d/%m/%Y"),
                "Turno": nombre_turno,
                "Actividad": f"PRODUCCIÓN: {nombre}",
                "Detalle": f"{int(tiempo_a_producir * capacidad)} kg",
                "Inicio": momento_actual.strftime("%H:%M"),
            })
            
            horas_restantes -= tiempo_a_producir
            momento_actual += timedelta(hours=tiempo_a_producir)

    return pd.DataFrame(programa)

def calcular_nombre_turno(dt):
    hora = dt.hour
    if 6 <= hora < 14: return "Turno 1 (Mañana)"
    elif 14 <= hora < 22: return "Turno 2 (Tarde)"
    else: return "Turno 3 (Noche)"

def calcular_horas_fin_turno(dt):
    hora = dt.hour
    if 6 <= hora < 14: limite = 14
    elif 14 <= hora < 22: limite = 22
    else: limite = 6 if hora < 6 else 30 # Caso especial trasnoche
    
    prox_cambio = dt.replace(hour=limite % 24, minute=0, second=0)
    if limite >= 24 or (limite == 6 and hora >= 22):
        prox_cambio += timedelta(days=1)
    
    return (prox_cambio - dt).total_seconds() / 3600

# --- INTERFAZ STREAMLIT ---
st.set_page_config(layout="wide")
st.title("⚙️ Programador de Planta Avanzado")

# Sidebar para Configuración Global
with st.sidebar:
    st.header("Configuración de Planta")
    tiempo_cambio = st.number_input("Tiempo de cambio entre productos (min)", value=30, step=15)
    
    st.subheader("Días Libres / Feriados")
    dias_libres = st.multiselect("Seleccione días que no se trabaja", 
                                 pd.date_range(start=datetime.now(), periods=30),
                                 format_func=lambda x: x.strftime("%d/%m"))
    
    st.subheader("Mantenimiento Programado")
    fecha_manto = st.date_input("Día de mantenimiento")
    horas_manto = st.slider("Duración mantenimiento (horas)", 1, 24, 4)

# Cuerpo Principal
col_a, col_b = st.columns(2)
with col_a:
    fecha_inicio = st.date_input("Fecha de Inicio de Producción", datetime.now())
with col_b:
    hora_inicio = st.time_input("Hora de Inicio", datetime.strptime("22:00", "%H:%M").time())

# Gestión de Productos (Dinámica)
st.subheader("Lista de Productos a Producir")
if 'productos' not in st.session_state:
    st.session_state.productos = []

with st.form("form_prod"):
    c1, c2, c3 = st.columns(3)
    p_nombre = c1.text_input("Producto")
    p_ton = c2.number_input("Tonelaje (kg)", step=500)
    p_cap = c3.number_input("Capacidad Planta (kg/h)", value=500)
    if st.form_submit_button("Añadir a la cola"):
        st.session_state.productos.append({"nombre": p_nombre, "tonelaje": p_ton, "capacidad": p_cap})

if st.session_state.productos:
    st.write("Cola de producción actual:")
    st.table(st.session_state.productos)
    
    if st.button("GENERAR PROGRAMA COMPLETO"):
        res = generar_programa_detallado(fecha_inicio, hora_inicio, st.session_state.productos, tiempo_cambio, dias_libres, None)
        st.dataframe(res, use_container_width=True)
        
        if st.button("Limpiar Cola"):
            st.session_state.productos = []
            st.rerun()
