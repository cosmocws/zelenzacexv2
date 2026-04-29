# super/super_panel.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from calendar import monthrange

# =============================================
# CONFIGURACIÓN DE PUNTOS POR PRODUCTO
# =============================================

PUNTOS_PRODUCTO = {
    "CAPTA": {
        "Electricidad": {"no_cumple": 100, "cumple": 180},
        "Gas": {"no_cumple": 40, "cumple": 70},
        "Pack Iberdrola (PI)": {"no_cumple": 50, "cumple": 90},
        "UEN": {"no_cumple": 50, "cumple": 90},
        "Pack Mantenimiento Gas (PMG)": {"no_cumple": 20, "cumple": 30},
        "Facturación Electrónica (FE)": {"no_cumple": 1, "cumple": 1},
    },
    "CROSS": {
        "Electricidad": {"no_cumple": 60, "cumple": 100},
        "Gas": {"no_cumple": 20, "cumple": 40},
        "Pack Iberdrola (PI)": {"no_cumple": 30, "cumple": 50},
        "UEN": {"no_cumple": 30, "cumple": 50},
        "Pack Mantenimiento Gas (PMG)": {"no_cumple": 10, "cumple": 20},
        "Facturación Electrónica (FE)": {"no_cumple": 1, "cumple": 1},
    },
    "WINBACK": {
        "Electricidad": {"no_cumple": 27, "cumple": 42},
        "Gas": {"no_cumple": 32, "cumple": 50},
        "Pack Iberdrola (PI)": {"no_cumple": 13, "cumple": 21},
        "UEN": {"no_cumple": 13, "cumple": 21},
        "Pack Mantenimiento Gas (PMG)": {"no_cumple": 16, "cumple": 25},
        "Facturación Electrónica (FE)": {"no_cumple": 1, "cumple": 1},
    }
}

PRODUCTOS = ["Electricidad", "Gas", "Pack Iberdrola (PI)", "UEN", "Pack Mantenimiento Gas (PMG)", "Facturación Electrónica (FE)"]
TIPOS_VENTA = ["CAPTA", "CROSS", "WINBACK"]

# =============================================
# FUNCIONES DE CARGA/GUARDADO
# =============================================

def cargar_registro_diario():
    try:
        with open('data/registro_diario.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def guardar_registro_diario(datos):
    os.makedirs('data', exist_ok=True)
    with open('data/registro_diario.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    from core.github_sync import sync_archivo
    sync_archivo("data/registro_diario.json")

def cargar_datos_puntos():
    try:
        with open('data/puntos_agentes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"ventas": {}, "objetivos_cumplidos": {}, "puntos_extra": {}, "pagos_realizados": {}}

def guardar_datos_puntos(datos):
    os.makedirs('data', exist_ok=True)
    with open('data/puntos_agentes.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    from core.github_sync import sync_archivo
    sync_archivo("data/puntos_agentes.json")

def obtener_fecha_hoy():
    return datetime.now().strftime('%Y-%m-%d')

def obtener_meses_con_ventas(ventas_agente):
    meses = set()
    if ventas_agente:
        for fecha in ventas_agente.keys():
            meses.add(fecha[:7])
    return sorted(meses, reverse=True)

def calcular_puntos_agente_mes(ventas_agente, mes_str, mes_cumplido=False):
    total_puntos = 0
    if not ventas_agente:
        return 0
    for fecha, ventas_dia in ventas_agente.items():
        if fecha.startswith(mes_str):
            for venta in ventas_dia:
                tipo = venta.get('tipo', 'CAPTA')
                if mes_cumplido:
                    producto = venta.get('producto', '')
                    puntos = PUNTOS_PRODUCTO.get(tipo, {}).get(producto, {}).get('cumple', 0)
                    for s in venta.get('servicios', []):
                        if s == "PI": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("Pack Iberdrola (PI)", {}).get('cumple', 0)
                        elif s == "UEN": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("UEN", {}).get('cumple', 0)
                        elif s == "PMG": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("Pack Mantenimiento Gas (PMG)", {}).get('cumple', 0)
                        elif s == "FE": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("Facturación Electrónica (FE)", {}).get('cumple', 0)
                    total_puntos += puntos
                else:
                    total_puntos += venta.get('puntos', 0)
    return total_puntos

def calcular_puntos_pendientes(username, datos):
    puntos_generados = 0
    ventas_agente = datos['ventas'].get(username, {})
    objetivos_globales = datos.get('objetivos_cumplidos', {})
    for fecha in ventas_agente.keys():
        mes_str = fecha[:7]
        mes_cumplido = objetivos_globales.get(mes_str, False)
        for venta in ventas_agente[fecha]:
            tipo = venta.get('tipo', 'CAPTA')
            if mes_cumplido:
                producto = venta.get('producto', '')
                puntos = PUNTOS_PRODUCTO.get(tipo, {}).get(producto, {}).get('cumple', 0)
                for s in venta.get('servicios', []):
                    if s == "PI": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("Pack Iberdrola (PI)", {}).get('cumple', 0)
                    elif s == "UEN": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("UEN", {}).get('cumple', 0)
                    elif s == "PMG": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("Pack Mantenimiento Gas (PMG)", {}).get('cumple', 0)
                    elif s == "FE": puntos += PUNTOS_PRODUCTO.get(tipo, {}).get("Facturación Electrónica (FE)", {}).get('cumple', 0)
                puntos_generados += puntos
            else:
                puntos_generados += venta.get('puntos', 0)
    extras_agente = datos['puntos_extra'].get(username, {})
    for fecha, extras in extras_agente.items():
        if isinstance(extras, list):
            puntos_generados += sum(e.get('puntos', 0) for e in extras)
        elif isinstance(extras, dict):
            puntos_generados += extras.get('puntos', 0)
    pagos_agente = datos['pagos_realizados'].get(username, [])
    puntos_pagados = sum(p.get('puntos_pagados', 0) for p in pagos_agente)
    return puntos_generados - puntos_pagados

def obtener_datos_agente_periodo(registro, username, fecha_inicio, fecha_fin, supervisor=None):
    resultado = {'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0, 'dias_ausente': 0}
    for fecha, agentes in registro.items():
        if fecha_inicio <= fecha <= fecha_fin:
            if username in agentes:
                datos_dia = agentes[username]
                if supervisor and datos_dia.get('supervisor', '') != supervisor:
                    continue
                resultado['ventas'] += datos_dia.get('ventas', 0)
                resultado['llamadas_5m'] += datos_dia.get('llamadas_5m', 0)
                resultado['llamadas_15m'] += datos_dia.get('llamadas_15m', 0)
                if datos_dia.get('ausente', False):
                    resultado['dias_ausente'] += 1
    return resultado

# =============================================
# PANEL PRINCIPAL DEL SUPERVISOR
# =============================================

def show_mi_equipo():
    st.title("👥 Mi Equipo - Panel de Supervisor")
    
    um = st.session_state.user_manager
    supervisor = st.session_state.user['username']
    mis_agentes = um.get_agents_by_manager(supervisor)
    
    if not mis_agentes:
        st.info("No tienes agentes asignados actualmente.")
        return
    
    st.write(f"👤 Supervisor: **{supervisor}** | Agentes a cargo: **{len(mis_agentes)}**")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Vista General",
        "📈 Registrar Ventas",
        "⭐ Puntos",
        "✅ Cumplir Objetivo",
        "💰 Cierres de Puntos"
    ])
    
    datos_puntos = cargar_datos_puntos()
    
    # =============================================
    # TAB 1: VISTA GENERAL
    # =============================================
    with tab1:
        st.subheader("📊 Vista General del Equipo")
        
        registro = cargar_registro_diario()
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            periodo = st.selectbox("Período:", ["Día específico", "Semana anterior (L-V)", "Mes actual"], key="periodo_vista")
        with col_f2:
            hoy = datetime.now()
            if periodo == "Día específico":
                fecha_dia = st.date_input("Selecciona el día:", value=hoy, key="fecha_dia_vista")
                fecha_inicio = fecha_dia.strftime('%Y-%m-%d')
                fecha_fin = fecha_dia.strftime('%Y-%m-%d')
                st.write(f"📅 {fecha_inicio}")
            elif periodo == "Semana anterior (L-V)":
                lunes_anterior = hoy - timedelta(days=hoy.weekday() + 7)
                viernes_anterior = lunes_anterior + timedelta(days=4)
                fecha_inicio = lunes_anterior.strftime('%Y-%m-%d')
                fecha_fin = viernes_anterior.strftime('%Y-%m-%d')
                st.write(f"📅 {fecha_inicio} → {fecha_fin}")
            else:
                fecha_inicio = hoy.strftime('%Y-%m') + '-01'
                fecha_fin = obtener_fecha_hoy()
                st.write(f"📅 {hoy.strftime('%B %Y')}")
        
        data_agentes = []
        for agente in mis_agentes:
            username = agente['username']
            datos_periodo = obtener_datos_agente_periodo(registro, username, fecha_inicio, fecha_fin, supervisor)
            
            sph_config = agente.get('sph_config', {})
            sph_target = sph_config.get('target', 0.06)
            
            schedule = agente.get('schedule', {})
            horas_diarias = schedule.get('daily_hours', 6.0)
            
            if periodo == "Día específico":
                dias_laborables = 1 if fecha_dia.weekday() < 5 else 0
            elif periodo == "Semana anterior (L-V)":
                dias_laborables = 5
            else:
                dias_laborables = 0
                for d in range(1, hoy.day + 1):
                    fecha = datetime(hoy.year, hoy.month, d)
                    if fecha.weekday() < 5:
                        dias_laborables += 1
            
            dias_efectivos = max(0, dias_laborables - datos_periodo['dias_ausente'])
            horas_totales = horas_diarias * dias_efectivos
            
            # Ajustar horas si hay ausencia parcial (solo para día específico)
            if periodo == "Día específico":
                datos_dia_especifico = registro.get(fecha_inicio, {}).get(username, {})
                hora_salida = datos_dia_especifico.get('hora_salida', '')
                if hora_salida:
                    try:
                        h_ini = datetime.strptime(schedule.get('start_time', '15:00'), '%H:%M')
                        h_fin = datetime.strptime(hora_salida, '%H:%M')
                        horas_totales = round((h_fin - h_ini).seconds / 3600, 2)
                    except:
                        pass
            
            ventas_periodo = datos_periodo['ventas']
            sph_real = round(ventas_periodo / (horas_totales * 0.83), 2) if ventas_periodo > 0 and horas_totales > 0 else 0.0
            
            ventas_periodo = datos_periodo['ventas']
            sph_real = round(ventas_periodo / (horas_totales * 0.83), 2) if ventas_periodo > 0 and horas_totales > 0 else 0.0
            
            ventas_mes = 0
            ventas_agente_puntos = datos_puntos['ventas'].get(username, {})
            mes_actual_str = hoy.strftime('%Y-%m')
            for fecha, ventas_dia in ventas_agente_puntos.items():
                if fecha.startswith(mes_actual_str):
                    for v in ventas_dia:
                        if v.get('supervisor', '') == supervisor:
                            ventas_mes += 1
            
            data_agentes.append({
                'Agente': username,
                'Nombre': agente.get('nombre', ''),
                'Campaña': agente.get('campaign', ''),
                'SPH Obj': sph_target,
                'SPH Real': sph_real,
                'Ventas Período': ventas_periodo,
                'Ventas Mes': ventas_mes,
                'Llamadas +5m': datos_periodo['llamadas_5m'],
                'Llamadas +15m': datos_periodo['llamadas_15m'],
                'Días Ausente': datos_periodo['dias_ausente'],
                'Standby': '💤' if agente.get('standby') else '✅',
                'Estado SPH': '🟢' if sph_real >= sph_target else '🔴'
            })
        
        df = pd.DataFrame(data_agentes)
        columnas_mostrar = ['Agente', 'Nombre', 'Campaña', 'SPH Obj', 'SPH Real', 'Estado SPH',
                           'Ventas Período', 'Ventas Mes', 'Llamadas +5m', 'Llamadas +15m', 'Días Ausente', 'Standby']
        st.dataframe(df[columnas_mostrar], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ventas Período", sum(d['Ventas Período'] for d in data_agentes))
        with col2:
            st.metric("Total Ventas Mes", sum(d['Ventas Mes'] for d in data_agentes))
        with col3:
            agentes_verdes = sum(1 for d in data_agentes if d['SPH Real'] >= d['SPH Obj'])
            st.metric("Agentes 🟢 SPH", agentes_verdes)
        with col4:
            total_ventas_equipo = sum(d['Ventas Período'] for d in data_agentes)
            total_horas_equipo = 0
            for agente in mis_agentes:
                username = agente['username']
                schedule = agente.get('schedule', {})
                horas_diarias = schedule.get('daily_hours', 6.0)
                datos_periodo = obtener_datos_agente_periodo(registro, username, fecha_inicio, fecha_fin, supervisor)
                if periodo == "Día específico":
                    dias_lab = 1 if fecha_dia.weekday() < 5 else 0
                elif periodo == "Semana anterior (L-V)":
                    dias_lab = 5
                else:
                    dias_lab = sum(1 for d in range(1, hoy.day + 1) if datetime(hoy.year, hoy.month, d).weekday() < 5)
                dias_efectivos = max(0, dias_lab - datos_periodo['dias_ausente'])
                total_horas_equipo += horas_diarias * dias_efectivos
            sph_global = round(total_ventas_equipo / (total_horas_equipo * 0.83), 2) if total_horas_equipo > 0 else 0.0
            st.metric("SPH Global Equipo", sph_global)
        
        # --- GESTIONAR DÍA A DÍA ---
        st.markdown("---")
        st.subheader("✏️ Gestionar Día a Día")
        
        fecha_gestion = st.date_input("Fecha a gestionar:", value=hoy, key="fecha_gestion_dia")
        fecha_g_str = fecha_gestion.strftime('%Y-%m-%d')
        
        registro = cargar_registro_diario()
        datos_hoy = registro.get(fecha_g_str, {})
        
        st.write(f"Gestionando: **{fecha_g_str}**")
        
        for agente in mis_agentes:
            username = agente['username']
            nombre = agente.get('nombre', username)
            
            agente_hoy = datos_hoy.get(username, {
                'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0,
                'ausente': False,
                'campaña': agente.get('campaign', 'CAPTA'),
                'supervisor': supervisor
            })
            
            esta_ausente = agente_hoy.get('ausente', False)
            en_standby = agente.get('standby', False)
            if en_standby:
                estado = "🟡 STANDBY"
            elif esta_ausente:
                estado = "🔴 AUSENTE"
            else:
                estado = "🟢 PRESENTE"
            
            with st.expander(f"{estado} | {nombre} ({username})", expanded=False):
                col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                
                with col_a1:
                    ausente = st.checkbox("🔴 Ausente", value=esta_ausente, key=f"ausente_{username}_{fecha_g_str}")
                    if ausente != esta_ausente:
                        agente_hoy['ausente'] = ausente
                
                with col_a2:
                    ventas_dia = st.number_input("📦 Ventas", min_value=0, value=int(agente_hoy.get('ventas', 0)), step=1, key=f"ventas_dia_{username}_{fecha_g_str}")
                    if ventas_dia != agente_hoy.get('ventas', 0):
                        agente_hoy['ventas'] = ventas_dia
                
                with col_a3:
                    llamadas_5m = st.number_input("📞 +5min", min_value=0, value=int(agente_hoy.get('llamadas_5m', 0)), step=1, key=f"llamadas5m_{username}_{fecha_g_str}")
                    if llamadas_5m != agente_hoy.get('llamadas_5m', 0):
                        agente_hoy['llamadas_5m'] = llamadas_5m
                
                with col_a4:
                    llamadas_15m = st.number_input("📞 +15min", min_value=0, value=int(agente_hoy.get('llamadas_15m', 0)), step=1, key=f"llamadas15m_{username}_{fecha_g_str}")
                    if llamadas_15m != agente_hoy.get('llamadas_15m', 0):
                        agente_hoy['llamadas_15m'] = llamadas_15m
                
                # --- AUSENCIA PARCIAL ---
                st.markdown("---")
                st.caption("⏰ Ausencia parcial (horas trabajadas)")
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    hora_salida = st.text_input("Hora salida", value=agente_hoy.get('hora_salida', ''), placeholder="Ej: 15:45", key=f"hora_salida_{username}_{fecha_g_str}")
                    if hora_salida != agente_hoy.get('hora_salida', ''):
                        agente_hoy['hora_salida'] = hora_salida
                with col_p2:
                    motivo_parcial = st.text_input("Motivo", value=agente_hoy.get('motivo_parcial', ''), placeholder="Ej: Motivos personales", key=f"motivo_parcial_{username}_{fecha_g_str}")
                    if motivo_parcial != agente_hoy.get('motivo_parcial', ''):
                        agente_hoy['motivo_parcial'] = motivo_parcial
                with col_p3:
                    if agente_hoy.get('hora_salida'):
                        try:
                            h_ini = datetime.strptime(agente.get('schedule', {}).get('start_time', '15:00'), '%H:%M')
                            h_fin = datetime.strptime(agente_hoy['hora_salida'], '%H:%M')
                            horas_trab = round((h_fin - h_ini).seconds / 3600, 2)
                            st.caption(f"🕐 {horas_trab}h trabajadas")
                        except:
                            pass
                
                datos_hoy[username] = agente_hoy
        
        if st.button("💾 Guardar Todo", type="primary", use_container_width=True, key="btn_guardar_gestion"):
            registro[fecha_g_str] = datos_hoy
            guardar_registro_diario(registro)
            st.success("✅ Datos guardados correctamente")
            st.rerun()
    
    # =============================================
    # TAB 2: REGISTRAR VENTAS
    # =============================================
    with tab2:
        st.subheader("📈 Registrar Ventas del Día")
        
        fecha_venta = st.date_input("Fecha:", value=datetime.now(), key="fecha_venta")
        fecha_str = fecha_venta.strftime('%Y-%m-%d')
        st.write(f"📅 Registrando ventas para: **{fecha_str}**")
        st.markdown("---")
        
        agentes_dict = {a['username']: a.get('nombre', a['username']) for a in mis_agentes}
        agente_sel = st.selectbox("Agente:", list(agentes_dict.keys()), format_func=lambda x: f"{x} ({agentes_dict[x]})")
        
        ventas_hoy = datos_puntos['ventas'].get(agente_sel, {}).get(fecha_str, [])
        if ventas_hoy:
            st.write("**📋 Ventas registradas hoy:**")
            for i, v in enumerate(ventas_hoy):
                col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns([2, 2, 1, 1, 1])
                with col_v1: st.write(f"**{v.get('producto', '')}**")
                with col_v2:
                    servicios = v.get('servicios', [])
                    st.write(f"+ {' + '.join(servicios)}" if servicios else "-")
                with col_v3: st.write(f"{v.get('puntos', 0)} pts")
                with col_v4:
                    if st.button("✏️", key=f"edit_venta_{i}"):
                        st.session_state.editing_venta = {'agente': agente_sel, 'fecha': fecha_str, 'index': i, 'venta': v}
                        st.rerun()
                with col_v5:
                    if st.button("🗑️", key=f"del_venta_{i}"):
                        ventas_hoy.pop(i)
                        if not ventas_hoy: del datos_puntos['ventas'][agente_sel][fecha_str]
                        else: datos_puntos['ventas'][agente_sel][fecha_str] = ventas_hoy
                        guardar_datos_puntos(datos_puntos)
                        registro = cargar_registro_diario()
                        if fecha_str in registro and agente_sel in registro[fecha_str]:
                            registro[fecha_str][agente_sel]['ventas'] = max(0, registro[fecha_str][agente_sel].get('ventas', 0) - 1)
                            guardar_registro_diario(registro)
                        st.success("✅ Venta eliminada")
                        st.rerun()
                st.markdown("---")
        
        if 'editing_venta' in st.session_state and st.session_state.editing_venta:
            ev = st.session_state.editing_venta
            if ev['agente'] == agente_sel and ev['fecha'] == fecha_str:
                st.warning(f"✏️ Editando venta #{ev['index']+1}")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    prod_edit = st.selectbox("Producto:", PRODUCTOS, index=PRODUCTOS.index(ev['venta'].get('producto', 'Electricidad')) if ev['venta'].get('producto', 'Electricidad') in PRODUCTOS else 0, key="edit_producto")
                with col_e2:
                    tipo_edit = st.selectbox("Tipo:", TIPOS_VENTA, index=TIPOS_VENTA.index(ev['venta'].get('tipo', 'CAPTA')) if ev['venta'].get('tipo', 'CAPTA') in TIPOS_VENTA else 0, key="edit_tipo")
                
                servicios_actuales = ev['venta'].get('servicios', [])
                st.write("**Servicios asociados:**")
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1: pi_edit = st.checkbox("PI", value="PI" in servicios_actuales, key="edit_pi")
                with col_s2: uen_edit = st.checkbox("UEN", value="UEN" in servicios_actuales, key="edit_uen", disabled=pi_edit)
                with col_s3: pmg_edit = st.checkbox("PMG", value="PMG" in servicios_actuales, key="edit_pmg", disabled=prod_edit not in ["Gas"])
                with col_s4: fe_edit = st.checkbox("FE", value="FE" in servicios_actuales, key="edit_fe")
                
                if st.button("💾 Guardar Cambios", type="primary"):
                    puntos = PUNTOS_PRODUCTO[tipo_edit][prod_edit]["no_cumple"]
                    nuevos_servicios = []
                    if pi_edit: nuevos_servicios.append("PI"); puntos += PUNTOS_PRODUCTO[tipo_edit]["Pack Iberdrola (PI)"]["no_cumple"]
                    if uen_edit and not pi_edit: nuevos_servicios.append("UEN"); puntos += PUNTOS_PRODUCTO[tipo_edit]["UEN"]["no_cumple"]
                    if pmg_edit and prod_edit == "Gas": nuevos_servicios.append("PMG"); puntos += PUNTOS_PRODUCTO[tipo_edit]["Pack Mantenimiento Gas (PMG)"]["no_cumple"]
                    if fe_edit: nuevos_servicios.append("FE"); puntos += PUNTOS_PRODUCTO[tipo_edit]["Facturación Electrónica (FE)"]["no_cumple"]
                    
                    datos_puntos['ventas'][agente_sel][fecha_str][ev['index']] = {
                        "producto": prod_edit, "tipo": tipo_edit, "servicios": nuevos_servicios, "puntos": puntos,
                        "campaña": next((a.get('campaign', 'CAPTA') for a in mis_agentes if a['username'] == agente_sel), 'CAPTA'),
                        "supervisor": supervisor
                    }
                    guardar_datos_puntos(datos_puntos)
                    st.session_state.pop('editing_venta')
                    st.success("✅ Venta actualizada")
                    st.rerun()
                
                if st.button("❌ Cancelar Edición"):
                    st.session_state.pop('editing_venta')
                    st.rerun()
        
        if 'editing_venta' not in st.session_state or st.session_state.editing_venta.get('agente') != agente_sel:
            st.markdown("---")
            st.write("**➕ Nueva Venta:**")
            col1, col2 = st.columns(2)
            with col1: producto = st.selectbox("Producto principal:", PRODUCTOS, key="nuevo_producto")
            with col2: tipo_venta = st.selectbox("Tipo de cliente:", TIPOS_VENTA, key="nuevo_tipo")
            
            st.write("**Servicios asociados:**")
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1: add_pi = st.checkbox("PI", value=False, key="add_pi")
            with col_s2: add_uen = st.checkbox("UEN", value=False, key="add_uen", disabled=add_pi)
            with col_s3: add_pmg = st.checkbox("PMG", value=False, key="add_pmg", disabled=producto != "Gas")
            with col_s4: add_fe = st.checkbox("FE", value=False, key="add_fe")
            
            puntos = PUNTOS_PRODUCTO[tipo_venta][producto]["no_cumple"]
            servicios = []
            if add_pi: servicios.append("PI"); puntos += PUNTOS_PRODUCTO[tipo_venta]["Pack Iberdrola (PI)"]["no_cumple"]
            if add_uen and not add_pi: servicios.append("UEN"); puntos += PUNTOS_PRODUCTO[tipo_venta]["UEN"]["no_cumple"]
            if add_pmg and producto == "Gas": servicios.append("PMG"); puntos += PUNTOS_PRODUCTO[tipo_venta]["Pack Mantenimiento Gas (PMG)"]["no_cumple"]
            if add_fe: servicios.append("FE"); puntos += PUNTOS_PRODUCTO[tipo_venta]["Facturación Electrónica (FE)"]["no_cumple"]
            
            st.info(f"**Puntos totales: {puntos} pts**")
            
            if st.button("➕ Añadir Venta", type="primary", use_container_width=True):
                nueva_venta = {
                    "producto": producto, "tipo": tipo_venta, "servicios": servicios, "puntos": puntos,
                    "campaña": next((a.get('campaign', 'CAPTA') for a in mis_agentes if a['username'] == agente_sel), 'CAPTA'),
                    "supervisor": supervisor
                }
                if agente_sel not in datos_puntos['ventas']: datos_puntos['ventas'][agente_sel] = {}
                if fecha_str not in datos_puntos['ventas'][agente_sel]: datos_puntos['ventas'][agente_sel][fecha_str] = []
                datos_puntos['ventas'][agente_sel][fecha_str].append(nueva_venta)
                guardar_datos_puntos(datos_puntos)
                
                registro = cargar_registro_diario()
                if fecha_str not in registro: registro[fecha_str] = {}
                if agente_sel not in registro[fecha_str]:
                    registro[fecha_str][agente_sel] = {
                        'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0, 'ausente': False,
                        'campaña': next((a.get('campaign', 'CAPTA') for a in mis_agentes if a['username'] == agente_sel), 'CAPTA'),
                        'supervisor': supervisor
                    }
                registro[fecha_str][agente_sel]['ventas'] = registro[fecha_str][agente_sel].get('ventas', 0) + 1
                guardar_registro_diario(registro)
                st.success(f"✅ Venta añadida: {producto} = {puntos} pts")
                st.rerun()
    
    # =============================================
    # TAB 3: PUNTOS
    # =============================================
    with tab3:
        st.subheader("⭐ Puntos del Equipo")
        subtab1, subtab2 = st.tabs(["📊 Ver Puntos", "➕ Añadir Puntos Extra"])
        
        with subtab1:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                periodo_puntos = st.selectbox("Período:", ["Semana actual (L-V)", "Mes actual", "Mes anterior"], key="periodo_puntos")
            with col_p2:
                hoy = datetime.now()
                if periodo_puntos == "Semana actual (L-V)":
                    lunes_actual = hoy - timedelta(days=hoy.weekday())
                    fecha_inicio_p = lunes_actual.strftime('%Y-%m-%d')
                    fecha_fin_p = (lunes_actual + timedelta(days=4)).strftime('%Y-%m-%d')
                    st.write(f"📅 {fecha_inicio_p} → {fecha_fin_p}")
                elif periodo_puntos == "Mes actual":
                    fecha_inicio_p = hoy.strftime('%Y-%m') + '-01'
                    fecha_fin_p = hoy.strftime('%Y-%m-%d')
                    st.write(f"📅 {hoy.strftime('%B %Y')}")
                else:
                    if hoy.month == 1: mes_anterior, año_anterior = 12, hoy.year - 1
                    else: mes_anterior, año_anterior = hoy.month - 1, hoy.year
                    fecha_inicio_p = f"{año_anterior}-{mes_anterior:02d}-01"
                    fecha_fin_p = f"{año_anterior}-{mes_anterior:02d}-{monthrange(año_anterior, mes_anterior)[1]}"
                    st.write(f"📅 {datetime(año_anterior, mes_anterior, 1).strftime('%B %Y')}")
            
            data_puntos = []
            for agente in mis_agentes:
                username = agente['username']
                ventas_agente = datos_puntos['ventas'].get(username, {})
                puntos_ventas = sum(v.get('puntos', 0) for fecha, ventas_dia in ventas_agente.items() if fecha_inicio_p <= fecha <= fecha_fin_p for v in ventas_dia if v.get('supervisor', '') == supervisor)
                puntos_extra_periodo = 0
                for fecha, extras in datos_puntos['puntos_extra'].get(username, {}).items():
                    if fecha_inicio_p <= fecha <= fecha_fin_p:
                        if isinstance(extras, list):
                            puntos_extra_periodo += sum(e.get('puntos', 0) for e in extras if e.get('supervisor', '') == supervisor)
                        elif isinstance(extras, dict):
                            if extras.get('supervisor', '') == supervisor:
                                puntos_extra_periodo += extras.get('puntos', 0)
                total_periodo = puntos_ventas + puntos_extra_periodo
                puntos_pend = calcular_puntos_pendientes(username, datos_puntos)
                data_puntos.append({'Agente': username, 'Nombre': agente.get('nombre', ''), 'Puntos Ventas': puntos_ventas, 'Puntos Extra': puntos_extra_periodo, 'Total Período': total_periodo, 'Pendientes Pago': puntos_pend})
            
            df_puntos = pd.DataFrame(data_puntos)
            st.dataframe(df_puntos, use_container_width=True, hide_index=True)
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Total Puntos Período", sum(d['Total Período'] for d in data_puntos))
            with col2: st.metric("Total Pendiente Pago", sum(d['Pendientes Pago'] for d in data_puntos))
            with col3: st.metric("Agentes con Puntos", sum(1 for d in data_puntos if d['Total Período'] > 0))
        
        with subtab2:
            st.write("### ⭐ Añadir Puntos Extra Manuales")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                fecha_extra = st.date_input("Fecha:", value=datetime.now(), key="fecha_extra")
                fecha_str = fecha_extra.strftime('%Y-%m-%d')
            with col_a2:
                agente_extra = st.selectbox("Agente:", [a['username'] for a in mis_agentes], format_func=lambda x: f"{x} ({next((a.get('nombre', x) for a in mis_agentes if a['username'] == x), x)})", key="agente_extra")
            col_b1, col_b2 = st.columns(2)
            with col_b1: puntos_extra = st.number_input("Puntos:", min_value=0, value=0, step=5, key="puntos_extra_input")
            with col_b2: motivo_extra = st.text_input("Motivo:", key="motivo_extra")
            
            if st.button("⭐ Añadir Puntos Extra", type="primary", use_container_width=True):
                if puntos_extra > 0 and motivo_extra:
                    if agente_extra not in datos_puntos['puntos_extra']: datos_puntos['puntos_extra'][agente_extra] = {}
                    if fecha_str not in datos_puntos['puntos_extra'][agente_extra]: datos_puntos['puntos_extra'][agente_extra][fecha_str] = []
                    datos_puntos['puntos_extra'][agente_extra][fecha_str].append({"puntos": puntos_extra, "motivo": motivo_extra, "campaña": next((a.get('campaign', 'CAPTA') for a in mis_agentes if a['username'] == agente_extra), 'CAPTA'), "supervisor": supervisor})
                    guardar_datos_puntos(datos_puntos)
                    st.success(f"✅ {puntos_extra} pts añadidos a {agente_extra}")
                    st.rerun()
                else:
                    st.error("❌ Indica los puntos y el motivo")
            
            st.markdown("---")
            st.write("### 📋 Últimos Puntos Extra")
            todos_extras = []
            for agente in mis_agentes:
                for fecha, extras in datos_puntos['puntos_extra'].get(agente['username'], {}).items():
                    if isinstance(extras, list):
                        for e in extras: todos_extras.append({'Fecha': fecha, 'Agente': agente['username'], 'Puntos': e.get('puntos', 0), 'Motivo': e.get('motivo', '')})
            if todos_extras:
                todos_extras.sort(key=lambda x: x['Fecha'], reverse=True)
                st.dataframe(pd.DataFrame(todos_extras[:20]), use_container_width=True, hide_index=True)
            else:
                st.info("No hay puntos extra registrados.")
    
    # =============================================
    # TAB 4: CUMPLIR OBJETIVO
    # =============================================
    with tab4:
        st.subheader("✅ Cumplir Objetivo Mensual")
        st.caption("Marca un mes como cumplido.")
        
        todos_meses = set()
        for agente in mis_agentes:
            ventas_agente = datos_puntos['ventas'].get(agente['username'], {})
            todos_meses.update(obtener_meses_con_ventas(ventas_agente))
        meses_disponibles = sorted(todos_meses, reverse=True)
        
        if not meses_disponibles:
            st.info("No hay ventas registradas todavía.")
        else:
            mes_a_cumplir = st.selectbox("Selecciona el mes:", meses_disponibles, key="mes_cumplir")
            objetivos_globales = datos_puntos.get('objetivos_cumplidos', {})
            mes_cumplido = objetivos_globales.get(mes_a_cumplir, False)
            
            if mes_cumplido:
                st.success(f"✅ {mes_a_cumplir} ya está marcado como CUMPLIDO")
                if st.button("❌ Desmarcar como cumplido", type="secondary"):
                    datos_puntos['objetivos_cumplidos'][mes_a_cumplir] = False
                    guardar_datos_puntos(datos_puntos)
                    st.warning("⚠️ Mes desmarcado.")
                    st.rerun()
            else:
                total_diferencia = 0
                agentes_afectados = []
                for agente in mis_agentes:
                    username = agente['username']
                    ventas_agente = datos_puntos['ventas'].get(username, {})
                    if ventas_agente:
                        puntos_no = calcular_puntos_agente_mes(ventas_agente, mes_a_cumplir, False)
                        puntos_si = calcular_puntos_agente_mes(ventas_agente, mes_a_cumplir, True)
                        diferencia = puntos_si - puntos_no
                        if diferencia > 0:
                            agentes_afectados.append({'agente': username, 'puntos_actuales': puntos_no, 'puntos_cumplido': puntos_si, 'diferencia': diferencia})
                            total_diferencia += diferencia
                
                if agentes_afectados:
                    st.info(f"📊 **Total a repartir: +{total_diferencia} puntos** entre {len(agentes_afectados)} agentes")
                    if st.button(f"✅ Marcar {mes_a_cumplir} como CUMPLIDO", type="primary", use_container_width=True):
                        if 'objetivos_cumplidos' not in datos_puntos: datos_puntos['objetivos_cumplidos'] = {}
                        datos_puntos['objetivos_cumplidos'][mes_a_cumplir] = True
                        fecha_hoy = obtener_fecha_hoy()
                        for a in agentes_afectados:
                            if a['agente'] not in datos_puntos['puntos_extra']: datos_puntos['puntos_extra'][a['agente']] = {}
                            if fecha_hoy not in datos_puntos['puntos_extra'][a['agente']]: datos_puntos['puntos_extra'][a['agente']][fecha_hoy] = []
                            datos_puntos['puntos_extra'][a['agente']][fecha_hoy].append({"puntos": a['diferencia'], "motivo": f"Por objetivo de campaña cumplido - {mes_a_cumplir}", "campaña": "CAPTA", "supervisor": supervisor})
                        guardar_datos_puntos(datos_puntos)
                        st.success(f"✅ ¡{mes_a_cumplir} marcado como CUMPLIDO! +{total_diferencia} pts repartidos.")
                        st.rerun()
                else:
                    st.info(f"No hay agentes con ventas en {mes_a_cumplir}")
    
    # =============================================
    # TAB 5: CIERRES DE PUNTOS
    # =============================================
    with tab5:
        st.subheader("💰 Gestión de Pagos de Puntos")
        
        subtab5_1, subtab5_2 = st.tabs(["💼 Cierre Puntos Ventas", "🎁 Cierre Puntos Extra"])
        
        # =============================================
        # SUBTAB 1: CIERRE PUNTOS VENTAS (mensual)
        # =============================================
        with subtab5_1:
            st.write("### 💼 Cierre de Puntos por Ventas")
            st.caption("Se paga a principios del mes siguiente. Elige si se cumplio objetivo o no.")
            
            # Seleccionar mes a cerrar
            meses_disponibles = set()
            for agente in mis_agentes:
                ventas_agente = datos_puntos['ventas'].get(agente['username'], {})
                for fecha in ventas_agente.keys():
                    meses_disponibles.add(fecha[:7])
            meses_disponibles = sorted(meses_disponibles, reverse=True)
            
            if not meses_disponibles:
                st.info("No hay ventas registradas.")
            else:
                mes_cierre = st.selectbox("Mes a cerrar:", meses_disponibles, key="mes_cierre_ventas")
                
                # Elegir si cumplio o no
                cumplio = st.radio("¿Se cumplio el objetivo?", ["NO cumplido", "SI cumplido"], horizontal=True, key="cumplio_ventas")
                mes_cumplido = cumplio == "SI cumplido"
                
                # Mostrar resumen
                st.write("**Resumen del mes:**")
                data_cierre = []
                total_puntos = 0
                
                for agente in mis_agentes:
                    username = agente['username']
                    ventas_agente = datos_puntos['ventas'].get(username, {})
                    
                    if mes_cumplido:
                        puntos_agente = calcular_puntos_agente_mes(ventas_agente, mes_cierre, True)
                    else:
                        puntos_agente = sum(v.get('puntos', 0) for fecha, ventas_dia in ventas_agente.items() if fecha.startswith(mes_cierre) for v in ventas_dia if v.get('supervisor', '') == supervisor)
                    
                    if puntos_agente > 0:
                        data_cierre.append({
                            'Agente': username,
                            'Nombre': agente.get('nombre', ''),
                            'Puntos': puntos_agente,
                            'Euros': f"{puntos_agente/22:.2f}€"
                        })
                        total_puntos += puntos_agente
                
                if data_cierre:
                    df_cierre = pd.DataFrame(data_cierre)
                    st.dataframe(df_cierre, use_container_width=True, hide_index=True)
                    
                    st.info(f"💰 Total a pagar: **{total_puntos} pts** ({total_puntos/22:.2f}€)")
                    
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        etiqueta = st.text_input("Etiqueta:", value=f"Ventas {mes_cierre} - {'Cumplido' if mes_cumplido else 'NO cumplido'}", key="etiqueta_ventas")
                    with col_c2:
                        nota = st.text_input("Nota:", key="nota_ventas")
                    
                    if st.button(f"💸 PAGAR Puntos Ventas ({total_puntos} pts)", type="primary", use_container_width=True):
                        fecha_hoy = obtener_fecha_hoy()
                        for agente in mis_agentes:
                            username = agente['username']
                            ventas_agente = datos_puntos['ventas'].get(username, {})
                            if mes_cumplido:
                                puntos_agente = calcular_puntos_agente_mes(ventas_agente, mes_cierre, True)
                            else:
                                puntos_agente = sum(v.get('puntos', 0) for fecha, ventas_dia in ventas_agente.items() if fecha.startswith(mes_cierre) for v in ventas_dia if v.get('supervisor', '') == supervisor)
                            
                            if puntos_agente > 0:
                                if username not in datos_puntos['pagos_realizados']:
                                    datos_puntos['pagos_realizados'][username] = []
                                datos_puntos['pagos_realizados'][username].append({
                                    "fecha": fecha_hoy,
                                    "puntos_pagados": puntos_agente,
                                    "semana": etiqueta,
                                    "nota": nota,
                                    "tipo": "ventas",
                                    "campaña": agente.get('campaign', 'CAPTA'),
                                    "supervisor": supervisor
                                })
                        
                        guardar_datos_puntos(datos_puntos)
                        st.success(f"✅ Pagados {total_puntos} pts en concepto de ventas")
                        st.rerun()
                else:
                    st.info(f"No hay puntos de ventas en {mes_cierre}")
        
        # =============================================
        # SUBTAB 2: CIERRE PUNTOS EXTRA (semanal)
        # =============================================
        with subtab5_2:
            st.write("### 🎁 Cierre de Puntos Extra")
            st.caption("Se pagan semanalmente.")
            
            # Seleccionar período
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                periodo_pago = st.selectbox("Período:", ["Semana actual (L-V)", "Semana anterior (L-V)", "Mes actual", "Mes anterior"], key="periodo_pago_extra")
            with col_f2:
                hoy = datetime.now()
                if periodo_pago == "Semana actual (L-V)":
                    lunes = hoy - timedelta(days=hoy.weekday())
                    fecha_ini = lunes.strftime('%Y-%m-%d')
                    fecha_fin = (lunes + timedelta(days=4)).strftime('%Y-%m-%d')
                    st.write(f"📅 {fecha_ini} → {fecha_fin}")
                elif periodo_pago == "Semana anterior (L-V)":
                    lunes = hoy - timedelta(days=hoy.weekday() + 7)
                    fecha_ini = lunes.strftime('%Y-%m-%d')
                    fecha_fin = (lunes + timedelta(days=4)).strftime('%Y-%m-%d')
                    st.write(f"📅 {fecha_ini} → {fecha_fin}")
                elif periodo_pago == "Mes actual":
                    fecha_ini = hoy.strftime('%Y-%m') + '-01'
                    fecha_fin = hoy.strftime('%Y-%m-%d')
                    st.write(f"📅 {hoy.strftime('%B %Y')}")
                else:
                    if hoy.month == 1: mes_ant, año_ant = 12, hoy.year - 1
                    else: mes_ant, año_ant = hoy.month - 1, hoy.year
                    fecha_ini = f"{año_ant}-{mes_ant:02d}-01"
                    fecha_fin = f"{año_ant}-{mes_ant:02d}-{monthrange(año_ant, mes_ant)[1]}"
                    st.write(f"📅 {datetime(año_ant, mes_ant, 1).strftime('%B %Y')}")
            
            data_extra = []
            total_extra = 0
            
            for agente in mis_agentes:
                username = agente['username']
                puntos_extra = 0
                extras_agente = datos_puntos['puntos_extra'].get(username, {})
                for fecha, extras in extras_agente.items():
                    if fecha_ini <= fecha <= fecha_fin:
                        if isinstance(extras, list):
                            puntos_extra += sum(e.get('puntos', 0) for e in extras if e.get('supervisor', '') == supervisor)
                        elif isinstance(extras, dict):
                            if extras.get('supervisor', '') == supervisor:
                                puntos_extra += extras.get('puntos', 0)
                
                if puntos_extra > 0:
                    data_extra.append({
                        'Agente': username,
                        'Nombre': agente.get('nombre', ''),
                        'Puntos Extra': puntos_extra,
                        'Euros': f"{puntos_extra/22:.2f}€"
                    })
                    total_extra += puntos_extra
            
            if data_extra:
                df_extra = pd.DataFrame(data_extra)
                st.dataframe(df_extra, use_container_width=True, hide_index=True)
                
                st.info(f"💰 Total puntos extra: **{total_extra} pts** ({total_extra/22:.2f}€)")
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    etiqueta_extra = st.text_input("Etiqueta:", value=f"Extra {fecha_ini} → {fecha_fin}", key="etiqueta_extra")
                with col_c2:
                    nota_extra = st.text_input("Nota:", key="nota_extra")
                
                if st.button(f"💸 PAGAR Puntos Extra ({total_extra} pts)", type="primary", use_container_width=True):
                    fecha_hoy = obtener_fecha_hoy()
                    for agente in mis_agentes:
                        username = agente['username']
                        puntos_extra_agente = 0
                        extras_agente = datos_puntos['puntos_extra'].get(username, {})
                        for fecha, extras in extras_agente.items():
                            if fecha_ini <= fecha <= fecha_fin:
                                if isinstance(extras, list):
                                    puntos_extra_agente += sum(e.get('puntos', 0) for e in extras if e.get('supervisor', '') == supervisor)
                                elif isinstance(extras, dict):
                                    if extras.get('supervisor', '') == supervisor:
                                        puntos_extra_agente += extras.get('puntos', 0)
                        
                        if puntos_extra_agente > 0:
                            if username not in datos_puntos['pagos_realizados']:
                                datos_puntos['pagos_realizados'][username] = []
                            datos_puntos['pagos_realizados'][username].append({
                                "fecha": fecha_hoy,
                                "puntos_pagados": puntos_extra_agente,
                                "semana": etiqueta_extra,
                                "nota": nota_extra,
                                "tipo": "extra",
                                "campaña": agente.get('campaign', 'CAPTA'),
                                "supervisor": supervisor
                            })
                    
                    guardar_datos_puntos(datos_puntos)
                    st.success(f"✅ Pagados {total_extra} pts en concepto de puntos extra")
                    st.rerun()
            else:
                st.info("No hay puntos extra en este período.")
        
        # =============================================
        # HISTORIAL DE PAGOS
        # =============================================
        st.markdown("---")
        st.write("### 📋 Historial de Pagos")
        
        todos_pagos = []
        for agente in mis_agentes:
            username = agente['username']
            pagos = datos_puntos['pagos_realizados'].get(username, [])
            for p in pagos:
                if p.get('supervisor', '') == supervisor:
                    todos_pagos.append({
                        'Fecha': p.get('fecha', ''),
                        'Agente': username,
                        'Puntos': p.get('puntos_pagados', 0),
                        'Tipo': p.get('tipo', ''),
                        'Etiqueta': p.get('semana', ''),
                        'Nota': p.get('nota', '')
                    })
        
        if todos_pagos:
            todos_pagos.sort(key=lambda x: x['Fecha'], reverse=True)
            st.dataframe(pd.DataFrame(todos_pagos[:30]), use_container_width=True, hide_index=True)
        else:
            st.info("No hay pagos registrados.")
        
        # =============================================
        # RESETEAR DATOS
        # =============================================
        st.markdown("---")
        st.write("### 🚨 Resetear Datos")
        with st.expander("⚠️ Resetear todos los datos", expanded=False):
            st.error("Esto borrará TODAS las ventas, puntos y registros.")
            col_r1, col_r2 = st.columns(2)
            with col_r1: confirm = st.text_input("Escribe 'BORRAR TODO':", key="reset_confirm")
            with col_r2:
                if st.button("🗑️ RESETEAR TODO", disabled=(confirm != "BORRAR TODO")):
                    guardar_datos_puntos({"ventas": {}, "objetivos_cumplidos": {}, "puntos_extra": {}, "pagos_realizados": {}})
                    guardar_registro_diario({})
                    st.success("✅ Datos reseteados")
                    st.rerun()
