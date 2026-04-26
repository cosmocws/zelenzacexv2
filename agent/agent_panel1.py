# agent/agent_panel.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from features.calculator.electricidad import comparar_planes, colorear_fila_por_tipo
from core.monitorizaciones import obtener_ultima_monitorizacion

def show_mi_panel():
    """Panel principal del agente con pestañas."""
    st.title("📊 Mi Panel de Agente")
    
    agente = st.session_state.user
    username = agente['username']
    campana_agente = agente.get('campaign', 'CAPTA')
    
    # Cargar datos
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    
    # Pestañas
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Inicio",
        "📊 Calculadora",
        "🎯 Mis Objetivos",
        "📅 Ausencias"
    ])
    
    # =============================================
    # TAB 1: INICIO
    # =============================================
    with tab1:
        st.subheader("🏠 Mi Inicio")
        
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
            
            hoy = datetime.now().strftime('%Y-%m-%d')
            mes_actual = datetime.now().strftime('%Y-%m')
            sph_target = agente.get('sph_config', {}).get('target', 0.06)
            horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
            
            # Calcular ventas del mes
            ventas_mes = 0
            ventas_agente = datos_puntos['ventas'].get(username, {})
            for fecha, ventas_dia in ventas_agente.items():
                if fecha.startswith(mes_actual):
                    ventas_mes += len(ventas_dia)
            
            # Calcular dias trabajados y ausencias
            dias_laborables = 0
            dias_ausente = 0
            hoy_dt = datetime.now()
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
            
            # Puntos pendientes
            from super.super_panel import calcular_puntos_pendientes
            pendientes = calcular_puntos_pendientes(username, datos_puntos)
            
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("Puntos Ventas", puntos_mes)
            with col_p2:
                st.metric("Puntos Extra", puntos_extra_mes)
            with col_p3:
                st.metric("Pendientes Pago", pendientes)
    
    # =============================================
    # TAB 2: CALCULADORA (lo que ya teniamos)
    # =============================================
    with tab2:
        st.subheader("📊 Calculadora de Tarifas")
        st.info(f"🎯 Estas en campaña: **{campana_agente}**")
        
        # --- BUSCADOR DE FACTURAS EN SCRIBD ---
        st.write("### 🔍 Buscar Modelo de Factura")
        col_busq1, col_busq2 = st.columns([3, 1])
        with col_busq1:
            texto_busqueda = st.text_input(
                "Buscar factura en Scribd",
                placeholder="Ej: factura endesa, factura iberdrola...",
                key="buscador_scribd"
            )
        with col_busq2:
            st.write("")
            st.write("")
            if st.button("🔍 Buscar", use_container_width=True, key="btn_scribd"):
                if texto_busqueda:
                    url_scribd = f"https://es.scribd.com/search?query={texto_busqueda.replace(' ', '+')}"
                    st.session_state.url_scribd = url_scribd
        
        if 'url_scribd' in st.session_state and st.session_state.url_scribd:
            st.info(f"📄 [Abrir '{texto_busqueda}' en Scribd]({st.session_state.url_scribd})", icon="🔗")
            st.caption("⬆️ Haz clic en el enlace para abrir la busqueda en una pestaña nueva")
        
        st.markdown("---")
        
        # --- FORMULARIO DE ENTRADA DE DATOS ---
        st.subheader("📝 Datos del Cliente")
        
        col1, col2 = st.columns(2)
        with col1:
            consumo_kwh = st.number_input("Consumo (kWh)*", min_value=0.0, value=300.0, step=10.0, format="%.0f")
            potencia_kw = st.number_input("Potencia contratada (kW)*", min_value=0.0, value=4.6, step=0.1, format="%.1f")
        with col2:
            dias_factura = st.number_input("Dias de la factura*", min_value=1, max_value=365, value=30, step=1)
            coste_actual = st.number_input("Coste actual de la factura (€)*", min_value=0.0, value=65.0, step=1.0, format="%.2f")
        
        tiene_excedentes = st.checkbox("☀️ ¿Tiene placas solares con excedentes?", value=False)
        excedentes_kwh = 0.0
        if tiene_excedentes:
            excedentes_kwh = st.number_input("Excedentes mensuales (kWh)", min_value=0.0, value=50.0, step=5.0, format="%.0f")
        
        if st.button("🧮 Calcular Mejor Tarifa", type="primary", use_container_width=True):
            if consumo_kwh <= 0 or potencia_kw <= 0 or coste_actual <= 0:
                st.error("❌ Todos los campos marcados con * son obligatorios")
            else:
                with st.spinner("Calculando mejores opciones..."):
                    resultados = comparar_planes(
                        consumo_kwh=consumo_kwh,
                        potencia_kw=potencia_kw,
                        coste_actual=coste_actual,
                        dias=dias_factura,
                        campana=campana_agente,
                        excedente_kwh=excedentes_kwh
                    )
                    if not resultados:
                        st.warning(f"⚠️ No hay planes configurados para la campaña **{campana_agente}**")
                        return
                    st.session_state.resultados_calculo = resultados
                    st.session_state.datos_cliente = {
                        'consumo': consumo_kwh, 'potencia': potencia_kw,
                        'dias': dias_factura, 'coste_actual': coste_actual,
                        'excedentes': excedentes_kwh if tiene_excedentes else 0.0
                    }
                    st.rerun()
        
        # --- MOSTRAR RESULTADOS ---
        if 'resultados_calculo' in st.session_state and st.session_state.resultados_calculo:
            resultados = st.session_state.resultados_calculo
            datos = st.session_state.datos_cliente
            
            st.markdown("---")
            st.subheader("📊 Resultados de la Comparativa")
            
            mejor_con_pi = next((r for r in resultados if r['tiene_pi']), None)
            if mejor_con_pi:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💶 Coste Actual", f"{datos['coste_actual']:.2f}€")
                with col2:
                    st.metric("💰 Mejor con Pack", f"{mejor_con_pi['plan']}")
                with col3:
                    delta = f"{mejor_con_pi['ahorro_mensual']:.2f}€"
                    st.metric("📈 Ahorro Mensual", f"{mejor_con_pi['ahorro_mensual']:.2f}€", delta=delta)
                with col4:
                    st.metric("🎯 Ahorro Anual", f"{mejor_con_pi['ahorro_anual']:.2f}€")
            
            st.write("### 📋 Comparativa Completa")
            st.caption("🟩 **Verde** = CON Pack Iberdrola | 🟦 **Azul** = SIN Pack Iberdrola")
            
            df_resultados = pd.DataFrame(resultados)
            
            def limpiar_aviso(aviso):
                if aviso and isinstance(aviso, str) and aviso.strip().lower() not in ['', 'nan', 'none']:
                    return aviso.strip()
                return ''
            
            df_resultados['Aviso'] = df_resultados['aviso_agente'].apply(limpiar_aviso)
            df_resultados['Plan Completo'] = df_resultados.apply(
                lambda r: f"{r['plan']} {('⚠️ ' + r['Aviso']) if r['Aviso'] else ''}".strip(), axis=1
            )
            
            df_mostrar = df_resultados[['Plan Completo', 'pack_iberdrola', 'precio_kwh', 'coste_nuevo', 'ahorro_mensual', 'ahorra', 'tiene_pi']].copy()
            df_mostrar.columns = ['Plan', 'Pack', '€/kWh', 'Coste Nuevo (€)', 'Ahorro/Mes (€)', '¿Ahorra?', '_tiene_pi']
            df_mostrar['€/kWh'] = df_mostrar['€/kWh'].apply(lambda x: f"{x:.4f}")
            df_mostrar['Coste Nuevo (€)'] = df_mostrar['Coste Nuevo (€)'].apply(lambda x: f"{x:.2f}")
            df_mostrar['Ahorro/Mes (€)'] = df_mostrar['Ahorro/Mes (€)'].apply(lambda x: f"{x:+.2f}")
            df_mostrar['¿Ahorra?'] = df_mostrar['¿Ahorra?'].apply(lambda x: '💚 AHORRA' if x else '🔴 NO AHORRA')
            
            indices_con_pi = df_mostrar[df_mostrar['_tiene_pi'] == True].index.tolist()
            indices_sin_pi = df_mostrar[df_mostrar['_tiene_pi'] == False].index.tolist()
            
            def colorear_filas(row):
                if row.name in indices_con_pi:
                    return ['background-color: #c8e6c9'] * len(row)
                elif row.name in indices_sin_pi:
                    return ['background-color: #bbdefb'] * len(row)
                return [''] * len(row)
            
            df_styled = df_mostrar.drop(columns=['_tiene_pi']).style.apply(colorear_filas, axis=1)
            df_styled = df_styled.set_properties(**{'text-align': 'center', 'padding': '10px', 'border': '1px solid #ccc', 'font-weight': '700', 'font-size': '14px'})
            st.dataframe(df_styled, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            if mejor_con_pi and mejor_con_pi['ahorra']:
                st.success(f"🎯 **RECOMENDACION**: {mejor_con_pi['plan']} con Pack Iberdrola - Ahorro de {mejor_con_pi['ahorro_mensual']:.2f}€/mes")
            elif mejor_con_pi:
                st.warning(f"ℹ️ Todos los planes con Pack Iberdrola son mas caros. El mejor es {mejor_con_pi['plan']} (+{abs(mejor_con_pi['ahorro_mensual']):.2f}€/mes)")
            
            if st.button("🔄 Nueva Consulta"):
                st.session_state.pop('resultados_calculo', None)
                st.session_state.pop('datos_cliente', None)
                st.rerun()
    
    # =============================================
    # TAB 3: MIS OBJETIVOS
    # =============================================
    with tab3:
        st.subheader("🎯 Mis Objetivos")
        
        # Obtener ultima monitorizacion para los objetivos a 7 dias
        ultima = obtener_ultima_monitorizacion(username)
        obj7 = ultima.get('objetivos_7d', {}) if ultima else {}
        
        # Datos actuales del mes
        hoy = datetime.now()
        mes_actual_str = hoy.strftime('%Y-%m')
        
        # Ventas del mes
        ventas_mes = 0
        ventas_agente = datos_puntos['ventas'].get(username, {})
        for fecha, ventas_dia in ventas_agente.items():
            if fecha.startswith(mes_actual_str):
                ventas_mes += len(ventas_dia)
        
        # SPH
        sph_target = agente.get('sph_config', {}).get('target', 0.06)
        horas_diarias = agente.get('schedule', {}).get('daily_hours', 6.0)
        
        dias_laborables = 0
        dias_ausente = 0
        for d in range(1, hoy.day + 1):
            fecha_check = datetime(hoy.year, hoy.month, d)
            if fecha_check.weekday() < 5:
                dias_laborables += 1
                fecha_str = fecha_check.strftime('%Y-%m-%d')
                if registro.get(fecha_str, {}).get(username, {}).get('ausente', False):
                    dias_ausente += 1
        
        dias_efectivos = max(0, dias_laborables - dias_ausente)
        horas_totales = horas_diarias * dias_efectivos
        sph_real = round(ventas_mes / (horas_totales * 0.83), 2) if ventas_mes > 0 and horas_totales > 0 else 0.0
        
        # Calcular objetivo mensual
        dias_restantes = sum(1 for d in range(hoy.day + 1, hoy.day + 1) if False)  # Simplificado
        dias_totales_mes = sum(1 for d in range(1, 32) if True)  # Ajustar segun mes
        try:
            from calendar import monthrange
            dias_totales_mes = monthrange(hoy.year, hoy.month)[1]
            dias_restantes = 0
            for d in range(hoy.day + 1, dias_totales_mes + 1):
                if datetime(hoy.year, hoy.month, d).weekday() < 5:
                    dias_restantes += 1
        except:
            dias_restantes = 10
        
        objetivo_ventas_mes = round((horas_diarias * (dias_laborables + dias_restantes - dias_ausente)) * sph_target * 0.83)
        
        # Mostrar metricas
        st.write("### 📈 Estado Actual del Mes")
        col_o1, col_o2, col_o3, col_o4 = st.columns(4)
        with col_o1:
            st.metric("SPH Objetivo", sph_target)
        with col_o2:
            st.metric("SPH Real", sph_real, delta=f"{sph_real - sph_target:.2f}")
        with col_o3:
            st.metric("Ventas Actuales", ventas_mes)
        with col_o4:
            st.metric("Objetivo Mensual", objetivo_ventas_mes, delta=f"{ventas_mes - objetivo_ventas_mes}")
        
        # Objetivos a 7 dias
        st.markdown("---")
        st.write("### 🎯 Objetivos a 7 Dias")
        
        if obj7 and any(v for k, v in obj7.items() if v and k != 'otros'):
            col_7d1, col_7d2, col_7d3 = st.columns(3)
            with col_7d1:
                st.metric("🎯 Ventas", obj7.get('ventas', 0))
            with col_7d2:
                st.metric("📞 Llamadas +5min", obj7.get('llamadas_5m', 0))
            with col_7d3:
                st.metric("📞 Llamadas +15min", obj7.get('llamadas_15m', 0))
            if obj7.get('otros'):
                st.info(f"📝 **Otros:** {obj7['otros']}")
        else:
            st.info("No tienes objetivos a 7 dias asignados en tu ultima monitorizacion.")
        
        # Llamadas del mes
        st.markdown("---")
        st.write("### 📞 Llamadas del Mes")
        
        llamadas_5m_mes = 0
        llamadas_15m_mes = 0
        for fecha, datos_dia in registro.items():
            if fecha.startswith(mes_actual_str) and username in datos_dia:
                llamadas_5m_mes += datos_dia[username].get('llamadas_5m', 0)
                llamadas_15m_mes += datos_dia[username].get('llamadas_15m', 0)
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.metric("Llamadas +5min (mes)", llamadas_5m_mes)
        with col_l2:
            st.metric("Llamadas +15min (mes)", llamadas_15m_mes)
    
    # =============================================
    # TAB 4: AUSENCIAS
    # =============================================
    with tab4:
        st.subheader("📅 Solicitar Ausencia")
        st.caption("Solicita tus dias de vacaciones o ausencias. Tu supervisor las revisara.")
        
        # Cargar ausencias existentes
        from super.super_panel import cargar_datos_ausencias, guardar_datos_ausencias
        ausencias = cargar_datos_ausencias()
        mis_ausencias = ausencias.get(username, {})
        
        # Mostrar ausencias actuales
        if mis_ausencias:
            st.write("**Tus ausencias registradas:**")
            for fecha, estado in sorted(mis_ausencias.items()):
                if estado:
                    st.write(f"- 📅 {fecha}")
        
        st.markdown("---")
        st.write("### ➕ Solicitar Nueva Ausencia")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            fecha_inicio = st.date_input("Fecha inicio", value=datetime.now())
        with col_a2:
            fecha_fin = st.date_input("Fecha fin", value=datetime.now())
        
        motivo = st.text_input("Motivo (opcional)", placeholder="Ej: Vacaciones, asuntos personales...")
        
        if st.button("📅 Solicitar Ausencia", type="primary", use_container_width=True):
            if fecha_inicio > fecha_fin:
                st.error("❌ La fecha de inicio no puede ser posterior a la fecha de fin")
            else:
                # Registrar cada dia como ausente
                fecha_actual = fecha_inicio
                while fecha_actual <= fecha_fin:
                    # Solo dias laborables (L-V)
                    if fecha_actual.weekday() < 5:
                        fecha_str = fecha_actual.strftime('%Y-%m-%d')
                        if username not in ausencias:
                            ausencias[username] = {}
                        ausencias[username][fecha_str] = True
                    fecha_actual += timedelta(days=1)
                
                guardar_datos_ausencias(ausencias)
                st.success(f"✅ Ausencia solicitada del {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}")
                st.rerun()