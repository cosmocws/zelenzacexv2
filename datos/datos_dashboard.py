# datos/datos_dashboard.py
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta, timezone

def show_dashboard():
    """Dashboard de sala - Modo pantalla grande."""
    
    st.markdown("""
    <style>
    .stApp { background-color: #1a1a2e; }
    .metric-card { background-color: #16213e; border-radius: 15px; padding: 20px; 
                   border: 2px solid #0f3460; text-align: center; margin: 10px; }
    .gold { border-color: #FFD700; }
    .silver { border-color: #C0C0C0; }
    .bronze { border-color: #CD7F32; }
    .capta { border-color: #00b894; }
    .winback { border-color: #6c5ce7; }
    h1, h2, h3 { color: white !important; text-align: center; }
    .big-number { font-size: 36px; font-weight: bold; color: #e94560; }
    .venta-card { background-color: #0f3460; border-radius: 10px; padding: 15px; 
                  margin: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)
    
    hora_esp = datetime.now(timezone(timedelta(hours=2)))
    st.markdown(f'<p style="text-align:right;color:gray">🔄 Auto-refresh: 5min | {hora_esp.strftime("%H:%M:%S")}</p>', 
                unsafe_allow_html=True)
    
    um = st.session_state.user_manager
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
    hoy = datetime.now()
    hoy_str = hoy.strftime('%Y-%m-%d')
    mes_actual = hoy.strftime('%Y-%m')
    
    # =============================================
    # CABECERA
    # =============================================
    st.markdown("<h1>⚡ ZELENZA CEX - PANEL DE SALA</h1>", unsafe_allow_html=True)
    
    # Calcular métricas por campaña
    ventas_capta = 0
    ventas_winback = 0
    activos_capta = 0
    activos_winback = 0
    llamadas_5m_capta = 0
    llamadas_5m_winback = 0
    llamadas_15m_capta = 0
    llamadas_15m_winback = 0
    horas_capta = 0
    horas_winback = 0
    
    for agente in um.get_all_agents():
        username = agente['username']
        campana = agente.get('campaign', 'CAPTA')
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        
        datos_dia = registro.get(hoy_str, {}).get(username, {})
        if datos_dia.get('ausente', False):
            continue
        
        ventas = datos_dia.get('ventas', 0)
        l5 = datos_dia.get('llamadas_5m', 0)
        l15 = datos_dia.get('llamadas_15m', 0)
        
        if campana == 'CAPTA':
            ventas_capta += ventas
            activos_capta += 1
            llamadas_5m_capta += l5
            llamadas_15m_capta += l15
            horas_capta += horas_diarias
        else:
            ventas_winback += ventas
            activos_winback += 1
            llamadas_5m_winback += l5
            llamadas_15m_winback += l15
            horas_winback += horas_diarias
    
    sph_capta = round(ventas_capta / (horas_capta * 0.83), 2) if ventas_capta > 0 and horas_capta > 0 else 0
    sph_winback = round(ventas_winback / (horas_winback * 0.83), 2) if ventas_winback > 0 and horas_winback > 0 else 0
    
    # =============================================
    # MÉTRICAS CAPTA
    # =============================================
    st.markdown("<h2 style='color:#00b894;'>🟢 CAPTA</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card capta"><h3>📦 Ventas</h3><p class="big-number">{ventas_capta}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card capta"><h3>👥 Activos</h3><p class="big-number">{activos_capta}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card capta"><h3>📞 +5min</h3><p class="big-number">{llamadas_5m_capta}</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card capta"><h3>📞 +15min</h3><p class="big-number">{llamadas_15m_capta}</p></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card capta"><h3>📈 SPH</h3><p class="big-number">{sph_capta}</p></div>', unsafe_allow_html=True)
    
    # =============================================
    # MÉTRICAS WINBACK
    # =============================================
    st.markdown("<h2 style='color:#6c5ce7;'>🟣 WINBACK</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card winback"><h3>📦 Ventas</h3><p class="big-number">{ventas_winback}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card winback"><h3>👥 Activos</h3><p class="big-number">{activos_winback}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card winback"><h3>📞 +5min</h3><p class="big-number">{llamadas_5m_winback}</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card winback"><h3>📞 +15min</h3><p class="big-number">{llamadas_15m_winback}</p></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card winback"><h3>📈 SPH</h3><p class="big-number">{sph_winback}</p></div>', unsafe_allow_html=True)
    
    # =============================================
    # RANKING CAPTA
    # =============================================
    st.markdown("---")
    st.markdown("<h2>🏆 RANKING CAPTA</h2>", unsafe_allow_html=True)
    
    ranking_capta = _calcular_ranking(um, registro, "CAPTA", mes_actual, hoy)
    
    if ranking_capta:
        cols = st.columns(min(len(ranking_capta), 5))
        medallas = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, r in enumerate(ranking_capta[:5]):
            with cols[i]:
                border = "gold" if i == 0 else ("silver" if i == 1 else ("bronze" if i == 2 else "capta"))
                st.markdown(f"""
                <div class="metric-card {border}">
                    <h2>{medallas[i]}</h2>
                    <h3>{r['Agente']}</h3>
                    <p style="color:white;">SPH: {r['SPH']} | Ventas: {r['Ventas']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # =============================================
    # RANKING WINBACK
    # =============================================
    st.markdown("---")
    st.markdown("<h2>🏆 RANKING WINBACK</h2>", unsafe_allow_html=True)
    
    ranking_winback = _calcular_ranking(um, registro, "WINBACK", mes_actual, hoy)
    
    if ranking_winback:
        cols = st.columns(min(len(ranking_winback), 5))
        for i, r in enumerate(ranking_winback[:5]):
            with cols[i]:
                border = "gold" if i == 0 else ("silver" if i == 1 else ("bronze" if i == 2 else "winback"))
                st.markdown(f"""
                <div class="metric-card {border}">
                    <h2>{medallas[i]}</h2>
                    <h3>{r['Agente']}</h3>
                    <p style="color:white;">SPH: {r['SPH']} | Ventas: {r['Ventas']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # =============================================
    # ÚLTIMAS VENTAS
    # =============================================
    st.markdown("---")
    st.markdown("<h2>⚡ ÚLTIMAS VENTAS</h2>", unsafe_allow_html=True)
    
    ultimas_ventas = []
    for username, ventas_agente in datos_puntos['ventas'].items():
        for fecha, ventas_dia in ventas_agente.items():
            for v in ventas_dia:
                ultimas_ventas.append({
                    'fecha': fecha,
                    'agente': username,
                    'producto': v.get('producto', ''),
                    'tipo': v.get('tipo', ''),
                    'puntos': v.get('puntos', 0)
                })
    
    ultimas_ventas.sort(key=lambda x: x['fecha'], reverse=True)
    
    cols = st.columns(5)
    for i, v in enumerate(ultimas_ventas[:5]):
        with cols[i]:
            st.markdown(f"""
            <div class="venta-card">
                <strong>{v['agente']}</strong><br>
                {v['producto']}<br>
                <small>{v['tipo']} | {v['puntos']} pts</small>
            </div>
            """, unsafe_allow_html=True)
    
    # =============================================
    # FRASE MOTIVACIONAL
    # =============================================
    st.markdown("---")
    frases = [
        "🚀 \"El éxito es la suma de pequeños esfuerzos repetidos cada día\"",
        "💪 \"No cuentes los días, haz que los días cuenten\"",
        "🎯 \"Cada llamada es una oportunidad de ser mejor que ayer\"",
        "⭐ \"La excelencia no es un acto, es un hábito\"",
        "🔥 \"Hoy es un buen día para romper récords\""
    ]
    random.seed(int(hoy.strftime('%Y%m%d')))
    frase = random.choice(frases)
    st.markdown(f"<h3 style='text-align:center; color:#e94560;'>{frase}</h3>", unsafe_allow_html=True)


def _calcular_ranking(um, registro, campana, mes_actual, hoy):
    """Calcula ranking para una campaña."""
    todos_agentes = um.get_all_agents()
    ranking = []
    
    for a in todos_agentes:
        if a.get('standby', False) or a.get('campaign', '') != campana:
            continue
        
        a_username = a['username']
        ventas = 0
        horas_dia = a.get('schedule', {}).get('daily_hours', 6.0)
        horas_tot = 0
        
        for fecha, agentes in registro.items():
            if fecha.startswith(mes_actual) and a_username in agentes:
                datos = agentes[a_username]
                if datos.get('campaña', '') == campana:
                    ventas += datos.get('ventas', 0)
        
        dia_inicio = max(datetime.strptime(a.get('incorporation_date', hoy.strftime('%Y-%m-%d')), '%Y-%m-%d').day if a.get('incorporation_date') else 1, 1)
        for d in range(dia_inicio, hoy.day + 1):
            fecha_check = datetime(hoy.year, hoy.month, d)
            if fecha_check.weekday() < 5:
                fecha_str = fecha_check.strftime('%Y-%m-%d')
                reg_dia = registro.get(fecha_str, {}).get(a_username, {})
                if reg_dia.get('campaña', '') == campana and not reg_dia.get('ausente', False):
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
        
        if ventas > 0:
            ranking.append({'Agente': a_username, 'Nombre': a.get('nombre', ''), 'SPH': sph, 'Ventas': ventas})
    
    ranking.sort(key=lambda x: x['SPH'], reverse=True)
    return ranking[:10]