# datos/datos_dashboard.py
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta, timezone

def show_dashboard():
    """Dashboard de sala - Carrusel de pantallas."""
    
    hora_esp = datetime.now(timezone(timedelta(hours=2)))
    
    um = st.session_state.user_manager
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
    hoy = datetime.now()
    hoy_str = hoy.strftime('%Y-%m-%d')
    mes_actual = hoy.strftime('%Y-%m')
    
    # Determinar qué pantalla mostrar según el minuto actual
    minuto = hora_esp.minute
    pantalla = (minuto // 5) % 5  # 0, 1, 2, 3, 4
    
    # =============================================
    # PANTALLA 0: MÉTRICAS DEL DÍA
    # =============================================
    if pantalla == 0:
        _mostrar_metricas_dia(um, registro, hoy_str)
    
    # =============================================
    # PANTALLA 1: RANKING MENSUAL CAPTA
    # =============================================
    elif pantalla == 1:
        _mostrar_ranking(um, registro, "CAPTA", mes_actual, hoy, "🏆 RANKING MENSUAL CAPTA", "#00b894")
    
    # =============================================
    # PANTALLA 2: RANKING MENSUAL WINBACK
    # =============================================
    elif pantalla == 2:
        _mostrar_ranking(um, registro, "WINBACK", mes_actual, hoy, "🏆 RANKING MENSUAL WINBACK", "#6c5ce7")
    
    # =============================================
    # PANTALLA 3: ÚLTIMAS VENTAS
    # =============================================
    elif pantalla == 3:
        _mostrar_ultimas_ventas(datos_puntos)
    
    # =============================================
    # PANTALLA 4: RESUMEN DE PUNTOS
    # =============================================
    elif pantalla == 4:
        _mostrar_resumen_puntos(um, datos_puntos, registro, mes_actual, hoy)
    
    # Barra de progreso del carrusel
    segundos_restantes = 300 - (hora_esp.second + hora_esp.minute * 60) % 300
    minutos_rest = segundos_restantes // 60
    segs_rest = segundos_restantes % 60
    
    pantallas_nombres = ["Métricas del Día", "Ranking CAPTA", "Ranking WINBACK", "Últimas Ventas", "Resumen Puntos"]
    # Contador en vivo con componente HTML
    st.components.v1.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial; }}
        .barra {{
            background: #0f3460; color: white; padding: 12px 20px;
            display: flex; justify-content: space-between; align-items: center;
            font-size: 16px; position: fixed; bottom: 0; left: 0; right: 0;
        }}
    </style>
    </head>
    <body>
    <div class="barra">
        <span>🔄 {pantallas_nombres[pantalla]}</span>
        <span>⏱️ Próxima pantalla en <b id="cuenta"></b></span>
        <span>📺 Pantalla {pantalla+1}/5</span>
        <span>🕐 {hora_esp.strftime('%H:%M:%S')}</span>
    </div>
    <script>
        var segundos = {segundos_restantes};
        function tick() {{
            var m = Math.floor(segundos / 60);
            var s = segundos % 60;
            document.getElementById('cuenta').innerText = m + 'm ' + s + 's';
            if (segundos <= 0) {{
                // Buscar y clickar el botón de refrescar de Streamlit
                var btns = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {{
                    if (btns[i].innerText.includes('🔄') || btns[i].title === 'Rerun') {{
                        btns[i].click();
                        break;
                    }}
                }}
            }}
            segundos--;
        }}
        tick();
        setInterval(tick, 1000);
    </script>
    </body>
    </html>
    """, height=60)


def _mostrar_metricas_dia(um, registro, hoy_str):
    """Pantalla 0: Métricas del día CAPTA + WINBACK."""
    st.markdown("""
    <style>
    .stApp { background-color: #1a1a2e; }
    .metric-card { background-color: #16213e; border-radius: 15px; padding: 20px; 
                   border: 2px solid #0f3460; text-align: center; margin: 10px; 
                   min-height: 160px; display: flex; flex-direction: column; justify-content: center; }
    .capta { border-color: #00b894; }
    .winback { border-color: #6c5ce7; }
    h1, h2, h3 { color: white !important; text-align: center; }
    .big-number { font-size: 52px; font-weight: bold; color: #e94560; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1>⚡ ZELENZA CEX - MÉTRICAS DEL DÍA</h1>", unsafe_allow_html=True)
    
    # Calcular métricas
    ventas_capta = ventas_winback = 0
    activos_capta = activos_winback = 0
    l5_capta = l5_winback = l15_capta = l15_winback = 0
    horas_capta = horas_winback = 0
    
    for agente in um.get_all_agents():
        if agente.get('standby', False):
            continue
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
            ventas_capta += ventas; activos_capta += 1
            l5_capta += l5; l15_capta += l15; horas_capta += horas_diarias
        else:
            ventas_winback += ventas; activos_winback += 1
            l5_winback += l5; l15_winback += l15; horas_winback += horas_diarias
    
    sph_capta = round(ventas_capta / (horas_capta * 0.83), 2) if ventas_capta > 0 and horas_capta > 0 else 0
    sph_winback = round(ventas_winback / (horas_winback * 0.83), 2) if ventas_winback > 0 and horas_winback > 0 else 0
    
    # CAPTA
    st.markdown("<h2 style='color:#00b894;'>🟢 CAPTA</h2>", unsafe_allow_html=True)
    cols = st.columns(5)
    _metrica(cols[0], "📦 Ventas", ventas_capta, "capta")
    _metrica(cols[1], "👥 Activos", activos_capta, "capta")
    _metrica(cols[2], "📞 +5min", l5_capta, "capta")
    _metrica(cols[3], "📞 +15min", l15_capta, "capta")
    _metrica(cols[4], "📈 SPH", sph_capta, "capta")
    
    # WINBACK
    st.markdown("<h2 style='color:#6c5ce7;'>🟣 WINBACK</h2>", unsafe_allow_html=True)
    cols = st.columns(5)
    _metrica(cols[0], "📦 Ventas", ventas_winback, "winback")
    _metrica(cols[1], "👥 Activos", activos_winback, "winback")
    _metrica(cols[2], "📞 +5min", l5_winback, "winback")
    _metrica(cols[3], "📞 +15min", l15_winback, "winback")
    _metrica(cols[4], "📈 SPH", sph_winback, "winback")


def _mostrar_ranking(um, registro, campana, mes_actual, hoy, titulo, color):
    """Pantalla 1/2: Ranking mensual."""
    st.markdown(f"""
    <style>
    .stApp {{ background-color: #1a1a2e; }}
    .rank-card {{ background-color: #16213e; border-radius: 15px; padding: 20px; 
                  text-align: center; margin: 10px; min-height: 200px;
                  display: flex; flex-direction: column; justify-content: center; }}
    .gold {{ border: 3px solid #FFD700; }}
    .silver {{ border: 3px solid #C0C0C0; }}
    .bronze {{ border: 3px solid #CD7F32; }}
    h1, h2, h3 {{ color: white !important; text-align: center; }}
    .rank-position {{ font-size: 60px; margin: 0; }}
    .rank-name {{ font-size: 28px; color: white; margin: 5px 0; }}
    .rank-sph {{ font-size: 36px; font-weight: bold; color: #e94560; }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<h1 style='color:{color};'>{titulo}</h1>", unsafe_allow_html=True)
    
    ranking = _calcular_ranking(um, registro, campana, mes_actual, hoy)
    
    if ranking:
        medallas = ["🥇", "🥈", "🥉"]
        borders = ["gold", "silver", "bronze"]
        cols = st.columns(min(len(ranking), 5))
        
        for i, r in enumerate(ranking[:5]):
            with cols[i]:
                border = borders[i] if i < 3 else ""
                medalla = medallas[i] if i < 3 else f"{i+1}️⃣"
                st.markdown(f"""
                <div class="rank-card {border}">
                    <p class="rank-position">{medalla}</p>
                    <p class="rank-name">{r['Agente']}</p>
                    <p style="color:white;">{r['Nombre']}</p>
                    <p class="rank-sph">SPH: {r['SPH']}</p>
                    <p style="color:white;">Ventas: {r['Ventas']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info(f"Sin datos de {campana}")


def _mostrar_ultimas_ventas(datos_puntos):
    """Pantalla 3: Últimas ventas."""
    st.markdown("""
    <style>
    .stApp { background-color: #1a1a2e; }
    .venta-card { background-color: #16213e; border-radius: 15px; padding: 20px; 
                  text-align: center; margin: 15px; min-height: 150px;
                  border: 2px solid #0f3460; }
    .capta-venta { border-color: #00b894; }
    .winback-venta { border-color: #6c5ce7; }
    h1, h2 { color: white !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1>⚡ ÚLTIMAS VENTAS</h1>", unsafe_allow_html=True)
    
    ultimas = []
    for username, ventas_agente in datos_puntos['ventas'].items():
        for fecha, ventas_dia in ventas_agente.items():
            for v in ventas_dia:
                ultimas.append({
                    'fecha': fecha,
                    'agente': username,
                    'producto': v.get('producto', ''),
                    'tipo': v.get('tipo', ''),
                    'puntos': v.get('puntos', 0),
                    'campaña': v.get('campaña', 'CAPTA')
                })
    
    ultimas.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Separar CAPTA y WINBACK
    capta_ventas = [v for v in ultimas if v['campaña'] == 'CAPTA'][:5]
    winback_ventas = [v for v in ultimas if v['campaña'] == 'WINBACK'][:5]
    
    if capta_ventas:
        st.markdown("<h2 style='color:#00b894;'>🟢 CAPTA</h2>", unsafe_allow_html=True)
        cols = st.columns(5)
        for i, v in enumerate(capta_ventas):
            with cols[i]:
                st.markdown(f"""
                <div class="venta-card capta-venta">
                    <h3>{v['agente']}</h3>
                    <p style="color:white;font-size:20px;">{v['producto']}</p>
                    <p style="color:#e94560;font-size:24px;">{v['puntos']} pts</p>
                </div>
                """, unsafe_allow_html=True)
    
    if winback_ventas:
        st.markdown("<h2 style='color:#6c5ce7;'>🟣 WINBACK</h2>", unsafe_allow_html=True)
        cols = st.columns(5)
        for i, v in enumerate(winback_ventas):
            with cols[i]:
                st.markdown(f"""
                <div class="venta-card winback-venta">
                    <h3>{v['agente']}</h3>
                    <p style="color:white;font-size:20px;">{v['producto']}</p>
                    <p style="color:#e94560;font-size:24px;">{v['puntos']} pts</p>
                </div>
                """, unsafe_allow_html=True)


def _mostrar_resumen_puntos(um, datos_puntos, registro, mes_actual, hoy):
    """Pantalla 4: Resumen de puntos."""
    st.markdown("""
    <style>
    .stApp { background-color: #1a1a2e; }
    .puntos-card { background-color: #16213e; border-radius: 15px; padding: 25px; 
                   text-align: center; margin: 10px; border: 2px solid #0f3460;
                   min-height: 180px; display: flex; flex-direction: column; justify-content: center; }
    h1, h2, h3 { color: white !important; text-align: center; }
    .puntos-number { font-size: 56px; font-weight: bold; color: #e94560; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1>💰 RESUMEN DE PUNTOS</h1>", unsafe_allow_html=True)
    
    # Puntos del día
    puntos_dia = 0
    hoy_str = hoy.strftime('%Y-%m-%d')
    for username, ventas_agente in datos_puntos['ventas'].items():
        for fecha, ventas_dia in ventas_agente.items():
            if fecha == hoy_str:
                for v in ventas_dia:
                    puntos_dia += v.get('puntos', 0)
        for fecha, extras in datos_puntos['puntos_extra'].get(username, {}).items():
            if fecha == hoy_str:
                if isinstance(extras, list):
                    puntos_dia += sum(e.get('puntos', 0) for e in extras)
                elif isinstance(extras, dict):
                    puntos_dia += extras.get('puntos', 0)
    
    # Puntos del mes
    puntos_mes = 0
    for username, ventas_agente in datos_puntos['ventas'].items():
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual):
                for v in ventas_dia:
                    puntos_mes += v.get('puntos', 0)
        for fecha, extras in datos_puntos['puntos_extra'].get(username, {}).items():
            if fecha.startswith(mes_actual):
                if isinstance(extras, list):
                    puntos_mes += sum(e.get('puntos', 0) for e in extras)
                elif isinstance(extras, dict):
                    puntos_mes += extras.get('puntos', 0)
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="puntos-card">
            <h2>📅 Puntos Hoy</h2>
            <p class="puntos-number">{puntos_dia}</p>
            <p style="color:white;">{puntos_dia/22:.2f}€</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="puntos-card">
            <h2>📆 Puntos Mes</h2>
            <p class="puntos-number">{puntos_mes}</p>
            <p style="color:white;">{puntos_mes/22:.2f}€</p>
        </div>
        """, unsafe_allow_html=True)
    
    # TOP 3 puntos del mes
    ranking_puntos = []
    for agente in um.get_all_agents():
        if agente.get('standby', False):
            continue
        username = agente['username']
        pts = 0
        for fecha, ventas_dia in datos_puntos['ventas'].get(username, {}).items():
            if fecha.startswith(mes_actual):
                for v in ventas_dia:
                    pts += v.get('puntos', 0)
        for fecha, extras in datos_puntos['puntos_extra'].get(username, {}).items():
            if fecha.startswith(mes_actual):
                if isinstance(extras, list):
                    pts += sum(e.get('puntos', 0) for e in extras)
                elif isinstance(extras, dict):
                    pts += extras.get('puntos', 0)
        if pts > 0:
            ranking_puntos.append({'Agente': username, 'Nombre': agente.get('nombre', ''), 'Puntos': pts})
    
    ranking_puntos.sort(key=lambda x: x['Puntos'], reverse=True)
    
    with col3:
        st.markdown(f"""
        <div class="puntos-card">
            <h2>🏆 TOP 3 Puntos</h2>
            {"".join(f'<p style="color:white;font-size:18px;">{r["Agente"]}: {r["Puntos"]} pts</p>' for r in ranking_puntos[:3])}
        </div>
        """, unsafe_allow_html=True)


def _metrica(col, titulo, valor, tipo):
    """Renderiza una métrica individual."""
    with col:
        st.markdown(f"""
        <div class="metric-card {tipo}">
            <h3>{titulo}</h3>
            <p class="big-number">{valor}</p>
        </div>
        """, unsafe_allow_html=True)


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