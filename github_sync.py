# core/github_sync.py
import os
import json
import time
import requests
import base64
import hashlib
from datetime import datetime
from typing import Dict, Optional

class GitHubSync:
    """Sincroniza archivos individuales con GitHub."""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str, branch: str = "main"):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.sync_log = []
    
    def _get_file_sha(self, file_path: str) -> Optional[str]:
        try:
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('sha')
        except:
            pass
        return None
    
    def upload_file(self, local_path: str, commit_message: str = None) -> tuple:
        """Sube UN archivo a GitHub. Retorna (exito, mensaje)."""
        try:
            if not os.path.exists(local_path):
                return False, f"No existe: {local_path}"
            
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_path = local_path.replace('\\', '/')
            existing_sha = self._get_file_sha(file_path)
            
            content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            payload = {
                "message": commit_message or f"Sync: {datetime.now().isoformat()}",
                "content": content_base64,
                "branch": self.branch
            }
            if existing_sha:
                payload["sha"] = existing_sha
            
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.put(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                self.sync_log.append({
                    "file": file_path,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                })
                return True, f"{os.path.basename(local_path)}"
            else:
                return False, f"Error {response.status_code}"
        
        except Exception as e:
            return False, str(e)[:100]
    
    def test_connection(self) -> tuple:
        """Prueba la conexion con GitHub."""
        try:
            url = f"{self.base_url}/contents/data"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200, "OK" if response.status_code == 200 else f"Error {response.status_code}"
        except Exception as e:
            return False, str(e)[:100]
    
    def get_sync_status(self) -> Dict:
        return {
            "last_sync": self.sync_log[-1] if self.sync_log else None,
            "total_syncs": len(self.sync_log),
            "recent_syncs": self.sync_log[-5:]
        }


class DataSyncManager:
    """Detecta cambios y sincroniza SOLO archivos modificados."""
    
    def __init__(self, github_sync: GitHubSync, data_dir: str = "data"):
        self.github_sync = github_sync
        self.data_dir = data_dir
        self.last_modified_times = {}
        self.last_sync_time = None
        self.sync_interval = 300  # 5 minutos entre syncs
    
    def _get_all_files(self) -> list:
        """Obtiene todos los archivos JSON y CSV en data/"""
        files = []
        if os.path.exists(self.data_dir):
            for f in os.listdir(self.data_dir):
                if (f.endswith('.json') or f.endswith('.csv')) and not f.startswith('.'):
                    files.append(os.path.join(self.data_dir, f))
        return files
    
    def check_for_changes(self) -> list:
        """Devuelve lista de archivos que cambiaron desde la ultima sincronizacion."""
        changed = []
        for file_path in self._get_all_files():
            if os.path.exists(file_path):
                current_mtime = os.path.getmtime(file_path)
                last_mtime = self.last_modified_times.get(file_path, 0)
                
                if current_mtime > last_mtime:
                    changed.append(file_path)
                    self.last_modified_times[file_path] = current_mtime
        
        return changed
    
    def sync_if_changed(self) -> tuple:
        """Sincroniza si hay cambios y ha pasado el intervalo. Retorna (exitos, total, mensajes)."""
        if self.github_sync is None:
            return 0, 0, ["GitHub no configurado"]
        
        # Respetar intervalo
        ahora = time.time()
        if self.last_sync_time and (ahora - self.last_sync_time) < self.sync_interval:
            return 0, 0, []
        
        changed_files = self.check_for_changes()
        if not changed_files:
            return 0, 0, []
        
        # Probar conexion primero
        test_ok, _ = self.github_sync.test_connection()
        if not test_ok:
            return 0, len(changed_files), ["Sin conexion a GitHub"]
        
        results = []
        success_count = 0
        
        for file_path in changed_files:
            ok, msg = self.github_sync.upload_file(file_path)
            results.append(msg)
            if ok:
                success_count += 1
        
        self.last_sync_time = ahora
        return success_count, len(changed_files), results
    
    def get_status(self) -> Dict:
        """Estado actual de la sincronizacion."""
        changed = self.check_for_changes()
        return {
            "last_sync": self.last_sync_time,
            "changed_files": [os.path.basename(f) for f in changed],
            "total_synced": len(self.github_sync.sync_log) if self.github_sync else 0,
            "github_available": self.github_sync is not None
        }


def init_sync_manager(github_sync: GitHubSync) -> DataSyncManager:
    """Inicializa el gestor de sincronizacion."""
    return DataSyncManager(github_sync)
