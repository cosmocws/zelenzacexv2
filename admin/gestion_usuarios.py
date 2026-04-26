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
        "🔄 Cambio Masivo Campaña"
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
                
                # --- Configuracion del agente (SPH y Horario) ---
                if role == "agent":
                    st.markdown("---")
                    st.write("⚙️ Configuracion del Agente")
                    col_sph1, col_sph2, col_sph3 = st.columns(3)
                    with col_sph1:
                        sph_target = st.number_input(
                            "SPH Objetivo",
                            min_value=0.01, max_value=1.0, value=0.06, step=0.01, format="%.2f",
                            help="SPH objetivo (0.06 para noveles)"
                        )
                    with col_sph2:
                        horas_diarias = st.number_input(
                            "Horas diarias",
                            min_value=1.0, max_value=8.0, value=6.0, step=0.5, format="%.1f",
                            help="Horas trabajadas al dia"
                        )
                    with col_sph3:
                        working_days = st.multiselect(
                            "Dias laborables",
                            ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"],
                            default=["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
                        )
                    
                    col_h1, col_h2 = st.columns(2)
                    with col_h1:
                        hora_inicio = st.text_input("Hora de inicio", value="15:00", help="Formato HH:MM")
                    with col_h2:
                        hora_fin = st.text_input("Hora de fin", value="21:00", help="Formato HH:MM")
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
                            dias_semana = {
                                "Lunes": 0, "Martes": 1, "Miercoles": 2,
                                "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6
                            }
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
                                sph_target=sph_target
                            )
                            st.success(f"✅ Usuario '{username}' creado con exito!")
                            if st.session_state.github_sync:
                                st.session_state.github_sync.sync_all_data_files()
                        except ValueError as e:
                            st.error(str(e))
        
        else:  # Modo Bulk
            st.info("Pega los datos en formato: `username,password,nombre,id_empleado,team,manager` (uno por linea)")
            
            bulk_text = st.text_area(
                "Datos de usuarios:",
                placeholder="agente01,pass123,Nombre Apellido,1469,Equipo A,super01\nagente02,pass456,Otro Nombre,1470,Equipo B,super02",
                height=150
            )
            
            # Configuracion comun para todos
            st.markdown("---")
            st.write("⚙️ Configuracion para TODOS los agentes:")
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                bulk_sph = st.number_input("SPH Objetivo", min_value=0.01, max_value=1.0, value=0.06, step=0.01, format="%.2f", key="bulk_sph")
            with col_b2:
                bulk_horas = st.number_input("Horas diarias", min_value=1.0, max_value=8.0, value=6.0, step=0.5, format="%.1f", key="bulk_horas")
            with col_b3:
                bulk_dias = st.multiselect(
                    "Dias laborables",
                    ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"],
                    default=["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"],
                    key="bulk_dias"
                )
            
            col_bh1, col_bh2 = st.columns(2)
            with col_bh1:
                bulk_hora_ini = st.text_input("Hora inicio", value="15:00", key="bulk_ini")
            with col_bh2:
                bulk_hora_fin = st.text_input("Hora fin", value="21:00", key="bulk_fin")
            
            if st.button("🚀 Crear Usuarios en Bloque", use_container_width=True):
                if bulk_text:
                    lines = [l.strip() for l in bulk_text.split('\n') if l.strip()]
                    agents_data = []
                    
                    dias_semana = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}
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
                        if st.session_state.github_sync:
                            st.session_state.github_sync.sync_all_data_files()
    
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
                            new_campaign = st.selectbox(
                                "Campaña", ["CAPTA", "WINBACK"],
                                index=0 if user_data.get('campaign') == 'CAPTA' else 1
                            )
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
                        new_password = st.text_input("Nueva contrasena (dejar vacio para no cambiar)", type="password")
                        
                        if user_data['role'] == 'agent':
                            current_sph = user_data.get('sph_config', {}).get('target', 0.06)
                            new_sph = st.number_input("SPH Objetivo", min_value=0.01, max_value=1.0, value=current_sph, step=0.01, format="%.2f")
                            
                            # Editar horario
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
                            
                            dias_semana = {0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"}
                            current_days = schedule.get('working_days', [0, 1, 2, 3, 4])
                            dias_nombres = [dias_semana[d] for d in current_days if d in dias_semana]
                            new_dias = st.multiselect(
                                "Dias laborables",
                                ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"],
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
                            if new_campaign != user_data.get('campaign'):
                                updates['campaign'] = new_campaign
                            if new_manager != user_data.get('manager'):
                                updates['manager'] = new_manager
                            if new_sph != current_sph:
                                updates['sph_target'] = new_sph
                            
                            dias_map = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}
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
                            if st.session_state.github_sync:
                                st.session_state.github_sync.sync_all_data_files()
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
            'Supervisor': u.get('manager', '')
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
                    if st.session_state.github_sync:
                        st.session_state.github_sync.sync_all_data_files()
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
                if st.session_state.github_sync:
                    st.session_state.github_sync.sync_all_data_files()
                st.rerun()
    
    # =============================================
    # PESTAÑA 4: CAMBIO MASIVO DE CAMPAÑA
    # =============================================
    with tab4:
        st.subheader("Cambiar Campaña en Bloque")
        
        agentes = um.get_all_agents()
        
        col1, col2 = st.columns(2)
        with col1:
            capta_count = len(um.get_agents_by_campaign("CAPTA"))
            st.metric("En CAPTA", capta_count)
        with col2:
            winback_count = len(um.get_agents_by_campaign("WINBACK"))
            st.metric("En WINBACK", winback_count)
        
        st.write("---")
        
        agents_to_move = st.multiselect(
            "Seleccionar agentes a mover:",
            [a['username'] for a in agentes],
            format_func=lambda x: f"{x} ({next((a['campaign'] for a in agentes if a['username'] == x), 'N/A')})"
        )
        
        new_campaign = st.selectbox("Nueva campaña:", ["WINBACK", "CAPTA"])
        
        if agents_to_move and st.button("🔄 Cambiar Campaña", use_container_width=True):
            result = um.change_campaign_bulk(agents_to_move, new_campaign)
            st.success(f"✅ {result['updated']} agentes movidos a {new_campaign}!")
            if st.session_state.github_sync:
                st.session_state.github_sync.sync_all_data_files()
            st.rerun()