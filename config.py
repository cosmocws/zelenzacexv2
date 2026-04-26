# config.py
"""
Configuracion central de la aplicacion Zelenza CEX v2.
"""

# ===========================================
# CONFIGURACION DE CAMPAÑAS
# ===========================================
CAMPAIGNS = {
    "CAPTA": {
        "name": "CAPTA",
        "description": "Captacion de nuevos clientes",
        "is_default": True
    },
    "WINBACK": {
        "name": "WINBACK",
        "description": "Recuperacion de clientes",
        "is_default": False
    }
}

DEFAULT_CAMPAIGN = "CAPTA"

# ===========================================
# CONFIGURACION DE SPH
# ===========================================
SPH_CONFIG = {
    "default_target": 0.06,
    "calculation_factor": 0.83,
    "rounding_threshold": 0.51,
    "ramp_up_months": 3
}

# ===========================================
# CONFIGURACION DE HORARIOS
# ===========================================
DEFAULT_SCHEDULE = {
    "start_time": "15:00",
    "end_time": "21:00",
    "working_days": [0, 1, 2, 3, 4],
    "daily_hours": 6.0,
    "weekly_hours": 30.0,
    "type": "full_time"
}

SCHEDULE_TYPES = ["full_time", "reduced", "extended"]

# ===========================================
# ROLES DE USUARIO
# ===========================================
USER_ROLES = {
    "agent": {
        "name": "Agente",
        "permissions": ["view_own_data", "request_absence", "view_schedule"]
    },
    "super": {
        "name": "Supervisor",
        "permissions": ["view_team", "manage_schedules", "approve_absences", "view_sph"]
    },
    "admin": {
        "name": "Administrador",
        "permissions": ["manage_users", "manage_campaigns", "view_all", "system_config"]
    }
}

# ===========================================
# CONFIGURACION DE STREAMLIT
# ===========================================
STREAMLIT_CONFIG = {
    "page_title": "Zelenza CEX v2.0",
    "page_icon": "⚡",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ===========================================
# CONFIGURACION DE SINCRONIZACION
# ===========================================
SYNC_CONFIG = {
    "auto_sync_enabled": True,
    "json_files": [
        "users.json",
        "registro_diario.json",
        "puntos_agentes.json",
        "monitorizaciones.json",
        "config_precios.json",
        "config_puntos_super.json",
        "porras_ventas.json"
    ],
    "csv_files": [
        "precios_luz.csv"
    ]
}
