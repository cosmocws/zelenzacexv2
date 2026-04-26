# admin/admin_configuracion.py
import streamlit as st
import json
import os
import shutil

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

def guardar_config_super(datos):
    os.makedirs('data', exist_ok=True)
    with open('data/config_puntos_super.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    os.makedirs('data_backup', exist_ok=True)
    shutil.copy('data/config_puntos_super.json', 'data_backup/config_puntos_super.json')

def show_configuracion():
    st.title("⚙️ Configuracion")
    
    config = cargar_config_super()
    
    tab1, tab2, tab3 = st.tabs(["🎯 Objetivos de Ventas", "⭐ Puntos Supervisores", "🏆 Bonus Diario"])
    
    # =============================================
    # TAB 1: OBJETIVOS DE VENTAS
    # =============================================
    with tab1:
        st.subheader("🎯 Ventas Objetivo Mensuales")
        st.caption("Estos objetivos se usan para saber si se cumple el objetivo global del mes.")
        
        with st.form("form_objetivos"):
            col1, col2 = st.columns(2)
            with col1:
                obj_capta = st.number_input("Objetivo CAPTA", min_value=0, value=config['objetivos_ventas'].get('CAPTA', 0), step=10)
            with col2:
                obj_winback = st.number_input("Objetivo WINBACK", min_value=0, value=config['objetivos_ventas'].get('WINBACK', 0), step=10)
            
            if st.form_submit_button("💾 Guardar Objetivos", type="primary"):
                config['objetivos_ventas']['CAPTA'] = obj_capta
                config['objetivos_ventas']['WINBACK'] = obj_winback
                guardar_config_super(config)
                st.success("✅ Objetivos guardados")
                st.rerun()
    
    # =============================================
    # TAB 2: PUNTOS SUPERVISORES
    # =============================================
    with tab2:
        st.subheader("⭐ Puntos por Venta para Supervisores")
        
        for campana in ["CAPTA", "WINBACK"]:
            st.write(f"### {campana}")
            pts = config['puntos_supervisor'][campana]
            
            with st.form(f"form_puntos_{campana}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Electricidad**")
                    elec_base = st.number_input(f"Base", min_value=0.0, value=float(pts['electricidad']), step=1.0, format="%.1f", key=f"{campana}_elec_base")
                    elec_serv = st.number_input(f"+ Servicio (PI/UEN)", min_value=0.0, value=float(pts['electricidad_servicio']), step=1.0, format="%.1f", key=f"{campana}_elec_serv")
                
                with col2:
                    st.write("**Gas**")
                    gas_base = st.number_input(f"Base", min_value=0.0, value=float(pts['gas']), step=1.0, format="%.1f", key=f"{campana}_gas_base")
                    gas_serv = st.number_input(f"+ Servicio (PMG)", min_value=0.0, value=float(pts['gas_servicio']), step=1.0, format="%.1f", key=f"{campana}_gas_serv")
                
                st.write("**Bonus Diario**")
                col3, col4 = st.columns(2)
                with col3:
                    bonus_elec = st.number_input(f"Bonus Electricidad", min_value=0.0, value=float(pts['bonus_electricidad']), step=1.0, format="%.1f", key=f"{campana}_bonus_elec")
                    bonus_elec_serv = st.number_input(f"Bonus Elec + Servicio", min_value=0.0, value=float(pts['bonus_electricidad_servicio']), step=1.0, format="%.1f", key=f"{campana}_bonus_elec_serv")
                with col4:
                    bonus_gas = st.number_input(f"Bonus Gas", min_value=0.0, value=float(pts['bonus_gas']), step=1.0, format="%.1f", key=f"{campana}_bonus_gas")
                    bonus_gas_serv = st.number_input(f"Bonus Gas + Servicio", min_value=0.0, value=float(pts['bonus_gas_servicio']), step=1.0, format="%.1f", key=f"{campana}_bonus_gas_serv")
                
                if st.form_submit_button(f"💾 Guardar {campana}", type="primary"):
                    config['puntos_supervisor'][campana] = {
                        "electricidad": elec_base,
                        "electricidad_servicio": elec_serv,
                        "gas": gas_base,
                        "gas_servicio": gas_serv,
                        "bonus_electricidad": bonus_elec,
                        "bonus_electricidad_servicio": bonus_elec_serv,
                        "bonus_gas": bonus_gas,
                        "bonus_gas_servicio": bonus_gas_serv
                    }
                    guardar_config_super(config)
                    st.success(f"✅ Puntos {campana} guardados")
                    st.rerun()
    
    # =============================================
    # TAB 3: BONUS DIARIO
    # =============================================
    with tab3:
        st.subheader("🏆 Activar/Desactivar Bonus Diario por Supervisor")
        st.caption("Marca los dias en los que un supervisor supero el SPH medio y aplica bonus a sus puntos.")
        
        from datetime import datetime
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            fecha_bonus = st.date_input("Fecha:", value=datetime.now(), key="fecha_bonus")
            fecha_str = fecha_bonus.strftime('%Y-%m-%d')
        with col_b2:
            campana_bonus = st.selectbox("Campaña:", ["CAPTA", "WINBACK"], key="campana_bonus")
        with col_b3:
            um = st.session_state.user_manager
            supervisores = um.get_users_by_role("super")
            supervisor_bonus = st.selectbox(
                "Supervisor:",
                [s['username'] for s in supervisores],
                format_func=lambda x: f"{x} ({next((s.get('nombre', x) for s in supervisores if s['username'] == x), x)})",
                key="supervisor_bonus"
            )
        
        # Ver estado actual
        bonus_actual = config['bonus_diarios'].get(fecha_str, {}).get(supervisor_bonus, {}).get(campana_bonus, False)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if bonus_actual:
                st.success(f"✅ {supervisor_bonus} YA tiene bonus en {campana_bonus} el {fecha_str}")
                if st.button("❌ Quitar Bonus", use_container_width=True):
                    config['bonus_diarios'][fecha_str][supervisor_bonus][campana_bonus] = False
                    guardar_config_super(config)
                    st.warning(f"Bonus quitado a {supervisor_bonus}")
                    st.rerun()
            else:
                st.info(f"❌ {supervisor_bonus} NO tiene bonus en {campana_bonus} el {fecha_str}")
                if st.button("✅ Activar Bonus", type="primary", use_container_width=True):
                    if fecha_str not in config['bonus_diarios']:
                        config['bonus_diarios'][fecha_str] = {}
                    if supervisor_bonus not in config['bonus_diarios'][fecha_str]:
                        config['bonus_diarios'][fecha_str][supervisor_bonus] = {}
                    config['bonus_diarios'][fecha_str][supervisor_bonus][campana_bonus] = True
                    guardar_config_super(config)
                    st.success(f"✅ Bonus activado para {supervisor_bonus} en {campana_bonus}")
                    st.rerun()
        
        # Mostrar últimos bonus registrados
        st.markdown("---")
        st.write("### 📋 Últimos Bonus Registrados")
        
        bonus_lista = []
        for fecha, supervisores_bonus in config['bonus_diarios'].items():
            for sup, campanas in supervisores_bonus.items():
                for camp, activo in campanas.items():
                    if activo:
                        bonus_lista.append({
                            'Fecha': fecha,
                            'Supervisor': sup,
                            'Campaña': camp,
                            'Bonus': '✅'
                        })
        
        if bonus_lista:
            bonus_lista.sort(key=lambda x: x['Fecha'], reverse=True)
            import pandas as pd
            df_bonus = pd.DataFrame(bonus_lista[:20])
            st.dataframe(df_bonus, use_container_width=True, hide_index=True)
        else:
            st.info("No hay bonus registrados.")