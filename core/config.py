# core/config.py
"""
Configuración central de la aplicación Zelenza v2.
Todas las constantes y configuraciones en un solo lugar.
"""

# ===========================================
# CONFIGURACIÓN DE CAMPAÑAS
# ===========================================
CAMPAIGNS = {
    "CAPTA": {
        "name": "CAPTA",
        "description": "Campaña de captación de nuevos clientes",
        "is_default": True
    },
    "WINBACK": {
        "name": "WINBACK",
        "description": "Campaña de recuperación de clientes",
        "is_default": False
    }
}

DEFAULT_CAMPAIGN = "CAPTA"

# ===========================================
# CONFIGURACIÓN DE SPH
# ===========================================
SPH_CONFIG = {
    "default_target": 0.06,        # SPH para agentes noveles
    "calculation_factor": 0.83,    # Factor de ajuste para horas efectivas
    "rounding_threshold": 0.51,    # Umbral para redondeo de ventas
    "ramp_up_months": 3            # Meses hasta alcanzar SPH completo
}

# ===========================================
# CONFIGURACIÓN DE HORARIOS
# ===========================================
DEFAULT_SCHEDULE = {
    "start_time": "15:00",
    "end_time": "21:00",
    "working_days": [0, 1, 2, 3, 4],  # 0=Lunes, 4=Viernes
    "daily_hours": 6.0,
    "weekly_hours": 30.0,
    "type": "full_time"
}

# Tipos de jornada permitidos
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
# CONFIGURACIÓN DE AUSENCIAS
# ===========================================
ABSENCE_TYPES = ["vacation", "sick_leave", "personal", "training", "other"]

ABSENCE_STATUS = ["pending", "approved", "rejected"]

# ===========================================
# CONFIGURACIÓN DE STREAMLIT
# ===========================================
STREAMLIT_CONFIG = {
    "page_title": "Zelenza CEX v2.0",
    "page_icon": "⚡",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ===========================================
# CONFIGURACIÓN DE SINCRONIZACIÓN
# ===========================================
SYNC_CONFIG = {
    "auto_sync_enabled": True,
    "sync_interval_minutes": 30,
    "data_files": ["users.json", "absences.json", "targets.json"],
    "backup_before_sync": True
}

# ===========================================
# CONSTANTES DE NEGOCIO
# ===========================================
BUSINESS_CONFIG = {
    "company_name": "Zelenza CEX",
    "default_currency": "EUR",
    "commission_base": 10.0,  # Base de comisión por venta en €
    "min_daily_hours": 4.0,
    "max_daily_hours": 8.0
}