# agent/agent_ausencias.py
import streamlit as st
from datetime import datetime, timedelta

def show_ausencias():
    """Pantalla de solicitud de ausencias del agente."""
    st.title("📅 Solicitar Ausencia")
    st.caption("Solicita tus dias de vacaciones o ausencias. Tu supervisor las revisara.")
    
    agente = st.session_state.user
    username = agente['username']
    
    # Cargar registro diario (ahi se guardan las ausencias)
    from super.super_panel import cargar_registro_diario, guardar_registro_diario
    registro = cargar_registro_diario()
    
    # Extraer ausencias del registro diario
    mis_ausencias = {}
    for fecha, agentes in registro.items():
        if username in agentes:
            if agentes[username].get('ausente', False):
                mis_ausencias[fecha] = True
    
    # Mostrar ausencias actuales del mes
    st.write("### 📋 Mis Ausencias del Mes")
    mes_actual = datetime.now().strftime('%Y-%m')
    
    ausencias_mes = {f: e for f, e in mis_ausencias.items() if f.startswith(mes_actual) and e}
    
    if ausencias_mes:
        for fecha in sorted(ausencias_mes.keys()):
            st.write(f"- 📅 {fecha}")
        st.write(f"**Total dias ausente este mes: {len(ausencias_mes)}**")
    else:
        st.info("No tienes ausencias registradas este mes.")
    
    # Proximas ausencias
    st.write("### 📅 Proximas Ausencias")
    hoy_str = datetime.now().strftime('%Y-%m-%d')
    futuras = {f: e for f, e in mis_ausencias.items() if f >= hoy_str and e}
    
    if futuras:
        for fecha in sorted(futuras.keys()):
            st.write(f"- 📅 {fecha}")
    else:
        st.info("No tienes ausencias programadas.")
    
    st.markdown("---")
    st.write("### ➕ Solicitar Nueva Ausencia")
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        fecha_inicio = st.date_input("Fecha inicio", value=datetime.now(), key="ausencia_ini")
    with col_a2:
        fecha_fin = st.date_input("Fecha fin", value=datetime.now(), key="ausencia_fin")
    
    motivo = st.text_input("Motivo (opcional)", placeholder="Ej: Vacaciones, asuntos personales...", key="ausencia_motivo")
    
    if st.button("📅 Solicitar Ausencia", type="primary", use_container_width=True):
        if fecha_inicio > fecha_fin:
            st.error("❌ La fecha de inicio no puede ser posterior a la fecha de fin")
        else:
            dias_solicitados = 0
            fecha_actual = fecha_inicio
            while fecha_actual <= fecha_fin:
                if fecha_actual.weekday() < 5:  # Solo L-V
                    fecha_str = fecha_actual.strftime('%Y-%m-%d')
                    
                    # Asegurar que existe la fecha y el agente en el registro
                    if fecha_str not in registro:
                        registro[fecha_str] = {}
                    if username not in registro[fecha_str]:
                        registro[fecha_str][username] = {
                            'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0, 'ausente': False
                        }
                    
                    # Marcar como ausente
                    registro[fecha_str][username]['ausente'] = True
                    dias_solicitados += 1
                
                fecha_actual += timedelta(days=1)
            
            guardar_registro_diario(registro)
            
            if dias_solicitados > 0:
                st.success(f"✅ Ausencia solicitada: {dias_solicitados} dias laborables del {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}")
            else:
                st.warning("⚠️ El rango seleccionado no incluye dias laborables (L-V).")
            st.rerun()