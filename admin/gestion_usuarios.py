# admin/gestion_usuarios.py
import streamlit as st
import pandas as pd
from auth.user_manager import UserManager

def show_gestion_usuarios():
    """Pagina de gestion de usuarios para el administrador."""
    st.title("👥 Gestion de Usuarios")
    st.write("Administra todos los usuarios del sistema desde aqui.")
    
    um = st.session_state.user_manager
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Crear Usuario",
        "✏️ Modificar Usuario",
        "🗑️ Gestionar Bajas",
        "🔄 Mover a WINBACK / CAPTA"
    ])
    
    # =============================================
    # PESTAÑA 1: CREAR USUARIO
    # =============================================
    with tab1:
        st.subheader("Crear Nuevos Usuarios")
        
        create_mode = st.radio("Modo de creacion:", ["Individual", "Masivo (Bulk)"], horizontal=True)
        
        if create_mode == "Individual":
            with st.form("create_single_user"):
                col1, col2 = st.columns(2)
                
                with col1:
                    username = st.text_input("Nombre de usuario*")
                    password = st.text_input("Contrasena*", type="password")
                    nombre = st.text_input("Nombre completo")
                    id_empleado = st.text_input("ID Empleado", placeholder="Ej: 1469")
                
                with col2:
                    role = st.selectbox("Rol*", ["agent", "super", "admin"])
                    team = st.text_input("Equipo", value="Sin equipo")
                    
                    if role == "agent":
                        campaign = st.selectbox("Campaña", ["CAPTA", "WINBACK"])
                        supervisores = um.get_users_by_role("super")
                        super_options = ["Ninguno"] + [s['username'] for s in supervisores]
                        manager = st.selectbox("Supervisor", super_options)
                        if manager == "Ninguno":
                            manager = None
                    else:
                        campaign = None
                        manager = None
                
                if role == "agent":
                    st.markdown("---")
                    st.write("⚙️ Configuracion del Agente")
                    
                    sph_target = st.number_input(
                        "SPH Objetivo", min_value=0.01, max_value=1.0, value=0.06, step=0.01, format="%.2f",
                        help="SPH objetivo para este agente"
                    )
                    
                    st.write("**Horario**")
                    col_h1, col_h2, col_h3 = st.columns(3)
                    with col_h1:
                        horas_diarias = st.number_input("Horas diarias", min_value=1.0, max_value=8.0, value=6.0, step=0.5, format="%.1f")
                    with col_h2:
                        hora_inicio = st.text_input("Hora inicio", value="15:00", help="Formato HH:MM")
                    with col_h3:
                        hora_fin = st.text_input("Hora fin", value="21:00", help="Formato HH:MM")
                    
                    working_days = st.multiselect(
                        "Dias laborables",
                        ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"],
                        default=["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
                    )
                else:
                    sph_target = None
                    horas_diarias = None
                    working_days = None
                    hora_inicio = None
                    hora_fin = None
                
                submitted = st.form_submit_button("✅ Crear Usuario", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.error("Nombre de usuario y contrasena son obligatorios")
                    else:
                        try:
                            dias_semana = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4}
                            working_days_list = [dias_semana[d] for d in working_days] if working_days else [0, 1, 2, 3, 4]
                            
                            schedule = None
                            if role == "agent":
                                schedule = {
                                    "start_time": hora_inicio or "15:00",
                                    "end_time": hora_fin or "21:00",
                                    "working_days": working_days_list,
                                    "daily_hours": horas_diarias or 6.0,
                                    "weekly_hours": (horas_diarias or 6.0) * len(working_days_list),
                                    "type": "full_time" if (horas_diarias or 6.0) >= 6.0 else "reduced"
                                }
                            
                            um.create_user(
                                username=username,
                                password=password,
                                role=role,
                                nombre=nombre,
                                id_empleado=id_empleado,
                                campaign=campaign or "CAPTA",
                                team=team,
                                manager=manager,
                                schedule=schedule,
                                sph_target=sph_target or 0.06
                            )
                            st.success(f"✅ Usuario '{username}' creado con exito!")
                        except ValueError as e:
                            st.error(str(e))
        
        else:
            st.info("Pega los datos en formato: `username,password,nombre,id_empleado,team,manager` (uno por linea)")
            
            bulk_text = st.text_area(
                "Datos de usuarios:",
                placeholder="agente01,pass123,Nombre Apellido,1469,Equipo A,super01",
                height=150
            )
            
            st.markdown("---")
            st.write("⚙️ Configuracion para TODOS los agentes:")
            
            bulk_sph = st.number_input("SPH Objetivo", min_value=0.01, max_value=1.0, value=0.06, step=0.01, format="%.2f", key="bulk_sph")
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                bulk_horas = st.number_input("Horas diarias", min_value=1.0, max_value=8.0, value=6.0, step=0.5, format="%.1f", key="bulk_horas")
            with col_b2:
                bulk_hora_ini = st.text_input("Hora inicio", value="15:00", key="bulk_ini")
            with col_b3:
                bulk_hora_fin = st.text_input("Hora fin", value="21:00", key="bulk_fin")
            
            bulk_dias = st.multiselect(
                "Dias laborables",
                ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"],
                default=["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"],
                key="bulk_dias"
            )
            
            if st.button("🚀 Crear Usuarios en Bloque", use_container_width=True):
                if bulk_text:
                    lines = [l.strip() for l in bulk_text.split('\n') if l.strip()]
                    agents_data = []
                    
                    dias_semana = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4}
                    working_days_list = [dias_semana[d] for d in bulk_dias] if bulk_dias else [0, 1, 2, 3, 4]
                    
                    for line in lines:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 2:
                            agent = {
                                "username": parts[0],
                                "password": parts[1],
                                "nombre": parts[2] if len(parts) > 2 else "",
                                "id_empleado": parts[3] if len(parts) > 3 else "",
                                "team": parts[4] if len(parts) > 4 else "Sin equipo",
                                "manager": parts[5] if len(parts) > 5 else None,
                                "schedule": {
                                    "start_time": bulk_hora_ini,
                                    "end_time": bulk_hora_fin,
                                    "working_days": working_days_list,
                                    "daily_hours": bulk_horas,
                                    "weekly_hours": bulk_horas * len(working_days_list),
                                    "type": "full_time" if bulk_horas >= 6.0 else "reduced"
                                },
                                "sph_target": bulk_sph
                            }
                            agents_data.append(agent)
                    
                    if agents_data:
                        result = um.create_agents_bulk(agents_data)
                        st.success(f"✅ Creados: {result['created']} agentes")
                        if result['errors']:
                            st.warning("Errores:")
                            for err in result['errors']:
                                st.write(f" - {err}")
    
    # =============================================
    # PESTAÑA 2: MODIFICAR USUARIO
    # =============================================
    with tab2:
        st.subheader("Modificar Usuario Existente")
        
        all_users = um._load_users()
        usernames = [u['username'] for u in all_users]
        selected_user = st.selectbox("Seleccionar usuario a modificar:", usernames)
        
        if selected_user:
            user_data = um.get_user(selected_user)
            
            if user_data:
                with st.form("modify_user"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_nombre = st.text_input("Nombre completo", value=user_data.get('nombre', ''))
                        new_id_empleado = st.text_input("ID Empleado", value=str(user_data.get('id_empleado', '')))
                        new_team = st.text_input("Equipo", value=user_data.get('team', ''))
                        
                        if user_data['role'] == 'agent':
                            st.write(f"**Campaña actual:** {user_data.get('campaign', 'CAPTA')}")
                            supervisores = um.get_users_by_role("super")
                            super_options = ["Ninguno"] + [s['username'] for s in supervisores]
                            current_manager = user_data.get('manager', 'Ninguno') or 'Ninguno'
                            try:
                                manager_index = super_options.index(current_manager)
                            except:
                                manager_index = 0
                            new_manager = st.selectbox("Supervisor", super_options, index=manager_index)
                            if new_manager == "Ninguno":
                                new_manager = None
                    
                    with col2:
                        st.write(f"**Rol:** {user_data['role']}")
                        if user_data.get('standby', False):
                            st.warning("⚠️ Este usuario esta en STANDBY")
                        if user_data.get('usuario_padre'):
                            st.info(f"🔗 Usuario padre: {user_data['usuario_padre']}")
                        
                        new_password = st.text_input("Nueva contrasena (dejar vacio para no cambiar)", type="password")
                        
                        if user_data['role'] == 'agent':
                            sph_config = user_data.get('sph_config', {})
                            sph_actual = sph_config.get('target', 0.06)
                            new_sph = st.number_input("SPH Objetivo", min_value=0.01, max_value=1.0, value=sph_actual, step=0.01, format="%.2f")
                            
                            st.markdown("---")
                            st.write("🕐 Horario")
                            schedule = user_data.get('schedule', {})
                            col_h1, col_h2, col_h3 = st.columns(3)
                            with col_h1:
                                new_hora_ini = st.text_input("Hora inicio", value=schedule.get('start_time', '15:00'))
                            with col_h2:
                                new_hora_fin = st.text_input("Hora fin", value=schedule.get('end_time', '21:00'))
                            with col_h3:
                                new_horas_dia = st.number_input("Horas diarias", min_value=1.0, max_value=8.0, value=schedule.get('daily_hours', 6.0), step=0.5, format="%.1f")
                            
                            dias_semana = {0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes"}
                            current_days = schedule.get('working_days', [0, 1, 2, 3, 4])
                            dias_nombres = [dias_semana[d] for d in current_days if d in dias_semana]
                            new_dias = st.multiselect(
                                "Dias laborables",
                                ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"],
                                default=dias_nombres
                            )
                    
                    submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                    
                    if submitted:
                        updates = {}
                        if new_nombre != user_data.get('nombre'):
                            updates['nombre'] = new_nombre
                        if new_id_empleado != str(user_data.get('id_empleado', '')):
                            updates['id_empleado'] = new_id_empleado
                        if new_team != user_data.get('team'):
                            updates['team'] = new_team
                        if user_data['role'] == 'agent':
                            if new_manager != user_data.get('manager'):
                                updates['manager'] = new_manager
                            if new_sph != sph_actual:
                                updates['sph_target'] = new_sph
                            
                            dias_map = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4}
                            nuevos_dias_list = [dias_map[d] for d in new_dias]
                            if (new_hora_ini != schedule.get('start_time') or
                                new_hora_fin != schedule.get('end_time') or
                                new_horas_dia != schedule.get('daily_hours') or
                                nuevos_dias_list != schedule.get('working_days')):
                                updates['schedule'] = {
                                    'start_time': new_hora_ini,
                                    'end_time': new_hora_fin,
                                    'daily_hours': new_horas_dia,
                                    'working_days': nuevos_dias_list,
                                    'weekly_hours': new_horas_dia * len(nuevos_dias_list),
                                    'type': schedule.get('type', 'full_time')
                                }
                        
                        if new_password:
                            updates['password_hash'] = um._hash_password(new_password)
                        
                        if updates:
                            um.update_user(selected_user, updates)
                            st.success(f"✅ Usuario '{selected_user}' actualizado!")
                        else:
                            st.info("No se detectaron cambios")
    
    # =============================================
    # PESTAÑA 3: GESTIONAR BAJAS
    # =============================================
    with tab3:
        st.subheader("Dar de Baja Usuarios")
        
        all_users = um._load_users()
        
        users_df = pd.DataFrame([{
            'Username': u['username'],
            'Nombre': u.get('nombre', ''),
            'ID Empleado': u.get('id_empleado', ''),
            'Rol': u['role'],
            'Equipo': u.get('team', ''),
            'Campaña': u.get('campaign', ''),
            'Supervisor': u.get('manager', ''),
            'Standby': '💤' if u.get('standby') else '✅'
        } for u in all_users])
        
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        
        st.write("---")
        delete_mode = st.radio("Modo de baja:", ["Individual", "Masivo (Bulk)"], horizontal=True)
        
        if delete_mode == "Individual":
            user_to_delete = st.selectbox(
                "Seleccionar usuario a eliminar:",
                [u for u in usernames if u != st.session_state.user['username']]
            )
            if st.button("🗑️ Eliminar Usuario", type="primary", use_container_width=True):
                if user_to_delete:
                    um.delete_user(user_to_delete)
                    st.success(f"✅ Usuario '{user_to_delete}' eliminado!")
                    st.rerun()
        else:
            users_to_delete = st.multiselect(
                "Seleccionar usuarios a eliminar:",
                [u for u in usernames if u != st.session_state.user['username']]
            )
            if users_to_delete and st.button("🗑️ Eliminar Seleccionados", type="primary", use_container_width=True):
                result = um.delete_agents_bulk(users_to_delete)
                st.success(f"✅ Eliminados: {result['deleted']} usuarios")
                if result['errors']:
                    st.warning("Errores:")
                    for err in result['errors']:
                        st.write(f" - {err}")
                st.rerun()
    
    # =============================================
    # PESTAÑA 4: SISTEMA W (WINBACK)
    # =============================================
    with tab4:
        st.subheader("🔄 Sistema W - Mover a WINBACK / Reactivar CAPTA")
        st.caption("Al mover a WINBACK se crea un usuario W+NOMBRE. El original queda en standby.")
        
        subtab1, subtab2 = st.tabs(["➡️ Mover a WINBACK", "⬅️ Reactivar CAPTA"])
        
        with subtab1:
            st.write("### Mover agente CAPTA → WINBACK")
            agentes_capta = [a for a in um.get_all_agents() if a.get('campaign') == 'CAPTA' and not a.get('standby', False)]
            
            if agentes_capta:
                agente_a_mover = st.selectbox(
                    "Seleccionar agente:",
                    [a['username'] for a in agentes_capta],
                    format_func=lambda x: f"{x} ({next((a.get('nombre', x) for a in agentes_capta if a['username'] == x), x)})",
                    key="mover_winback"
                )
                
                if st.button("➡️ Mover a WINBACK", type="primary", use_container_width=True):
                    resultado = um.mover_a_winback(agente_a_mover)
                    if resultado['success']:
                        st.success(f"✅ Usuario W{agente_a_mover} creado en WINBACK. {agente_a_mover} en standby.")
                        st.info(f"🔑 El nuevo usuario puede iniciar sesion como: **{resultado['w_username']}** con la misma contrasena.")
                    else:
                        st.error(f"❌ {resultado['error']}")
            else:
                st.info("No hay agentes activos en CAPTA.")
        
        with subtab2:
            st.write("### Reactivar agente WINBACK → CAPTA")
            agentes_winback = [a for a in um.get_all_agents() if a.get('campaign') == 'WINBACK' and not a.get('standby', False) and a['username'].startswith('W')]
            
            if agentes_winback:
                agente_a_reactivar = st.selectbox(
                    "Seleccionar agente W:",
                    [a['username'] for a in agentes_winback],
                    format_func=lambda x: f"{x} → {x[1:]} ({next((a.get('nombre', x) for a in agentes_winback if a['username'] == x), x)})",
                    key="reactivar_capta"
                )
                
                if st.button("⬅️ Reactivar en CAPTA", type="primary", use_container_width=True):
                    resultado = um.reactivar_de_winback(agente_a_reactivar)
                    if resultado['success']:
                        st.success(f"✅ {agente_a_reactivar} en standby. {resultado['original']} reactivado en CAPTA.")
                    else:
                        st.error(f"❌ {resultado['error']}")
            else:
                st.info("No hay agentes W activos en WINBACK.")