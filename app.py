import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- LÓGICA DE PROGRAMACIÓN DINÁMICA ---
def calcular_programa_maestro(fecha_inicio, lista_pedidos, paradas_manto, feriados):
    programa = []
    momento_actual = fecha_inicio
    
    for pedido in lista_pedidos:
        producto = pedido['nombre']
        tonelaje = pedido['tonelaje']
        tasa_h = pedido['tasa_h']
        setup_min = pedido['setup']
        
        # 1. Bloque de Set-up
        inicio_setup = momento_actual
        momento_actual += timedelta(minutes=setup_min)
        programa.append({
            "Actividad": f"SET-UP: {producto}",
            "Inicio": inicio_setup, "Fin": momento_actual,
            "Detalle": f"Preparación de línea ({setup_min} min)"
        })

        # 2. Bloque de Producción con Saltos de Paradas
        kg_pendientes = tonelaje
        tasa_minuto = tasa_h / 60
        
        while kg_pendientes > 0:
            # ¿Estamos en un día feriado? (Salto al siguiente día laboral a las 06:00)
            if momento_actual.date() in feriados:
                momento_actual = (momento_actual + timedelta(days=1)).replace(hour=6, minute=0)
                continue
            
            # ¿Estamos en una ventana de mantenimiento?
            manto_activo = False
            for m_inicio, m_fin in paradas_manto:
                if m_inicio <= momento_actual < m_fin:
                    momento_actual = m_fin
                    manto_activo = True
                    break
            
            if manto_activo: continue

            # Producimos en bloques de 10 min para precisión
            tiempo_bloque = 10 
            producido = min(kg_pendientes, tasa_minuto * tiempo_bloque)
            
            inicio_p = momento_actual
            momento_actual += timedelta(minutes=tiempo_bloque)
            kg_pendientes -= producido

            # Agrupar registros de producción para el reporte
            if not programa or programa[-1]['Actividad'] != f"PROD: {producto}":
                programa.append({"Actividad": f"PROD: {producto}", "Inicio": inicio_p, "Fin": momento_actual, "Detalle": f"Carga: {tonelaje} kg"})
            else:
                programa[-1]['Fin'] = momento_actual

    return pd.DataFrame(programa)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Rebar Master Scheduler", layout="wide")
st.title("🏭 Programador Maestro de Producción 2.0")

# 1. Carga de Catálogo
with st.sidebar:
    st.header("📂 Datos Maestros")
    archivo_cat = st.file_uploader("Cargar catálogo (Excel)", type=['xlsx'])
    
    # Gestión de Mantenimientos Múltiples
    st.divider()
    st.subheader("🛠️ Paradas de Mantenimiento")
    if 'mantenimientos' not in st.session_state: st.session_state.mantenimientos = []
    
    with st.form("manto_form", clear_on_submit=True):
        f_manto = st.date_input("Día")
        h_ini = st.time_input("Inicio")
        h_fin = st.time_input("Fin")
        if st.form_submit_button("Añadir Parada"):
            st.session_state.mantenimientos.append((datetime.combine(f_manto, h_ini), datetime.combine(f_manto, h_fin)))
    
    for i, (ini, fin) in enumerate(st.session_state.mantenimientos):
        st.caption(f"{i+1}. {ini.strftime('%d/%m %H:%M')} a {fin.strftime('%H:%M')}")
    if st.button("Limpiar Mantenimientos"): st.session_state.mantenimientos = []; st.rerun()

# 2. Configuración de la Corrida
if archivo_cat:
    df_cat = pd.read_excel(archivo_cat)
    productos_disponibles = df_cat['Nombre'].tolist()
    
    col1, col2, col3 = st.columns([1,1,2])
    with col1: f_arranque = st.date_input("Fecha Inicio Real", datetime.now())
    with col2: h_arranque = st.time_input("Hora Inicio Real", datetime.strptime("22:00", "%H:%M").time())
    with col3: feriados = st.multiselect("Días Libres/Feriados", pd.date_range(datetime.now(), periods=60).date)

    st.divider()
    
    # 3. Selección de Productos
    st.subheader("📝 Plan de Carga")
    if 'cola' not in st.session_state: st.session_state.cola = []
    
    with st.expander("Agregar producto al plan"):
        c1, c2, c3 = st.columns(3)
        p_sel = c1.selectbox("Seleccionar
