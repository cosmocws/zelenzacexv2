# core/github_sync.py
import json
import os
import requests
import base64
import os as _os
import hashlib as _hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional

class GitHubSync:
    """
    Sincroniza automáticamente los archivos JSON modificados con GitHub.
    Garantiza que los datos de Streamlit Cloud persistan entre reinicios.
    """
    
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
    
    def sync_file(self, local_path: str, commit_message: Optional[str] = None) -> bool:
        """
        Sincroniza un archivo local con GitHub.
        
        Args:
            local_path: Ruta del archivo local a sincronizar
            commit_message: Mensaje del commit (opcional)
        
        Returns:
            True si la sincronización fue exitosa
        """
        try:
            if not os.path.exists(local_path):
                print(f"Archivo no encontrado: {local_path}")
                return False
            
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Normalizar la ruta para GitHub
            file_path = local_path.replace('\\', '/')
            
            # Intentar obtener el archivo actual de GitHub
            existing_sha = self._get_file_sha(file_path)
            
            # Preparar el contenido para GitHub
            content_bytes = content.encode('utf-8')
            content_base64 = base64.b64encode(content_bytes).decode('utf-8')
            
            # Preparar el payload
            payload = {
                "message": commit_message or f"Auto-sync: {datetime.now().isoformat()}",
                "content": content_base64,
                "branch": self.branch
            }
            
            if existing_sha:
                payload["sha"] = existing_sha
            
            # Hacer la petición a GitHub
            url = f"{self.base_url}/contents/{file_path}"
            
            if existing_sha:
                response = requests.put(url, headers=self.headers, json=payload)
            else:
                response = requests.put(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                self.sync_log.append({
                    "file": file_path,
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "commit": response.json().get('commit', {}).get('sha', 'unknown')
                })
                print(f"✅ Sincronizado: {file_path}")
                return True
            else:
                print(f"❌ Error sincronizando {file_path}: {response.status_code}")
                print(f"Respuesta: {response.json()}")
                return False
        
        except Exception as e:
            print(f"❌ Excepción sincronizando {file_path}: {e}")
            return False
    
    def sync_multiple_files(self, file_paths: list, commit_message: Optional[str] = None) -> Dict:
        """
        Sincroniza múltiples archivos de una vez.
        
        Returns:
            Diccionario con el resumen de la operación
        """
        results = {"success": [], "failed": []}
        
        for path in file_paths:
            if self.sync_file(path, commit_message):
                results["success"].append(path)
            else:
                results["failed"].append(path)
        
        return results
    
    def sync_all_data_files(self, data_dir: str = "data") -> Dict:
        """
        Sincroniza todos los archivos JSON del directorio de datos.
        Este es el método que más usarás.
        """
        if not os.path.exists(data_dir):
            return {"success": [], "failed": []}
        
        json_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.json')]
        return self.sync_multiple_files(json_files, f"Auto-sync all data: {datetime.now().isoformat()}")
    
    def restore_file(self, file_path: str) -> bool:
        """
        Restaura un archivo desde GitHub al sistema local.
        Útil cuando Streamlit Cloud se reinicia y se pierden los datos.
        """
        try:
            sha = self._get_file_sha(file_path)
            if not sha:
                print(f"Archivo no encontrado en GitHub: {file_path}")
                return False
            
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                content_base64 = response.json()['content']
                content_bytes = base64.b64decode(content_base64)
                
                # Asegurar que el directorio existe
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    f.write(content_bytes)
                
                print(f"✅ Restaurado desde GitHub: {file_path}")
                return True
            else:
                print(f"❌ Error restaurando {file_path}")
                return False
        except Exception as e:
            print(f"❌ Excepción restaurando {file_path}: {e}")
            return False
    
    def restore_all_data_files(self, data_dir: str = "data") -> Dict:
        """Restaura todos los archivos de datos desde GitHub."""
        # Listar archivos en el repositorio
        url = f"{self.base_url}/contents/{data_dir}"
        response = requests.get(url, headers=self.headers)
        
        results = {"success": [], "failed": []}
        
        if response.status_code == 200:
            for item in response.json():
                if item['type'] == 'file' and item['name'].endswith('.json'):
                    file_path = f"{data_dir}/{item['name']}"
                    if self.restore_file(file_path):
                        results["success"].append(file_path)
                    else:
                        results["failed"].append(file_path)
        
        return results
    
    def _get_file_sha(self, file_path: str) -> Optional[str]:
        """Obtiene el SHA de un archivo en GitHub."""
        url = f"{self.base_url}/contents/{file_path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json().get('sha')
        return None
    
    def get_sync_status(self) -> Dict:
        """Devuelve el estado actual de las sincronizaciones."""
        return {
            "last_sync": self.sync_log[-1] if self.sync_log else None,
            "total_syncs": len(self.sync_log),
            "recent_syncs": self.sync_log[-5:]
        }


# Decorador para sincronización automática después de operaciones
def auto_sync_github(github_sync_instance):
    """
    Decorador para sincronizar automáticamente después de modificar datos.
    
    Uso:
        @auto_sync_github(github_sync)
        def crear_usuario():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            github_sync_instance.sync_all_data_files()
            return result
        return wrapper
    return decorator
    
# =============================================
# SINCRONIZACION AUTOMATICA
# =============================================
def sincronizar_si_cambio(data_dir: str = "data"):
    """
    Comprueba si algun archivo JSON en data/ ha cambiado y sincroniza.
    """
    import streamlit as st
    
    if not st.session_state.get('github_sync'):
        return
    
    if 'hash_archivos' not in st.session_state:
        st.session_state.hash_archivos = {}
    
    archivos_json = [f for f in _os.listdir(data_dir) if f.endswith('.json')]
    algo_cambio = False
    
    for archivo in archivos_json:
        ruta = _os.path.join(data_dir, archivo)
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            hash_actual = _hashlib.md5(contenido.encode()).hexdigest()
            
            if archivo not in st.session_state.hash_archivos:
                st.session_state.hash_archivos[archivo] = hash_actual
            elif st.session_state.hash_archivos[archivo] != hash_actual:
                algo_cambio = True
                st.session_state.hash_archivos[archivo] = hash_actual
        except:
            pass
    
    if algo_cambio:
        try:
            st.session_state.github_sync.sync_all_data_files(data_dir)
        except Exception as e:
            print(f"Error en auto-sync: {e}")