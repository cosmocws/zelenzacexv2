# agent/agent_inicio.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from calendar import monthrange
from core.monitorizaciones import obtener_ultima_monitorizacion, obtener_monitorizaciones_empleado
from super.super_panel import PUNTOS_PRODUCTO, cargar_datos_puntos, cargar_registro_diario

@st.cache_data(ttl=30)
def cargar_datos_inicio():
    return cargar_datos_puntos(), cargar_registro_diario()

def show_inicio():
    """Pantalla de inicio del agente."""
    st.title("🏠 Mi Inicio")
    
    agente = st.session_state.user
    username = agente['username']
    campana_agente = agente.get('campaign', 'CAPTA')
    
    datos_puntos, registro = cargar_datos_inicio()
    
    hoy_dt = datetime.now()
    mes_actual = hoy_dt.strftime('%Y-%m')
    incorporacion_str = agente.get('incorporation_date', hoy_dt.strftime('%Y-%m-%d'))
    try:
        fecha_incorporacion = datetime.strptime(incorporacion_str, '%Y-%m-%d')
    except:
        fecha_incorporacion = hoy_dt
    
    # Lista de meses disponibles (desde incorporación hasta hoy)
    meses_disponibles = []
    for y in range(fecha_incorporacion.year, hoy_dt.year + 1):
        for m in range(1, 13):
            mes_str = f"{y}-{m:02d}"
            if mes_str >= fecha_incorporacion.strftime('%Y-%m') and mes_str <= mes_actual:
                meses_disponibles.append(mes_str)
    meses_disponibles.sort(reverse=True)
    meses_nombres = {m: datetime.strptime(m, '%Y-%m').strftime('%B %Y') for m in meses_disponibles}
    
    # =============================================
    # MENSAJES CON EL SUPERVISOR
    # =============================================
    with st.expander(f"💬 Mensajes ({_contar_no_leidos(username)})", expanded=False):
        _mostrar_mensajes_agente(username)
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        # --- MONITORIZACIONES (con selector de mes) ---
        col_tit1, col_sel1 = st.columns([3, 1])
        with col_tit1:
            st.write("### 📋 Monitorizaciones")
        with col_sel1:
            monis_disponibles = obtener_monitorizaciones_empleado(username)
            fechas_monis = ["Última"] + [m.get('fecha_monitorizacion', '?') for m in (monis_disponibles or [])]
            moni_sel = st.selectbox("Ver", fechas_monis, key="moni_sel", label_visibility="collapsed")
        
        if monis_disponibles:
            if moni_sel == "Última":
                ultima = monis_disponibles[0]
            else:
                ultima = next((m for m in monis_disponibles if m.get('fecha_monitorizacion') == moni_sel), monis_disponibles[0])
            
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
                st.markdown("**🔑 Puntos Clave:**")
                for p in puntos:
                    st.markdown(f"""
                    <div style="background-color: #fff3cd; border: 2px solid #ffc107; 
                                border-radius: 8px; padding: 12px; margin: 5px 0; 
                                font-size: 20px; font-weight: bold; color: #856404; text-align: center;">
                        ⚠️ {p}
                    </div>
                    """, unsafe_allow_html=True)
            
            if ultima.get('feedback'):
                with st.expander("📝 Feedback"):
                    st.write(ultima['feedback'])
            
            if ultima.get('plan_accion'):
                with st.expander("🎯 Plan de Accion"):
                    st.write(ultima['plan_accion'])
        else:
            st.info("No tienes monitorizaciones registradas.")
    
    with col_der:
        # --- MI SPH (con selector de mes) ---
        col_tit2, col_sel2 = st.columns([3, 1])
        with col_tit2:
            st.write("### 📈 Mi SPH")
        with col_sel2:
            mes_sph = st.selectbox("Mes", meses_disponibles, format_func=lambda x: meses_nombres.get(x, x), key="mes_sph", label_visibility="collapsed")
        
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        sph_config = agente.get('sph_config', {})
        sph_target = sph_config.get('target', 0.06)
        
        ventas_mes = sum(len(ventas_dia) for fecha, ventas_dia in datos_puntos['ventas'].get(username, {}).items() if fecha.startswith(mes_sph))
        
        año_mes, mes_mes = int(mes_sph[:4]), int(mes_sph[5:7])
        dias_en_mes = monthrange(año_mes, mes_mes)[1]
        dia_fin = hoy_dt.day if mes_sph == mes_actual else dias_en_mes
        dia_ini = max(fecha_incorporacion.day, 1) if mes_sph == fecha_incorporacion.strftime('%Y-%m') else 1
        
        horas_totales = 0
        for d in range(dia_ini, dia_fin + 1):
            fecha_check = datetime(año_mes, mes_mes, d)
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
        
        sph_real = round(ventas_mes / (horas_totales * 0.83), 3) if ventas_mes > 0 and horas_totales > 0 else 0.0
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: st.metric("SPH Objetivo", sph_target)
        with col_s2: st.metric("SPH Real", sph_real, delta=f"{sph_real - sph_target:.2f}")
        with col_s3: st.metric("Ventas Mes", ventas_mes)
        
        # --- MIS PUNTOS (con selector de mes) ---
        col_tit3, col_sel3 = st.columns([3, 1])
        with col_tit3:
            st.write("### ⭐ Mis Puntos")
        with col_sel3:
            mes_ptos = st.selectbox("Mes", meses_disponibles, format_func=lambda x: meses_nombres.get(x, x), key="mes_ptos", label_visibility="collapsed")
        
        ventas_agente = datos_puntos['ventas'].get(username, {})
        puntos_ventas_no_cumple = sum(v.get('puntos', 0) for fecha, ventas_dia in ventas_agente.items() if fecha.startswith(mes_ptos) for v in ventas_dia)
        
        puntos_ventas_cumple = 0
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_ptos):
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
        
        puntos_extra_mes = 0
        for fecha, extras in datos_puntos['puntos_extra'].get(username, {}).items():
            if fecha.startswith(mes_ptos):
                if isinstance(extras, list): puntos_extra_mes += sum(e.get('puntos', 0) for e in extras)
                elif isinstance(extras, dict): puntos_extra_mes += extras.get('puntos', 0)
        
        st.write("**💼 Puntos por Ventas**")
        st.caption("Se pagan al cerrar el mes")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.metric("Obj NO Cumplido", f"{puntos_ventas_no_cumple} pts")
            st.caption(f"💰 {puntos_ventas_no_cumple/22:.2f}€")
        with col_v2:
            st.metric("Obj Cumplido", f"{puntos_ventas_cumple} pts")
            st.caption(f"💰 {puntos_ventas_cumple/22:.2f}€")
        
        st.write("**🎁 Puntos Extra**")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.metric("Puntos Extra", puntos_extra_mes)
            st.caption(f"💰 {puntos_extra_mes/22:.2f}€")
        with col_e2:
            pagos = datos_puntos['pagos_realizados'].get(username, [])
            pagado_mes = sum(p.get('puntos_pagados', 0) for p in pagos if p.get('fecha', '').startswith(mes_ptos))
            st.metric("PAGADOS", pagado_mes)
            st.caption(f"💰 {pagado_mes/22:.2f}€")
    
    # =============================================
    # RANKING DE CAMPAÑA (con selector de mes)
    # =============================================
    st.markdown("---")
    col_tit4, col_sel4 = st.columns([3, 1])
    with col_tit4:
        st.write("### 🏆 Ranking de Campaña")
    with col_sel4:
        mes_rank = st.selectbox("Mes", meses_disponibles, format_func=lambda x: meses_nombres.get(x, x), key="mes_rank", label_visibility="collapsed")
    
    st.caption(f"Agentes en campaña **{campana_agente}** ordenados por SPH")
    
    um = st.session_state.user_manager
    todos_agentes = um.get_all_agents()
    
    año_r, mes_r = int(mes_rank[:4]), int(mes_rank[5:7])
    dias_r = monthrange(año_r, mes_r)[1]
    dia_fin_r = hoy_dt.day if mes_rank == mes_actual else dias_r
    
    ranking = []
    for a in todos_agentes:
        a_username = a['username']
        
        ventas = 0
        for fecha, agentes in registro.items():
            if fecha.startswith(mes_rank) and a_username in agentes:
                datos = agentes[a_username]
                if datos.get('campaña', '') == campana_agente:
                    ventas += datos.get('ventas', 0)
        
        horas_dia = a.get('schedule', {}).get('daily_hours', 6.0)
        sph_config_a = a.get('sph_config', {})
        sph_obj = sph_config_a.get('target', 0.06)
        
        horas_tot = 0
        dia_inicio_a = max(datetime.strptime(a.get('incorporation_date', hoy_dt.strftime('%Y-%m-%d')), '%Y-%m-%d').day if a.get('incorporation_date') else 1, 1)
        dia_ini_r = dia_inicio_a if mes_rank == fecha_incorporacion.strftime('%Y-%m') else 1
        for d in range(dia_ini_r, dia_fin_r + 1):
            fecha_check = datetime(año_r, mes_r, d)
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
        
        sph = round(ventas / (horas_tot * 0.83), 3) if ventas > 0 and horas_tot > 0 else 0.0
        dias_efec = round(horas_tot / horas_dia, 1) if horas_dia > 0 else 0
        
        ranking.append({
            'Agente': a_username, 'Nombre': a.get('nombre', ''),
            'SPH': sph, 'SPH Obj': sph_obj, 'Ventas': ventas, 'Dias Trab.': dias_efec
        })
    
    ranking.sort(key=lambda x: x['Ventas'], reverse=True)
    ranking = [r for r in ranking if r['Ventas'] > 0]
    
    for i, r in enumerate(ranking):
        r['#'] = i + 1
        r['Tu'] = '👈 TU' if r['Agente'] == username else ''
    
    df_ranking = pd.DataFrame(ranking)
    columnas = ['#', 'Agente', 'Nombre', 'SPH', 'SPH Obj', 'Ventas', 'Dias Trab.', 'Tu']
    
    def colorear_ranking(row):
        posicion = row['#']
        if posicion == 1: return ['background-color: #FFD700; color: #000000; font-weight: bold'] * len(row)
        elif posicion == 2: return ['background-color: #C0C0C0; color: #000000; font-weight: bold'] * len(row)
        elif posicion == 3: return ['background-color: #CD7F32; color: #000000; font-weight: bold'] * len(row)
        if row['Tu'] == '👈 TU': return ['background-color: #fff3cd; color: #000000; font-weight: bold'] * len(row)
        return ['font-weight: bold'] * len(row)
    
    df_styled = df_ranking[columnas].style.apply(colorear_ranking, axis=1)
    df_styled = df_styled.set_properties(**{'text-align': 'center', 'padding': '10px', 'font-weight': 'bold', 'font-size': '14px'})
    df_styled = df_styled.set_table_styles([
        {'selector': 'thead th', 'props': [('background-color', '#2c3e50'), ('color', 'white'), ('font-weight', 'bold'), ('font-size', '14px'), ('text-align', 'center'), ('padding', '10px')]},
    ])
    
    st.dataframe(df_styled, use_container_width=True, hide_index=True)


# =============================================
# FUNCIONES DE MENSAJERIA
# =============================================

def _contar_no_leidos(username):
    try:
        with open('data/mensajes.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return sum(1 for m in datos['mensajes'] if m['para'] == username and not m['leido'])
    except:
        return 0

def _mostrar_mensajes_agente(username):
    supervisor = st.session_state.user.get('manager', '')
    
    try:
        with open('data/mensajes.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except:
        datos = {"mensajes": [], "ultimo_id": 0}
    
    mis_mensajes = [m for m in datos['mensajes'] if m['para'] == username or m['de'] == username]
    mis_mensajes.sort(key=lambda x: x['id'], reverse=True)
    
    if mis_mensajes:
        st.write("**📋 Bandeja de mensajes:**")
        for m in mis_mensajes[:10]:
            leido_icon = "✅" if m['leido'] else "🔵"
            direccion = m.get('direccion', '')
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.caption(f"{m['fecha'][:16]}")
                with col2:
                    st.write(f"{leido_icon} **{m['de']}**: {m['texto']}")
                    if direccion:
                        st.caption(f"📍 {direccion}")
                with col3:
                    if not m['leido'] and m['para'] == username:
                        if st.button("✅ Leído", key=f"leer_{m['id']}"):
                            m['leido'] = True
                            os.makedirs('data', exist_ok=True)
                            with open('data/mensajes.json', 'w', encoding='utf-8') as f:
                                json.dump(datos, f, indent=4, ensure_ascii=False)
                            st.rerun()
    else:
        st.info("No tienes mensajes")
    
    st.markdown("---")
    st.write("**📤 Enviar mensaje a tu supervisor:**")
    texto = st.text_area("Mensaje", key="msg_agente_texto", height=80, placeholder="Escribe tu mensaje...")
    direccion = st.text_input("Dirección (opcional)", key="msg_agente_dir", placeholder="Ej: Calle Mayor 1, Madrid")
    
    if st.button("📤 Enviar", key="msg_agente_enviar"):
        if texto.strip() and supervisor:
            datos['ultimo_id'] += 1
            datos['mensajes'].append({
                "id": datos['ultimo_id'],
                "de": username,
                "para": supervisor,
                "fecha": datetime.now().isoformat(),
                "texto": texto.strip(),
                "leido": False,
                "direccion": direccion.strip()
            })
            os.makedirs('data', exist_ok=True)
            with open('data/mensajes.json', 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            st.success("✅ Mensaje enviado")
            st.rerun()
        elif not supervisor:
            st.warning("No tienes supervisor asignado")