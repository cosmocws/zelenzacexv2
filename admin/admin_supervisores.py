# admin/admin_supervisores.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from calendar import monthrange

def cargar_config_super():
    try:
        with open('data/config_puntos_super.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "puntos_supervisor": {
                "CAPTA": {"electricidad": 20, "electricidad_servicio": 20, "gas": 15, "gas_servicio": 15,
                          "bonus_electricidad": 15, "bonus_electricidad_servicio": 15, "bonus_gas": 10, "bonus_gas_servicio": 10},
                "WINBACK": {"electricidad": 5, "electricidad_servicio": 5, "gas": 4, "gas_servicio": 4,
                            "bonus_electricidad": 3.5, "bonus_electricidad_servicio": 3.5, "bonus_gas": 2.5, "bonus_gas_servicio": 2.5}
            },
            "objetivos_ventas": {"CAPTA": 0, "WINBACK": 0},
            "bonus_diarios": {}
        }

def calcular_puntos_supervisor_dia(supervisor, fecha_str, config, datos_puntos):
    """Calcula los puntos de un supervisor en un dia. Puntos por TIPO de venta."""
    um = st.session_state.user_manager
    
    puntos_capta = 0.0
    puntos_winback = 0.0
    detalle = []
    
    bonus_dia = config['bonus_diarios'].get(fecha_str, {}).get(supervisor, {})
    bonus_capta = bonus_dia.get('CAPTA', False)
    bonus_winback = bonus_dia.get('WINBACK', False)
    
    pts_capta = config['puntos_supervisor']['CAPTA']
    pts_winback = config['puntos_supervisor']['WINBACK']
    
    todos_agentes = um.get_all_agents()
    
    for agente in todos_agentes:
        username = agente['username']
        ventas_dia = datos_puntos['ventas'].get(username, {}).get(fecha_str, [])
        
        for venta in ventas_dia:
            if venta.get('supervisor', '') != supervisor:
                continue
            
            tipo_venta = venta.get('tipo', 'CAPTA')
            producto = venta.get('producto', '')
            servicios = venta.get('servicios', [])
            tiene_servicio = len(servicios) > 0
            
            if tipo_venta in ['CAPTA', 'CROSS']:
                pts = pts_capta
                bonus_activo = bonus_capta
                es_capta = True
            else:
                pts = pts_winback
                bonus_activo = bonus_winback
                es_capta = False
            
            puntos_venta = 0.0
            detalle_venta = ""
            
            if producto == "Electricidad":
                puntos_venta += pts['electricidad']
                detalle_venta = f"Elec (+{pts['electricidad']})"
                if tiene_servicio:
                    puntos_venta += pts['electricidad_servicio']
                    detalle_venta += f" +Serv (+{pts['electricidad_servicio']})"
                if bonus_activo:
                    puntos_venta += pts['bonus_electricidad']
                    detalle_venta += f" +Bonus (+{pts['bonus_electricidad']})"
                    if tiene_servicio:
                        puntos_venta += pts['bonus_electricidad_servicio']
                        detalle_venta += f" +Bonus Serv (+{pts['bonus_electricidad_servicio']})"
            
            elif producto == "Gas":
                puntos_venta += pts['gas']
                detalle_venta = f"Gas (+{pts['gas']})"
                if tiene_servicio:
                    puntos_venta += pts['gas_servicio']
                    detalle_venta += f" +Serv (+{pts['gas_servicio']})"
                if bonus_activo:
                    puntos_venta += pts['bonus_gas']
                    detalle_venta += f" +Bonus (+{pts['bonus_gas']})"
                    if tiene_servicio:
                        puntos_venta += pts['bonus_gas_servicio']
                        detalle_venta += f" +Bonus Serv (+{pts['bonus_gas_servicio']})"
            
            if es_capta:
                puntos_capta += puntos_venta
            else:
                puntos_winback += puntos_venta
            
            detalle.append({
                'agente': username,
                'producto': producto,
                'servicios': servicios,
                'tipo': tipo_venta,
                'puntos': puntos_venta,
                'detalle': detalle_venta,
                'bonus': bonus_activo
            })
    
    return {
        'puntos_capta': round(puntos_capta, 1),
        'puntos_winback': round(puntos_winback, 1),
        'total': round(puntos_capta + puntos_winback, 1),
        'detalle': detalle
    }

def show_supervisores():
    st.title("👤 Supervisores")
    
    um = st.session_state.user_manager
    from super.super_panel import cargar_datos_puntos, cargar_registro_diario
    datos_puntos = cargar_datos_puntos()
    registro = cargar_registro_diario()
    config = cargar_config_super()
    
    supervisores = um.get_users_by_role("super")
    
    if not supervisores:
        st.info("No hay supervisores registrados.")
        return
    
    tab1, tab2, tab3 = st.tabs(["📊 Resumen del Mes", "📅 Historial Diario", "💰 Cierre Mensual"])
    
    # =============================================
    # TAB 1: RESUMEN DEL MES
    # =============================================
    with tab1:
        st.subheader("📊 Puntos Acumulados del Mes")
        
        mes_actual = datetime.now().strftime('%Y-%m')
        
        data_sup = []
        for sup in supervisores:
            username = sup['username']
            total_capta = 0.0
            total_winback = 0.0
            
            for fecha_str in sorted(registro.keys()):
                if fecha_str.startswith(mes_actual):
                    resultado = calcular_puntos_supervisor_dia(username, fecha_str, config, datos_puntos)
                    total_capta += resultado['puntos_capta']
                    total_winback += resultado['puntos_winback']
            
            total = total_capta + total_winback
            
            obj_cumplido = datos_puntos.get('objetivos_cumplidos', {}).get(mes_actual, False)
            if obj_cumplido:
                total *= 2
                total_capta *= 2
                total_winback *= 2
            
            data_sup.append({
                'Supervisor': username,
                'Nombre': sup.get('nombre', ''),
                'Puntos CAPTA': round(total_capta, 1),
                'Puntos WINBACK': round(total_winback, 1),
                'Total': round(total, 1),
                'Obj Cumplido': '✅ x2' if obj_cumplido else '❌ x1'
            })
        
        df = pd.DataFrame(data_sup)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total CAPTA", round(sum(d['Puntos CAPTA'] for d in data_sup), 1))
        with col2: st.metric("Total WINBACK", round(sum(d['Puntos WINBACK'] for d in data_sup), 1))
        with col3: st.metric("Total General", round(sum(d['Total'] for d in data_sup), 1))
    
    # =============================================
    # TAB 2: HISTORIAL DIARIO
    # =============================================
    with tab2:
        st.subheader("📅 Historial Diario por Supervisor")
        
        sup_sel = st.selectbox(
            "Supervisor:",
            [s['username'] for s in supervisores],
            format_func=lambda x: f"{x} ({next((s.get('nombre', x) for s in supervisores if s['username'] == x), x)})",
            key="hist_sup"
        )
        
        fecha_sel = st.date_input("Fecha:", value=datetime.now(), key="hist_fecha")
        fecha_str = fecha_sel.strftime('%Y-%m-%d')
        
        if sup_sel and fecha_str:
            resultado = calcular_puntos_supervisor_dia(sup_sel, fecha_str, config, datos_puntos)
            
            bonus_dia = config['bonus_diarios'].get(fecha_str, {}).get(sup_sel, {})
            
            col_b1, col_b2 = st.columns(2)
            with col_b1: st.metric("Bonus CAPTA", "✅" if bonus_dia.get('CAPTA') else "❌")
            with col_b2: st.metric("Bonus WINBACK", "✅" if bonus_dia.get('WINBACK') else "❌")
            
            st.write(f"**Total del dia: {resultado['total']} pts** (CAPTA: {resultado['puntos_capta']} | WINBACK: {resultado['puntos_winback']})")
            
            if resultado['detalle']:
                st.write("**Desglose:**")
                for d in resultado['detalle']:
                    bonus_icon = "🏆" if d.get('bonus') else ""
                    st.write(f"- {d['agente']} | {d['detalle']} {bonus_icon}")
            else:
                st.info("No hay ventas registradas este dia.")
    
    # =============================================
    # TAB 3: CIERRE MENSUAL
    # =============================================
    with tab3:
        st.subheader("💰 Cierre Mensual de Puntos Supervisor")
        st.caption("Al cerrar el mes, se aplica x2 si se cumplio el objetivo global.")
        
        meses = set()
        for fecha in datos_puntos.get('objetivos_cumplidos', {}).keys():
            meses.add(fecha)
        for fecha in registro.keys():
            meses.add(fecha[:7])
        meses = sorted(meses, reverse=True)
        
        if meses:
            mes_cierre = st.selectbox("Mes a revisar:", meses, key="mes_cierre")
            obj_cumplido = datos_puntos.get('objetivos_cumplidos', {}).get(mes_cierre, False)
            
            if obj_cumplido:
                st.success(f"✅ {mes_cierre} - Objetivo CUMPLIDO → Se aplica x2")
            else:
                st.warning(f"❌ {mes_cierre} - Objetivo NO cumplido → Sin multiplicador")
            
            st.write("**Totales del mes:**")
            for sup in supervisores:
                username = sup['username']
                total_mes = 0.0
                for fecha_str in registro.keys():
                    if fecha_str.startswith(mes_cierre):
                        resultado = calcular_puntos_supervisor_dia(username, fecha_str, config, datos_puntos)
                        total_mes += resultado['total']
                total_final = total_mes * 2 if obj_cumplido else total_mes
                st.write(f"- **{username}**: {total_mes:.1f} pts → **{total_final:.1f} pts** {'(x2)' if obj_cumplido else ''}")
        else:
            st.info("No hay datos registrados.")