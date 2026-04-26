# agent/agent_inicio.py
import streamlit as st
import pandas as pd
from datetime import datetime
from core.monitorizaciones import obtener_ultima_monitorizacion

def show_inicio():
    """Pantalla de inicio del agente."""
    st.title("🏠 Mi Inicio")
    
    agente = st.session_state.user
    username = agente['username']
    
    # Cargar datos
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario, calcular_puntos_pendientes
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
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
                        dias = (datetime.strptime(prox, '%Y-%m-%d') - datetime.now()).days
                        st.metric("Proxima", prox, delta=f"{dias} dias")
                    except:
                        st.metric("Proxima", prox)
            
            # Puntuaciones
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
            
            # Puntos clave
            puntos = ultima.get('puntos_clave', [])
            if puntos:
                st.write("**🔑 Puntos Clave:**")
                for p in puntos:
                    st.write(f"- {p}")
            
            # Feedback
            if ultima.get('feedback'):
                with st.expander("📝 Feedback"):
                    st.write(ultima['feedback'])
            
            # Plan de accion
            if ultima.get('plan_accion'):
                with st.expander("🎯 Plan de Accion"):
                    st.write(ultima['plan_accion'])
        else:
            st.info("No tienes monitorizaciones registradas.")
    
    with col_der:
        # --- SPH ACTUAL ---
        st.write("### 📈 Mi SPH")
        
        mes_actual = datetime.now().strftime('%Y-%m')
        sph_target = agente.get('sph_config', {}).get('target', 0.06)
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        
        # Ventas del mes
        ventas_mes = 0
        ventas_agente = datos_puntos['ventas'].get(username, {})
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual):
                ventas_mes += len(ventas_dia)
        
        # Dias trabajados
        hoy_dt = datetime.now()
        dias_laborables = 0
        dias_ausente = 0
        for d in range(1, hoy_dt.day + 1):
            fecha_check = datetime(hoy_dt.year, hoy_dt.month, d)
            if fecha_check.weekday() < 5:
                dias_laborables += 1
                fecha_str = fecha_check.strftime('%Y-%m-%d')
                if registro.get(fecha_str, {}).get(username, {}).get('ausente', False):
                    dias_ausente += 1
        
        dias_efectivos = max(0, dias_laborables - dias_ausente)
        horas_totales = horas_diarias * dias_efectivos
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
        
        puntos_mes = 0
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual):
                for venta in ventas_dia:
                    puntos_mes += venta.get('puntos', 0)
        
        puntos_extra_mes = 0
        extras_agente = datos_puntos['puntos_extra'].get(username, {})
        for fecha, extras in extras_agente.items():
            if fecha.startswith(mes_actual):
                if isinstance(extras, list):
                    puntos_extra_mes += sum(e.get('puntos', 0) for e in extras)
                elif isinstance(extras, dict):
                    puntos_extra_mes += extras.get('puntos', 0)
        
        pendientes = calcular_puntos_pendientes(username, datos_puntos)
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("Puntos Ventas", puntos_mes)
        with col_p2:
            st.metric("Puntos Extra", puntos_extra_mes)
        with col_p3:
            st.metric("Pendientes Pago", pendientes)
            
    # =============================================
    # RANKING DE CAMPAÑA
    # =============================================
    st.markdown("---")
    st.write("### 🏆 Ranking de Campaña")
    st.caption(f"Agentes en campaña **{agente.get('campaign', 'CAPTA')}** ordenados por SPH")
    
    # Cargar todos los agentes de la misma campaña
    um = st.session_state.user_manager
    campana_agente = agente.get('campaign', 'CAPTA')
    todos_agentes = um.get_agents_by_campaign(campana_agente)
    
    mes_actual = datetime.now().strftime('%Y-%m')
    hoy_dt = datetime.now()
    
    ranking = []
    for a in todos_agentes:
        a_username = a['username']
        
        # Ventas del mes
        ventas = 0
        ventas_a = datos_puntos['ventas'].get(a_username, {})
        for fecha, ventas_dia in ventas_a.items():
            if fecha.startswith(mes_actual):
                ventas += len(ventas_dia)
        
        # Calcular SPH
        horas_dia = a.get('schedule', {}).get('daily_hours', 6.0)
        sph_obj = a.get('sph_config', {}).get('target', 0.06)
        
        dias_lab = 0
        dias_aus = 0
        for d in range(1, hoy_dt.day + 1):
            fecha_check = datetime(hoy_dt.year, hoy_dt.month, d)
            if fecha_check.weekday() < 5:
                dias_lab += 1
                fecha_str = fecha_check.strftime('%Y-%m-%d')
                if registro.get(fecha_str, {}).get(a_username, {}).get('ausente', False):
                    dias_aus += 1
        
        dias_efec = max(0, dias_lab - dias_aus)
        horas_tot = horas_dia * dias_efec
        sph = round(ventas / (horas_tot * 0.83), 2) if ventas > 0 and horas_tot > 0 else 0.0
        
        ranking.append({
            'Agente': a_username,
            'Nombre': a.get('nombre', ''),
            'SPH': sph,
            'SPH Obj': sph_obj,
            'Ventas': ventas,
            'Dias Trab.': dias_efec
        })
    
    # Ordenar por SPH de mayor a menor
    ranking.sort(key=lambda x: x['SPH'], reverse=True)
    
    # Añadir posición
    for i, r in enumerate(ranking):
        r['#'] = i + 1
        if r['Agente'] == username:
            r['Tu'] = '👈 TU'
        else:
            r['Tu'] = ''
    
    # Mostrar tabla
    df_ranking = pd.DataFrame(ranking)
    columnas = ['#', 'Agente', 'Nombre', 'SPH', 'SPH Obj', 'Ventas', 'Dias Trab.', 'Tu']
    
    # Colorear la fila del agente actual
    # Colorear filas: oro, plata, bronce + resaltar al agente actual
    def colorear_ranking(row):
        posicion = row['#']
        
        # Medallas para top 3
        if posicion == 1:
            return ['background-color: #FFD700; color: #000000; font-weight: bold'] * len(row)
        elif posicion == 2:
            return ['background-color: #C0C0C0; color: #000000; font-weight: bold'] * len(row)
        elif posicion == 3:
            return ['background-color: #CD7F32; color: #000000; font-weight: bold'] * len(row)
        
        # Resaltar al agente actual
        if row['Tu'] == '👈 TU':
            return ['background-color: #fff3cd; font-weight: bold'] * len(row)
        
        return ['font-weight: bold'] * len(row)
    
    # Aplicar estilos
    df_styled = df_ranking[columnas].style.apply(colorear_ranking, axis=1)
    df_styled = df_styled.set_properties(**{
        'text-align': 'center',
        'padding': '10px',
        'font-weight': 'bold',
        'font-size': '14px'
    })
    
    # Estilo para cabecera
    df_styled = df_styled.set_table_styles([
        {'selector': 'thead th',
         'props': [
             ('background-color', '#2c3e50'),
             ('color', 'white'),
             ('font-weight', 'bold'),
             ('font-size', '14px'),
             ('text-align', 'center'),
             ('padding', '10px')
         ]
        }
    ])
    
    st.dataframe(df_styled, use_container_width=True, hide_index=True)