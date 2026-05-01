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
    
    # Lista de meses disponibles
    meses_disponibles = []
    for y in range(fecha_incorporacion.year, hoy.year + 1):
        for m in range(1, 13):
            mes_str = f"{y}-{m:02d}"
            if mes_str >= fecha_incorporacion.strftime('%Y-%m') and mes_str <= mes_actual_str:
                meses_disponibles.append(mes_str)
    meses_disponibles.sort(reverse=True)
    meses_nombres = {m: datetime.strptime(m, '%Y-%m').strftime('%B %Y') for m in meses_disponibles}
    
    # Selector de mes
    col_tit, col_sel = st.columns([3, 1])
    with col_tit:
        st.write("### 📈 Estado del Mes")
    with col_sel:
        mes_sel = st.selectbox("Mes", meses_disponibles, format_func=lambda x: meses_nombres.get(x, x), key="mes_obj", label_visibility="collapsed")
    
    # Determinar si es el mes actual o pasado
    es_mes_actual = mes_sel == mes_actual_str
    
    año_sel, mes_sel_num = int(mes_sel[:4]), int(mes_sel[5:7])
    dias_en_mes = monthrange(año_sel, mes_sel_num)[1]
    dia_fin = hoy.day if es_mes_actual else dias_en_mes
    dia_ini = max(fecha_incorporacion.day, 1) if mes_sel == fecha_incorporacion.strftime('%Y-%m') else 1
    
    # Ventas del mes seleccionado
    ventas_mes = 0
    ventas_agente = datos_puntos['ventas'].get(username, {})
    for fecha, ventas_dia in ventas_agente.items():
        if fecha.startswith(mes_sel):
            ventas_mes += len(ventas_dia)
    
    # Calcular horas reales
    horas_totales = 0
    dias_ausente = 0
    for d in range(dia_ini, dia_fin + 1):
        fecha_check = datetime(año_sel, mes_sel_num, d)
        if fecha_check.weekday() < 5:
            fecha_str = fecha_check.strftime('%Y-%m-%d')
            reg_dia = registro.get(fecha_str, {}).get(username, {})
            if reg_dia.get('ausente', False):
                dias_ausente += 1
            else:
                hora_salida = reg_dia.get('hora_salida', '')
                if hora_salida:
                    try:
                        h_ini = datetime.strptime(agente.get('schedule', {}).get('start_time', '15:00'), '%H:%M')
                        h_fin = datetime.strptime(hora_salida, '%H:%M')
                        horas_totales += round((h_fin - h_ini).seconds / 3600, 2)
                    except:
                        horas_totales += horas_diarias
                else:
                    horas_totales += horas_diarias
    
    dias_efectivos = round(horas_totales / horas_diarias, 1) if horas_diarias > 0 else 0
    sph_real = round(ventas_mes / (horas_totales * 0.83), 3) if ventas_mes > 0 and horas_totales > 0 else 0.0
    
    # Calcular métricas del mes anterior para comparar
    if len(meses_disponibles) >= 2:
        mes_anterior_str = meses_disponibles[1]  # El segundo en la lista
        ventas_anterior = 0
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_anterior_str):
                ventas_anterior += len(ventas_dia)
        
        # Horas mes anterior (simplificado)
        año_ant, mes_ant_num = int(mes_anterior_str[:4]), int(mes_anterior_str[5:7])
        dias_ant = monthrange(año_ant, mes_ant_num)[1]
        horas_ant = horas_diarias * dias_ant * 0.8  # Aproximación
        sph_anterior = round(ventas_anterior / (horas_ant * 0.83), 3) if ventas_anterior > 0 and horas_ant > 0 else 0.0
        
        delta_ventas = ventas_mes - ventas_anterior
        delta_sph = sph_real - sph_anterior
    else:
        ventas_anterior = 0
        sph_anterior = 0
        delta_ventas = 0
        delta_sph = 0
    
    # Objetivo mensual (solo para mes actual)
    if es_mes_actual:
        dias_restantes = 0
        for d in range(hoy.day + 1, dias_en_mes + 1):
            if datetime(hoy.year, hoy.month, d).weekday() < 5:
                dias_restantes += 1
        ausencias_futuras = 0
        for d in range(hoy.day + 1, dias_en_mes + 1):
            fecha_str = datetime(hoy.year, hoy.month, d).strftime('%Y-%m-%d')
            if registro.get(fecha_str, {}).get(username, {}).get('ausente', False):
                ausencias_futuras += 1
        dias_restantes_efectivos = max(0, dias_restantes - ausencias_futuras)
        objetivo_ventas_mes = round(horas_diarias * (dias_efectivos + dias_restantes_efectivos) * sph_target * 0.83)
    else:
        objetivo_ventas_mes = 0
        dias_restantes_efectivos = 0
    
    # Mostrar métricas
    col_o1, col_o2, col_o3, col_o4 = st.columns(4)
    with col_o1:
        st.metric("SPH Objetivo", sph_target)
    with col_o2:
        st.metric("SPH Real", sph_real, delta=f"{delta_sph:+.3f}" if delta_sph != 0 else None)
    with col_o3:
        st.metric("Ventas", ventas_mes, delta=f"{delta_ventas:+d}" if delta_ventas != 0 else None)
    with col_o4:
        if es_mes_actual:
            st.metric("Objetivo Mensual", objetivo_ventas_mes, delta=f"{ventas_mes - objetivo_ventas_mes:+d}")
        else:
            st.metric("Ventas Mes Ant.", ventas_anterior)
    
    if len(meses_disponibles) >= 2 and not es_mes_actual:
        st.caption(f"📊 Comparando con {meses_nombres.get(mes_actual_str, 'mes actual')}")
    
    st.write("### 📅 Dias del Mes")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric("Dias Trabajados", f"{dias_efectivos:.1f}")
    with col_d2:
        st.metric("Dias Ausente", dias_ausente)
    with col_d3:
        if es_mes_actual:
            st.metric("Dias Restantes", dias_restantes_efectivos)
        else:
            st.metric("Total Dias", dias_en_mes)
    
    # Objetivos a 7 dias con progreso
    st.markdown("---")
    st.write("### 🎯 Objetivos a 7 Dias")
    
    ultima = obtener_ultima_monitorizacion(username)
    obj7 = ultima.get('objetivos_7d', {}) if ultima else {}
    
    if obj7 and any(v for k, v in obj7.items() if v and k != 'otros'):
        fecha_obj = ultima.get('fecha_monitorizacion', '') if ultima else ''
        
        # Calcular progreso desde la fecha de monitorización
        ventas_desde = 0
        llamadas_5m_desde = 0
        llamadas_15m_desde = 0
        
        if fecha_obj:
            for fecha_str, datos_dia in registro.items():
                if fecha_str >= fecha_obj:
                    if username in datos_dia:
                        datos = datos_dia[username]
                        if not datos.get('ausente', False):
                            ventas_desde += datos.get('ventas', 0)
                            llamadas_5m_desde += datos.get('llamadas_5m', 0)
                            llamadas_15m_desde += datos.get('llamadas_15m', 0)
        
        obj_ventas = obj7.get('ventas', 0)
        obj_5m = obj7.get('llamadas_5m', 0)
        obj_15m = obj7.get('llamadas_15m', 0)
        
        pct_ventas = min(ventas_desde / obj_ventas, 1.0) if obj_ventas > 0 else 0
        pct_5m = min(llamadas_5m_desde / obj_5m, 1.0) if obj_5m > 0 else 0
        pct_15m = min(llamadas_15m_desde / obj_15m, 1.0) if obj_15m > 0 else 0
        
        # Días restantes
        if fecha_obj:
            dias_pasados = (hoy - datetime.strptime(fecha_obj, '%Y-%m-%d')).days
            dias_restantes = max(0, 7 - dias_pasados)
        else:
            dias_restantes = 7
        
        st.caption(f"Desde: {fecha_obj} | {dias_restantes} días restantes")
        
        # Ventas
        st.write(f"**🎯 Ventas: {ventas_desde}/{obj_ventas}**")
        col_v1, col_v2 = st.columns([4, 1])
        with col_v1:
            if pct_ventas >= 1.0: st.progress(1.0); st.success("¡Completado!")
            elif pct_ventas >= 0.5: st.progress(pct_ventas); st.info("Buen ritmo")
            elif pct_ventas >= 0.15: st.progress(pct_ventas); st.warning("Necesita mejorar")
            else: st.progress(pct_ventas); st.error("Muy por debajo")
        with col_v2: st.write(f"**{pct_ventas*100:.0f}%**")
        
        # Llamadas +5m
        st.write(f"**📞 Llamadas +5min: {llamadas_5m_desde}/{obj_5m}**")
        col_l1, col_l2 = st.columns([4, 1])
        with col_l1:
            if pct_5m >= 1.0: st.progress(1.0)
            elif pct_5m >= 0.7: st.progress(pct_5m)
            elif pct_5m >= 0.3: st.progress(pct_5m)
            else: st.progress(pct_5m)
        with col_l2: st.write(f"**{pct_5m*100:.0f}%**")
        
        # Llamadas +15m
        st.write(f"**📞 Llamadas +15min: {llamadas_15m_desde}/{obj_15m}**")
        col_l3, col_l4 = st.columns([4, 1])
        with col_l3:
            if pct_15m >= 1.0: st.progress(1.0)
            elif pct_15m >= 0.7: st.progress(pct_15m)
            elif pct_15m >= 0.3: st.progress(pct_15m)
            else: st.progress(pct_15m)
        with col_l4: st.write(f"**{pct_15m*100:.0f}%**")
        
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
        if fecha.startswith(mes_sel) and username in datos_dia:
            reg_dia = datos_dia[username]
            llamadas_5m_mes += reg_dia.get('llamadas_5m', 0)
            llamadas_15m_mes += reg_dia.get('llamadas_15m', 0)
    
    # Llamadas mes anterior
    if len(meses_disponibles) >= 2:
        llamadas_5m_ant = 0
        llamadas_15m_ant = 0
        for fecha, datos_dia in registro.items():
            if fecha.startswith(mes_anterior_str) and username in datos_dia:
                reg_dia = datos_dia[username]
                llamadas_5m_ant += reg_dia.get('llamadas_5m', 0)
                llamadas_15m_ant += reg_dia.get('llamadas_15m', 0)
        delta_5m = llamadas_5m_mes - llamadas_5m_ant
        delta_15m = llamadas_15m_mes - llamadas_15m_ant
    else:
        delta_5m = 0
        delta_15m = 0
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.metric("Llamadas +5min", llamadas_5m_mes, delta=f"{delta_5m:+d}" if delta_5m != 0 else None)
    with col_l2:
        st.metric("Llamadas +15min", llamadas_15m_mes, delta=f"{delta_15m:+d}" if delta_15m != 0 else None)