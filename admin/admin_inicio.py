# admin/admin_inicio.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from calendar import monthrange

def show_inicio_admin():
    """Panel de inicio del administrador con metricas globales."""
    st.title("🏠 Panel de Administracion")
    
    um = st.session_state.user_manager
    
    # =============================================
    # FILTROS
    # =============================================
    st.write("### 🔍 Filtros")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        campana_filtro = st.selectbox("Campaña:", ["TODAS", "CAPTA", "WINBACK"], key="admin_campana")
    
    with col_f2:
        supervisores = um.get_users_by_role("super")
        supervisor_filtro = st.selectbox("Supervisor:", ["TODOS"] + [s['username'] for s in supervisores], key="admin_super")
    
    with col_f3:
        periodo_filtro = st.selectbox("Período:", ["Dia especifico", "Dia anterior (L-V)", "Mes actual", "Mes anterior"], key="admin_periodo")
    
    hoy = datetime.now()
    dias_lab = 1
    año_ant = hoy.year
    mes_ant = hoy.month
    ultimo_dia = hoy.day
    
    if periodo_filtro == "Dia especifico":
        fecha_dia = st.date_input("Selecciona el dia:", value=hoy, key="admin_fecha_dia")
        fecha_inicio = fecha_dia.strftime('%Y-%m-%d')
        fecha_fin = fecha_dia.strftime('%Y-%m-%d')
        dias_lab = 1 if fecha_dia.weekday() < 5 else 0
        st.caption(f"📅 {fecha_inicio}")
    
    elif periodo_filtro == "Dia anterior (L-V)":
        fecha_check = hoy - timedelta(days=1)
        while fecha_check.weekday() >= 5:
            fecha_check -= timedelta(days=1)
        fecha_inicio = fecha_check.strftime('%Y-%m-%d')
        fecha_fin = fecha_check.strftime('%Y-%m-%d')
        dias_lab = 1
        st.caption(f"📅 {fecha_inicio}")
    
    elif periodo_filtro == "Mes actual":
        fecha_inicio = hoy.strftime('%Y-%m') + '-01'
        fecha_fin = hoy.strftime('%Y-%m-%d')
        dias_lab = sum(1 for d in range(1, hoy.day + 1) if datetime(hoy.year, hoy.month, d).weekday() < 5)
        st.caption(f"📅 {hoy.strftime('%B %Y')}")
    
    else:
        if hoy.month == 1:
            mes_ant = 12
            año_ant = hoy.year - 1
        else:
            mes_ant = hoy.month - 1
            año_ant = hoy.year
        fecha_inicio = f"{año_ant}-{mes_ant:02d}-01"
        ultimo_dia = monthrange(año_ant, mes_ant)[1]
        fecha_fin = f"{año_ant}-{mes_ant:02d}-{ultimo_dia}"
        dias_lab = sum(1 for d in range(1, ultimo_dia + 1) if datetime(año_ant, mes_ant, d).weekday() < 5)
        st.caption(f"📅 {datetime(año_ant, mes_ant, 1).strftime('%B %Y')}")
    
    # =============================================
    # CARGAR DATOS
    # =============================================
    from super.super_panel import cargar_registro_diario, cargar_datos_puntos
    registro = cargar_registro_diario()
    datos_puntos = cargar_datos_puntos()
    
    # Obtener agentes según filtro de campaña
    if campana_filtro == "TODAS":
        agentes = um.get_all_agents()
    else:
        agentes = um.get_agents_by_campaign(campana_filtro)
    
    # Filtrar por supervisor
    if supervisor_filtro != "TODOS":
        agentes = [a for a in agentes if a.get('manager') == supervisor_filtro]
    
    if not agentes:
        st.warning("No hay agentes con los filtros seleccionados.")
        return
    
    # =============================================
    # CALCULAR MÉTRICAS
    # =============================================
    total_ventas = 0
    total_llamadas_5m = 0
    total_llamadas_15m = 0
    total_horas_equipo = 0
    total_ausentes = 0
    
    for agente in agentes:
        username = agente['username']
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        
        for fecha_str, datos_dia in registro.items():
            if fecha_inicio <= fecha_str <= fecha_fin:
                if username in datos_dia:
                    datos = datos_dia[username]
                    if not datos.get('ausente', False):
                        total_ventas += datos.get('ventas', 0)
                        total_llamadas_5m += datos.get('llamadas_5m', 0)
                        total_llamadas_15m += datos.get('llamadas_15m', 0)
                    else:
                        total_ausentes += 1
        
        total_horas_equipo += horas_diarias * dias_lab
    
    horas_ausentes = 0
    for agente in agentes:
        username = agente['username']
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        for fecha_str, datos_dia in registro.items():
            if fecha_inicio <= fecha_str <= fecha_fin:
                if username in datos_dia and datos_dia[username].get('ausente', False):
                    horas_ausentes += horas_diarias
    
    horas_efectivas = max(0, total_horas_equipo - horas_ausentes)
    sph_global = round(total_ventas / (horas_efectivas * 0.83), 2) if total_ventas > 0 and horas_efectivas > 0 else 0.0
    
    # =============================================
    # MÉTRICAS PRINCIPALES
    # =============================================
    st.markdown("---")
    st.write("### 📊 Metricas Generales")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("👥 Agentes", len(agentes))
    with col2: st.metric("📦 Ventas Totales", total_ventas)
    with col3: st.metric("📈 SPH Global", sph_global)
    with col4: st.metric("📞 Llamadas +5m", total_llamadas_5m)
    with col5: st.metric("📞 Llamadas +15m", total_llamadas_15m)
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1: st.metric("⏰ Horas Efectivas", f"{horas_efectivas:.1f}h")
    with col_a2: st.metric("🔴 Ausentes", total_ausentes)
    with col_a3:
        ventas_por_agente = round(total_ventas / len(agentes), 1) if agentes else 0
        st.metric("📦 Media Ventas/Agente", ventas_por_agente)
    
    # =============================================
    # OBJETIVOS DE VENTAS
    # =============================================
    st.markdown("---")
    st.write("### 🎯 Objetivos de Ventas del Mes")
    
    try:
        with open('data/config_puntos_super.json', 'r', encoding='utf-8') as f:
            config_obj = json.load(f)
        objetivos = config_obj.get('objetivos_ventas', {'CAPTA': 0, 'WINBACK': 0})
    except:
        objetivos = {'CAPTA': 0, 'WINBACK': 0}
    
    mes_actual_str = datetime.now().strftime('%Y-%m')
    ventas_capta_mes = 0
    ventas_winback_mes = 0
    
    for agente in um.get_all_agents():
        username = agente['username']
        campana = agente.get('campaign', 'CAPTA')
        ventas_agente = datos_puntos['ventas'].get(username, {})
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual_str):
                if campana == 'CAPTA':
                    ventas_capta_mes += len(ventas_dia)
                else:
                    ventas_winback_mes += len(ventas_dia)
    
    col_obj1, col_obj2 = st.columns(2)
    
    with col_obj1:
        st.write("**CAPTA**")
        obj_capta = objetivos.get('CAPTA', 0)
        if obj_capta > 0:
            pct_capta = min(ventas_capta_mes / obj_capta, 1.0)
            st.metric("Ventas CAPTA", f"{ventas_capta_mes} / {obj_capta}", delta=f"{pct_capta*100:.1f}%")
            if pct_capta >= 1.0: st.progress(1.0); st.success("🏆 ¡OBJETIVO CUMPLIDO!")
            elif pct_capta >= 0.8: st.progress(pct_capta); st.warning("⚠️ Al 80%")
            elif pct_capta >= 0.4: st.progress(pct_capta); st.info("📈 Al 40%")
            else: st.progress(pct_capta); st.caption("🌱 Por debajo del 40%")
            st.caption(f"🔴 0% ─── 🟡 40% ({int(obj_capta*0.4)}) ─── 🟠 80% ({int(obj_capta*0.8)}) ─── 🟢 100% ({obj_capta})")
        else:
            st.info("Objetivo CAPTA no configurado")
    
    with col_obj2:
        st.write("**WINBACK**")
        obj_winback = objetivos.get('WINBACK', 0)
        if obj_winback > 0:
            pct_winback = min(ventas_winback_mes / obj_winback, 1.0)
            st.metric("Ventas WINBACK", f"{ventas_winback_mes} / {obj_winback}", delta=f"{pct_winback*100:.1f}%")
            if pct_winback >= 1.0: st.progress(1.0); st.success("🏆 ¡OBJETIVO CUMPLIDO!")
            elif pct_winback >= 0.8: st.progress(pct_winback); st.warning("⚠️ Al 80%")
            elif pct_winback >= 0.4: st.progress(pct_winback); st.info("📈 Al 40%")
            else: st.progress(pct_winback); st.caption("🌱 Por debajo del 40%")
            st.caption(f"🔴 0% ─── 🟡 40% ({int(obj_winback*0.4)}) ─── 🟠 80% ({int(obj_winback*0.8)}) ─── 🟢 100% ({obj_winback})")
        else:
            st.info("Objetivo WINBACK no configurado")
    
    # =============================================
    # TABLA DE AGENTES
    # =============================================
    st.markdown("---")
    st.write("### 📋 Desglose por Agente")
    
    data_agentes = []
    for agente in agentes:
        username = agente['username']
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        sph_config = agente.get('sph_config', {})
        sph_target = sph_config.get('target', 0.06)
        
        ventas_agente = 0
        llamadas_5m_agente = 0
        llamadas_15m_agente = 0
        ausente_agente = False
        
        for fecha_str, datos_dia in registro.items():
            if fecha_inicio <= fecha_str <= fecha_fin:
                if username in datos_dia:
                    datos = datos_dia[username]
                    if not datos.get('ausente', False):
                        ventas_agente += datos.get('ventas', 0)
                        llamadas_5m_agente += datos.get('llamadas_5m', 0)
                        llamadas_15m_agente += datos.get('llamadas_15m', 0)
                    else:
                        ausente_agente = True
        
        dias_efectivos = max(0, dias_lab - (1 if ausente_agente else 0))
        horas_efect = horas_diarias * dias_efectivos
        sph_agente = round(ventas_agente / (horas_efect * 0.83), 2) if ventas_agente > 0 and horas_efect > 0 else 0.0
        
        data_agentes.append({
            'Agente': username,
            'Nombre': agente.get('nombre', ''),
            'Supervisor': agente.get('manager', ''),
            'Campaña': agente.get('campaign', ''),
            'SPH Obj': sph_target,
            'SPH': sph_agente,
            'Ventas': ventas_agente,
            '+5m': llamadas_5m_agente,
            '+15m': llamadas_15m_agente,
            'Ausente': '🔴' if ausente_agente else '🟢',
            'Estado': '🟢' if sph_agente >= sph_target else '🔴',
            'Standby': '💤' if agente.get('standby') else '✅'
        })
    
    df = pd.DataFrame(data_agentes)
    df = df.sort_values('SPH', ascending=False)
    
    columnas_mostrar = ['Agente', 'Nombre', 'Supervisor', 'Campaña', 'SPH Obj', 'SPH', 'Ventas', '+5m', '+15m', 'Ausente', 'Estado', 'Standby']
    st.dataframe(df[columnas_mostrar], use_container_width=True, hide_index=True)