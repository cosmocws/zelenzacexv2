# super/super_evolucion.py
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# =============================================
# FRASES MOTIVACIONALES
# =============================================
FRASES_MOTIVACIONALES = [
    "🚀 \"El exito es la suma de pequeños esfuerzos repetidos cada dia\"",
    "💪 \"No cuentes los dias, haz que los dias cuenten\"",
    "🎯 \"Cada llamada es una oportunidad de ser mejor que ayer\"",
    "⭐ \"La excelencia no es un acto, es un habito\"",
    "🔥 \"Hoy es un buen dia para romper records\"",
    "🏆 \"Los campeones no se hacen en el ring, se hacen en el entrenamiento diario\"",
    "🌟 \"El unico limite es el que te pones tu mismo\"",
    "📈 \"Cada venta empieza con una buena actitud\"",
    "🎪 \"Convierte cada NO en un TODAVIA NO\"",
    "💎 \"La persistencia es el camino del exito\""
]

RETOS_DIARIOS = [
    "🎯 Reto de hoy: ¿Quien consigue la primera venta del dia?",
    "📞 Reto de hoy: ¿Quien hace mas llamadas de +15min?",
    "⭐ Reto de hoy: ¿Quien consigue mas PI en sus ventas?",
    "🔥 Reto de hoy: ¿Quien mejora mas su SPH respecto a ayer?",
    "💬 Reto de hoy: Primer agente que haga 2 ventas con PVA",
    "🏆 Reto de hoy: ¿Que equipo llega antes a 5 ventas?",
    "🎯 Reto de hoy: ¿Quien consigue venta dual con PVA?",
    "📈 Reto de hoy: Superar el SPH de ayer entre todos"
]

def show_evolucion():
    """Seccion de evolucion SPH y dinamicas de equipo."""
    st.title("📈 Evolucion y Dinamicas")
    
    um = st.session_state.user_manager
    supervisor = st.session_state.user['username']
    mis_agentes = um.get_agents_by_manager(supervisor)
    
    if not mis_agentes:
        st.info("No tienes agentes asignados.")
        return
    
    from super.super_panel import cargar_registro_diario, cargar_datos_puntos
    registro = cargar_registro_diario()
    
    hoy = datetime.now()
    
    # =============================================
    # DINÁMICA DEL DÍA
    # =============================================
    st.write("### 🎮 Dinamica del Dia")
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        # Frase motivacional (cambia cada dia automaticamente)
        semilla = int(hoy.strftime('%Y%m%d'))
        random.seed(semilla)
        frase = random.choice(FRASES_MOTIVACIONALES)
        st.info(frase)
    
    with col_d2:
        random.seed(semilla + 1)
        reto = random.choice(RETOS_DIARIOS)
        st.warning(reto)
    
    # =============================================
    # RACHA DE LOGROS
    # =============================================
    st.markdown("---")
    st.write("### 🔥 Racha de Logros del Equipo")
    
    # Calcular dias consecutivos superando SPH
    dias_consecutivos = 0
    fecha_check = hoy - timedelta(days=1)
    
    while True:
        fecha_str = fecha_check.strftime('%Y-%m-%d')
        datos_dia = registro.get(fecha_str, {})
        
        if not datos_dia:
            break
        
        total_ventas = 0
        total_horas = 0
        
        for agente in mis_agentes:
            username = agente['username']
            if username in datos_dia:
                datos = datos_dia[username]
                if not datos.get('ausente', False):
                    total_ventas += datos.get('ventas', 0)
                    total_horas += agente.get('schedule', {}).get('daily_hours', 6.0)
        
        if total_horas > 0:
            sph_dia = round(total_ventas / (total_horas * 0.83), 2)
            sph_objetivo_medio = sum(a.get('sph_config', {}).get('target', 0.06) for a in mis_agentes) / max(len(mis_agentes), 1)
            
            if sph_dia >= sph_objetivo_medio:
                dias_consecutivos += 1
            else:
                break
        else:
            break
        
        fecha_check -= timedelta(days=1)
        if fecha_check < hoy - timedelta(days=30):
            break
    
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        if dias_consecutivos >= 5:
            st.metric("🔥 Racha Actual", f"{dias_consecutivos} dias", delta="¡Imparables!")
        elif dias_consecutivos >= 3:
            st.metric("📈 Racha Actual", f"{dias_consecutivos} dias", delta="¡Buen trabajo!")
        elif dias_consecutivos >= 1:
            st.metric("👍 Racha Actual", f"{dias_consecutivos} dias")
        else:
            st.metric("😴 Racha Actual", "0 dias", delta="¡A romperla hoy!")
    
    with col_r2:
        # Mejor racha del mes
        mejor_racha = dias_consecutivos
        st.metric("🏆 Record del Mes", f"{mejor_racha} dias")
    
    with col_r3:
        # Dias restantes del mes
        from calendar import monthrange
        dias_totales = monthrange(hoy.year, hoy.month)[1]
        dias_restantes = dias_totales - hoy.day
        st.metric("📅 Dias Restantes", dias_restantes, delta="del mes")
    
    # =============================================
    # EVOLUCIÓN SPH (GRÁFICO DE BARRAS)
    # =============================================
    st.markdown("---")
    st.write("### 📈 Evolucion SPH del Equipo (Ultimos 15 dias)")
    
    # Recopilar datos de los ultimos 15 dias
    datos_evolucion = []
    for i in range(14, -1, -1):
        fecha_check = hoy - timedelta(days=i)
        fecha_str = fecha_check.strftime('%Y-%m-%d')
        dia_semana = fecha_check.strftime('%a')
        
        datos_dia = registro.get(fecha_str, {})
        total_ventas = 0
        total_horas = 0
        agentes_activos = 0
        
        for agente in mis_agentes:
            username = agente['username']
            if username in datos_dia:
                datos = datos_dia[username]
                if not datos.get('ausente', False):
                    total_ventas += datos.get('ventas', 0)
                    total_horas += agente.get('schedule', {}).get('daily_hours', 6.0)
                    agentes_activos += 1
        
        if total_horas > 0 and agentes_activos > 0:
            sph = round(total_ventas / (total_horas * 0.83), 2)
        else:
            sph = 0.0
        
        # Calcular SPH objetivo medio del equipo
        sph_obj_medio = sum(a.get('sph_config', {}).get('target', 0.06) for a in mis_agentes) / max(len(mis_agentes), 1)
        
        es_fin_semana = fecha_check.weekday() >= 5
        es_hoy = fecha_str == hoy.strftime('%Y-%m-%d')
        
        datos_evolucion.append({
            'Fecha': fecha_str,
            'Dia': dia_semana,
            'SPH': sph,
            'SPH Obj': round(sph_obj_medio, 2),
            'Ventas': total_ventas,
            'Agentes': agentes_activos,
            'Fin de Semana': '🔴' if es_fin_semana else '',
            'Hoy': '⭐' if es_hoy else ''
        })
    
    df_evo = pd.DataFrame(datos_evolucion)
    
    # Mostrar grafico de barras con st.bar_chart
    st.subheader("SPH Diario vs Objetivo")
    
    chart_data = df_evo.set_index('Fecha')[['SPH', 'SPH Obj']]
    st.bar_chart(chart_data, use_container_width=True)
    
    # Tabla detallada
    st.write("**Desglose diario:**")
    
    def colorear_fila_evo(row):
        if row['Hoy'] == '⭐':
            return ['background-color: #fff3cd; color: #000000; font-weight: bold'] * len(row)
        elif row['SPH'] >= row['SPH Obj'] and row['Ventas'] > 0:
            return ['background-color: #d4edda'] * len(row)
        elif row['Ventas'] == 0:
            return ['color: #999'] * len(row)
        return [''] * len(row)
    
    df_styled = df_evo[['Fecha', 'Dia', 'SPH', 'SPH Obj', 'Ventas', 'Agentes', 'Fin de Semana', 'Hoy']].style.apply(colorear_fila_evo, axis=1)
    st.dataframe(df_styled, use_container_width=True, hide_index=True)
    
    # =============================================
    # PORRA DE VENTAS (OBJETIVO DE MAÑANA)
    # =============================================
    st.markdown("---")
    st.write("### 🎯 Porra de Ventas - Mañana")
    st.caption("Define un objetivo de ventas para mañana y motiva a tus agentes a superarlo")
    
    # Calcular media de ventas de los ultimos 5 dias laborables
    ventas_ultimos = []
    for i in range(1, 10):
        fecha_check = hoy - timedelta(days=i)
        if fecha_check.weekday() < 5:
            fecha_str = fecha_check.strftime('%Y-%m-%d')
            datos_dia = registro.get(fecha_str, {})
            ventas_dia = sum(
                datos_dia.get(a['username'], {}).get('ventas', 0)
                for a in mis_agentes
                if a['username'] in datos_dia and not datos_dia[a['username']].get('ausente', False)
            )
            if ventas_dia > 0:
                ventas_ultimos.append(ventas_dia)
            if len(ventas_ultimos) >= 5:
                break
    
    media_ventas = round(sum(ventas_ultimos) / max(len(ventas_ultimos), 1)) if ventas_ultimos else 10
    
    manana = (hoy + timedelta(days=1)).strftime('%Y-%m-%d')
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.metric("Media Ultimos Dias", f"{media_ventas} ventas")
    with col_p2:
        obj_porra = st.number_input("🎯 Objetivo para mañana", min_value=1, value=media_ventas + 2, step=1, key="obj_porra")
    with col_p3:
        st.write("")
        if st.button("🎯 Guardar Objetivo", type="primary", use_container_width=True):
            # Guardar en un archivo simple
            import json, os
            try:
                with open('data/porras_ventas.json', 'r', encoding='utf-8') as f:
                    porras = json.load(f)
            except:
                porras = {}
            
            if supervisor not in porras:
                porras[supervisor] = {}
            porras[supervisor][manana] = obj_porra
            
            os.makedirs('data', exist_ok=True)
            with open('data/porras_ventas.json', 'w', encoding='utf-8') as f:
                json.dump(porras, f, indent=4, ensure_ascii=False)
            
            st.success(f"✅ Objetivo guardado: {obj_porra} ventas para {manana}")
            st.rerun()
    
    # Mostrar porras activas
    try:
        with open('data/porras_ventas.json', 'r', encoding='utf-8') as f:
            porras = json.load(f)
        porras_sup = porras.get(supervisor, {})
        if porras_sup:
            st.write("**Porras activas:**")
            for fecha, obj in sorted(porras_sup.items()):
                st.write(f"- {fecha}: {obj} ventas")
    except:
        pass