# main_app.py
import streamlit as st
import os
import time as _time
import os as _os
from datetime import datetime

# Importar nuestros módulos
from auth.user_manager import UserManager
from core.config import STREAMLIT_CONFIG, USER_ROLES, DEFAULT_CAMPAIGN
from core.github_sync import GitHubSync

# ===========================================
# CONFIGURACIÓN INICIAL DE STREAMLIT
# ===========================================
st.set_page_config(
    page_title=STREAMLIT_CONFIG["page_title"],
    page_icon=STREAMLIT_CONFIG["page_icon"],
    layout=STREAMLIT_CONFIG["layout"],
    initial_sidebar_state=STREAMLIT_CONFIG["initial_sidebar_state"]
)

# ===========================================
# INICIALIZACIÓN DE SERVICIOS
# ===========================================
@st.cache_resource
def init_services():
    """Inicializa los servicios principales de la aplicación."""
    user_manager = UserManager()
    
    # CREAR ADMIN POR DEFECTO SI NO EXISTE
    user_manager.initialize_default_admin()
    
    # Intentar inicializar GitHub Sync (opcional, solo si hay token)
    github_sync = None
    try:
        if "GITHUB_TOKEN" in st.secrets:
            github_sync = GitHubSync(
                token=st.secrets["GITHUB_TOKEN"],
                repo_owner=st.secrets.get("GITHUB_REPO_OWNER", "cosmocws"),
                repo_name=st.secrets.get("GITHUB_REPO_NAME", "zelenza_app_v2")
            )
    except Exception as e:
        st.warning(f"GitHub Sync no configurado: {e}")
    
    return user_manager, github_sync

# ===========================================
# FUNCIONES DE UI
# ===========================================
def login_screen():
    """Pantalla de inicio de sesión."""
    st.title("⚡ Zelenza CEX v2.0")
    st.subheader("Iniciar Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Nombre de usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Contraseña")
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Por favor, completa todos los campos")
                    return
                
                user = st.session_state.user_manager.authenticate(username, password)
                
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    # FORZAR CAMBIO DE CONTRASEÑA SI ES NECESARIO
                    if user.get('force_password_change', False):
                        st.session_state.current_page = "change_password"
                    else:
                        st.session_state.current_page = "home"
                    
                    # Sincronizar datos después del login
                    if st.session_state.github_sync:
                        st.session_state.github_sync.sync_all_data_files()
                    
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

def sidebar_navigation():
    """Barra lateral de navegación según el rol del usuario."""
    with st.sidebar:
        st.title("⚡ Zelenza CEX")
        
        # --- BOTÓN DE REFRESCAR ---
        col_r1, col_r2 = st.columns([3, 1])
        with col_r2:
            if st.button("🔄", help="Refrescar datos", use_container_width=True):
                st.rerun()
        
        st.divider()
        
        user = st.session_state.user
        role = user['role']
        
        # Mostrar información del usuario
        st.write(f"👤 **{user['username']}**")
        st.write(f"📋 Rol: **{USER_ROLES[role]['name']}**")
        
        if role == 'agent' and user.get('campaign'):
            st.write(f"🎯 Campaña: **{user['campaign']}**")
        
        st.divider()
        
        # Navegación común
        pages = ["🏠 Inicio"]
        
        # Páginas específicas por rol
        if role == 'admin':
            pages.extend([
                "👥 Gestión de Usuarios",
                "⚡ Gestión de Planes",
                "👤 Supervisores",
                "⚙️ Configuración"
            ])
        elif role == 'super':
            pages.extend([
                "👥 Mi Equipo",
                "📋 Monitorizaciones",
                "📈 Evolución y Dinámicas"
            ])
        elif role == 'agent':
            pages.extend([
                "📊 Calculadora",
                "🎯 Mis Objetivos",
                "📅 Solicitar Ausencia"
            ])
        
        # Selección de página
        selected_page = st.radio("Navegación", pages, label_visibility="collapsed")
        st.session_state.current_page = selected_page
        
        st.divider()
        
        # Botón de cerrar sesión
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout()
            
        st.divider()
        with st.expander("🔒 Cambiar Contraseña"):
            with st.form("change_password_form"):
                old_password = st.text_input("Contraseña actual", type="password")
                new_password = st.text_input("Nueva contraseña", type="password")
                confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
                
                if st.form_submit_button("Actualizar Contraseña"):
                    if not old_password or not new_password or not confirm_password:
                        st.error("Todos los campos son obligatorios")
                    elif new_password != confirm_password:
                        st.error("Las contraseñas no coinciden")
                    else:
                        # Verificar contraseña actual
                        user_check = st.session_state.user_manager.authenticate(
                            st.session_state.user['username'], 
                            old_password
                        )
                        if user_check:
                            # Actualizar contraseña
                            st.session_state.user_manager.update_user(
                                st.session_state.user['username'],
                                {'password_hash': st.session_state.user_manager._hash_password(new_password)}
                            )
                            st.success("✅ Contraseña actualizada correctamente")
                            if st.session_state.github_sync:
                                st.session_state.github_sync.sync_all_data_files()
                        else:
                            st.error("Contraseña actual incorrecta")
        
        # Estado de sincronización
        if st.session_state.github_sync:
            sync_status = st.session_state.github_sync.get_sync_status()
            with st.expander("🔄 Estado Sync"):
                if sync_status['last_sync']:
                    st.write(f"Última: {sync_status['last_sync']['timestamp'][:19]}")
                    st.write(f"Archivo: {sync_status['last_sync']['file']}")
                else:
                    st.write("Sin sincronizaciones")

def logout():
    """Cierra la sesión del usuario."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def show_home():
    """Página de inicio según el rol."""
    st.title(f"Bienvenido, {st.session_state.user['username']}! 👋")
    
    role = st.session_state.user['role']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Rol", USER_ROLES[role]['name'])
        if role == 'agent':
            st.metric("Campaña", st.session_state.user.get('campaign', 'No asignada'))
            st.metric("Equipo", st.session_state.user.get('team', 'No asignado'))
    
    with col2:
        st.metric("Último Acceso", datetime.now().strftime("%d/%m/%Y %H:%M"))
        if role == 'super':
            agentes = st.session_state.user.get('managed_agents', [])
            st.metric("Agentes Asignados", len(agentes))
    
    st.divider()
    st.info("🚀 Sistema en construcción. Próximamente más funcionalidades.")

def show_under_construction():
    """Página en construcción."""
    st.title("🚧 En Construcción")
    st.info("Esta sección estará disponible próximamente.")

# ===========================================
# APLICACIÓN PRINCIPAL
# ===========================================
def main():
    """Punto de entrada principal de la aplicación."""
    
    # Inicializar servicios si no existen
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager, st.session_state.github_sync = init_services()
    
    # =============================================
    # SINCRONIZACION AUTOMATICA AL INICIAR
    # =============================================
    if 'first_run' not in st.session_state:
        st.session_state.first_run = True
    
    if st.session_state.first_run and st.session_state.github_sync:
        try:
            st.session_state.github_sync.restore_all_data_files()
            st.session_state.first_run = False
        except Exception as e:
            print(f"No se pudieron restaurar datos: {e}")
    
    # Sincronizar periódicamente (cada 5 minutos y solo si hay cambios)
    
    archivo_sync = "data/.last_sync"
    ahora = _time.time()
    
    try:
        with open(archivo_sync, 'r') as f:
            ultima_sync = float(f.read().strip())
    except:
        ultima_sync = 0
    
    # Solo sincronizar cada 5 minutos
    if ahora - ultima_sync > 300:
        if st.session_state.github_sync:
            try:
                st.session_state.github_sync.sync_all_data_files()
                with open(archivo_sync, 'w') as f:
                    f.write(str(ahora))
            except:
                pass
    
    # Verificar si hay sesión activa
    if not st.session_state.get('logged_in', False):
        login_screen()
        return
    
    # Mostrar barra lateral
    sidebar_navigation()
    
    # Router de páginas
    current_page = st.session_state.get('current_page', "🏠 Inicio")
    
    if current_page == "🏠 Inicio":
        role = st.session_state.user['role']
        if role == 'admin':
            from admin.admin_inicio import show_inicio_admin
            show_inicio_admin()
        elif role == 'super':
            from super.super_inicio import show_inicio_super
            show_inicio_super()
        elif role == 'agent':
            from agent.agent_inicio import show_inicio
            show_inicio()
    elif current_page == "👥 Gestión de Usuarios":
        from admin.gestion_usuarios import show_gestion_usuarios
        show_gestion_usuarios()
    elif current_page == "⚡ Gestión de Planes":
        from admin.gestion_planes import gestion_electricidad
        gestion_electricidad()
    elif current_page == "📊 Monitorización":
        show_under_construction()
    elif current_page == "👥 Mi Equipo":
        from super.super_panel import show_mi_equipo
        show_mi_equipo()
    elif current_page == "📋 Monitorizaciones":
        from super.monitorizaciones import show_monitorizaciones
        show_monitorizaciones()
    elif current_page == "👤 Supervisores":
        from admin.admin_supervisores import show_supervisores
        show_supervisores()
    elif current_page == "📈 Evolución y Dinámicas":
        from super.super_evolucion import show_evolucion
        show_evolucion()
    elif current_page == "📊 Calculadora":
        from agent.agent_calculadora import show_calculadora
        show_calculadora()
    elif current_page == "🎯 Mis Objetivos":
        from agent.agent_objetivos import show_objetivos
        show_objetivos()
    elif current_page == "📅 Solicitar Ausencia":
        from agent.agent_ausencias import show_ausencias
        show_ausencias()
    elif current_page == "⚙️ Configuración":
        from admin.admin_configuracion import show_configuracion
        show_configuracion()

# ===========================================
# EJECUCIÓN
# ===========================================
if __name__ == "__main__":
    main()
