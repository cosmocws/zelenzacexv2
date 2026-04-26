# agent/agent_objetivos.py
import streamlit as st
from datetime import datetime
from calendar import monthrange
from core.monitorizaciones import obtener_ultima_monitorizacion

def show_objetivos():
    """Pantalla de objetivos del agente."""
    st.title("🎯 Mis Objetivos")
    
    agente = st.session_state.user
    username = agente['username']
    
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
    # Datos del agente
    sph_config = agente.get('sph_config', {})
    sph_target = sph_config.get('target', 0.06)
    horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
    
    hoy = datetime.now()
    mes_actual_str = hoy.strftime('%Y-%m')
    
    incorporacion_str = agente.get('incorporation_date', hoy.strftime('%Y-%m-%d'))
    try:
        fecha_incorporacion = datetime.strptime(incorporacion_str, '%Y-%m-%d')
    except:
        fecha_incorporacion = hoy
    
    # Ventas del mes
    ventas_mes = 0
    ventas_agente = datos_puntos['ventas'].get(username, {})
    for fecha, ventas_dia in ventas_agente.items():
        if fecha.startswith(mes_actual_str):
            ventas_mes += len(ventas_dia)
    
    # Dias trabajados desde incorporacion
    dias_laborables = 0
    dias_ausente = 0
    dia_inicio = max(fecha_incorporacion.day, 1) if fecha_incorporacion.month == hoy.month else 1
    for d in range(dia_inicio, hoy.day + 1):
        fecha_check = datetime(hoy.year, hoy.month, d)
        if fecha_check.weekday() < 5:
            dias_laborables += 1
            fecha_str = fecha_check.strftime('%Y-%m-%d')
            reg_dia = registro.get(fecha_str, {}).get(username, {})
            if reg_dia.get('ausente', False):
                dias_ausente += 1
    
    dias_efectivos = max(0, dias_laborables - dias_ausente)
    horas_totales = horas_diarias * dias_efectivos
    sph_real = round(ventas_mes / (horas_totales * 0.83), 2) if ventas_mes > 0 and horas_totales > 0 else 0.0
    
    # Objetivo mensual
    dias_totales_mes = monthrange(hoy.year, hoy.month)[1]
    dias_restantes = 0
    for d in range(hoy.day + 1, dias_totales_mes + 1):
        if datetime(hoy.year, hoy.month, d).weekday() < 5:
            dias_restantes += 1
    
    ausencias_futuras = 0
    for d in range(hoy.day + 1, dias_totales_mes + 1):
        fecha_str = datetime(hoy.year, hoy.month, d).strftime('%Y-%m-%d')
        if registro.get(fecha_str, {}).get(username, {}).get('ausente', False):
            ausencias_futuras += 1
    
    dias_restantes_efectivos = max(0, dias_restantes - ausencias_futuras)
    objetivo_ventas_mes = round(horas_diarias * (dias_laborables + dias_restantes_efectivos) * sph_target * 0.83)
    
    # Mostrar metricas
    st.write("### 📈 Estado Actual del Mes")
    col_o1, col_o2, col_o3, col_o4 = st.columns(4)
    with col_o1:
        st.metric("SPH Objetivo", sph_target)
    with col_o2:
        st.metric("SPH Real", sph_real, delta=f"{sph_real - sph_target:.2f}")
    with col_o3:
        st.metric("Ventas Actuales", ventas_mes)
    with col_o4:
        st.metric("Objetivo Mensual", objetivo_ventas_mes, delta=f"{ventas_mes - objetivo_ventas_mes}")
    
    st.write("### 📅 Dias del Mes")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric("Dias Trabajados", dias_efectivos)
    with col_d2:
        st.metric("Dias Ausente", dias_ausente)
    with col_d3:
        st.metric("Dias Restantes", dias_restantes_efectivos)
    
    # Objetivos a 7 dias
    st.markdown("---")
    st.write("### 🎯 Objetivos a 7 Dias (de tu ultima monitorizacion)")
    
    ultima = obtener_ultima_monitorizacion(username)
    obj7 = ultima.get('objetivos_7d', {}) if ultima else {}
    
    if obj7 and any(v for k, v in obj7.items() if v and k != 'otros'):
        col_7d1, col_7d2, col_7d3 = st.columns(3)
        with col_7d1:
            st.metric("🎯 Ventas", obj7.get('ventas', 0))
        with col_7d2:
            st.metric("📞 Llamadas +5min", obj7.get('llamadas_5m', 0))
        with col_7d3:
            st.metric("📞 Llamadas +15min", obj7.get('llamadas_15m', 0))
        if obj7.get('otros'):
            st.info(f"📝 **Otros:** {obj7['otros']}")
    else:
        st.info("No tienes objetivos a 7 dias asignados.")
    
    # Llamadas del mes
    st.markdown("---")
    st.write("### 📞 Llamadas del Mes")
    
    llamadas_5m_mes = 0
    llamadas_15m_mes = 0
    for fecha, datos_dia in registro.items():
        if fecha.startswith(mes_actual_str) and username in datos_dia:
            reg_dia = datos_dia[username]
            llamadas_5m_mes += reg_dia.get('llamadas_5m', 0)
            llamadas_15m_mes += reg_dia.get('llamadas_15m', 0)
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.metric("Llamadas +5min (mes)", llamadas_5m_mes)
    with col_l2:
        st.metric("Llamadas +15min (mes)", llamadas_15m_mes)