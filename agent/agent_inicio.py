# agent/agent_inicio.py
import streamlit as st
import pandas as pd
from datetime import datetime
from core.monitorizaciones import obtener_ultima_monitorizacion
from super.super_panel import PUNTOS_PRODUCTO

def show_inicio():
    """Pantalla de inicio del agente."""
    st.title("🏠 Mi Inicio")
    
    agente = st.session_state.user
    username = agente['username']
    campana_agente = agente.get('campaign', 'CAPTA')
    
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario, calcular_puntos_pendientes
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
    hoy_dt = datetime.now()
    mes_actual = hoy_dt.strftime('%Y-%m')
    incorporacion_str = agente.get('incorporation_date', hoy_dt.strftime('%Y-%m-%d'))
    try:
        fecha_incorporacion = datetime.strptime(incorporacion_str, '%Y-%m-%d')
    except:
        fecha_incorporacion = hoy_dt
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        # --- ULTIMA MONITORIZACION ---
        st.write("### 📋 Ultima Monitorizacion")
        ultima = obtener_ultima_monitorizacion(username)
        
        if ultima:
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                nota = ultima.get('nota_global', 0)
                objetivo = ultima.get('objetivo', 85)
                st.metric("Nota Global", f"{nota:.0f}%", delta=f"{nota - objetivo:.0f}%")
            with col_m2:
                st.metric("Fecha", ultima.get('fecha_monitorizacion', '-'))
            with col_m3:
                prox = ultima.get('fecha_proxima_monitorizacion', '-')
                if prox and prox != '-':
                    try:
                        dias = (datetime.strptime(prox, '%Y-%m-%d') - hoy_dt).days
                        st.metric("Proxima", prox, delta=f"{dias} dias")
                    except:
                        st.metric("Proxima", prox)
            
            st.write("**Puntuaciones:**")
            areas = [
                ("Experiencia", ultima.get('experiencia', 0)),
                ("Comunicacion", ultima.get('comunicacion', 0)),
                ("Deteccion", ultima.get('deteccion', 0)),
                ("Habilidades Venta", ultima.get('habilidades_venta', 0)),
                ("Resolucion Obj.", ultima.get('resolucion_objeciones', 0)),
                ("Cierre Contacto", ultima.get('cierre_contacto', 0))
            ]
            cols = st.columns(3)
            for i, (nombre, valor) in enumerate(areas):
                with cols[i % 3]:
                    st.metric(nombre, f"{valor:.0f}%")
            
            puntos = ultima.get('puntos_clave', [])
            if puntos:
                st.write("**🔑 Puntos Clave:**")
                for p in puntos:
                    st.write(f"- {p}")
            
            if ultima.get('feedback'):
                with st.expander("📝 Feedback"):
                    st.write(ultima['feedback'])
            
            if ultima.get('plan_accion'):
                with st.expander("🎯 Plan de Accion"):
                    st.write(ultima['plan_accion'])
        else:
            st.info("No tienes monitorizaciones registradas.")
    
    with col_der:
        # --- MI SPH ---
        st.write("### 📈 Mi SPH")
        
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        sph_config = agente.get('sph_config', {})
        sph_target = sph_config.get('target', 0.06)
        
        # Ventas del mes
        ventas_mes = 0
        ventas_agente = datos_puntos['ventas'].get(username, {})
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual):
                ventas_mes += len(ventas_dia)
        
        # Dias laborables desde incorporacion
        dias_laborables = 0
        dias_ausente = 0
        dia_inicio = max(fecha_incorporacion.day, 1)
        for d in range(dia_inicio, hoy_dt.day + 1):
            fecha_check = datetime(hoy_dt.year, hoy_dt.month, d)
            if fecha_check.weekday() < 5:
                dias_laborables += 1
                fecha_str = fecha_check.strftime('%Y-%m-%d')
                reg_dia = registro.get(fecha_str, {}).get(username, {})
                if reg_dia.get('ausente', False):
                    dias_ausente += 1
        
        # Calcular horas reales (con ausencias parciales)
        horas_totales = 0
        for d in range(dia_inicio, hoy_dt.day + 1):
            fecha_check = datetime(hoy_dt.year, hoy_dt.month, d)
            if fecha_check.weekday() < 5:
                fecha_str = fecha_check.strftime('%Y-%m-%d')
                reg_dia = registro.get(fecha_str, {}).get(username, {})
                if not reg_dia.get('ausente', False):
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
        
        sph_real = round(ventas_mes / (horas_totales * 0.83), 2) if ventas_mes > 0 and horas_totales > 0 else 0.0
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("SPH Objetivo", sph_target)
        with col_s2:
            st.metric("SPH Real", sph_real, delta=f"{sph_real - sph_target:.2f}")
        with col_s3:
            st.metric("Ventas Mes", ventas_mes)
        
        # --- PUNTOS DEL MES ---
        st.write("### ⭐ Mis Puntos")
        
        # Puntos por ventas (NO cumplido)
        puntos_ventas_no_cumple = sum(v.get('puntos', 0) for fecha, ventas_dia in ventas_agente.items() if fecha.startswith(mes_actual) for v in ventas_dia)
        
        # Puntos por ventas (SI cumplido)
        puntos_ventas_cumple = 0
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual):
                for venta in ventas_dia:
                    tipo = venta.get('tipo', 'CAPTA')
                    producto = venta.get('producto', '')
                    pts = PUNTOS_PRODUCTO.get(tipo, {}).get(producto, {}).get('cumple', 0)
                    for s in venta.get('servicios', []):
                        if s == "PI": pts += PUNTOS_PRODUCTO.get(tipo, {}).get("Pack Iberdrola (PI)", {}).get('cumple', 0)
                        elif s == "UEN": pts += PUNTOS_PRODUCTO.get(tipo, {}).get("UEN", {}).get('cumple', 0)
                        elif s == "PMG": pts += PUNTOS_PRODUCTO.get(tipo, {}).get("Pack Mantenimiento Gas (PMG)", {}).get('cumple', 0)
                        elif s == "FE": pts += PUNTOS_PRODUCTO.get(tipo, {}).get("Facturación Electrónica (FE)", {}).get('cumple', 0)
                    puntos_ventas_cumple += pts
        
        # Puntos extra (pago semanal)
        puntos_extra_mes = 0
        extras_agente = datos_puntos['puntos_extra'].get(username, {})
        for fecha, extras in extras_agente.items():
            if fecha.startswith(mes_actual):
                if isinstance(extras, list):
                    puntos_extra_mes += sum(e.get('puntos', 0) for e in extras)
                elif isinstance(extras, dict):
                    puntos_extra_mes += extras.get('puntos', 0)
        
        # Mostrar puntos por ventas (pendientes de cierre mensual)
        st.write("**💼 Puntos por Ventas**")
        st.caption("Se pagan al cerrar el mes, segun cumplimiento")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.metric("Obj NO Cumplido", f"{puntos_ventas_no_cumple} pts")
            st.caption(f"💰 {puntos_ventas_no_cumple/22:.2f}€")
        with col_v2:
            st.metric("Obj Cumplido", f"{puntos_ventas_cumple} pts")
            st.caption(f"💰 {puntos_ventas_cumple/22:.2f}€")
        
        # Mostrar puntos extra (pago semanal)
        st.write("**🎁 Puntos Extra**")
        st.caption("Se pagan semanalmente")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.metric("Puntos Extra", puntos_extra_mes)
            st.caption(f"💰 {puntos_extra_mes/22:.2f}€")
        with col_e2:
            # Puntos ya pagados este mes
            pagos = datos_puntos['pagos_realizados'].get(username, [])
            pagado_mes = sum(p.get('puntos_pagados', 0) for p in pagos if p.get('fecha', '').startswith(mes_actual))
            st.metric("PAGADOS", pagado_mes)
            st.caption(f"💰 {pagado_mes/22:.2f}€")
    
    # =============================================
    # RANKING DE CAMPAÑA
    # =============================================
    st.markdown("---")
    st.write("### 🏆 Ranking de Campaña")
    st.caption(f"Agentes en campaña **{campana_agente}** ordenados por SPH")
    
    um = st.session_state.user_manager
    todos_agentes = um.get_all_agents()
    
    ranking = []
    for a in todos_agentes:
        a_username = a['username']
        
        # Ventas del mes desde REGISTRO DIARIO
        ventas = 0
        for fecha, agentes in registro.items():
            if fecha.startswith(mes_actual) and a_username in agentes:
                datos = agentes[a_username]
                if datos.get('campaña', '') == campana_agente:
                    ventas += datos.get('ventas', 0)
        
        horas_dia = a.get('schedule', {}).get('daily_hours', 6.0)
        sph_config_a = a.get('sph_config', {})
        sph_obj = sph_config_a.get('target', 0.06)
        
        # Calcular horas REALES desde registro diario
        horas_tot = 0
        dia_inicio_a = max(datetime.strptime(a.get('incorporation_date', hoy_dt.strftime('%Y-%m-%d')), '%Y-%m-%d').day if a.get('incorporation_date') else 1, 1)
        for d in range(dia_inicio_a, hoy_dt.day + 1):
            fecha_check = datetime(hoy_dt.year, hoy_dt.month, d)
            if fecha_check.weekday() < 5:
                fecha_str = fecha_check.strftime('%Y-%m-%d')
                reg_dia = registro.get(fecha_str, {}).get(a_username, {})
                if reg_dia.get('campaña', '') == campana_agente and not reg_dia.get('ausente', False):
                    hora_salida = reg_dia.get('hora_salida', '')
                    if hora_salida:
                        try:
                            h_ini = datetime.strptime(a.get('schedule', {}).get('start_time', '15:00'), '%H:%M')
                            h_fin = datetime.strptime(hora_salida, '%H:%M')
                            horas_tot += round((h_fin - h_ini).seconds / 3600, 2)
                        except:
                            horas_tot += horas_dia
                    else:
                        horas_tot += horas_dia
        
        sph = round(ventas / (horas_tot * 0.83), 2) if ventas > 0 and horas_tot > 0 else 0.0
        dias_efec = round(horas_tot / horas_dia, 1) if horas_dia > 0 else 0
        
        ranking.append({
            'Agente': a_username,
            'Nombre': a.get('nombre', ''),
            'SPH': sph,
            'SPH Obj': sph_obj,
            'Ventas': ventas,
            'Dias Trab.': dias_efec
        })
    
    ranking.sort(key=lambda x: x['SPH'], reverse=True)
    ranking = [r for r in ranking if r['Ventas'] > 0]
    
    for i, r in enumerate(ranking):
        r['#'] = i + 1
        r['Tu'] = '👈 TU' if r['Agente'] == username else ''
    
    df_ranking = pd.DataFrame(ranking)
    columnas = ['#', 'Agente', 'Nombre', 'SPH', 'SPH Obj', 'Ventas', 'Dias Trab.', 'Tu']
    
    def colorear_ranking(row):
        posicion = row['#']
        if posicion == 1:
            return ['background-color: #FFD700; color: #000000; font-weight: bold'] * len(row)
        elif posicion == 2:
            return ['background-color: #C0C0C0; color: #000000; font-weight: bold'] * len(row)
        elif posicion == 3:
            return ['background-color: #CD7F32; color: #000000; font-weight: bold'] * len(row)
        if row['Tu'] == '👈 TU':
            return ['background-color: #fff3cd; color: #000000; font-weight: bold'] * len(row)
        return ['font-weight: bold'] * len(row)
    
    df_styled = df_ranking[columnas].style.apply(colorear_ranking, axis=1)
    df_styled = df_styled.set_properties(**{
        'text-align': 'center', 'padding': '10px', 'font-weight': 'bold', 'font-size': '14px'
    })
    df_styled = df_styled.set_table_styles([
        {'selector': 'thead th',
         'props': [('background-color', '#2c3e50'), ('color', 'white'), ('font-weight', 'bold'),
                   ('font-size', '14px'), ('text-align', 'center'), ('padding', '10px')]},
    ])
    
    st.dataframe(df_styled, use_container_width=True, hide_index=True)