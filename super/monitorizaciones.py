# super/monitorizaciones.py
import streamlit as st
from datetime import datetime, timedelta
from core.monitorizaciones import (
    cargar_monitorizaciones, guardar_monitorizacion,
    OPCIONES_PUNTOS_CLAVE, analizar_pdf_monitorizacion,
    obtener_monitorizaciones_empleado, obtener_ultima_monitorizacion
)

def show_monitorizaciones():
    """Seccion independiente de monitorizaciones para el supervisor."""
    st.title("📋 Monitorizaciones")
    
    um = st.session_state.user_manager
    supervisor = st.session_state.user['username']
    mis_agentes = um.get_agents_by_manager(supervisor)
    
    if not mis_agentes:
        st.info("No tienes agentes asignados.")
        return
    
    tab1, tab2 = st.tabs(["📤 Nueva Monitorizacion", "📋 Historial"])
    
    # =============================================
    # TAB 1: NUEVA MONITORIZACION
    # =============================================
    with tab1:
        st.subheader("📤 Crear Monitorizacion")
        
        # =============================================
        # SUBIR PDF Y EXTRAER DATOS
        # =============================================
        st.write("### 📄 Extraer datos de PDF (opcional)")
        
        uploaded_file = st.file_uploader("Subir PDF de monitorizacion", type=['pdf'], key="pdf_monitor")
        
        if uploaded_file:
            if st.button("🔍 Extraer datos del PDF", key="btn_extraer", use_container_width=True):
                with st.spinner("Analizando PDF..."):
                    datos_extraidos = analizar_pdf_monitorizacion(uploaded_file)
                    st.session_state.datos_extraidos_pdf = datos_extraidos
                    st.rerun()
            
            # Si hay datos extraidos, mostrar previsualizacion
            if 'datos_extraidos_pdf' in st.session_state:
                d = st.session_state.datos_extraidos_pdf
                
                # Buscar agente por ID empleado
                id_detectado = str(d.get('id_empleado', ''))
                agente_encontrado = None
                for agente in mis_agentes:
                    if str(agente.get('id_empleado', '')) == id_detectado:
                        agente_encontrado = agente['username']
                        break
                
                st.markdown("---")
                
                if agente_encontrado:
                    st.success(f"✅ Agente identificado: **{agente_encontrado}** (ID: {id_detectado})")
                    d['agente_username'] = agente_encontrado
                else:
                    st.warning(f"⚠️ No se encontro ningun agente con ID empleado: {id_detectado}")
                
                # Mostrar JSON limpio
                st.write("**Datos extraidos del PDF:**")
                datos_mostrar = {
                    'id_empleado': d.get('id_empleado', ''),
                    'fecha_monitorizacion': d.get('fecha_monitorizacion', ''),
                    'nota_global': d.get('nota_global', 0),
                    'objetivo': d.get('objetivo', 85),
                    'experiencia': d.get('experiencia', 0),
                    'comunicacion': d.get('comunicacion', 0),
                    'deteccion': d.get('deteccion', 0),
                    'habilidades_venta': d.get('habilidades_venta', 0),
                    'resolucion_objeciones': d.get('resolucion_objeciones', 0),
                    'cierre_contacto': d.get('cierre_contacto', 0),
                    'feedback': d.get('feedback', '')[:200] + '...' if len(d.get('feedback', '')) > 200 else d.get('feedback', ''),
                    'plan_accion': d.get('plan_accion', '')[:200] + '...' if len(d.get('plan_accion', '')) > 200 else d.get('plan_accion', ''),
                    'puntos_clave': d.get('puntos_clave', [])
                }
                st.json(datos_mostrar)
                
                # Botones de accion
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("📋 Pasar datos al formulario", type="primary", use_container_width=True):
                        obj7_actuales = st.session_state.get('datos_mon', {}).get('objetivos_7d', {})
                        if not obj7_actuales:
                            obj7_actuales = {'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0, 'otros': ''}
                        d['objetivos_7d'] = obj7_actuales
                        st.session_state.datos_mon = d
                        st.session_state.pop('datos_extraidos_pdf', None)
                        st.success("✅ Datos transferidos al formulario de abajo. Revisa y guarda.")
                        st.rerun()
                with col_b2:
                    if st.button("🗑️ Descartar extraccion", use_container_width=True):
                        st.session_state.pop('datos_extraidos_pdf', None)
                        st.rerun()
        
        # =============================================
        # FORMULARIO MANUAL
        # =============================================
        st.markdown("---")
        st.write("### 📝 Formulario de Monitorizacion")
        
        if 'datos_mon' not in st.session_state:
            st.session_state.datos_mon = _datos_vacios()
        
        d = st.session_state.datos_mon
        
        with st.form("form_monitorizacion"):
            # Datos basicos
            st.write("#### 📅 Datos Basicos")
            col1, col2, col3 = st.columns(3)
            with col1:
                # Si hay agente_username del PDF, usarlo
                agente_username = d.get('agente_username', '')
                if agente_username:
                    st.text_input("Agente (auto-detectado)", value=agente_username, disabled=True)
                    agente_id = agente_username
                else:
                    agente_id = st.selectbox(
                        "Agente*",
                        [a['username'] for a in mis_agentes],
                        format_func=lambda x: f"{x} ({next((a.get('nombre', x) for a in mis_agentes if a['username'] == x), x)})"
                    )
            with col2:
                fecha_mon_str = d.get('fecha_monitorizacion', datetime.now().strftime('%Y-%m-%d'))
                try:
                    fecha_mon_dt = datetime.strptime(fecha_mon_str, '%Y-%m-%d')
                except:
                    fecha_mon_dt = datetime.now()
                fecha_mon = st.date_input("Fecha Monitorizacion", value=fecha_mon_dt)
            with col3:
                fecha_prox = st.date_input("Proxima Monitorizacion", value=datetime.now() + timedelta(days=7))
            
            # Puntuaciones
            st.markdown("---")
            st.write("#### 📈 Puntuaciones (%)")
            
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                nota_global = st.slider("Nota Global", 0.0, 100.0, float(d.get('nota_global', 0.0)), 1.0)
                objetivo = st.slider("Objetivo", 0.0, 100.0, float(d.get('objetivo', 85.0)), 1.0)
                experiencia = st.slider("Experiencia", 0.0, 100.0, float(d.get('experiencia', 0.0)), 1.0)
                comunicacion = st.slider("Comunicacion", 0.0, 100.0, float(d.get('comunicacion', 0.0)), 1.0)
            with col_n2:
                deteccion = st.slider("Deteccion", 0.0, 100.0, float(d.get('deteccion', 0.0)), 1.0)
                habilidades = st.slider("Habilidades de Venta", 0.0, 100.0, float(d.get('habilidades_venta', 0.0)), 1.0)
                objeciones = st.slider("Resolucion de Objeciones", 0.0, 100.0, float(d.get('resolucion_objeciones', 0.0)), 1.0)
                cierre = st.slider("Cierre de Contacto", 0.0, 100.0, float(d.get('cierre_contacto', 0.0)), 1.0)
            
            # Feedback y Plan de Accion
            st.markdown("---")
            st.write("#### 📝 Feedback y Plan de Accion")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                feedback = st.text_area("Feedback para el agente", value=str(d.get('feedback', '')), height=200,
                                       placeholder="Escribe aqui el feedback detallado...")
            with col_f2:
                plan_accion = st.text_area("Plan de accion", value=str(d.get('plan_accion', '')), height=200,
                                          placeholder="Escribe aqui el plan de accion...")
            
            # Puntos Clave
            st.markdown("---")
            st.write("#### 🔑 Puntos Clave")
            
            puntos_actuales = d.get('puntos_clave', [])
            if isinstance(puntos_actuales, str):
                puntos_actuales = [p.strip() for p in puntos_actuales.split(',') if p.strip()]
            
            puntos_clave = st.multiselect(
                "Selecciona los puntos clave a mejorar:",
                OPCIONES_PUNTOS_CLAVE,
                default=[p for p in puntos_actuales if p in OPCIONES_PUNTOS_CLAVE]
            )
            
            # Objetivos a 7 dias
            st.markdown("---")
            st.write("#### 🎯 Objetivos a 7 Dias")
            
            obj7 = d.get('objetivos_7d', {})
            if not isinstance(obj7, dict):
                obj7 = {'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0, 'otros': ''}
            
            col_o1, col_o2, col_o3 = st.columns(3)
            with col_o1:
                obj_ventas = st.number_input("🎯 Ventas objetivo", 0, 100, int(obj7.get('ventas', 0)))
            with col_o2:
                obj_llamadas_5m = st.number_input("📞 Llamadas +5min", 0, 1000, int(obj7.get('llamadas_5m', 0)))
            with col_o3:
                obj_llamadas_15m = st.number_input("📞 Llamadas +15min", 0, 1000, int(obj7.get('llamadas_15m', 0)))
            
            otros_obj = st.text_area("📝 Otros objetivos", value=str(obj7.get('otros', '')),
                                    placeholder="Cualquier otro objetivo, nota o comentario...", height=80)
            
            # Guardar
            st.markdown("---")
            if st.form_submit_button("💾 Guardar Monitorizacion", type="primary", use_container_width=True):
                if not agente_id:
                    st.error("❌ El agente es obligatorio")
                else:
                    datos_guardar = {
                        'id_empleado': str(d.get('id_empleado', agente_id)),
                        'fecha_monitorizacion': fecha_mon.strftime('%Y-%m-%d'),
                        'fecha_proxima_monitorizacion': fecha_prox.strftime('%Y-%m-%d'),
                        'nota_global': nota_global,
                        'objetivo': objetivo,
                        'experiencia': experiencia,
                        'comunicacion': comunicacion,
                        'deteccion': deteccion,
                        'habilidades_venta': habilidades,
                        'resolucion_objeciones': objeciones,
                        'cierre_contacto': cierre,
                        'feedback': feedback,
                        'plan_accion': plan_accion,
                        'puntos_clave': puntos_clave,
                        'objetivos_7d': {
                            'ventas': obj_ventas,
                            'llamadas_5m': obj_llamadas_5m,
                            'llamadas_15m': obj_llamadas_15m,
                            'otros': otros_obj
                        }
                    }
                    id_mon = guardar_monitorizacion(datos_guardar, supervisor)
                    st.session_state.pop('datos_mon', None)
                    st.session_state.pop('datos_extraidos_pdf', None)
                    st.success(f"✅ Monitorizacion guardada correctamente")
                    st.rerun()
    
    # =============================================
    # TAB 2: HISTORIAL
    # =============================================
    with tab2:
        st.subheader("📋 Historial de Monitorizaciones")
        
        agente_ver = st.selectbox(
            "Seleccionar agente:",
            [a['username'] for a in mis_agentes],
            format_func=lambda x: f"{x} ({next((a.get('nombre', x) for a in mis_agentes if a['username'] == x), x)})",
            key="hist_agente"
        )
        
        if agente_ver:
            monis = obtener_monitorizaciones_empleado(agente_ver)
            
            if monis:
                st.write(f"**{len(monis)} monitorizaciones encontradas**")
                for mon in monis:
                    with st.expander(
                        f"📅 {mon.get('fecha_monitorizacion', '?')} | "
                        f"Nota: {mon.get('nota_global', 0):.0f}% | "
                        f"Prox: {mon.get('fecha_proxima_monitorizacion', '?')}"
                    ):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Nota Global", f"{mon.get('nota_global', 0):.0f}%")
                            st.write(f"Experiencia: {mon.get('experiencia', 0):.0f}%")
                            st.write(f"Comunicacion: {mon.get('comunicacion', 0):.0f}%")
                            st.write(f"Deteccion: {mon.get('deteccion', 0):.0f}%")
                        with col_b:
                            st.write(f"Habilidades Venta: {mon.get('habilidades_venta', 0):.0f}%")
                            st.write(f"Resolucion Obj.: {mon.get('resolucion_objeciones', 0):.0f}%")
                            st.write(f"Cierre Contacto: {mon.get('cierre_contacto', 0):.0f}%")
                        
                        if mon.get('puntos_clave'):
                            st.write("**🔑 Puntos Clave:**")
                            st.write(" • " + " • ".join(mon['puntos_clave']))
                        
                        if mon.get('feedback'):
                            with st.expander("📝 Feedback"):
                                st.text(mon['feedback'])
                        
                        if mon.get('plan_accion'):
                            with st.expander("🎯 Plan de Accion"):
                                st.text(mon['plan_accion'])
                        
                        obj7 = mon.get('objetivos_7d', {})
                        if obj7 and any(v for k, v in obj7.items() if v):
                            st.write("**🎯 Objetivos 7 dias:**")
                            cols = st.columns(4)
                            with cols[0]: st.metric("Ventas", obj7.get('ventas', 0))
                            with cols[1]: st.metric("+5min", obj7.get('llamadas_5m', 0))
                            with cols[2]: st.metric("+15min", obj7.get('llamadas_15m', 0))
                            if obj7.get('otros'):
                                with cols[3]: st.caption(f"Otros: {obj7['otros']}")
            else:
                st.info(f"No hay monitorizaciones para **{agente_ver}**")


def _datos_vacios():
    """Devuelve estructura vacia de monitorizacion."""
    return {
        'id_empleado': '',
        'fecha_monitorizacion': datetime.now().strftime('%Y-%m-%d'),
        'fecha_proxima_monitorizacion': '',
        'nota_global': 0.0,
        'objetivo': 85.0,
        'experiencia': 0.0,
        'comunicacion': 0.0,
        'deteccion': 0.0,
        'habilidades_venta': 0.0,
        'resolucion_objeciones': 0.0,
        'cierre_contacto': 0.0,
        'feedback': '',
        'plan_accion': '',
        'puntos_clave': [],
        'objetivos_7d': {'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0, 'otros': ''}
    }