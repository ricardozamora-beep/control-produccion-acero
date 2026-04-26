import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- LÓGICA DE PROGRAMACIÓN ---
def calcular_programa_maestro(fecha_inicio, lista_pedidos, paradas_manto, feriados):
    programa = []
    momento_actual = fecha_inicio
    
    for pedido in lista_pedidos:
        producto = pedido['nombre']
        tonelaje = pedido['tonelaje']
        tasa_h = pedido['tasa_h']
        setup_min = pedido['setup']
        
        # Guardamos el inicio real (incluye el cambio)
        inicio_bloque = momento_actual
        
        # 1. Contabilizar tiempo de cambio (interno)
        minutos_proceso = setup_min
        momento_actual += timedelta(minutes=setup_min)

        # 2. Producción con saltos por paradas
        kg_pendientes = tonelaje
        tasa_minuto = tasa_h / 60
        
        while kg_pendientes > 0:
            # Salto de Feriados
            if momento_actual.date() in feriados:
                momento_actual = (momento_actual + timedelta(days=1)).replace(hour=6, minute=0, second=0)
                continue
            
            # Salto de Mantenimientos
            manto_activo = False
            for m_inicio, m_fin in paradas_manto:
                if m_inicio <= momento_actual < m_fin:
                    momento_actual = m_fin
                    manto_activo = True
                    break
            
            if manto_activo: continue

            # Avance de producción (bloques de 10 min)
            tiempo_bloque = 10 
            producido = min(kg_pendientes, tasa_minuto * tiempo_bloque)
            momento_actual += timedelta(minutes=tiempo_bloque)
            minutos_proceso += tiempo_bloque
            kg_pendientes -= producido

        # Cálculo de tiempo de producción puro (horas)
        tiempo_prod_horas = tonelaje / tasa_h
        
        # 3. Construcción del registro con el orden solicitado
        programa.append({
            "Tipo de Producto": producto,
            "Toneladas Solicitadas": f"{tonelaje} kg",
            "Velocidad de Producción": f"{tasa_h} kg/h",
            "Tiempo de Producción": f"{tiempo_prod_horas:.2f} h",
            "Tiempo de Cambio": f"{setup_min} min",
            "Fecha y Hora de Inicio": inicio_bloque,
            "Fecha y Hora de Finalización": momento_actual
        })

    return pd.DataFrame(programa)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Rebar Master Scheduler", layout="wide")
st.title("🏭 Programador Maestro de Producción 2.0")

# 1. Configuración en Sidebar
with st.sidebar:
    st.header("📂 Configuración")
    archivo_cat = st.file_uploader("Cargar catálogo (Excel)", type=['xlsx'])
    
    st.divider()
    st.subheader("🛠️ Mantenimientos")
    if 'mantenimientos' not in st.session_state: st.session_state.mantenimientos = []
    
    with st.form("manto_form", clear_on_submit=True):
        f_manto = st.date_input("Día")
        h_ini = st.time_input("Inicio")
        h_fin = st.time_input("Fin")
        if st.form_submit_button("Añadir Parada"):
            st.session_state.mantenimientos.append((datetime.combine(f_manto, h_ini), datetime.combine(f_manto, h_fin)))
            st.rerun()
    
    if st.session_state.mantenimientos:
        for i, (ini, fin) in enumerate(st.session_state.mantenimientos):
            st.caption(f"{i+1}. {ini.strftime('%d/%m %H:%M')} a {fin.strftime('%H:%M')}")
        if st.button("Limpiar Mantenimientos"):
            st.session_state.mantenimientos = []
            st.rerun()

# 2. Cuerpo Principal
if archivo_cat:
    df_cat = pd.read_excel(archivo_cat)
    productos_disponibles = df_cat['Nombre'].tolist()
    
    col1, col2, col3 = st.columns([1,1,2])
    with col1: 
        f_arranque = st.date_input("Fecha Inicio Producción", datetime.now())
    with col2: 
        h_arranque = st.time_input("Hora Inicio", datetime.strptime("22:00", "%H:%M").time())
    with col3: 
        # MEJORA: Calendario multiselect para días libres
        feriados = st.multiselect(
            "Seleccionar días libres (Feriados)",
            pd.date_range(start=datetime.now().date() - timedelta(days=30), periods=120).date,
            default=[],
            format_func=lambda x: x.strftime('%d/%m/%Y')
        )

    st.divider()
    
    # 3. Ingreso de Productos
    if 'cola' not in st.session_state: st.session_state.cola = []
    
    st.subheader("📝 Ingreso de Productos")
    with st.expander("Añadir nuevo producto", expanded=True):
        c1, c2, c3 = st.columns(3)
        p_sel = c1.selectbox("Producto", productos_disponibles)
        p_ton = c2.number_input("Tonelaje (kg)", step=500, value=1000)
        p_setup = c3.number_input("Tiempo de cambio (min)", value=30, step=15)
        
        if st.button("Agregar a la cola"):
            tasa = df_cat[df_cat['Nombre'] == p_sel]['Tasa_kg_h'].values[0]
            st.session_state.cola.append({
                'nombre': p_sel, 'tonelaje': p_ton, 'tasa_h': tasa, 'setup': p_setup
            })
            st.rerun()

    # 4. Generación Automática del Programa
    if st.session_state.cola:
        st.subheader("📅 Programa de Producción")
        
        dt_inicio = datetime.combine(f_arranque, h_arranque)
        df_res = calcular_programa_maestro(dt_inicio, st.session_state.cola, st.session_state.mantenimientos, feriados)
        
        # Formateo final para visualización
        df_view = df_res.copy()
        df_view['Fecha y Hora de Inicio'] = df_view['Fecha y Hora de Inicio'].dt.strftime('%d/%m/%Y %H:%M')
        df_view['Fecha y Hora de Finalización'] = df_view['Fecha y Hora de Finalización'].dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(df_view, use_container_width=True)
        
        if st.button("🗑️ Limpiar Plan de Carga"):
            st.session_state.cola = []
            st.rerun()
else:
    st.info("Cargue el archivo de catálogo para habilitar el sistema.")
