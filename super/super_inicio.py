# super/super_inicio.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from calendar import monthrange
from core.monitorizaciones import obtener_monitorizaciones_empleado

def show_inicio_super():
    """Inicio del supervisor con puntos, monitorizaciones y ranking."""
    st.title("🏠 Mi Inicio - Supervisor")
    
    um = st.session_state.user_manager
    supervisor = st.session_state.user['username']
    mis_agentes = um.get_agents_by_manager(supervisor)
    
    if not mis_agentes:
        st.info("No tienes agentes asignados.")
        return
    
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
    # Cargar config de puntos supervisor
    try:
        with open('data/config_puntos_super.json', 'r', encoding='utf-8') as f:
            config_super = json.load(f)
    except:
        config_super = {"puntos_supervisor": {}, "objetivos_ventas": {}, "bonus_diarios": {}}
    
    hoy = datetime.now()
    mes_actual = hoy.strftime('%Y-%m')
    
    # =============================================
    # MIS PUNTOS DEL MES
    # =============================================
    st.write("### ⭐ Mis Puntos del Mes")
    
    total_puntos_capta = 0.0
    total_puntos_winback = 0.0
    dias_con_bonus = 0
    
    for fecha_str in sorted(registro.keys()):
        if fecha_str.startswith(mes_actual):
            resultado = _calcular_puntos_super_dia(supervisor, fecha_str, config_super, datos_puntos, registro, um)
            total_puntos_capta += resultado['puntos_capta']
            total_puntos_winback += resultado['puntos_winback']
            if resultado['bonus_capta'] or resultado['bonus_winback']:
                dias_con_bonus += 1
    
    total_puntos = total_puntos_capta + total_puntos_winback
    
    # Ver si aplica x2
    obj_cumplido = datos_puntos.get('objetivos_cumplidos', {}).get(mes_actual, False)
    if obj_cumplido:
        total_puntos *= 2
        total_puntos_capta *= 2
        total_puntos_winback *= 2
    
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric("Puntos CAPTA", f"{total_puntos_capta:.1f}")
    with col_p2:
        st.metric("Puntos WINBACK", f"{total_puntos_winback:.1f}")
    with col_p3:
        st.metric("Total Puntos", f"{total_puntos:.1f}", delta="x2" if obj_cumplido else None)
    with col_p4:
        st.metric("Días con Bonus", dias_con_bonus)
    
    # =============================================
    # MONITORIZACIONES PENDIENTES
    # =============================================
    st.markdown("---")
    st.write("### 📋 Monitorizaciones Pendientes")
    
    col_mon1, col_mon2 = st.columns(2)
    
    with col_mon1:
        st.write("**📅 Para HOY**")
        hoy_str = hoy.strftime('%Y-%m-%d')
        encontrados_hoy = []
        for agente in mis_agentes:
            monis = obtener_monitorizaciones_empleado(agente['username'])
            if monis:
                ultima = monis[0]
                prox = ultima.get('fecha_proxima_monitorizacion', '')
                if prox == hoy_str:
                    encontrados_hoy.append(agente)
        
        if encontrados_hoy:
            for a in encontrados_hoy:
                st.write(f"- {a['username']} ({a.get('nombre', '')})")
        else:
            st.info("Ninguno para hoy")
    
    with col_mon2:
        st.write("**📅 Para MAÑANA**")
        manana_str = (hoy + timedelta(days=1)).strftime('%Y-%m-%d')
        encontrados_manana = []
        for agente in mis_agentes:
            monis = obtener_monitorizaciones_empleado(agente['username'])
            if monis:
                ultima = monis[0]
                prox = ultima.get('fecha_proxima_monitorizacion', '')
                if prox == manana_str:
                    encontrados_manana.append(agente)
        
        if encontrados_manana:
            for a in encontrados_manana:
                st.write(f"- {a['username']} ({a.get('nombre', '')})")
        else:
            st.info("Ninguno para mañana")
    
    # =============================================
    # TOP 3 AGENTES SPH DEL MES
    # =============================================
    st.markdown("---")
    st.write("### 🏆 Top 3 Agentes - SPH del Mes")
    
    ranking = []
    for agente in mis_agentes:
        username = agente['username']
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        
        ventas_mes = 0
        ventas_agente = datos_puntos['ventas'].get(username, {})
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual):
                ventas_mes += len(ventas_dia)
        
        dias_lab = sum(1 for d in range(1, hoy.day + 1) if datetime(hoy.year, hoy.month, d).weekday() < 5)
        dias_aus = 0
        for fecha_str, datos_dia in registro.items():
            if fecha_str.startswith(mes_actual) and username in datos_dia:
                if datos_dia[username].get('ausente', False):
                    dias_aus += 1
        
        dias_efec = max(0, dias_lab - dias_aus)
        horas_tot = horas_diarias * dias_efec
        sph = round(ventas_mes / (horas_tot * 0.83), 2) if ventas_mes > 0 and horas_tot > 0 else 0.0
        
        ranking.append({
            'Agente': username,
            'Nombre': agente.get('nombre', ''),
            'SPH': sph,
            'SPH Obj': agente.get('sph_config', {}).get('target', 0.06),
            'Ventas': ventas_mes
        })
    
    ranking.sort(key=lambda x: x['SPH'], reverse=True)
    
    if ranking:
        top3 = ranking[:3]
        col_t1, col_t2, col_t3 = st.columns(3)
        medallas = ["🥇", "🥈", "🥉"]
        
        for i, ag in enumerate(top3):
            with [col_t1, col_t2, col_t3][i]:
                st.metric(
                    f"{medallas[i]} {ag['Agente']}",
                    f"SPH: {ag['SPH']}",
                    delta=f"Obj: {ag['SPH Obj']}"
                )
                st.caption(f"{ag['Ventas']} ventas")
    
    # =============================================
    # AGENTES SIN MONITORIZAR (+7 días)
    # =============================================
    st.markdown("---")
    st.write("### ⚠️ Agentes sin Monitorizar (+7 días)")
    
    sin_monitorizar = []
    for agente in mis_agentes:
        monis = obtener_monitorizaciones_empleado(agente['username'])
        if monis:
            ultima = monis[0]
            fecha_ultima = ultima.get('fecha_monitorizacion', '')
            if fecha_ultima:
                try:
                    dias_desde = (hoy - datetime.strptime(fecha_ultima, '%Y-%m-%d')).days
                    if dias_desde > 7:
                        sin_monitorizar.append({
                            'Agente': agente['username'],
                            'Nombre': agente.get('nombre', ''),
                            'Ultima Mon.': fecha_ultima,
                            'Días sin Mon.': dias_desde
                        })
                except:
                    pass
        else:
            sin_monitorizar.append({
                'Agente': agente['username'],
                'Nombre': agente.get('nombre', ''),
                'Ultima Mon.': 'Nunca',
                'Días sin Mon.': 'N/A'
            })
    
    if sin_monitorizar:
        df_sin = pd.DataFrame(sin_monitorizar)
        st.dataframe(df_sin, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Todos tus agentes tienen monitorización reciente")

    # =============================================
    # SEGUIMIENTO OBJETIVOS A 7 DÍAS
    # =============================================
    st.markdown("---")
    st.write("### 🎯 Seguimiento Objetivos a 7 Días")
    st.caption("Progreso de cada agente respecto a los objetivos de su última monitorización")
    
    seguimiento = []
    for agente in mis_agentes:
        username = agente['username']
        
        # Obtener última monitorización con objetivos 7d
        monis = obtener_monitorizaciones_empleado(username)
        obj_7d = None
        fecha_obj = None
        if monis:
            ultima = monis[0]
            obj_7d = ultima.get('objetivos_7d', {})
            fecha_obj = ultima.get('fecha_monitorizacion', '')
        
        if not obj_7d or not any(v for k, v in obj_7d.items() if v and k != 'otros'):
            continue
        
        # Calcular ventas y llamadas desde la fecha de monitorización
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
        
        obj_ventas = obj_7d.get('ventas', 0)
        obj_5m = obj_7d.get('llamadas_5m', 0)
        obj_15m = obj_7d.get('llamadas_15m', 0)
        
        pct_ventas = min(ventas_desde / obj_ventas, 1.0) if obj_ventas > 0 else 0
        pct_5m = min(llamadas_5m_desde / obj_5m, 1.0) if obj_5m > 0 else 0
        pct_15m = min(llamadas_15m_desde / obj_15m, 1.0) if obj_15m > 0 else 0
        
        # Calcular días restantes
        if fecha_obj:
            dias_totales = 7
            dias_pasados = (hoy - datetime.strptime(fecha_obj, '%Y-%m-%d')).days
            dias_restantes = max(0, dias_totales - dias_pasados)
        else:
            dias_restantes = 7
        
        seguimiento.append({
            'Agente': username,
            'Nombre': agente.get('nombre', ''),
            'Desde': fecha_obj,
            'Días Rest.': dias_restantes,
            'Ventas': f"{ventas_desde}/{obj_ventas}",
            '% Ventas': pct_ventas,
            'Llamadas +5m': f"{llamadas_5m_desde}/{obj_5m}",
            '% +5m': pct_5m,
            'Llamadas +15m': f"{llamadas_15m_desde}/{obj_15m}",
            '% +15m': pct_15m,
            'Otros': obj_7d.get('otros', '')[:50]
        })
    
    if seguimiento:
        for s in seguimiento:
            with st.expander(f"{'✅' if s['% Ventas'] >= 1.0 and s['% +5m'] >= 1.0 and s['% +15m'] >= 1.0 else '📊'} {s['Agente']} ({s['Nombre']}) - {s['Días Rest.']} días rest."):
                st.caption(f"Desde: {s['Desde']} | Objetivos a 7 días")
                
                # Ventas
                st.write(f"**🎯 Ventas: {s['Ventas']}**")
                col_v1, col_v2 = st.columns([4, 1])
                with col_v1:
                    if s['% Ventas'] >= 1.0:
                        st.progress(1.0)
                        st.success("¡Completado!")
                    elif s['% Ventas'] >= 0.7:
                        st.progress(s['% Ventas'])
                        st.info("Buen ritmo")
                    elif s['% Ventas'] >= 0.3:
                        st.progress(s['% Ventas'])
                        st.warning("Necesita mejorar")
                    else:
                        st.progress(s['% Ventas'])
                        st.error("Muy por debajo")
                with col_v2:
                    st.write(f"**{s['% Ventas']*100:.0f}%**")
                
                # Llamadas +5m
                st.write(f"**📞 Llamadas +5m: {s['Llamadas +5m']}**")
                col_l1, col_l2 = st.columns([4, 1])
                with col_l1:
                    if s['% +5m'] >= 1.0:
                        st.progress(1.0)
                    elif s['% +5m'] >= 0.7:
                        st.progress(s['% +5m'])
                    elif s['% +5m'] >= 0.3:
                        st.progress(s['% +5m'])
                    else:
                        st.progress(s['% +5m'])
                with col_l2:
                    st.write(f"**{s['% +5m']*100:.0f}%**")
                
                # Llamadas +15m
                st.write(f"**📞 Llamadas +15m: {s['Llamadas +15m']}**")
                col_l3, col_l4 = st.columns([4, 1])
                with col_l3:
                    if s['% +15m'] >= 1.0:
                        st.progress(1.0)
                    elif s['% +15m'] >= 0.7:
                        st.progress(s['% +15m'])
                    elif s['% +15m'] >= 0.3:
                        st.progress(s['% +15m'])
                    else:
                        st.progress(s['% +15m'])
                with col_l4:
                    st.write(f"**{s['% +15m']*100:.0f}%**")
                
                if s['Otros']:
                    st.caption(f"📝 {s['Otros']}")
    else:
        st.info("No hay objetivos a 7 días asignados para tus agentes.")

def _calcular_puntos_super_dia(supervisor, fecha_str, config_super, datos_puntos, registro, um):
    """Calcula puntos del supervisor en un dia."""
    pts_config = config_super.get('puntos_supervisor', {})
    agentes = um.get_agents_by_manager(supervisor)
    
    puntos_capta = 0.0
    puntos_winback = 0.0
    
    bonus_dia = config_super.get('bonus_diarios', {}).get(fecha_str, {}).get(supervisor, {})
    bonus_capta = bonus_dia.get('CAPTA', False)
    bonus_winback = bonus_dia.get('WINBACK', False)
    
    for agente in agentes:
        username = agente['username']
        campana = agente.get('campaign', 'CAPTA')
        pts = pts_config.get(campana, {})
        
        ventas_dia = datos_puntos['ventas'].get(username, {}).get(fecha_str, [])
        
        for venta in ventas_dia:
            producto = venta.get('producto', '')
            servicios = venta.get('servicios', [])
            tiene_serv = len(servicios) > 0
            bonus_activo = bonus_capta if campana == 'CAPTA' else bonus_winback
            
            if producto == "Electricidad":
                pts_v = pts.get('electricidad', 0)
                if tiene_serv:
                    pts_v += pts.get('electricidad_servicio', 0)
                if bonus_activo:
                    pts_v += pts.get('bonus_electricidad', 0)
                    if tiene_serv:
                        pts_v += pts.get('bonus_electricidad_servicio', 0)
            elif producto == "Gas":
                pts_v = pts.get('gas', 0)
                if tiene_serv:
                    pts_v += pts.get('gas_servicio', 0)
                if bonus_activo:
                    pts_v += pts.get('bonus_gas', 0)
                    if tiene_serv:
                        pts_v += pts.get('bonus_gas_servicio', 0)
            else:
                pts_v = 0
            
            if campana == 'CAPTA':
                puntos_capta += pts_v
            else:
                puntos_winback += pts_v
    
    return {
        'puntos_capta': round(puntos_capta, 1),
        'puntos_winback': round(puntos_winback, 1),
        'bonus_capta': bonus_capta,
        'bonus_winback': bonus_winback
    }