# coo/coo_inicio.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show_inicio_coo():
    st.title("🏠 Panel de Operaciones")
    
    um = st.session_state.user_manager
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
    hoy = datetime.now()
    mes_actual = hoy.strftime('%Y-%m')
    
    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        campana_filtro = st.selectbox("Campaña:", ["TODAS", "CAPTA", "WINBACK"], key="coo_campana")
    with col_f2:
        periodo_filtro = st.selectbox("Período:", ["Día específico", "Semana anterior (L-V)", "Mes actual"], key="coo_periodo")
    with col_f3:
        orden = st.selectbox("Ordenar por:", ["Ventas", "SPH"], key="coo_orden")
    
    # Determinar fechas
    if periodo_filtro == "Día específico":
        fecha_dia = st.date_input("Día:", value=hoy, key="coo_fecha")
        fecha_ini = fecha_fin = fecha_dia.strftime('%Y-%m-%d')
    elif periodo_filtro == "Semana anterior (L-V)":
        lunes = hoy - timedelta(days=hoy.weekday() + 7)
        fecha_ini = lunes.strftime('%Y-%m-%d')
        fecha_fin = (lunes + timedelta(days=4)).strftime('%Y-%m-%d')
    else:
        fecha_ini = hoy.strftime('%Y-%m') + '-01'
        fecha_fin = hoy.strftime('%Y-%m-%d')
    
    # =============================================
    # MÉTRICAS GENERALES
    # =============================================
    # Obtener agentes según filtro
    if campana_filtro == "TODAS":
        agentes = um.get_all_agents()
    else:
        agentes = um.get_agents_by_campaign(campana_filtro)
    
    agentes_activos = [a for a in agentes if not a.get('standby', False)]
    
    total_ventas = 0
    total_llamadas_5m = 0
    total_llamadas_15m = 0
    total_horas_efectivas = 0
    total_ausentes = 0
    
    for agente in agentes:
        username = agente['username']
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        
        if agente.get('standby', False):
            continue
        
        for fecha_str, datos_dia in registro.items():
            if fecha_ini <= fecha_str <= fecha_fin:
                if username in datos_dia:
                    datos = datos_dia[username]
                    if not datos.get('ausente', False):
                        total_ventas += datos.get('ventas', 0)
                        total_llamadas_5m += datos.get('llamadas_5m', 0)
                        total_llamadas_15m += datos.get('llamadas_15m', 0)
                        hora_salida = datos.get('hora_salida', '')
                        if hora_salida:
                            try:
                                h_ini = datetime.strptime(agente.get('schedule', {}).get('start_time', '15:00'), '%H:%M')
                                h_fin = datetime.strptime(hora_salida, '%H:%M')
                                total_horas_efectivas += round((h_fin - h_ini).seconds / 3600, 2)
                            except:
                                total_horas_efectivas += horas_diarias
                        else:
                            total_horas_efectivas += horas_diarias
                    else:
                        total_ausentes += 1
    
    sph_global = round(total_ventas / (total_horas_efectivas * 0.83), 3) if total_ventas > 0 and total_horas_efectivas > 0 else 0.0
    
    st.markdown("---")
    st.write("### 📊 Métricas Generales")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("👥 Agentes", len(agentes_activos))
    with col2: st.metric("📦 Ventas", total_ventas)
    with col3: st.metric("📈 SPH Global", sph_global)
    with col4: st.metric("📞 Llamadas +5m", total_llamadas_5m)
    with col5: st.metric("📞 Llamadas +15m", total_llamadas_15m)
    
    col_a1, col_a2 = st.columns(2)
    with col_a1: st.metric("⏰ Horas Efectivas", f"{total_horas_efectivas:.1f}h")
    with col_a2: st.metric("🔴 Ausentes", total_ausentes)
    
    # Ranking CAPTA
    st.markdown("---")
    st.subheader("🏆 Ranking CAPTA")
    _mostrar_ranking_coo(um, registro, "CAPTA", fecha_ini, fecha_fin, campana_filtro, orden, hoy)
    
    # Ranking WINBACK
    st.markdown("---")
    st.subheader("🏆 Ranking WINBACK")
    _mostrar_ranking_coo(um, registro, "WINBACK", fecha_ini, fecha_fin, campana_filtro, orden, hoy)


def _mostrar_ranking_coo(um, registro, campana, fecha_ini, fecha_fin, campana_filtro, orden, hoy):
    if campana_filtro != "TODAS" and campana_filtro != campana:
        st.info(f"Filtrado por {campana_filtro}")
        return
    
    agentes = um.get_agents_by_campaign(campana) if campana != "TODAS" else um.get_all_agents()
    
    ranking = []
    for a in agentes:
        if a.get('standby', False):
            continue
        username = a['username']
        ventas = 0
        horas_tot = 0
        horas_dia = a.get('schedule', {}).get('daily_hours', 6.0)
        
        for fecha, datos in registro.items():
            if fecha_ini <= fecha <= fecha_fin and username in datos:
                d = datos[username]
                if d.get('campaña', '') == campana and not d.get('ausente', False):
                    ventas += d.get('ventas', 0)
                    horas_tot += horas_dia
        
        sph = round(ventas / (horas_tot * 0.83), 3) if ventas > 0 and horas_tot > 0 else 0.0
        
        if ventas > 0:
            ranking.append({'Agente': username, 'Nombre': a.get('nombre', ''), 'SPH': sph, 'Ventas': ventas})
    
    if orden == "Ventas":
        ranking.sort(key=lambda x: x['Ventas'], reverse=True)
    else:
        ranking.sort(key=lambda x: x['SPH'], reverse=True)
    
    if ranking:
        df = pd.DataFrame(ranking[:10])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"Sin datos para {campana}")