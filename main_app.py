# main_app.py
import streamlit as st
import os
from datetime import datetime

# Importar nuestros modulos
from auth.user_manager import UserManager
from core.config import STREAMLIT_CONFIG, USER_ROLES, DEFAULT_CAMPAIGN
from core.github_sync import GitHubSync

# ===========================================
# CONFIGURACION INICIAL DE STREAMLIT
# ===========================================
st.set_page_config(
    page_title=STREAMLIT_CONFIG["page_title"],
    page_icon=STREAMLIT_CONFIG["page_icon"],
    layout=STREAMLIT_CONFIG["layout"],
    initial_sidebar_state=STREAMLIT_CONFIG["initial_sidebar_state"]
)

# ===========================================
# INICIALIZACION DE SERVICIOS
# ===========================================
@st.cache_resource
def init_services():
    """Inicializa los servicios principales de la aplicacion."""
    user_manager = UserManager()
    user_manager.initialize_default_admin()
    
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
    """Pantalla de inicio de sesion."""
    st.title("⚡ Zelenza CEX v2.0")
    st.subheader("Iniciar Sesion")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Nombre de usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Contraseña")
            submit = st.form_submit_button("Iniciar Sesion", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Por favor, completa todos los campos")
                    return
                
                user = st.session_state.user_manager.authenticate(username, password)
                
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    
                    if user.get('force_password_change', False):
                        st.session_state.current_page = "change_password"
                    else:
                        st.session_state.current_page = "home"
                    
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

def sidebar_navigation():
    """Barra lateral de navegacion segun el rol del usuario."""
    with st.sidebar:
        st.title("⚡ Zelenza CEX")
        
        # Boton de refrescar
        col_r1, col_r2 = st.columns([3, 1])
        with col_r2:
            if st.button("🔄", help="Refrescar datos", use_container_width=True):
                st.rerun()
        
        st.divider()
        
        user = st.session_state.user
        role = user['role']
        
        st.write(f"👤 **{user['username']}**")
        st.write(f"📋 Rol: **{USER_ROLES[role]['name']}**")
        
        if role == 'agent' and user.get('campaign'):
            st.write(f"🎯 Campaña: **{user['campaign']}**")
        
        st.divider()
        
        pages = ["🏠 Inicio"]
        
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
        
        selected_page = st.radio("Navegacion", pages, label_visibility="collapsed")
        st.session_state.current_page = selected_page
        
        st.divider()
        
        if st.button("🚪 Cerrar Sesion", use_container_width=True):
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
                        user_check = st.session_state.user_manager.authenticate(
                            st.session_state.user['username'], 
                            old_password
                        )
                        if user_check:
                            st.session_state.user_manager.update_user(
                                st.session_state.user['username'],
                                {'password_hash': st.session_state.user_manager._hash_password(new_password)}
                            )
                            st.success("✅ Contraseña actualizada correctamente")
                            from core.github_sync import sync_archivo
                            sync_archivo("data/users.json")
                        else:
                            st.error("Contraseña actual incorrecta")
        
        # Estado Sync (SOLO ADMIN)
        if role == 'admin':
            with st.expander("🔄 Estado Sync"):
                gs = st.session_state.get('github_sync')
                if gs:
                    status = gs.get_sync_status()
                    if status['last_sync']:
                        st.write(f"Ultima: {status['last_sync']['time'][:19]}")
                        st.write(f"Archivo: {status['last_sync']['file']}")
                    st.write(f"Total: {status['total_syncs']}")
                else:
                    st.write("Sync no configurado")

def logout():
    """Cierra la sesion del usuario."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def show_under_construction():
    st.title("🚧 En Construccion")
    st.info("Esta seccion estara disponible proximamente.")

# ===========================================
# APLICACION PRINCIPAL
# ===========================================
def main():
    """Punto de entrada principal de la aplicacion."""
    
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager, st.session_state.github_sync = init_services()
    
    if not st.session_state.get('logged_in', False):
        login_screen()
        return
    
    sidebar_navigation()
    
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
# EJECUCION
# ===========================================
if __name__ == "__main__":
    main()