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
        
        # El inicio del bloque incluye el tiempo de cambio
        inicio_total = momento_actual
        
        # 1. Sumamos el tiempo de Set-up internamente
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

            # Avance de producción
            tiempo_bloque = 10 
            producido = min(kg_pendientes, tasa_minuto * tiempo_bloque)
            momento_actual += timedelta(minutes=tiempo_bloque)
            kg_pendientes -= producido

        # Registramos el bloque completo (Set-up + Producción) como una sola línea
        programa.append({
            "Producto": producto,
            "Inicio": inicio_total,
            "Fin": momento_actual,
            "Tonelaje": f"{tonelaje} kg",
            "Detalle": f"Incluye {setup_min} min de cambio"
        })

    return pd.DataFrame(programa)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Rebar Master Scheduler", layout="wide")
st.title("🏭 Programador Maestro de Producción 2.0")

# 1. Configuración en Sidebar
with st.sidebar:
    st.header("📂 Configuración General")
    archivo_cat = st.file_uploader("1. Cargar catálogo (Excel)", type=['xlsx'])
    
    st.divider()
    st.subheader("🛠️ Paradas de Mantenimiento")
    if 'mantenimientos' not in st.session_state: 
        st.session_state.mantenimientos = []
    
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
        # Mejora: Calendario para días libres
        feriados = st.multiselect(
            "Seleccionar días libres (Feriados)",
            pd.date_range(start=datetime.now().date(), periods=60).date,
            format_func=lambda x: x.strftime('%d/%m/%Y')
        )

    st.divider()
    
    # 3. Gestión de Pedidos
    if 'cola' not in st.session_state: st.session_state.cola = []
    
    st.subheader("📝 Ingreso de Productos")
    with st.expander("Añadir nuevo producto", expanded=True):
        c1, c2, c3 = st.columns(3)
        p_sel = c1.selectbox("Producto", productos_disponibles)
        p_ton = c2.number_input("Tonelaje (kg)", step=500, value=1000)
        # Mejora: Step de 15 minutos
        p_setup = c3.number_input("Tiempo de cambio (min)", value=30, step=15)
        
        if st.button("Agregar a la cola"):
            tasa = df_cat[df_cat['Nombre'] == p_sel]['Tasa_kg_h'].values[0]
            st.session_state.cola.append({
                'nombre': p_sel, 'tonelaje': p_ton, 'tasa_h': tasa, 'setup': p_setup
            })
            st.rerun()

    # 4. Programa Automático
    if st.session_state.cola:
        st.subheader("📅 Programa de Producción Generado")
        
        # Cálculo automático sin necesidad de botón extra
        dt_inicio = datetime.combine(f_arranque, h_arranque)
        df_res = calcular_programa_maestro(dt_inicio, st.session_state.cola, st.session_state.mantenimientos, feriados)
        
        # Formateo para visualización
        df_view = df_res.copy()
        df_view['Inicio'] = df_view['Inicio'].dt.strftime('%d/%m/%Y %H:%M')
        df_view['Fin'] = df_view['Fin'].dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(df_view, use_container_width=True)
        
        if st.button("🗑️ Limpiar Plan"):
            st.session_state.cola = []
            st.rerun()
else:
    st.info("Por favor, sube el catálogo de Excel para habilitar el programador.")
