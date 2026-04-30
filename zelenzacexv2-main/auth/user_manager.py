# auth/user_manager.py
import json
import os
import hashlib
from typing import Optional, List, Dict
from datetime import datetime, timedelta

class UserManager:
    VALID_ROLES = ["agent", "super", "admin", "datos"]
    VALID_CAMPAIGNS = ["CAPTA", "WINBACK"]
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_users(self) -> List[Dict]:
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_users(self, users: List[Dict]):
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        from core.github_sync import sync_archivo
        sync_archivo(self.users_file)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_default_schedule(start_time: str = "15:00", end_time: str = "21:00",
                                working_days: List[int] = None) -> Dict:
        if working_days is None:
            working_days = [0, 1, 2, 3, 4]
        return {
            "start_time": start_time,
            "end_time": end_time,
            "working_days": working_days,
            "daily_hours": UserManager._calculate_daily_hours(start_time, end_time),
            "weekly_hours": UserManager._calculate_weekly_hours(start_time, end_time, working_days),
            "type": "full_time"
        }
    
    @staticmethod
    def _calculate_daily_hours(start_time: str, end_time: str) -> float:
        try:
            start = datetime.strptime(start_time, "%H:%M")
            end = datetime.strptime(end_time, "%H:%M")
            if end <= start:
                end += timedelta(days=1)
            return round((end - start).seconds / 3600, 2)
        except ValueError:
            return 6.0
    
    @staticmethod
    def _calculate_weekly_hours(start_time: str, end_time: str, working_days: List[int]) -> float:
        daily = UserManager._calculate_daily_hours(start_time, end_time)
        return round(daily * len(working_days), 2)
    
    def initialize_default_admin(self):
        users = self._load_users()
        if any(u['role'] == 'admin' for u in users):
            return
        default_admin = {
            "username": "admin",
            "password_hash": self._hash_password("Zelenza2026!"),
            "role": "admin",
            "nombre": "Administrador",
            "id_empleado": "",
            "campaign": None,
            "team": "Administracion",
            "manager": None,
            "schedule": self.create_default_schedule("09:00", "18:00"),
            "managed_agents": [],
            "sph_config": None,
            "incorporation_date": datetime.now().strftime('%Y-%m-%d'),
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        users.append(default_admin)
        self._save_users(users)
    
    def create_user(self, username: str, password: str, role: str = "agent",
                    nombre: str = "", id_empleado: str = "",
                    campaign: str = "CAPTA", team: str = "Sin equipo",
                    manager: Optional[str] = None, schedule: Optional[Dict] = None,
                    sph_target: float = 0.06) -> Dict:
        if role not in self.VALID_ROLES:
            raise ValueError(f"Rol '{role}' no valido")
        users = self._load_users()
        if any(u['username'] == username for u in users):
            raise ValueError(f"El usuario '{username}' ya existe")
        if schedule is None:
            schedule = self.create_default_schedule()
        
        hoy = datetime.now().strftime('%Y-%m-%d')
        
        new_user = {
            "username": username,
            "password_hash": self._hash_password(password),
            "role": role,
            "nombre": nombre,
            "id_empleado": id_empleado,
            "campaign": campaign if role == "agent" else None,
            "team": team,
            "manager": manager,
            "schedule": schedule,
            "managed_agents": [] if role == "super" else [],
            "sph_config": {
                "target": sph_target,
                "enabled": True,
                "start_date": hoy,
                "history": [{"target": sph_target, "set_at": datetime.now().isoformat()}]
            } if role == "agent" else None,
            "incorporation_date": hoy,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "standby": False,
            "usuario_padre": None
        }
        if manager:
            for u in users:
                if u['username'] == manager and u['role'] == 'super':
                    if 'managed_agents' not in u:
                        u['managed_agents'] = []
                    u['managed_agents'].append(username)
        users.append(new_user)
        self._save_users(users)
        return new_user
    
    def get_user(self, username: str) -> Optional[Dict]:
        users = self._load_users()
        for user in users:
            if user['username'] == username:
                return user
        return None
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        users = self._load_users()
        hashed = self._hash_password(password)
        for user in users:
            if user['username'] == username and user['password_hash'] == hashed:
                user['last_login'] = datetime.now().isoformat()
                self._save_users(users)
                user_copy = user.copy()
                del user_copy['password_hash']
                return user_copy
        return None
    
    def update_user(self, username: str, updates: Dict) -> bool:
        users = self._load_users()
        for user in users:
            if user['username'] == username:
                if 'schedule' in updates and isinstance(updates['schedule'], dict):
                    s = updates['schedule']
                    if 'start_time' in s and 'end_time' in s:
                        s['daily_hours'] = self._calculate_daily_hours(s['start_time'], s['end_time'])
                        s['weekly_hours'] = self._calculate_weekly_hours(s['start_time'], s['end_time'], s.get('working_days', [0,1,2,3,4]))
                if 'sph_target' in updates:
                    if 'sph_config' not in user:
                        user['sph_config'] = {'history': []}
                    user['sph_config']['target'] = updates.pop('sph_target')
                    user['sph_config']['history'].append({"target": user['sph_config']['target'], "set_at": datetime.now().isoformat()})
                user.update(updates)
                self._save_users(users)
                return True
        return False
    
    def delete_user(self, username: str) -> bool:
        users = self._load_users()
        user_to_delete = next((u for u in users if u['username'] == username), None)
        if not user_to_delete:
            return False
        if user_to_delete['role'] == 'super':
            for u in users:
                if u.get('manager') == username:
                    u['manager'] = None
        if user_to_delete.get('manager'):
            for u in users:
                if u['username'] == user_to_delete['manager']:
                    if username in u.get('managed_agents', []):
                        u['managed_agents'].remove(username)
        users = [u for u in users if u['username'] != username]
        self._save_users(users)
        return True
    
    def delete_agents_bulk(self, usernames: List[str]) -> Dict:
        users = self._load_users()
        deleted = []
        errors = []
        to_delete_set = set(usernames)
        for username in usernames:
            user = next((u for u in users if u['username'] == username), None)
            if user:
                if user.get('manager'):
                    for u in users:
                        if u['username'] == user['manager']:
                            if username in u.get('managed_agents', []):
                                u['managed_agents'].remove(username)
                deleted.append(username)
            else:
                errors.append(f"Usuario '{username}' no encontrado")
        users = [u for u in users if u['username'] not in to_delete_set]
        self._save_users(users)
        return {"deleted": len(deleted), "errors": errors, "deleted_users": deleted}
    
    def create_agents_bulk(self, agents_data: List[Dict]) -> Dict:
        users = self._load_users()
        existing_usernames = {u['username'] for u in users}
        created = []
        errors = []
        hoy = datetime.now().strftime('%Y-%m-%d')
        for agent in agents_data:
            username = agent['username']
            if username in existing_usernames:
                errors.append(f"Usuario '{username}' ya existe")
                continue
            if not agent.get('password'):
                errors.append(f"Contrasena requerida para '{username}'")
                continue
            schedule = agent.get('schedule', self.create_default_schedule())
            sph_target = agent.get('sph_target', 0.06)
            new_user = {
                "username": username,
                "password_hash": self._hash_password(agent['password']),
                "role": "agent",
                "nombre": agent.get('nombre', ''),
                "id_empleado": agent.get('id_empleado', ''),
                "campaign": "CAPTA",
                "team": agent.get('team', 'Sin equipo'),
                "manager": agent.get('manager'),
                "schedule": schedule,
                "managed_agents": [],
                "sph_config": {
                    "target": sph_target, "enabled": True, "start_date": hoy,
                    "history": [{"target": sph_target, "set_at": datetime.now().isoformat()}]
                },
                "incorporation_date": hoy,
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "standby": False,
                "usuario_padre": None
            }
            if agent.get('manager'):
                for u in users:
                    if u['username'] == agent['manager'] and u['role'] == 'super':
                        if 'managed_agents' not in u:
                            u['managed_agents'] = []
                        u['managed_agents'].append(username)
            users.append(new_user)
            created.append(username)
            existing_usernames.add(username)
        self._save_users(users)
        return {"created": len(created), "errors": errors}
    
    # =============================================
    # SISTEMA W (WINBACK)
    # =============================================
    
    def mover_a_winback(self, username: str) -> Dict:
        """Crea el usuario W+username en WINBACK y pone el original en standby."""
        users = self._load_users()
        original = next((u for u in users if u['username'] == username), None)
        if not original:
            return {"success": False, "error": "Usuario no encontrado"}
        if original['role'] != 'agent':
            return {"success": False, "error": "Solo se puede mover agentes"}
        if original.get('campaign') == 'WINBACK':
            return {"success": False, "error": "Ya esta en WINBACK"}
        
        w_username = f"W{username}"
        if any(u['username'] == w_username for u in users):
            return {"success": False, "error": f"El usuario {w_username} ya existe"}
        
        # Poner original en standby
        original['standby'] = True
        
        # Crear usuario W
        hoy = datetime.now().strftime('%Y-%m-%d')
        nuevo_w = {
            "username": w_username,
            "password_hash": original['password_hash'],
            "role": "agent",
            "nombre": original.get('nombre', ''),
            "id_empleado": original.get('id_empleado', ''),
            "campaign": "WINBACK",
            "team": original.get('team', 'Sin equipo'),
            "manager": original.get('manager'),
            "schedule": original.get('schedule', self.create_default_schedule()),
            "managed_agents": [],
            "sph_config": {
                "target": 0.06, "enabled": True, "start_date": hoy,
                "history": [{"target": 0.06, "set_at": datetime.now().isoformat()}]
            },
            "incorporation_date": hoy,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "standby": False,
            "usuario_padre": username
        }
        users.append(nuevo_w)
        
        # Añadir al supervisor
        if original.get('manager'):
            for u in users:
                if u['username'] == original['manager'] and u['role'] == 'super':
                    if 'managed_agents' not in u:
                        u['managed_agents'] = []
                    u['managed_agents'].append(w_username)
        
        self._save_users(users)
        return {"success": True, "w_username": w_username}
    
    def reactivar_de_winback(self, w_username: str) -> Dict:
        """Reactiva el usuario original desde WINBACK y pone W en standby."""
        if not w_username.startswith('W'):
            return {"success": False, "error": "El usuario no es W (WINBACK)"}
        
        users = self._load_users()
        w_user = next((u for u in users if u['username'] == w_username), None)
        if not w_user:
            return {"success": False, "error": "Usuario W no encontrado"}
        
        original_username = w_user.get('usuario_padre', w_username[1:])
        original = next((u for u in users if u['username'] == original_username), None)
        if not original:
            return {"success": False, "error": f"Usuario original {original_username} no encontrado"}
        
        # Poner W en standby, reactivar original
        w_user['standby'] = True
        original['standby'] = False
        original['campaign'] = 'CAPTA'
        
        self._save_users(users)
        return {"success": True, "original": original_username}
    
    def get_usuarios_activos(self) -> List[Dict]:
        """Devuelve solo usuarios NO en standby."""
        users = self._load_users()
        return [u for u in users if not u.get('standby', False)]
    
    def get_users_by_role(self, role: str) -> List[Dict]:
        users = self._load_users()
        return [u for u in users if u['role'] == role]
    
    def get_agents_by_campaign(self, campaign: str) -> List[Dict]:
        users = self._load_users()
        return [u for u in users if u['role'] == 'agent' and u.get('campaign') == campaign]
    
    def get_agents_by_manager(self, manager_username: str) -> List[Dict]:
        users = self._load_users()
        return [u for u in users if u.get('manager') == manager_username]
    
    def get_all_agents(self) -> List[Dict]:
        return self.get_users_by_role("agent")
    
    def change_campaign_bulk(self, usernames: List[str], new_campaign: str) -> Dict:
        """Ya no se usa - reemplazado por mover_a_winback"""
        return {"updated": 0, "errors": ["Usa mover_a_winback en su lugar"], "updated_users": []}