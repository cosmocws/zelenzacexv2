# coo/coo_pagos.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from calendar import monthrange

def show_pagos():
    st.title("💰 Cierres de Puntos - COO")
    
    um = st.session_state.user_manager
    from super.super_panel import cargar_datos_puntos, guardar_datos_puntos, obtener_fecha_hoy, calcular_puntos_agente_mes, PUNTOS_PRODUCTO, cargar_registro_diario
    
    datos_puntos = cargar_datos_puntos()
    registro_diario = cargar_registro_diario()
    todos_agentes = um.get_all_agents()
    
    # Cargar config de supervisores
    try:
        with open('data/config_puntos_super.json', 'r', encoding='utf-8') as f:
            config_super = json.load(f)
    except:
        config_super = {"puntos_supervisor": {}, "objetivos_ventas": {}, "bonus_diarios": {}}
    
    from admin.admin_supervisores import calcular_puntos_supervisor_dia
    
    tab1, tab2, tab3, tab4 = st.tabs(["💼 Ventas", "🎁 Extra", "👤 Supervisores", "📋 Historial"])
    
    # =============================================
    # TAB 1: CIERRE PUNTOS VENTAS
    # =============================================
    with tab1:
        st.write("### 💼 Cierre de Puntos por Ventas")
        st.caption("Pago mensual. Elige si se cumplio objetivo.")
        
        meses_disponibles = set()
        for agente in todos_agentes:
            ventas_agente = datos_puntos['ventas'].get(agente['username'], {})
            for fecha in ventas_agente.keys():
                meses_disponibles.add(fecha[:7])
        meses_disponibles = sorted(meses_disponibles, reverse=True)
        
        if not meses_disponibles:
            st.info("No hay ventas registradas.")
        else:
            mes_cierre = st.selectbox("Mes a cerrar:", meses_disponibles, key="coo_mes_ventas")
            cumplio = st.radio("¿Se cumplio el objetivo?", ["NO cumplido", "SI cumplido"], horizontal=True, key="coo_cumplio")
            mes_cumplido = cumplio == "SI cumplido"
            
            agentes_sel = st.multiselect(
                "Agentes a pagar (todos si vacío):",
                [a['username'] for a in todos_agentes],
                format_func=lambda x: f"{x} ({next((a.get('nombre', x) for a in todos_agentes if a['username'] == x), x)})",
                key="coo_agentes_ventas"
            )
            
            data_cierre = []
            total_puntos = 0
            
            for agente in todos_agentes:
                username = agente['username']
                if agentes_sel and username not in agentes_sel:
                    continue
                
                ventas_agente = datos_puntos['ventas'].get(username, {})
                
                if mes_cumplido:
                    puntos_agente = calcular_puntos_agente_mes(ventas_agente, mes_cierre, True)
                else:
                    puntos_agente = sum(v.get('puntos', 0) for fecha, ventas_dia in ventas_agente.items() if fecha.startswith(mes_cierre) for v in ventas_dia)
                
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
                st.info(f"💰 Total: **{total_puntos} pts** ({total_puntos/22:.2f}€)")
                
                col1, col2 = st.columns(2)
                with col1: etiqueta = st.text_input("Etiqueta:", value=f"Ventas {mes_cierre}", key="coo_etiq_ventas")
                with col2: nota = st.text_input("Nota:", key="coo_nota_ventas")
                
                if st.button(f"💸 PAGAR ({total_puntos} pts)", type="primary", use_container_width=True):
                    fecha_hoy = obtener_fecha_hoy()
                    for agente in todos_agentes:
                        username = agente['username']
                        if agentes_sel and username not in agentes_sel:
                            continue
                        ventas_agente = datos_puntos['ventas'].get(username, {})
                        if mes_cumplido:
                            puntos_agente = calcular_puntos_agente_mes(ventas_agente, mes_cierre, True)
                        else:
                            puntos_agente = sum(v.get('puntos', 0) for fecha, ventas_dia in ventas_agente.items() if fecha.startswith(mes_cierre) for v in ventas_dia)
                        
                        if puntos_agente > 0:
                            if username not in datos_puntos['pagos_realizados']:
                                datos_puntos['pagos_realizados'][username] = []
                            datos_puntos['pagos_realizados'][username].append({
                                "fecha": fecha_hoy, "puntos_pagados": puntos_agente,
                                "semana": etiqueta, "nota": nota, "tipo": "ventas",
                                "campaña": agente.get('campaign', 'CAPTA'), "supervisor": "COO"
                            })
                    guardar_datos_puntos(datos_puntos)
                    st.success(f"✅ Pagados {total_puntos} pts")
                    st.rerun()
            else:
                st.info(f"No hay puntos en {mes_cierre}")
    
    # =============================================
    # TAB 2: CIERRE PUNTOS EXTRA
    # =============================================
    with tab2:
        st.write("### 🎁 Cierre de Puntos Extra")
        st.caption("Pago semanal.")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            periodo_pago = st.selectbox("Período:", ["Semana actual (L-V)", "Semana anterior (L-V)", "Mes actual", "Mes anterior"], key="coo_periodo")
        with col_f2:
            hoy = datetime.now()
            if periodo_pago == "Semana actual (L-V)":
                lunes = hoy - timedelta(days=hoy.weekday())
                fecha_ini = lunes.strftime('%Y-%m-%d')
                fecha_fin = (lunes + timedelta(days=4)).strftime('%Y-%m-%d')
            elif periodo_pago == "Semana anterior (L-V)":
                lunes = hoy - timedelta(days=hoy.weekday() + 7)
                fecha_ini = lunes.strftime('%Y-%m-%d')
                fecha_fin = (lunes + timedelta(days=4)).strftime('%Y-%m-%d')
            elif periodo_pago == "Mes actual":
                fecha_ini = hoy.strftime('%Y-%m') + '-01'
                fecha_fin = hoy.strftime('%Y-%m-%d')
            else:
                if hoy.month == 1: mes_ant, año_ant = 12, hoy.year - 1
                else: mes_ant, año_ant = hoy.month - 1, hoy.year
                fecha_ini = f"{año_ant}-{mes_ant:02d}-01"
                fecha_fin = f"{año_ant}-{mes_ant:02d}-{monthrange(año_ant, mes_ant)[1]}"
            st.write(f"📅 {fecha_ini} → {fecha_fin}")
        
        agentes_sel_extra = st.multiselect(
            "Agentes a pagar (todos si vacío):",
            [a['username'] for a in todos_agentes],
            format_func=lambda x: f"{x} ({next((a.get('nombre', x) for a in todos_agentes if a['username'] == x), x)})",
            key="coo_agentes_extra"
        )
        
        data_extra = []
        total_extra = 0
        
        for agente in todos_agentes:
            username = agente['username']
            if agentes_sel_extra and username not in agentes_sel_extra:
                continue
            
            puntos_extra = 0
            for fecha, extras in datos_puntos['puntos_extra'].get(username, {}).items():
                if fecha_ini <= fecha <= fecha_fin:
                    if isinstance(extras, list):
                        puntos_extra += sum(e.get('puntos', 0) for e in extras)
                    elif isinstance(extras, dict):
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
            st.info(f"💰 Total: **{total_extra} pts** ({total_extra/22:.2f}€)")
            
            col1, col2 = st.columns(2)
            with col1: etiqueta = st.text_input("Etiqueta:", value=f"Extra {fecha_ini} → {fecha_fin}", key="coo_etiq_extra")
            with col2: nota = st.text_input("Nota:", key="coo_nota_extra")
            
            if st.button(f"💸 PAGAR Extra ({total_extra} pts)", type="primary", use_container_width=True):
                fecha_hoy = obtener_fecha_hoy()
                for agente in todos_agentes:
                    username = agente['username']
                    if agentes_sel_extra and username not in agentes_sel_extra:
                        continue
                    
                    puntos_extra_agente = 0
                    for fecha, extras in datos_puntos['puntos_extra'].get(username, {}).items():
                        if fecha_ini <= fecha <= fecha_fin:
                            if isinstance(extras, list):
                                puntos_extra_agente += sum(e.get('puntos', 0) for e in extras)
                            elif isinstance(extras, dict):
                                puntos_extra_agente += extras.get('puntos', 0)
                    
                    if puntos_extra_agente > 0:
                        if username not in datos_puntos['pagos_realizados']:
                            datos_puntos['pagos_realizados'][username] = []
                        datos_puntos['pagos_realizados'][username].append({
                            "fecha": fecha_hoy, "puntos_pagados": puntos_extra_agente,
                            "semana": etiqueta, "nota": nota, "tipo": "extra",
                            "campaña": agente.get('campaign', 'CAPTA'), "supervisor": "COO"
                        })
                guardar_datos_puntos(datos_puntos)
                st.success(f"✅ Pagados {total_extra} pts extra")
                st.rerun()
        else:
            st.info("No hay puntos extra.")
    
    # =============================================
    # TAB 3: CIERRE PUNTOS SUPERVISORES
    # =============================================
    with tab3:
        st.write("### 👤 Cierre de Puntos Supervisores")
        st.caption("Pago mensual. Si objetivo cumplido → x2.")
        
        supervisores = um.get_users_by_role("super")
        
        meses_disp = set()
        for fecha_str in registro_diario.keys():
            meses_disp.add(fecha_str[:7])
        meses_disp = sorted(meses_disp, reverse=True)
        
        if not meses_disp:
            st.info("No hay datos registrados.")
        else:
            mes_sup = st.selectbox("Mes a cerrar:", meses_disp, key="coo_mes_sup")
            cumplio_sup = st.radio("¿Se cumplió el objetivo?", ["NO cumplido", "SI cumplido (x2)"], horizontal=True, key="coo_cumplio_sup")
            
            sup_sel = st.multiselect(
                "Supervisores a pagar (todos si vacío):",
                [s['username'] for s in supervisores],
                format_func=lambda x: f"{x} ({next((s.get('nombre', x) for s in supervisores if s['username'] == x), x)})",
                key="coo_sup_sel"
            )
            
            data_sup = []
            total_sup = 0
            
            for sup in supervisores:
                username = sup['username']
                if sup_sel and username not in sup_sel:
                    continue
                
                puntos_sup = 0
                for fecha_str in sorted(registro_diario.keys()):
                    if fecha_str.startswith(mes_sup):
                        resultado = calcular_puntos_supervisor_dia(username, fecha_str, config_super, datos_puntos)
                        puntos_sup += resultado['total']
                
                if cumplio_sup == "SI cumplido (x2)":
                    puntos_sup *= 2
                
                if puntos_sup > 0:
                    data_sup.append({
                        'Supervisor': username,
                        'Nombre': sup.get('nombre', ''),
                        'Puntos': puntos_sup,
                        'Euros': f"{puntos_sup/22:.2f}€"
                    })
                    total_sup += puntos_sup
            
            if data_sup:
                df_sup = pd.DataFrame(data_sup)
                st.dataframe(df_sup, use_container_width=True, hide_index=True)
                st.info(f"💰 Total supervisores: **{total_sup} pts** ({total_sup/22:.2f}€)")
                
                col1, col2 = st.columns(2)
                with col1: etiqueta_sup = st.text_input("Etiqueta:", value=f"Supervisores {mes_sup}", key="coo_etiq_sup")
                with col2: nota_sup = st.text_input("Nota:", key="coo_nota_sup")
                
                if st.button(f"💸 PAGAR Supervisores ({total_sup} pts)", type="primary", use_container_width=True):
                    fecha_hoy = obtener_fecha_hoy()
                    for sup in supervisores:
                        username = sup['username']
                        if sup_sel and username not in sup_sel:
                            continue
                        
                        puntos_sup = 0
                        for fecha_str in sorted(registro_diario.keys()):
                            if fecha_str.startswith(mes_sup):
                                resultado = calcular_puntos_supervisor_dia(username, fecha_str, config_super, datos_puntos)
                                puntos_sup += resultado['total']
                        
                        if cumplio_sup == "SI cumplido (x2)":
                            puntos_sup *= 2
                        
                        if puntos_sup > 0:
                            if username not in datos_puntos['pagos_realizados']:
                                datos_puntos['pagos_realizados'][username] = []
                            datos_puntos['pagos_realizados'][username].append({
                                "fecha": fecha_hoy, "puntos_pagados": puntos_sup,
                                "semana": etiqueta_sup, "nota": nota_sup, "tipo": "supervisor",
                                "campaña": "TODAS", "supervisor": "COO"
                            })
                    guardar_datos_puntos(datos_puntos)
                    st.success(f"✅ Pagados {total_sup} pts a supervisores")
                    st.rerun()
            else:
                st.info(f"No hay puntos de supervisores en {mes_sup}")
    
    # =============================================
    # TAB 4: HISTORIAL DE PAGOS
    # =============================================
    with tab4:
        st.write("### 📋 Historial de Pagos")
        
        todos_pagos = []
        for agente in todos_agentes:
            username = agente['username']
            for p in datos_puntos['pagos_realizados'].get(username, []):
                todos_pagos.append({
                    'Fecha': p.get('fecha', ''),
                    'Agente': username,
                    'Puntos': p.get('puntos_pagados', 0),
                    'Tipo': p.get('tipo', ''),
                    'Etiqueta': p.get('semana', ''),
                    'Nota': p.get('nota', '')
                })
        
        # Añadir pagos de supervisores
        for sup in supervisores:
            username = sup['username']
            for p in datos_puntos['pagos_realizados'].get(username, []):
                todos_pagos.append({
                    'Fecha': p.get('fecha', ''),
                    'Agente': f"👤 {username}",
                    'Puntos': p.get('puntos_pagados', 0),
                    'Tipo': p.get('tipo', ''),
                    'Etiqueta': p.get('semana', ''),
                    'Nota': p.get('nota', '')
                })
        
        if todos_pagos:
            todos_pagos.sort(key=lambda x: x['Fecha'], reverse=True)
            st.dataframe(pd.DataFrame(todos_pagos[:50]), use_container_width=True, hide_index=True)
        else:
            st.info("No hay pagos registrados.")