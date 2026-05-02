# agent/agent_calculadora.py
import streamlit as st
import pandas as pd
from features.calculator.electricidad import comparar_planes

def show_calculadora():
    """Calculadora de tarifas con buscador de facturas."""
    st.title("📊 Calculadora de Tarifas")
    
    agente = st.session_state.user
    campana_agente = agente.get('campaign', 'CAPTA')
    
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
        df_styled = df_styled.set_properties(**{'text-align': 'center', 'padding': '10px', 'border': '1px solid #ccc', 'font-weight': '700', 'font-size': '14px', 'color': '#000000'})
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